import random
import re
import os
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django import views
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.cache import never_cache  # 不缓存

# 随机生成图片的模块pillow模块
from PIL import Image, ImageDraw, ImageFont

# 内存级别储存的模块
from io import BytesIO

# 滑动验证码的模块
from utils.geetest import GeetestLib
# 导入form组件的注册类
from blog.my_forms import RegisterForm
from blog import models

# index页面
from utils.mypage import MyPage  # 分页

# 点赞
from django.db import transaction
from django.db.models import F

# backend
from BBS import settings
# 清洗用户提交的内容
from bs4 import BeautifulSoup


# Create your views here.

# V_CODE = ""

# 请在官网申请ID使用，示例ID不可使用
pc_geetest_id = "51cf04c39b7e55a0712647dad311d54d"
pc_geetest_key = "2c4cab3f25fb2efac0e7e64b809cceb0"

# pc_geetest_id = "b46d1900d0a894591916ea94ea91bd2c"
# pc_geetest_key = "36fc3fe98530eea08dfc6ce76e3d24c4"


# 滑动验证码第一步的API,初始化一些参数用来校验滑动验证码
def pcgetcaptcha(request):
    user_id = 'test'
    gt = GeetestLib(pc_geetest_id, pc_geetest_key)
    status = gt.pre_process(user_id)
    request.session[gt.GT_STATUS_SESSION_KEY] = status
    request.session["user_id"] = user_id
    response_str = gt.get_response_str()
    return HttpResponse(response_str)


def login_huadong(request):
    res = {"code": 0}
    err_msg = ""
    if request.method == "POST":
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        challenge = request.POST.get(gt.FN_CHALLENGE, '')
        validate = request.POST.get(gt.FN_VALIDATE, '')
        seccode = request.POST.get(gt.FN_SECCODE, '')
        status = request.session[gt.GT_STATUS_SESSION_KEY]
        user_id = request.session["user_id"]
        if status:
            result = gt.success_validate(challenge, validate, seccode, user_id)
        else:
            result = gt.failback_validate(challenge, validate, seccode)

        if result:
            # 滑动验证码校验通过
            username = request.POST.get("username")
            pwd = request.POST.get("pwd")
            # # 校验用户名密码是否正确
            user = auth.authenticate(username=username, password=pwd)
            if user:
                # 用户名密码正确,让用户登陆，写入用户相关信息的session,cookie
                auth.login(request, user)
            else:
                res["code"] = 1
                res["msg"] = "用户名或者密码错误"
        else:
            res["code"] = 1
            res["msg"] = "验证码错误"
        return JsonResponse(res)
    return render(request, "login_huadong.html", {"err_msg": err_msg})


class Login(views.View):
    def get(self, request):
        err_msg = ""
        return render(request, "login.html", {"err_msg": err_msg})

    def post(self, request):
        res = {"code": 0}
        username = request.POST.get("username")
        pwd = request.POST.get("pwd")
        random_code = request.POST.get("v_code")
        if random_code.upper() != request.session.get("v_code", ""):
            res["code"] = 1
            res["msg"] = "验证码错误"
        else:
            # # 校验用户名密码是否正确
            user = auth.authenticate(username=username, password=pwd)
            if user:
                # 用户名密码正确,让用户登陆，写入用户相关信息的session,cookie
                auth.login(request, user)
                # 处理某个网页需要登陆的需要，登陆成功后，返回道原来的页面
                next_url = request.GET.get("next")
                if next_url:
                    res["msg"] = next_url
                else:
                    res["msg"] = "/blog/{}/".format(username)
            else:
                res["code"] = 1
                res["msg"] = "用户名或者密码错误"
        return JsonResponse(res)


def log_out(request):
    auth.logout(request)
    return redirect("/login/")


class Index(views.View):
    @staticmethod
    def get(request):
        article_list = models.Article.objects.all()
        page_num = request.GET.get("page", 1)
        all_data = article_list.count()
        page_obj = MyPage(page_num, all_data, url_prefix='index', per_page_data=2)
        page_data = article_list[page_obj.start:page_obj.end]
        page_html = page_obj.ret_html()
        return render(request, "index.html", {"article_list": page_data, "page_html": page_html})


@never_cache
def v_code(request):
    # 生成随机颜色的方法
    def random_color():
        return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
    # 生成图片对象
    image_obj = Image.new(
        "RGB",  # 生成图片的模式
        (170, 34),  # 图片大小
        # random_color()  # 获取一个随机颜色
        (250, 250, 250, 5)
    )
    # 生成一个准备写字的画笔
    draw_obj = ImageDraw.Draw(image_obj)  # 在哪里写,写到一个创建的图片对象上
    font_obj = ImageFont.truetype('static/font/kumo.ttf', size=28)  # 加载本地的字体文件,和文件大小

    # 生成随机验证码
    random_code = ""
    for i in range(1):
        num = str(random.randint(0, 9))
        lower = chr(random.randint(65, 90))
        upper = chr(random.randint(97, 122))
        res = random.choice([num, lower, upper])
        random_code += str(res)
        # 每一次取到要写的东西之后，往图片上写,
        # 注意是一个一个的写
        draw_obj.text(
            (i*30+17, 0),  # x, y 坐标
            res,  # 写的内容
            fill=random_color(),  # 填充的颜色
            font=font_obj  # 使用什么字体写
        )

    # # 加干扰线
    # width = 170  # 图片宽度（防止越界）
    # height = 34
    # for i in range(5):
    #     x1 = random.randint(0, width)
    #     x2 = random.randint(0, width)
    #     y1 = random.randint(0, height)
    #     y2 = random.randint(0, height)
    #     draw_obj.line((x1, y1, x2, y2), fill=random_color())
    #
    # # 加干扰点
    # for i in range(20):
    #     draw_obj.point([random.randint(0, width), random.randint(0, height)], fill=random_color())
    #     x = random.randint(0, width)
    #     y = random.randint(0, height)
    #     draw_obj.arc((x, y, x+4, y+4), 0, 90, fill=random_color())

    # print("+++", random_code)

    # global V_CODE
    # V_CODE = random_code  # 保存在全局变量不行！！！
    # 将该次请求生成的验证码保存在该请求对应的session数据中
    request.session["v_code"] = random_code.upper()

    # 将上一步生成的图片保存在本地的static目录下,
    # 然后每一次 都在硬盘中保存再读取都涉及IO操作，会慢
    # with open("./static/img/xx.png", "wb") as write_f:
    #     image_obj.save(write_f)
    # with open("./static/img/xx.png", 'rb') as read_f:
    #     data = read_f.read()

    # from io import BytesIO  导入 内存级别储存的模块
    f = BytesIO()
    image_obj.save(f, "png")  # 在内存种暂时保存图片，指定为png格式
    data = f.getvalue()  # 从内存读取图片数据
    return HttpResponse(data, content_type="image/png")


class Register(views.View):

    @staticmethod
    def get(request):
        form_obj = RegisterForm()
        return render(request, "register.html", {"form_obj": form_obj})

    @staticmethod
    def post(request):
        print(request.POST)
        # <QueryDict: {'username': ['bbb'], 'password': ['bbbbbb'],
        #  're_password': ['bbbbbb'], 'phone': ['15832146589'], 'email': ['179@qq.com'],
        #  'v_code': ['ngbe8'],
        # 'csrfmiddlewaretoken': ['rFuVtD7CgRRD89ZRWysoP3A0r4AiiDhrnwUxzSdFjqNjx2oWOASwBQwVrjy4MFqQ']}>

        res = {"code": 0}
        random_code = request.POST.get("v_code")
        if random_code.upper() == request.session.get("v_code"):
            # 验证码正确
            form_obj = RegisterForm(request.POST)
            # 字段都有效
            if form_obj.is_valid():
                # 数据有效
                # 1. 注册用户
                print(form_obj.cleaned_data)
                # {'username': 'bbb', 'password': 'bbbbbb', 're_password': 'bbbbbb',
                # 'phone': '15832146589', 'email': '179@qq.com'}
                # 注意移除不需要的re_password
                form_obj.cleaned_data.pop("re_password")
                avater_file = request.FILES.get("avatar")
                print("++++", avater_file, type(avater_file))  # hmbb.png, 因为数据库中都是存的文件路径，所以直接存
                models.UserInfo.objects.create_user(**form_obj.cleaned_data, avatar=avater_file)
                res["msg"] = "/login/"
            else:
                res["code"] = 1
                res["msg"] = form_obj.errors   # 返回所有字段的错误提示信息
        else:
            res["code"] = 2
            res["msg"] = "验证码错误"
        return JsonResponse(res)


def home(request, username, *args):
    user_obj = get_object_or_404(models.UserInfo, username=username)
    # 上面一句用于如果找不到用户名，函数直接return 返回404页面
    user_obj = models.UserInfo.objects.filter(username=username).first()
    blog_obj = user_obj.blog
    article_obj_list = models.Article.objects.filter(user=user_obj).order_by("-create_time")
    # 以下使用inclusion_tag代替，优化代码
    # category_obj_list = models.Category.objects.filter(blog=blog_obj)
    # tag_obj_list = models.Tag.objects.filter(blog=blog_obj)
    # archive_list = models.Article.objects.filter(user=user_obj).extra(
    #     # 这里需要注意的是，我上面的article_obj_list是有一个排序的（order_by("-create_time")），所以直接用这个对象
    #     # 不可以，排序之后，有多少的对象就会显示多少个对象，会导致分组不起作用，所以需要重新查询
    #     select={"y_m": "DATE_FORMAT(create_time, '%%Y年%%m月')"}
    # ).values("y_m").annotate(num=Count("title")).values("y_m", "num")
    # # extra执行额外的sql语句，与ORM连在一起使用，为orm查询的对象添加了一个键值对
    # # 即"y_m":"DATA_FORMAT(create_time, '%Y-%m')"(后面是mysql的内置函数，时间格式化)
    # # 在对该对象按照需要的时间格式分组，在取数量，
    # # 最后返回一个values(特殊的QuerySet
    # # <QuerySet [{'y_m': '2015-06', 'num': 1}, {'y_m': '2017-09', 'num': 2}, {'y_m': '2018-05', 'num': 2}]>)
    # # 返回到模板中渲染，模板使用点的方式渲染

    if args:
        # 如果有参数，说明是走的具体分类的标签，对上面查出来的所有的文章，继续按照url传过来的参数筛选，
        if args[0] == "category":
            article_obj_list = article_obj_list.filter(category__title=args[1])
        elif args[0] == "tags":
            article_obj_list = article_obj_list.filter(tags__title=args[1])
        else:
            try:
                year, month = re.findall("\d+", args[1])  # 按照正则 分割，拿到年和月，如果拿不到，
                #                                               说明有错误，直接让article_obj_list变为空
                article_obj_list = article_obj_list.filter(create_time__year=year, create_time__month=month)
            except Exception:
                article_obj_list = []
        return render(request, "home.html", {
            "username": username,
            "blog_obj": blog_obj,
            "article_obj_list": article_obj_list,
            # "category_obj_list": category_obj_list,  # 使用inclusion_tag代替
            # "tag_obj_list": tag_obj_list,
            # "archive_list": archive_list,
        })
    else:
        page_num = request.GET.get("page", 1)
        all_data = article_obj_list.count()
        page_obj = MyPage(page_num, all_data, url_prefix='blog/{}'.format(username), per_page_data=2)
        page_data = article_obj_list[page_obj.start:page_obj.end]
        page_html = page_obj.ret_html()

        return render(request, "home.html", {
            "username": username,
            "blog_obj": blog_obj,
            "article_obj_list": page_data,
            # "category_obj_list": category_obj_list,  # 使用inclusion_tag代替
            # "tag_obj_list": tag_obj_list,
            # "archive_list": archive_list,
            "page_html": page_html
        })


def article(request, username, pk):
    user_obj = get_object_or_404(models.UserInfo, username=username)
    blog_obj = user_obj.blog
    article_obj = models.Article.objects.filter(id=pk).first()
    comment_obj_list = models.Comment.objects.filter(article=article_obj)
    return render(request, "article_tree.html", {
        "article_obj": article_obj,
        "username": username,
        "blog_obj": blog_obj,
        "comment_obj_list": comment_obj_list
    })


def up_down(request):
    # 1. 需求分析
    # 			1. 没有登录不能点赞
    # 			2. 点赞成功之后 页面上点赞数立马更新 下方会有点赞成功的提示
    # 			3. 同一个人只能给同一篇文章点赞一次
    # 			4. 点赞和反对两个只能选一个
    # 			5. 不能给自己点赞
    #
    # 			6. 点赞可以取消
    # 		2. 需求实现
    # 			1. 点赞？
    # 				谁   给 哪篇文章  点赞还是反对？
    res = {"code": 0}
    if request.method == "POST":
        user_id = request.POST.get("userId")
        article_id = request.POST.get("articleId")
        is_up = request.POST.get("isUp")  # 注意这里的is_up是 小写的true <class 'str'>，且是字符串
        # print(is_up, type(is_up))
        is_up = True if is_up.upper() == "TRUE" else False
        # 首先判断 不能给自己点赞； 通过前端传过来的文章id和用户id，去文章表里查询，如果能查到，表示是自己给自己点赞
        article_obj = models.Article.objects.filter(user_id=user_id, id=article_id).first()
        if article_obj:
            # 表示自己给自己点赞
            res["code"] = 1
            if is_up:
                res["msg"] = "您不能给自己点赞！"
            else:
                res["msg"] = "您不能反对自己！"
        else:
            # 同一个人只能给同一篇文章点赞一次
            # 点赞和反对两个只能选一个

            # 判断一下当前这个人和这篇文章 在点赞表里有没有记录
            is_exist = models.ArticleUpDown.objects.filter(user_id=user_id, article_id=article_id).first()
            if is_exist:
                res["code"] = 1

                # if is_exist.is_up:
                #     # 表示 是已经点赞过
                #     res["msg"] = "您已经给该文章点过赞了！"
                # else:
                #     # 表示 是已经反对过了
                #     res["msg"] = "您已经反对过该文章了！"

                res["msg"] = "您已经给该文章点过赞了！" if is_exist.is_up else "您已经反对过该文章了！"
            else:
                # 符合条件，真正点赞
                # 注意是 原子操作， 一下2操作同时进行
                with transaction.atomic():
                    # 1. 先创建点赞记录
                    models.ArticleUpDown.objects.create(user_id=user_id, article_id=article_id, is_up=is_up)
                    # 2. 再更新文章表
                    if is_up:
                        # 创建文章表中的点赞字段 up_count
                        models.Article.objects.filter(id=article_id).update(up_count=F('up_count')+1)
                    else:
                        # 创建文章表中的反对字段 down_count
                        models.Article.objects.filter(id=article_id).update(down_count=F("down_count")+1)
                    res["msg"] = "点赞成功！" if is_up else "反对成功！"
    return JsonResponse(res)


def comment(request):
    res = {"code": 0}
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        article_id = request.POST.get("article_id")
        content = request.POST.get("content")
        parent_id = request.POST.get("parent_id")
        # 创建评论内容
        with transaction.atomic():
            # 1. 先去创建新评论
            if parent_id:  # 如果有父id，需要把父id 也存储
                new_comment_obj = models.Comment.objects.create(user_id=user_id,
                                                                article_id=article_id,
                                                                content=content,
                                                                parent_comment_id=parent_id)
            else:
                # 没有父id,只是一级评论
                new_comment_obj = models.Comment.objects.create(user_id=user_id, article_id=article_id, content=content)
            # 2. 去更新该文章的评论数
            models.Article.objects.filter(id=article_id).update(comment_count=F("comment_count")+1)
            print(content)
            res["data"] = {
                "parent_id": parent_id,
                "new_content": content,
                "username": new_comment_obj.user.username,
                "create_time": new_comment_obj.create_time.strftime("%Y-%m-%d %H:%M")
            }
    return JsonResponse(res)


def comment_tree(request, article_id):
    res = {"code": 0}
    comment_obj_list = models.Comment.objects.filter(article_id=article_id).order_by("-create_time")
    # 需要把Queryset数据转化为列表 才能序列化
    res["data"] = [{
                    "id": comment.id,
                    "content": comment.content,
                    "username": comment.user.username,
                    "create_time": comment.create_time.strftime("%Y-%m-%d %H:%M"),
                    "pid": comment.parent_comment_id}for comment in comment_obj_list]
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        article_id = request.POST.get("article_id")
        content = request.POST.get("content")
        parent_id = request.POST.get("parent_id")
        # 创建评论内容
        with transaction.atomic():
            # 1. 先去创建新评论
            if parent_id:  # 如果有父id，需要把父id 也存储
                new_comment_obj = models.Comment.objects.create(user_id=user_id,
                                                                article_id=article_id,
                                                                content=content,
                                                                parent_comment_id=parent_id)
            else:
                # 没有父id,只是一级评论
                new_comment_obj = models.Comment.objects.create(user_id=user_id, article_id=article_id, content=content)
            # 2. 去更新该文章的评论数
            models.Article.objects.filter(id=article_id).update(comment_count=F("comment_count") + 1)
            res["data"] = {
                "parent_id": parent_id,
                "new_content": content,
                "username": new_comment_obj.user.username,
                "create_time": new_comment_obj.create_time.strftime("%Y-%m-%d %H:%M")
            }
    return JsonResponse(res)


@login_required
def backend(request):
    article_list = models.Article.objects.filter(user=request.user)
    return render(request, "backend.html", {"article_list": article_list})


def add_article(request):
    err_msg = ""
    if request.method == "POST":
        article_title = request.POST.get("title")
        content = request.POST.get("content")
        category_id = request.POST.get("category")
        if content:
            # 清洗用户发布的文章的内容，去掉script标签
            soup = BeautifulSoup(content, "html.parser")
            script_list = soup.select("script")  # 挑选出所有的script标签，生成一个列表
            for script in script_list:
                script.decompose()  # 删除所有的script标签
            # print(soup.text)  # 只读取文本,注意这是属性
            # print(soup.prettify())  # 读取规范化的html文档， 注意这是方法

            # 写入数据库
            with transaction.atomic():
                # 先写文章
                article_obj = models.Article.objects.create(
                    title=article_title,
                    desc=soup.text[0: 150],  # 文章描述一般都是文本
                    category_id=category_id,
                    user=request.user
                )
                # 同时要写文章详情
                models.ArticleDetail.objects.create(
                    content=soup.prettify(),
                    article=article_obj
                )
            return redirect("/blog/backend/")
        else:
            err_msg = "提交内容为空"
    category_list = models.Category.objects.filter(blog__userinfo=request.user)
    return render(request, "add_article.html", {"category_list": category_list, "err_msg": err_msg})


# 富文本编辑器的图片上传
def upload(request):
    print(request.FILES)
    res = {"error": 0}  # 必须是error
    file_obj = request.FILES.get("imgFile")
    print(file_obj.name)
    file_path = os.path.join(settings.MEDIA_ROOT, "article_img", file_obj.name)
    with open(file_path, "wb") as f:
        for chunk in file_obj.chunks():
            f.write(chunk)
    res["url"] = "/media/article_img/" + file_obj.name  # 必须有个叫url的
    return JsonResponse(res)


@login_required
def del_article(request, del_id):
    models.Article.objects.filter(id=del_id).delete()
    return redirect("/blog/backend")


def edit_article(request, edit_id):
    err_msg = ""
    edit_article_obj = models.Article.objects.filter(id=edit_id).first()
    category_list = models.Category.objects.filter(blog__userinfo=request.user)
    if request.method == "POST":
        article_title = request.POST.get("title")
        content = request.POST.get("content")
        category_id = request.POST.get("category")
        if content:
            # 清洗用户发布的文章的内容，去掉script标签
            soup = BeautifulSoup(content, "html.parser")
            script_list = soup.select("script")  # 挑选出所有的script标签，生成一个列表
            for script in script_list:
                script.decompose()  # 删除所有的script标签
            # print(soup.text)  # 只读取文本,注意这是属性
            # print(soup.prettify())  # 读取规范化的html文档， 注意这是方法

            # 写入数据库
            with transaction.atomic():
                # 先更新文章
                edit_article_obj.title = article_title
                edit_article_obj.desc = soup.text[0: 150]
                edit_article_obj.category_id = category_id
                edit_article_obj.user = request.user
                edit_article_obj.save()
                # 同时要更新文章详情
                detail_obj = models.ArticleDetail.objects.filter(article_id=edit_id).first()
                detail_obj.content = soup.prettify()
                detail_obj.save()
            return redirect("/blog/backend/")
        else:
            err_msg = "提交内容为空"
    return render(request, "edit_article.html", {"edit_article_obj": edit_article_obj,
                                                 "category_list": category_list,
                                                 "err_msg": err_msg
                                                 })



