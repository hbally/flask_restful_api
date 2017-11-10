# coding:utf-8
import hashlib
import time
import random

import requests
import json
from qiniu import put_file


class APITest(object):
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {}
        self.token = None
        # 七牛相关
        self.qiniu_token = None
        self.qiniu_key = None
        self.qiniu_base_url = 'http://7xq5fy.com1.z0.glb.clouddn.com/'

    def login(self, phone_number, password, path='/login'):
        payload = {'phone_number': phone_number, 'password': password}
        self.headers = {'content-type': 'application/json'}
        response = requests.post(url=self.base_url + path, data=json.dumps(payload), headers=self.headers)
        response_data = json.loads(response.content)
        self.token = response_data.get('token')
        return response_data

    def user(self, path='/user'):
        self.headers = {'token': self.token}
        response = requests.get(url=self.base_url + path, headers=self.headers)
        response_data = json.loads(response.content)
        return response_data

    def logout(self, path='/logout'):
        self.headers = {'token': self.token}
        response = requests.get(url=self.base_url + path, headers=self.headers)
        response_data = json.loads(response.content)
        return response_data

    def get_qiniu_token(self, path='/get-qiniu-token'):
        '''获取qiniu token 并立即上传图片'''
        response = requests.get(url=self.base_url + path)
        response_data = json.loads(response.content)
        self.qiniu_token = response_data.get('token')
        self.qiniu_key = response_data.get('key')
        if self.qiniu_token and self.qiniu_key:
            print '成功获取qiniu_token和qiniu_key,分别为%s和%s' % (
                self.qiniu_token.encode('utf-8'), self.qiniu_key.encode('utf-8'))
            localfile = './static/test_photo.jpg'
            ret, info = put_file(self.qiniu_token, self.qiniu_key, localfile)
            print info.status_code
            if info.status_code == 200:
                print '上传成功'
                self.head_picture = self.qiniu_base_url + self.qiniu_key
                print '其url为:' + self.head_picture.encode('utf-8')
            else:
                print '上传失败'
        return response_data

    def set_head_picture(self, path='/set-head-picture'):
        payload = {'head_picture': self.head_picture}
        self.headers = {'token': self.token, 'content-type': 'application/json'}
        response = requests.post(url=self.base_url + path, data=json.dumps(payload), headers=self.headers)
        response_data = json.loads(response.content)
        print response_data.get('message')
        return response_data

    def register_step_1(self, phone_number, path='/register-step-1'):
        payload = {'phone_number': phone_number}
        self.headers = {'content-type': 'application/json'}
        response = requests.post(url=self.base_url + path, data=json.dumps(payload), headers=self.headers)
        response_data = json.loads(response.content)
        print response_data.get('code')
        return response_data

    def register_step_2(self, phone_number, validate_number, path='/register-step-2'):
        payload = {'phone_number': phone_number, 'validate_number': validate_number}
        self.headers = {'content-type': 'application/json'}
        response = requests.post(url=self.base_url + path, data=json.dumps(payload), headers=self.headers)
        response_data = json.loads(response.content)
        print response_data.get('code')
        return response_data

    def register_step_3(self, phone_number, password, password_confirm, path='/register-step-3'):
        payload = {'phone_number': phone_number, 'password': password, 'password_confirm': password_confirm}
        self.headers = {'content-type': 'application/json'}
        response = requests.post(url=self.base_url + path, data=json.dumps(payload), headers=self.headers)
        response_data = json.loads(response.content)
        print response_data.get('code')
        return response_data

    def register_step_4(self, phone_number, nickname, path='/register-step-4'):
        payload = {'phone_number': phone_number, 'nickname': nickname}
        self.headers = {'content-type': 'application/json'}
        response = requests.post(url=self.base_url + path, data=json.dumps(payload), headers=self.headers)
        response_data = json.loads(response.content)
        print response_data.get('code')
        return response_data


class APITest1_1(APITest):
    def login(self, phone_number, password, path='/login'):
        random_str = str(random.randint(10000, 100000))
        time_stamp = str(int(time.time()))
        s = hashlib.sha256()
        s.update(password)
        s.update(random_str)
        s.update(time_stamp)
        encryption_str = s.hexdigest()
        # payload = {'phone_number': phone_number, 'password': password}
        payload = {'phone_number': phone_number, 'encryption_str': encryption_str, 'random_str': random_str,
                   'time_stamp': time_stamp}
        self.headers = {'content-type': 'application/json'}
        response = requests.post(url=self.base_url + path, data=json.dumps(payload), headers=self.headers)
        response_data = json.loads(response.content)
        self.token = response_data.get('token')
        return response_data

    def get_multi_qiniu_token(self, count, path='/get-multi-qiniu-token'):
        """获取多个七牛的token"""
        self.headers = {'token': self.token}
        payload = {'count': count}
        response = requests.get(url=self.base_url + path, params=payload, headers=self.headers)
        response_data = json.loads(response.content)
        key_token_s = response_data.get('key_token_s')
        return key_token_s

    def post_blog(self, title, text_content, picture_files, path='/post-blog'):
        """发布帖子里面上传图片和文字"""
        self.headers = {'token': self.token}
        count = len(picture_files)
        key_token_s = self.get_multi_qiniu_token(count=count)
        pictures = []

        for x in range(count):
            put_file(key_token_s[x][1], key_token_s[x][0], picture_files[x])  # 上传图片
            pictures.append(self.qiniu_base_url + key_token_s[x][0])

        payload = {'title': title, 'text_content': text_content, 'pictures': pictures}
        self.headers = {'content-type': 'application/json', 'token': self.token}
        response = requests.post(url=self.base_url + path, data=json.dumps(payload), headers=self.headers)
        response_data = json.loads(response.content)
        print response_data.get('code')
        return response_data

    def get_blogs(self, last_id, path='/get-blogs'):
        self.headers = {'token': self.token}
        payload = {'last_id': last_id}
        response = requests.get(url=self.base_url + path, params=payload, headers=self.headers)
        response_data = json.loads(response.content)
        return response_data


def testApi(api):
    # 登陆获取token
    # api = APITest('http://127.0.0.1:5001')
    # 改为蓝图后http地址变更

    data = api.login('13247102980', '123456')
    print json.dumps(data)
    # {"message": "\u6210\u529f\u767b\u5f55", "code": 1, "nickname": "test1", "token": "7f7442fa0ec2b6e84f9ddf3cd0ef1c96"}
    # 通过token获取用户信息
    user = api.user()
    print json.dumps(user)
    # 七牛图片上传
    api.get_qiniu_token()
    api.set_head_picture()
    # 查看更新的user信息
    user = api.user()
    print json.dumps(user)
    # {"phone_number": "13247102980", "code": 1, "nickname": "test1"}
    # 退出登录
    logoutresult = api.logout()
    print json.dumps(logoutresult)
    # {"message": "\u6210\u529f\u6ce8\u9500", "code": 1}


def testpostbolg():
    api1_1 = APITest1_1('http://127.0.0.1:5001/api/v1100')
    data = api1_1.login('13247102980', '123456')
    print json.dumps(data)
    localfiles = ['./static/rad600-06752062.jpg', './static/rad600-06752558.jpg', './static/rad600-06758166.jpg']
    # key_token_s = api.get_multi_qiniu_token(4)
    api1_1.post_blog(title="发个微博到天上", text_content="这个是猴子，还是只石头变得，齐天大圣也...",
                     picture_files=localfiles)
    blogs = api1_1.get_blogs(0)
    print json.dumps(blogs)

    print json.dumps(
        api1_1.logout())


if __name__ == '__main__':
    # 测试版本1.0接口
    # api1_0 = APITest('http://127.0.0.1:5001/api/v1000')
    # testApi(api1_0)
    # 测试版本1.1接口
    # api1_1 = APITest1_1('http://127.0.0.1:5001/api/v1100')
    # testApi(api1_1)
    testpostbolg()
