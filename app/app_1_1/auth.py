# coding:utf-8
#验证和注册接口
import hashlib
import random
import time

from flask import request, jsonify, g, current_app

from app.model import User, db_session
from . import api
from .decorators import login_check
from .util import message_validate


@api.route('/login', methods=['POST'])
def login():
    phone_number = request.get_json().get('phone_number')
    encryption_str = request.get_json().get('encryption_str')
    random_str = request.get_json().get('random_str')
    time_stamp = request.get_json().get('time_stamp')
    user = User.query.filter_by(phone_number=phone_number).first()

    if not user:
        return jsonify({'code': 0, 'message': '没有此用户'})

    password_in_sql = user.password

    s = hashlib.sha256()
    s.update(password_in_sql)
    s.update(random_str)
    s.update(time_stamp)
    server_encryption_str = s.hexdigest()

    if server_encryption_str != encryption_str:
        return jsonify({'code': 0, 'message': '密码错误'})

    m = hashlib.md5()
    m.update(phone_number)
    m.update(user.password)
    m.update(str(int(time.time())))
    token = m.hexdigest()

    pipeline = current_app.redis.pipeline()
    pipeline.hmset('user:%s' % user.phone_number, {'token': token, 'nickname': user.nickname, 'app_online': 1})
    pipeline.set('token:%s' % token, user.phone_number)
    pipeline.expire('token:%s' % token, 3600*24*30)
    pipeline.execute()

    return jsonify({'code': 1, 'message': '成功登录', 'nickname': user.nickname, 'token': token})


@api.route('/user')
@login_check
def user():
    user = g.current_user

    nickname = current_app.redis.hget('user:%s' % user.phone_number, 'nickname')
    return jsonify({'code': 1, 'nickname': nickname, 'phone_number': user.phone_number})


@api.route('/logout')
@login_check
def logout():
    user = g.current_user

    pipeline = current_app.redis.pipeline()
    pipeline.delete('token:%s' % g.token)
    pipeline.hmset('user:%s' % user.phone_number, {'app_online': 0})
    pipeline.execute()
    return jsonify({'code': 1, 'message': '成功注销'})


@api.route('/set-head-picture', methods=['POST'])
@login_check
def set_head_picture():
    head_picture = request.get_json().get('head_picture')
    user = g.current_user
    user.head_picture = head_picture
    try:
        db_session.commit()
    except Exception as e:
        print e
        db_session.rollback()
        return jsonify({'code': 0, 'message': '未能成功上传'})
    current_app.redis.hset('user:%s' % user.phone_number, 'head_picture', head_picture)
    return jsonify({'code': 1, 'message': '成功上传'})


@api.route('/register-step-1', methods=['POST'])
def register_step_1():
    """
    接受phone_number,发送短信
    """
    phone_number = request.get_json().get('phone_number')
    user = User.query.filter_by(phone_number=phone_number).first()

    if user:
        return jsonify({'code': 0, 'message': '该用户已经存在,注册失败'})
    validate_number = str(random.randint(100000, 1000000))
    result, err_message = message_validate(phone_number, validate_number)

    if not result:
        return jsonify({'code': 0, 'message': err_message})

    pipeline = current_app.redis.pipeline()
    pipeline.set('validate:%s' % phone_number, validate_number)
    pipeline.expire('validate:%s' % phone_number, 60)
    pipeline.execute()

    return jsonify({'code': 1, 'message': '发送成功'})


@api.route('/register-step-2', methods=['POST'])
def register_step_2():
    """
    验证短信接口
    """
    phone_number = request.get_json().get('phone_number')
    validate_number = request.get_json().get('validate_number')
    validate_number_in_redis = current_app.redis.get('validate:%s' % phone_number)

    if validate_number != validate_number_in_redis:
        return jsonify({'code': 0, 'message': '验证没有通过'})

    pipe_line = current_app.redis.pipeline()
    pipe_line.set('is_validate:%s' % phone_number, '1')
    pipe_line.expire('is_validate:%s' % phone_number, 120)
    pipe_line.execute()

    return jsonify({'code': 1, 'message': '短信验证通过'})


@api.route('/register-step-3', methods=['POST'])
def register_step_3():
    """
    密码提交
    """
    phone_number = request.get_json().get('phone_number')
    password = request.get_json().get('password')
    password_confirm = request.get_json().get('password_confirm')

    if len(password) < 7 or len(password) > 30:
        # 这边可以自己拓展条件
        return jsonify({'code': 0, 'message': '密码长度不符合要求'})

    if password != password_confirm:
        return jsonify({'code': 0, 'message': '密码和密码确认不一致'})

    is_validate = current_app.redis.get('is_validate:%s' % phone_number)

    if is_validate != '1':
        return jsonify({'code': 0, 'message': '验证码没有通过'})

    pipeline = current_app.redis.pipeline()
    pipeline.hset('register:%s' % phone_number, 'password', password)
    pipeline.expire('register:%s' % phone_number, 120)
    pipeline.execute()

    return jsonify({'code': 1, 'message': '提交密码成功'})


@api.route('/register-step-4', methods=['POST'])
def register_step_4():
    """
    基本资料提交
    """
    phone_number = request.get_json().get('phone_number')
    nickname = request.get_json().get('nickname')

    is_validate = current_app.redis.get('is_validate:%s' % phone_number)

    if is_validate != '1':
        return jsonify({'code': 0, 'message': '验证码没有通过'})

    password = current_app.redis.hget('register:%s' % phone_number, 'password')

    new_user = User(phone_number=phone_number, password=password, nickname=nickname)
    db_session.add(new_user)

    try:
        db_session.commit()
    except Exception as e:
        print e
        db_session.rollback()
        return jsonify({'code': 0, 'message': '注册失败'})
    finally:
        current_app.redis.delete('is_validate:%s' % phone_number)
        current_app.redis.delete('register:%s' % phone_number)

    return jsonify({'code': 1, 'message': '注册成功'})