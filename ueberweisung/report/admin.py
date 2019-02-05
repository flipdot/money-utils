from django.contrib import admin

from .models import *

admin.register(Member)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    pass

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    pass

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    pass

@admin.register(FeeEntry)
class FeeEntryAdmin(admin.ModelAdmin):
    pass
