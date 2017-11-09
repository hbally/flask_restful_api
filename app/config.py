class Config(object):
    SECRET_KEY = 'saduhsuaihfe332r32rfo43rtn3noiYUG9jijoNF23'
    QINIU_ACCESS_KEY = 'nkZdP9QwpdAeJxU-muIzpEUrWVZhGPsCG8WjwQCe'
    QINIU_SECRET_KEY = 'XYFyGSSTIIDi6ZCiydNSK4CZPWN6ocOPH9TWVWjH'
    BUCKET_NAME = 'hbally'


class DevelopmentConfig(Config):
    DEBUG = True

    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 4
    REDIS_PASSWORD = '123456'

    MYSQL_INFO = "mysql://root:123456@127.0.0.1:3306/blog01?charset=utf8"


class ProductionConfig(Config):
    DEBUG = False

    REDIS_HOST = 'server-ip'
    REDIS_PORT = 6380
    REDIS_DB = 4
    REDIS_PASSWORD = ''

    MYSQL_INFO = "mysql://root:123456@127.0.0.1:3306/blog01?charset=utf8"


Conf = DevelopmentConfig
