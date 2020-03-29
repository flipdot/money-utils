from django.contrib import admin
from .models import *

@admin.register(TanRequest)
class TanRequestAdmin(admin.ModelAdmin):
    list_display = ('date', 'expired', 'challenge', 'hhduc', 'answer')
