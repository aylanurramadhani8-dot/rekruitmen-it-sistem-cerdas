from django.db import models


class RiwayatSeleksi(models.Model):
    nama_pelamar = models.CharField(max_length=150)
    tes_coding = models.FloatField()
    wawancara = models.FloatField()
    portofolio_uiux = models.FloatField()
    pengalaman_tahun = models.FloatField()
    status_kelulusan = models.CharField(max_length=20)
    estimasi_gaji = models.FloatField()
    penjelasan_ai = models.TextField()
    tanggal_input = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal_input']
        verbose_name = 'Riwayat seleksi'
        verbose_name_plural = 'Riwayat seleksi'

    def __str__(self):
        return f'{self.nama_pelamar} - {self.status_kelulusan}'
