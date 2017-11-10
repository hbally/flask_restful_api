# coding:utf-8
# 公用，运行接口前后以及七牛token和key的获取
import uuid
from flask import request, jsonify, g, current_app
from app.model import User, db_session
from . import api
from .decorators import login_check


@api.before_request
def before_request():
    token = request.headers.get('token')
    phone_number = current_app.redis.get('token:%s' % token)
    if phone_number:
        g.current_user = User.query.filter_by(phone_number=phone_number).first()
        g.token = token
    return


@api.teardown_request
def handle_teardown_request(exception):
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


@api.route('/get-qiniu-token')
def get_qiniu_token():
    key = uuid.uuid4()
    token = current_app.q.upload_token(current_app.bucket_name, key, 3600)
    return jsonify({'code': 1, 'key': key, 'token': token})
