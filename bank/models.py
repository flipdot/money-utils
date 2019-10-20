from django.db import models

class TanRequest(models.Model):
    date = models.DateTimeField(primary_key=True, auto_now_add=True)
    expired = models.BooleanField(default=False)
    challenge = models.TextField()
    hhduc = models.TextField(null=True)
    answer = models.TextField(null=True)
