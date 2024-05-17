import base64

from django.shortcuts import render
from apkapps.apk_search import APKPureScraper
import asyncio
from django.http import JsonResponse,HttpResponse
# Create your views here.
from apkapps.models import MoreVersionApk
from pymysql import cursors
from apkapps.RSA算法 import RSA
import rsa


async def process_request(app_id):
    apk_scraper = APKPureScraper()
    result = await asyncio.get_event_loop().run_in_executor(None, apk_scraper.main, app_id)
    return result


async def async_search_apk_function(request):
    rsa = RSA()
    if request.method == 'POST':
        app_id = request.POST.get('app_id')
        signature = request.POST.get('signature')
        print(signature)

        if not signature:
            return JsonResponse({
                'message': '签名为空',
                'status': 'Fail',
            })

        aa = rsa.decrypt(signature)
        print(aa)

        if rsa.decrypt(signature):
            if rsa.decrypt(signature) == app_id:
                result = await process_request(app_id)
                if result == '获取失败':
                    return JsonResponse({
                        'code': 1,
                        # 'msg': '获取失败',  # 修改为具体的错误消息
                        # 'data': result
                    })

                elif result == '无最新版本':
                    return JsonResponse({
                        'code': 2,
                        # 'msg': '无最新版本',  # 修改为具体的错误消息
                        # 'data': result
                    })

                else:
                    for item in result:
                        apk_version = item['apk_version']
                        if item["is_update"] == 1:
                            return JsonResponse({
                                'code': 0,
                                # 'msg': f'获取最新版本{apk_version}',
                                # 'data': result
                            })
                        else:
                            return JsonResponse({
                                'code': 0,
                                # 'msg': f'版本{apk_version}获取成功',
                                # 'data': result
                            })
            else:
                print('包id不匹配', rsa.decrypt(signature))
                return JsonResponse({
                    'message': '匹配不成功',
                    'status': 'Fail',
                })
        else:
            print(rsa.decrypt(signature), '不是base64格式')
            return JsonResponse({
                'message': '匹配不成功',
                'status': 'Fail',
            })
    return HttpResponse("Success")


def earch_apk_more_version(request):
    if request.method == 'POST':
        app_id = request.POST.get('app_id')
        print(app_id)
        all_apk = MoreVersionApk.objects.filter(apk_name=app_id)
        print(all_apk)
        data = []
        if len(all_apk) > 0:
            for i in all_apk:
                data.append({
                    'apk_name': i.apk_name,
                    'apk_version': i.apk_version,
                    'apk_download_url': i.apk_download_url,
                    'update_content': i.update_content,
                    'down_path': i.down_path,
                    'status': i.status
                })

            # print(data)
            return JsonResponse({
                'code': 200,
                'msg': 'success',
                'data': data
            })
        else:
            return JsonResponse({
                'code': 400,
                'msg': 'defeat',
                'data': '数据库中搜索不到请先爬取数据'
            })
