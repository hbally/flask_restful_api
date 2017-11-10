# coding:utf-8
from flask import Blueprint

api = Blueprint('api1_1', __name__)

from app.app_1_1 import view