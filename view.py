# coding:utf-8
from flask import Flask, request, jsonify
from model import User, db_session
import hashlib
import time
import redis

app = Flask(__name__)
# redis服务器缓存
redis_store = redis.Redis(host='localhost', port=6379, db=4, password='123456')


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/login', methods=['POST'])
def login():
    phone_number = request.get_json().get('phone_number')
    password = request.get_json().get('password')
    user = User.query.filter_by(phone_number=phone_number).first()
    if not user:
        return jsonify({'code': 0, 'message': '没有此用户'})

    if user.password != password:
        return jsonify({'code': 0, 'message': '密码错误'})

    # 生成token
    m = hashlib.md5()
    m.update(phone_number)
    m.update(password)
    m.update(str(int(time.time())))
    token = m.hexdigest()

    # 缓存token 设置有效期,设置用户在线app_online = 1
    redis_store.hmset('user:%s' % user.phone_number, {'token': token, 'nickname': user.nickname, 'app_online': 1})
    redis_store.set('token:%s' % token, user.phone_number)
    redis_store.expire('token:%s' % token, 3600 * 24 * 30)

    return jsonify({'code': 1, 'message': '成功登录', 'nickname': user.nickname, 'token': token})


@app.route('/user')
def user():
    # 首先获取token
    token = request.headers.get('token')
    if not token:
        return jsonify({'code': 0, 'message': '需要验证'})
    # 通过token在redis中获取phone_number
    phone_number = redis_store.get('token:%s' % token)
    if not phone_number or token != redis_store.hget('user:%s' % phone_number, 'token'):
        return jsonify({'code': 2, 'message': '验证信息错误'})
    # 在redis中获取用户信息
    nickname = redis_store.hget('user:%s' % phone_number, 'nickname')
    return jsonify({'code': 1, 'nickname': nickname, 'phone_number': phone_number})


@app.route('/logout')
def logout():
    token = request.headers.get('token')
    if not token:
        return jsonify({'code': 0, 'message': '需要验证'})
    phone_number = redis_store.get('token:%s' % token)
    if not phone_number or token != redis_store.hget('user:%s' % phone_number, 'token'):
        return jsonify({'code': 2, 'message': '验证信息错误'})

    redis_store.delete('token:%s' % token)
    # 缓存的token删除 ,设置用户在线app_online = 0 表示离线状态
    redis_store.hmset('user:%s' % phone_number, {'app_online': 0})
    return jsonify({'code': 1, 'message': '成功注销'})


@app.teardown_request
def handle_teardown_request(exception):
    '''
    如果没有这个函数，每一个会话以后，db_session都不会清除，
    很多时候，数据库改变了，前台找不到，或者明明已经提交，
    数据库还是没有更改，或者长时间没有访问接口，mysql gong away，这样的错误。总之，一定要加上。
    '''
    db_session.remove()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
