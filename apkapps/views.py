from django.shortcuts import render
from apkapps.apk_search import APKPureScraper
import asyncio
from django.http import JsonResponse
# Create your views here.
from apkapps.models import MoreVersionApk
from pymysql import cursors


async def process_request(app_id):
    apk_scraper = APKPureScraper()
    result = await asyncio.get_event_loop().run_in_executor(None, apk_scraper.main, app_id)
    return result

async def async_search_apk_function(request):
    if request.method == 'POST':
        app_id = request.POST.get('app_id')
        result = await process_request(app_id)
        if result == '获取失败':



            return JsonResponse({
                'code': 1,
                'msg': '失败',
                # 'data': result
            })
        else:
            return JsonResponse({
                'code': 0,
                'msg': '成功',
                # 'data': result
            })












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
                'msg':'success',
                'data': data
            })
        else:
            return JsonResponse({
                'code': 400,
                'msg': 'defeat',
                'data': '数据库中搜索不到请先爬取数据'
            })









