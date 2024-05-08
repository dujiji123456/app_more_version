import requests
from tqdm import tqdm


def download_file(url, local_filename=None):
    """
    使用requests下载文件并显示进度条
    :param url: 文件的URL地址
    :param local_filename: 本地保存的文件名，默认为URL的最后一部分
    :return: 文件的本地路径
    """
    if local_filename is None:
        # 从URL中提取文件名
        local_filename = url.split('/')[-1]

    with requests.get(url, stream=True) as r:
        r.raise_for_status()

        total_size = int(r.headers.get('content-length', 0))

        with tqdm(total=total_size, unit='B', unit_scale=True, desc=local_filename, ncols=100) as pbar:
            with open('local_filename.apk', 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))


url = 'https://apkpure.net/crush-quotes-and-sayings/com.tangoquotes.crushquotes/downloading/5'
output_filename = 'aa.apk'
download_file(url)
