from .filters import *
from .models import *


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "applicant_name",
        "member",
        "date",
        "entry_date",
        "purpose",
        "amount",
        "import_date",
        "tx_id",
    )
    date_hierarchy = "date"
    list_filter = ("date", "import_date", "member", "applicant_name")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("admin.css",)}

    def is_member(self, obj):
        return obj.is_member()

    list_display = (
        "id",
        "is_member",
        "nick",
        "first_name",
        "last_name",
        "email",
        "entry_date",
        "exit_date",
        "pay_interval",
        "last_fee",
        "fee",
    )
    list_filter = (
        IsMemberFilter,
        "entry_date",
        "exit_date",
        "pay_interval",
        "last_fee",
        "fee",
    )

    is_member.boolean = True
    is_member.admin_order_field = "exit_date"

    date_hierarchy = "entry_date"
    ordering = ("id",)


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ("key", "value_str", "value_dt")


@admin.register(FeeEntry)
class FeeEntryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "member",
        "month",
        "fee",
        "pay_interval",
        "detect_method",
        "tx",
    )
    date_hierarchy = "month"

    list_filter = ("detect_method", "month", "fee", "pay_interval", "member")
