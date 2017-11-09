# coding:utf-8
from flask import Flask, request, jsonify, g
from model import User, db_session
import hashlib
import time
import redis
from functools import wraps

app = Flask(__name__)
# redis服务器缓存
redis_store = redis.Redis(host='localhost', port=6379, db=4, password='123456')


@app.route('/')
def hello_world():
    return 'Hello World!'

@app.before_request
def before_request():
    '''每次在请求之前都要做token检测，和查phone_number,
       在这里存储在全局变量g中
    '''
    token = request.headers.get('token')
    phone_number = redis_store.get('token:%s' % token)
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
        phone_number = redis_store.get('token:%s' % token)
        if not phone_number or token != redis_store.hget('user:%s' % phone_number, 'token'):
            return jsonify({'code': 2, 'message': '验证信息错误'})
        return f(*args, **kwargs)

    return decorator


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
    # redis_store.hmset('user:%s' % user.phone_number, {'token': token, 'nickname': user.nickname, 'app_online': 1})
    # redis_store.set('token:%s' % token, user.phone_number)
    # redis_store.expire('token:%s' % token, 3600 * 24 * 30)

    pipeline = redis_store.pipeline()
    # 执行redis时改用pipeline管道执行,防止执行到一半终止
    pipeline.hmset('user:%s' % user.phone_number, {'token': token, 'nickname': user.nickname, 'app_online': 1})
    pipeline.set('token:%s' % token, user.phone_number)
    pipeline.expire('token:%s' % token, 3600 * 24 * 30)
    pipeline.execute()

    return jsonify({'code': 1, 'message': '成功登录', 'nickname': user.nickname, 'token': token})


@app.route('/user')
@login_check  # 使用装饰器就可以移除下面的验证token
def user():
    # 首先获取token
    # token = request.headers.get('token')
    # phone_number = redis_store.get('token:%s' % token)
    #不用通过上面redis代码中获取,在@app.before_request中已经有了存储
    user = g.current_user
    # 在redis中获取用户信息
    nickname = redis_store.hget('user:%s' % user.phone_number, 'nickname')
    return jsonify({'code': 1, 'nickname': nickname, 'phone_number': user.phone_number})


@app.route('/logout')
@login_check  # 使用装饰器就可以移除下面的验证token
def logout():
    user = g.current_user
    # 执行redis时改用pipeline管道执行,防止执行到一半终止
    pipeline = redis_store.pipeline()
    pipeline.delete('token:%s' % g.token)
    pipeline.hmset('user:%s' % user.phone_number, {'app_online': 0})
    pipeline.execute()
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
