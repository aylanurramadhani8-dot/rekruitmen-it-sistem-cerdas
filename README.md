# Sistem Cerdas Seleksi Programmer IT

Aplikasi Django untuk mengklasifikasikan kelayakan pelamar programmer IT dan
mengestimasi gaji bulanan menggunakan machine learning.

## Menjalankan aplikasi

Gunakan Python dan pasang dependensi:

```powershell
python -m pip install -r requirements.txt
```

Opsional, isi `COHERE_API_KEY` di `.env` untuk mengaktifkan penjelasan Cohere.
Tanpa kunci API atau saat layanan tidak tersedia, aplikasi tetap menampilkan
penjelasan otomatis.

Latih model dan buat grafik visualisasi, kemudian siapkan database:

```powershell
python train_model.py
python manage.py migrate
```

Jalankan server pengembangan:

```powershell
python manage.py runserver
```

Buka `http://127.0.0.1:8000/`. Model tersimpan di `ml_models/`, grafik di
`static/images/`, dan data riwayat disimpan di `db.sqlite3`.

## Pengujian

```powershell
python manage.py check
python manage.py test seleksi_it
```
