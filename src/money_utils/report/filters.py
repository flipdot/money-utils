from django.contrib import admin


class IsMemberFilter(admin.SimpleListFilter):
    title = "is_member"
    parameter_name = "is_member"

    def lookups(self, request, model_admin):
        return (
            ("Yes", "Yes"),
            ("No", "No"),
        )

    def queryset(self, request, queryset):
        if self.value() == "Yes":
            return queryset.filter(exit_date__isnull=True)
        elif self.value() == "No":
            return queryset.filter(exit_date__isnull=False)
