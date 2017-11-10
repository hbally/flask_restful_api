# coding:utf-8
from flask import Blueprint

api = Blueprint('api', __name__)

#1.1版本接口调整：
#1.登陆接口不适用明文传输密码，密码+随机值+时间戳 的加密方式传过

from app.app_1_0 import view