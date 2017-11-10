# coding:utf-8
from flask import Flask
from config import Conf
import redis
from qiniu import Auth, put_file, etag, urlsafe_base64_encode


def create_app():
    app = Flask(__name__)
    app.config.from_object(Conf)
    app.secret_key = app.config['SECRET_KEY']
    app.redis = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'],
                            db=app.config['REDIS_DB'], password=app.config['REDIS_PASSWORD'])

    app.q = Auth(access_key=app.config['QINIU_ACCESS_KEY'], secret_key=app.config['QINIU_SECRET_KEY'])
    app.bucket_name = app.config['BUCKET_NAME']
    app.debug = app.config['DEBUG']

    # 注册1.0版本接口到app
    from app.app_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1000')
    # 注册1.1版本接口到app
    from app.app_1_1 import api as api_1_1_blueprint
    app.register_blueprint(api_1_1_blueprint, url_prefix='/api/v1100')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.debug, host='0.0.0.0', port=5001)
