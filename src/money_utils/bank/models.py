from django.db import models


class TanRequest(models.Model):
    date = models.DateTimeField(primary_key=True, auto_now_add=True)
    expired = models.BooleanField(default=False)
    challenge = models.TextField()
    hhduc = models.TextField(null=True)
    answer = models.TextField(null=True)

    @classmethod
    def active_requests(cls):
        return cls.objects.filter(expired=False).filter(answer=None).order_by("-date")

    @classmethod
    def expired_requests(cls):
        return cls.objects.filter(expired=True)

    @classmethod
    def active_request(cls):
        res = cls.active_requests()
        if res:
            return res[0]
