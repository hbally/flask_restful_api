#基本的flask api 接口设计
#适用于移动端访问token验证
#整个框架用的是flask + sqlalchemy + redis

##
变成数据
1.首先安装alembic
2.然后在工程目录下初始化migration
  alembic init my_migration
3.这时候编辑一下alembic.ini，这是alembic的配置文件，基本只要修改一处就可以了。
  sqlalchemy.url = mysql://root:a12345678@127.0.0.1:3306/blog01?charset=utf8
