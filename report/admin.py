from django.contrib import admin

from .models import *

admin.register(Member)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('applicant_name', 'member', 'date', 'entry_date', 'purpose', 'amount',
        'import_date', 'tx_id')
    date_hierarchy = 'date'

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'nick', 'first_name', 'last_name', 'email', 'entry_date', 'exit_date',
        'pay_interval', 'last_fee', 'fee')
    date_hierarchy = 'entry_date'

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_str', 'value_dt')

@admin.register(FeeEntry)
class FeeEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'member', 'month', 'fee', 'pay_interval', 'detect_method', 'tx')
    date_hierarchy = 'month'
