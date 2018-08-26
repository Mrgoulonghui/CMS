"""BBS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from blog import views
from django.views.static import serve
from BBS import settings
from blog import urls as blog_urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # 登陆相关
    url(r'^login/', views.Login.as_view()),
    url(r'^login_huadong/', views.login_huadong),  # 滑动验证码
    url(r'^pcgetcaptcha/', views.pcgetcaptcha),
    url(r'^index/', views.Index.as_view()),
    url(r'^v_code/', views.v_code),
    # 注册相关
    url(r'^register/', views.Register.as_view()),
    # 给用户上传文件 配置一个处理的路由, 标准写法，就这么写
    url(r'^media/(?P<path>.*)', serve, {"document_root": settings.MEDIA_ROOT}),

    # 注销
    url(r'^logout/', views.log_out),

    # 个人博客站点
    url(r'^blog/', include(blog_urls)),

    # 点赞和返回
    url(r"^UpDown/", views.up_down),

    # 评论
    url(r'^comment/$', views.comment),  # 评论楼
    url(r'^comment_tree/(\d+)$', views.comment_tree),  # 评论树

    url(r'^$', views.Index.as_view()),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
