from django.urls import path

from . import views

app_name = 'seleksi_it'

urlpatterns = [
    path('', views.index, name='index'),
    path('riwayat/<int:pk>/hapus/', views.hapus_riwayat, name='hapus_riwayat'),
]
