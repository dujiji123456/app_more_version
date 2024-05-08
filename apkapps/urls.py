from django.urls import path
from apkapps import views


urlpatterns = [
    path('search/',views.async_search_apk_function),#从网站获取数据
    path('show_apk/',views.earch_apk_more_version),#从数据库获取数据
]
