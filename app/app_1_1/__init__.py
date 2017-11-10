# coding:utf-8
from flask import Blueprint

api = Blueprint('api1_1', __name__)

# from app.app_1_1 import view
#将view的接口分拆到以下模块中
from app.app_1_1 import auth, blogs, decorators, main