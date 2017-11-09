# coding:utf-8
from qiniu import Auth, put_file, etag, urlsafe_base64_encode

access_key = 'nkZdP9QwpdAeJxU-muIzpEUrWVZhGPsCG8WjwQCe'
secret_key = 'XYFyGSSTIIDi6ZCiydNSK4CZPWN6ocOPH9TWVWjH'

q = Auth(access_key=access_key, secret_key=secret_key)

bucket_name = 'hbally'

key = 'my-test-picture.jpg'

if __name__ == '__main__':
    '''测试七牛云上传图片'''
    token = q.upload_token(bucket_name, key, 3600)
    print token
    localfile = './static/test_photo.jpg'
    ret, info = put_file(token, key, localfile)
    print ret
    print info

