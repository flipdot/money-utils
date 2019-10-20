from django.urls import path

from . import views

app_name = 'report'

urlpatterns = [
    path('', views.index, name='index'),
    path('drinks/', views.drinks, name='drinks'),
    path('member/', views.member, name='member'),
    path('recharges.json', views.recharges, name='recharges'),
    path('admin/tan', views.admin_tan, name='tan')
]
