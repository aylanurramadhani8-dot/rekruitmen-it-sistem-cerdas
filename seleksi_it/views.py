import logging
from pathlib import Path

import cohere
import httpx
import joblib
import pandas as pd
from cohere.core.api_error import ApiError
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from dotenv import load_dotenv

from .forms import SeleksiPelamarForm
from .models import RiwayatSeleksi

logger = logging.getLogger(__name__)
load_dotenv(settings.BASE_DIR / '.env')


def _fallback_explanation(candidate, status, salary):
    status_text = 'memenuhi' if status == 'DITERIMA' else 'belum memenuhi'
    return (
        f"Berdasarkan nilai tes coding {candidate['tes_coding']:.1f}, wawancara "
        f"{candidate['wawancara']:.1f}, dan portofolio UI/UX "
        f"{candidate['portofolio_uiux']:.1f}, model klasifikasi menilai pelamar "
        f"{status_text} kriteria seleksi dengan status {status}. Estimasi gaji "
        f"sebesar Rp{salary:.2f} juta per bulan dihitung menggunakan model "
        f"regresi berdasarkan pengalaman kerja {candidate['pengalaman_tahun']:g} "
        f"tahun dan skor tes coding {candidate['tes_coding']:.1f}. Hasil ini "
        "merupakan estimasi berbasis data dan dapat disesuaikan dengan "
        "kebutuhan serta kebijakan perusahaan."
    )


def _generate_explanation(candidate, status, salary):
    from os import environ

    api_key = environ.get('COHERE_API_KEY', '').strip()
    fallback = _fallback_explanation(candidate, status, salary)
    if not api_key:
        return fallback, False

    prompt = (
        'Tuliskan satu paragraf penjelasan profesional dalam bahasa Indonesia '
        'mengenai kelayakan pelamar programmer IT dan alasan estimasi gajinya. '
        'Gunakan hanya informasi berikut, jangan mengubah hasil model, dan '
        'jelaskan bahwa gaji merupakan estimasi per bulan dalam juta rupiah.\n'
        f"Nama: {candidate['nama_pelamar']}\n"
        f"Tes coding: {candidate['tes_coding']:.1f}/100\n"
        f"Wawancara: {candidate['wawancara']:.1f}/100\n"
        f"Portofolio UI/UX: {candidate['portofolio_uiux']:.1f}/100\n"
        f"Pengalaman: {candidate['pengalaman_tahun']:g} tahun\n"
        f"Status model: {status}\n"
        f"Estimasi gaji: Rp{salary:.2f} juta per bulan"
    )
    try:
        response = cohere.Client(api_key=api_key).chat(
            model='command-r-08-2024',
            message=prompt,
            temperature=0.3,
        )
        explanation = (response.text or '').strip()
        if explanation:
            return explanation, True
        logger.warning('Cohere returned an empty explanation; using fallback.')
    except (ApiError, httpx.HTTPError):
        logger.exception('Cohere explanation request failed; using fallback.')
    return fallback, False


def index(request):
    if request.method == 'POST':
        form = SeleksiPelamarForm(request.POST)
        if form.is_valid():
            models_dir = Path(settings.BASE_DIR) / 'ml_models'
            classification_path = models_dir / 'model_rekrutmen.joblib'
            salary_path = models_dir / 'model_gaji.joblib'
            if not classification_path.is_file() or not salary_path.is_file():
                messages.error(
                    request,
                    'Model belum tersedia. Jalankan python train_model.py '
                    'terlebih dahulu.',
                )
                return redirect('seleksi_it:index')

            try:
                classifier = joblib.load(classification_path)
                salary_model = joblib.load(salary_path)
            except (OSError, EOFError, ValueError, ImportError) as error:
                logger.exception('Failed to load trained ML models.')
                messages.error(
                    request,
                    f'Model tidak dapat dimuat ({error}). Jalankan ulang '
                    'python train_model.py.',
                )
                return redirect('seleksi_it:index')

            candidate = form.cleaned_data
            classification_features = pd.DataFrame([{
                'tes_coding': candidate['tes_coding'],
                'wawancara': candidate['wawancara'],
                'portofolio_uiux': candidate['portofolio_uiux'],
            }])
            salary_features = pd.DataFrame([{
                'pengalaman_tahun': candidate['pengalaman_tahun'],
                'skor_tes': candidate['tes_coding'],
            }])
            status = classifier.predict(classification_features)[0]
            salary = float(salary_model.predict(salary_features)[0])
            explanation, used_ai = _generate_explanation(candidate, status, salary)

            result = form.save(commit=False)
            result.status_kelulusan = status
            result.estimasi_gaji = salary
            result.penjelasan_ai = explanation
            result.save()
            if not used_ai:
                messages.info(
                    request,
                    'Penjelasan menggunakan analisis otomatis karena layanan '
                    'Cohere tidak dikonfigurasi atau sedang tidak tersedia.',
                )
            return redirect(f"{reverse('seleksi_it:index')}?hasil={result.pk}")
    else:
        form = SeleksiPelamarForm()

    selected_id = request.GET.get('hasil')
    latest_result = None
    if selected_id:
        latest_result = RiwayatSeleksi.objects.filter(pk=selected_id).first()

    context = {
        'form': form,
        'latest_result': latest_result,
        'riwayat': RiwayatSeleksi.objects.all(),
    }
    return render(request, 'seleksi_it/index.html', context)


def hapus_riwayat(request, pk):
    if request.method != 'POST':
        return redirect('seleksi_it:index')
    record = get_object_or_404(RiwayatSeleksi, pk=pk)
    record.delete()
    messages.success(request, 'Riwayat seleksi berhasil dihapus.')
    return redirect('seleksi_it:index')
