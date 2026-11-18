from django.contrib import admin

from .models import RiwayatSeleksi


@admin.register(RiwayatSeleksi)
class RiwayatSeleksiAdmin(admin.ModelAdmin):
    list_display = (
        'nama_pelamar',
        'tes_coding',
        'wawancara',
        'portofolio_uiux',
        'pengalaman_tahun',
        'status_kelulusan',
        'estimasi_gaji',
        'tanggal_input',
    )
