# coding:utf-8
#博客接口
from flask import request, jsonify, g

from app.model import db_session, SmallBlog, desc
from . import api
from .decorators import login_check

@api.route('/post-blog', methods=['POST'])
@login_check
def post_blog():
    user = g.current_user

    title = request.get_json().get('title')
    text_content = request.get_json().get('text_content')
    pictures = request.get_json().get('pictures')

    newblog = SmallBlog(title=title, text_content=text_content, post_user=user)

    newblog.pictures = pictures
    db_session.add(newblog)
    try:
        db_session.commit()
    except Exception as e:
        print e
        db_session.rollback()
        return jsonify({'code': 0, 'message': '上传不成功'})
    return jsonify({'code': 1, 'message': '上传成功'})


@api.route('/get-blogs')
@login_check
def get_blogs():
    last_id = request.args.get('last_id')
    if not int(last_id):
        blogs = db_session.query(SmallBlog).order_by(desc(SmallBlog.id)).limit(10)
    else:
        blogs = db_session.query(SmallBlog).filter(SmallBlog.id < int(last_id)).order_by(desc(SmallBlog.id)).limit(10)
    return jsonify({'code': 1, 'blogs': [blog.to_dict() for blog in blogs]})