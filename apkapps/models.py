from django.db import models


class MoreVersionApk(models.Model):
    apk_version = models.CharField(max_length=255)
    apk_name = models.CharField(max_length=255)
    apk_download_url = models.CharField(max_length=255)
    update_content = models.TextField(null=True)
    down_path = models.CharField(max_length=255,null=True)
    status = models.IntegerField(default=0)

    class Meta:
        unique_together = [['apk_name', 'apk_version']]
