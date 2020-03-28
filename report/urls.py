from django.urls import path

from . import views

app_name = 'report'

urlpatterns = [
    path('', views.index, name='index'),
    path('drinks/', views.drinks, name='drinks'),
    path('members_per_month/', views.members_per_month, name='members_per_month'),
    path('member_report/', views.member_report_view, name='member_report'),
    path('recharges.json', views.recharges, name='recharges'),
    path('admin/tan', views.admin_tan, name='tan')
]
