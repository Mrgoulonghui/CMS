#!/usr/bin/env python
# -*- coding:utf8 -*-

import os


if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BBS.settings")
    import django
    django.setup()

    from blog import models
    from django.db.models import Count

    # ret = models.Article.objects.values("create_time")
    # for i in ret:
    #     print(i.get("create_time"))
    # ret = models.Article.objects.filter(user__username="觉先生").extra(
    #     select={"y_m": "DATE_FORMAT(create_time, '%%Y年%%m月')"}
    # ).values("y_m").annotate(num=Count("title")).values("y_m", "num")
    # print(ret)

    # user_obj = models.UserInfo.objects.filter(username="觉先生").first()
    # article_obj_list = models.Article.objects.filter(user=user_obj).order_by("-create_time")
    # print(article_obj_list)
    # print("========================")
    # archive_list = article_obj_list.extra(
    #     select={"y_m": "DATE_FORMAT(create_time, '%%Y年%%m月')"}
    # ).values("y_m").annotate(num=Count("id")).values("y_m", "num")
    # print(archive_list)

    obj = models.Article.objects.get(id=8)
    print(obj)
    print(obj.articledetail.content)

