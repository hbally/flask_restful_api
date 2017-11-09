# coding:utf-8
import requests
import json


class APITest(object):
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {}
        self.token = None

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


if __name__ == '__main__':
    # 登陆获取token
    api = APITest('http://127.0.0.1:5001')
    data = api.login('13247102980', '123456')
    print json.dumps(data)
    # {"message": "\u6210\u529f\u767b\u5f55", "code": 1, "nickname": "test1", "token": "7f7442fa0ec2b6e84f9ddf3cd0ef1c96"}
    # 通过token获取用户信息
    user = api.user()
    print json.dumps(user)
    # {"phone_number": "13247102980", "code": 1, "nickname": "test1"}
    # 退出登录
    logoutresult = api.logout()
    print json.dumps(logoutresult)
    #{"message": "\u6210\u529f\u6ce8\u9500", "code": 1}
