# coding:utf-8
import datetime
import hashlib
import requests
import json
import base64


def message_validate(phone_number, validate_number):
    '''云通讯提供的短信验证测试'''
    accountSid = "8a48b5514f73ea32014f9c7a2d954df4"
    accountToken = "0d447f3e53424191b43247a7c48b373f"
    appid = "8aaf07085f9eb021015fa03987e6005c"
    templateId = '1'
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    signature = accountSid + accountToken + now
    m = hashlib.md5()
    m.update(signature)
    sigParameter = m.hexdigest().upper()
    # 基本都是把账号的id和token加上时间戳，转换成md5值，然后再encode一下，变成http的基本验证
    # sigParameter = hashlib.md5().update(signature).hexdigest().upper()
    url = "https://sandboxapp.cloopen.com:8883/2013-12-26/Accounts/%s/SMS/TemplateSMS?sig=%s" % (
    accountSid, sigParameter)
    authorization = accountSid + ':' + now
    new_authorization = base64.encodestring(authorization).strip()
    headers = {'content-type': 'application/json;charset=utf-8', 'accept': 'application/json',
               'Authorization': new_authorization}
    data = {'to': phone_number, 'appId': appid, 'templateId': templateId, 'datas': [str(validate_number), '3']}
    response = requests.post(url=url, data=json.dumps(data), headers=headers)
    if response.json()['statusCode'] == '000000':
        return True, response.json().get('statusMsg')
    else:
        return False, response.json().get('statusMsg')


if __name__ == '__main__':
    result, reason = message_validate('13247102980', '123456')
    if result:
        print '发送成功'
    else:
        print '发送失败'
        print '原因是:' + reason.encode('utf-8')
