# coding:utf-8
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


if __name__ == '__main__':
    # 登陆获取token
    api = APITest('http://127.0.0.1:5001')
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
