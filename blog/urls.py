#!/usr/bin/env python
# -*- coding:utf8 -*-

from django.conf.urls import url
from blog import views

urlpatterns = [

    url(r"^backend/$", views.backend),
    url(r'^add_article/$', views.add_article),
    url(r'^upload/$', views.upload),
    url(r'^del_article/(\d+)$', views.del_article),
    url(r'^edit_article/(\d+)$', views.edit_article),



    # 个人home页面
    url(r"^(\w+)/$", views.home),

    # url(r"^(\w+)/category/(\w+)$", views.home),
    # url(r"^(\w+)/tag/(\w+)$", views.home),
    # url(r"^(\w+)/archive/(\w+)$", views.home),
    # 优化1，
    # url(r"^(\w+)/(category|tags|archive)/(\w+)/$", views.home),
    # 注意，上面如果是时间归类，且时间是按照2018-08的方式，则上面的url不可用，（\w+）不能匹配 -,需要下面的url
    url(r'^(\w+)/(category|tags|archive)/(.*)/$', views.home),

    # 文章详情页面
    url(r"^(\w+)/p/(\d+)/$", views.article),
]

