# coding:utf-8
from flask import Flask, request, jsonify, g
from app.model import User, db_session
import hashlib
import time
import redis
from functools import wraps
import uuid
from qiniu import Auth, put_file, etag, urlsafe_base64_encode
import datetime
import hashlib
import requests
import json
import base64
from random import random
from app.config import Conf
# 引入蓝图
from . import api
from flask import current_app
from app.model import SmallBlog,desc


# 改为蓝图后边有好几个需要注意的点。
# 第一，运行的代码取消掉了，因为统一从run.py来运行，作为入口点。
# 第二，原先的app.route也全部改成api.route， api也从本地的__init__.py中导入。因为你现在代表树枝，不能代表整棵树了。
# 第三，app.redis，可以用current_app.redis来代替，其实就是我在run.py中定义的一些变量，在整颗树中使用。


# app = Flask(__name__)
# app.config.from_object(Conf)
#
# app.secret_key = app.config['SECRET_KEY']
# app.redis = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'],
#                         db=app.config['REDIS_DB'], password=app.config['REDIS_PASSWORD'])
# app.q = Auth(access_key=app.config['QINIU_ACCESS_KEY'], secret_key=app.config['QINIU_SECRET_KEY'])
# bucket_name = app.config['BUCKET_NAME']

#####app = Flask(__name__) 已经被蓝图api = Blueprint('api', __name__)替代

@api.route('/')
def hello_world():
    return 'Hello World! api1.1'


@api.route('/get-qiniu-token')
def get_qiniu_token():
    '''七牛云的token获取'''
    key = uuid.uuid4()
    token = current_app.q.upload_token(current_app.bucket_name, key, 3600)
    return jsonify({'code': 1, 'key': key, 'token': token})


@api.before_request
def before_request():
    '''每次在请求之前都要做token检测，和查phone_number,
       在这里存储在全局变量g中
    '''
    token = request.headers.get('token')
    phone_number = current_app.redis.get('token:%s' % token)
    if phone_number:
        g.current_user = User.query.filter_by(phone_number=phone_number).first()
        g.token = token
    return


def login_check(f):
    '''验证token的方法,装饰器'''

    @wraps(f)
    def decorator(*args, **kwargs):
        token = request.headers.get('token')
        if not token:
            return jsonify({'code': 0, 'message': '需要验证'})
        phone_number = current_app.redis.get('token:%s' % token)
        if not phone_number or token != current_app.redis.hget('user:%s' % phone_number, 'token'):
            return jsonify({'code': 2, 'message': '验证信息错误'})
        return f(*args, **kwargs)

    return decorator


@api.route('/set-head-picture', methods=['POST'])
@login_check
def set_head_picture():
    '''给user设置图片'''
    head_picture = request.get_json().get('head_picture')
    user = g.current_user
    user.head_picture = head_picture
    try:
        db_session.commit()
    except Exception as e:
        print e
        db_session.rollback()
        return jsonify({'code': 0, 'message': '未能成功上传'})
        app.redis.hset('user:%s' % user.phone_number, 'head_picture', head_picture)
    return jsonify({'code': 1, 'message': '成功上传'})


@api.route('/login', methods=['POST'])
def login():
    phone_number = request.get_json().get('phone_number')
    # password = request.get_json().get('password')
    # 都是把用户名，和 密码 + 随机值 + 时间戳的加密方式传过去
    encryption_str = request.get_json().get('encryption_str')
    # encryption_str就是加密串，是由密码 + 随机值 + 时间戳用sha256加密的
    random_str = request.get_json().get('random_str')
    time_stamp = request.get_json().get('time_stamp')

    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        return jsonify({'code': 0, 'message': '没有此用户'})

    password_in_sql = user.password
    #
    s = hashlib.sha256()
    s.update(password_in_sql)
    s.update(random_str)
    s.update(time_stamp)
    server_encryption_str = s.hexdigest()

    if server_encryption_str != encryption_str:
        return jsonify({'code': 0, 'message': '密码错误'})

    # 生成token
    m = hashlib.md5()
    m.update(phone_number)
    m.update(user.password)
    m.update(str(int(time.time())))
    token = m.hexdigest()

    # 缓存token 设置有效期,设置用户在线app_online = 1
    # redis_store.hmset('user:%s' % user.phone_number, {'token': token, 'nickname': user.nickname, 'app_online': 1})
    # redis_store.set('token:%s' % token, user.phone_number)
    # redis_store.expire('token:%s' % token, 3600 * 24 * 30)

    pipeline = current_app.redis.pipeline()
    # 执行redis时改用pipeline管道执行,防止执行到一半终止
    pipeline.hmset('user:%s' % user.phone_number, {'token': token, 'nickname': user.nickname, 'app_online': 1})
    pipeline.set('token:%s' % token, user.phone_number)
    pipeline.expire('token:%s' % token, 3600 * 24 * 30)
    pipeline.execute()

    return jsonify({'code': 1, 'message': '成功登录', 'nickname': user.nickname, 'token': token})


@api.route('/user')
@login_check  # 使用装饰器就可以移除下面的验证token
def user():
    # 首先获取token
    # token = request.headers.get('token')
    # phone_number = redis_store.get('token:%s' % token)
    # 不用通过上面redis代码中获取,在@app.before_request中已经有了存储
    user = g.current_user
    # 在redis中获取用户信息
    nickname = current_app.redis.hget('user:%s' % user.phone_number, 'nickname')
    return jsonify(
        {'code': 1, 'nickname': nickname, 'phone_number': user.phone_number, 'head_picture': user.head_picture})


@api.route('/logout')
@login_check  # 使用装饰器就可以移除下面的验证token
def logout():
    user = g.current_user
    # 执行redis时改用pipeline管道执行,防止执行到一半终止
    pipeline = current_app.redis.pipeline()
    pipeline.delete('token:%s' % g.token)
    pipeline.hmset('user:%s' % user.phone_number, {'app_online': 0})
    pipeline.execute()
    return jsonify({'code': 1, 'message': '成功注销'})


# 一般的移动注册api接口可以分为3步
# 1、提交电话号码，发送短信验证，
# 2、验证短信
# 3、密码提交，
# 4、基本资料提交

def message_validate(phone_number, validate_number):
    '''云通讯提供的短信验证测试'''
    accountSid = "8a48b5514f73ea32014f9c7a2d954df4"
    accountToken = "0d447f3e53424191b43247a7c48b373f"
    appid = "8aaf07085f9eb021015fa03987e6005c"
    templateId = '1'
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    signature = accountSid + accountToken + now
    m = hashlib.md5()
    m.update(signature)
    sigParameter = m.hexdigest().upper()
    # 基本都是把账号的id和token加上时间戳，转换成md5值，然后再encode一下，变成http的基本验证
    # sigParameter = hashlib.md5().update(signature).hexdigest().upper()
    url = "https://sandboxapp.cloopen.com:8883/2013-12-26/Accounts/%s/SMS/TemplateSMS?sig=%s" % (
        accountSid, sigParameter)
    authorization = accountSid + ':' + now
    new_authorization = base64.encodestring(authorization).strip()
    headers = {'content-type': 'application/json;charset=utf-8', 'accept': 'application/json',
               'Authorization': new_authorization}
    data = {'to': phone_number, 'appId': appid, 'templateId': templateId, 'datas': [str(validate_number), '3']}
    response = requests.post(url=url, data=json.dumps(data), headers=headers)
    if response.json()['statusCode'] == '000000':
        return True, response.json().get('statusMsg')
    else:
        return False, response.json().get('statusMsg')


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
    pipe_line.set('is_validate:%s' % phone_number, '1')  # 添加次数
    pipe_line.expire('is_validate:%s' % phone_number, 120)  # 添加有效期执行的有效时间
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


@api.teardown_request
def handle_teardown_request(exception):
    '''
    如果没有这个函数，每一个会话以后，db_session都不会清除，
    很多时候，数据库改变了，前台找不到，或者明明已经提交，
    数据库还是没有更改，或者长时间没有访问接口，mysql gong away，这样的错误。总之，一定要加上。
    '''
    db_session.remove()


@api.route('/get-multi-qiniu-token')
@login_check
def get_multi_qiniu_token():
    count = request.args.get('count')

    if not 0 < int(count) < 10:
        return jsonify({'code': 0, 'message': '一次只能获取1到9个'})

    key_token_s = []
    for x in range(int(count)):
        key = uuid.uuid1()
        token = current_app.q.upload_token(current_app.bucket_name, key, 3600)
        key_token_s.append((key, token))
    return jsonify({'code': 1, 'key_token_s': key_token_s})


@api.route('/post-blog', methods=['POST'])
@login_check
def post_blog():
    user = g.current_user

    title = request.get_json().get('title')
    text_content = request.get_json().get('text_content')
    pictures = request.get_json().get('pictures')

    newblog = SmallBlog(title=title, text_content=text_content, post_user=user)

    newblog.pictures = pictures
    db_session.add(newblog)
    try:
        db_session.commit()
    except Exception as e:
        print e
        db_session.rollback()
        return jsonify({'code': 0, 'message': '上传不成功'})
    return jsonify({'code': 1, 'message': '上传成功'})


@api.route('/get-blogs')
@login_check
def get_blogs():
    last_id = request.args.get('last_id')
    if not int(last_id):
        blogs = db_session.query(SmallBlog).order_by(desc(SmallBlog.id)).limit(10)
    else:
        blogs = db_session.query(SmallBlog).filter(SmallBlog.id < int(last_id)).order_by(desc(SmallBlog.id)).limit(10)
    return jsonify({'code': 1, 'blogs': [blog.to_dict() for blog in blogs]})

# if __name__ == '__main__':
# app.run(debug=True, host='0.0.0.0', port=5001)
# app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5001)
