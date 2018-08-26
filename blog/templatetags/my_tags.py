#!/usr/bin/env python
# -*- coding:utf8 -*-
from blog import models
from django.db.models import Count
from django import template
register = template.Library()


@register.inclusion_tag("side_bar.html")
def side_bar(username):
    user_obj = models.UserInfo.objects.filter(username=username).first()
    blog_obj = user_obj.blog
    category_obj_list = models.Category.objects.filter(blog=blog_obj)
    tag_obj_list = models.Tag.objects.filter(blog=blog_obj)
    archive_list = models.Article.objects.filter(user=user_obj).extra(
        # 这里需要注意的是，我上面的article_obj_list是有一个排序的（order_by("-create_time")），所以直接用这个对象
        # 不可以，排序之后，有多少的对象就会显示多少个对象，会导致分组不起作用，所以需要重新查询
        select={"y_m": "DATE_FORMAT(create_time, '%%Y年%%m月')"}
    ).values("y_m").annotate(num=Count("title")).values("y_m", "num")
    # extra执行额外的sql语句，与ORM连在一起使用，为orm查询的对象添加了一个键值对
    # 即"y_m":"DATA_FORMAT(create_time, '%Y-%m')"(后面是mysql的内置函数，时间格式化)
    # 在对该对象按照需要的时间格式分组，在取数量，
    # 最后返回一个values(特殊的QuerySet
    # <QuerySet [{'y_m': '2015-06', 'num': 1}, {'y_m': '2017-09', 'num': 2}, {'y_m': '2018-05', 'num': 2}]>)
    # 返回到模板中渲染，模板使用点的方式渲染
    return {
        "username": username,
        "category_obj_list": category_obj_list,
        "tag_obj_list": tag_obj_list,
        "archive_list": archive_list
    }

