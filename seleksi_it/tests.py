import math
import os
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .models import RiwayatSeleksi


class SeleksiPelamarTests(TestCase):
    def test_dashboard_renders_form_and_visualizations(self):
        response = self.client.get(reverse('seleksi_it:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Input data pelamar')
        self.assertContains(response, 'images/decision_tree.png')
        self.assertContains(response, 'images/regresi_gaji.png')

    @patch.dict(os.environ, {'COHERE_API_KEY': ''})
    def test_valid_submission_saves_predictions_and_fallback_explanation(self):
        response = self.client.post(reverse('seleksi_it:index'), {
            'nama_pelamar': 'Andi Pratama',
            'tes_coding': '88',
            'wawancara': '82',
            'portofolio_uiux': '90',
            'pengalaman_tahun': '3',
        })

        self.assertEqual(response.status_code, 302)
        record = RiwayatSeleksi.objects.get(nama_pelamar='Andi Pratama')
        self.assertIn(record.status_kelulusan, {'DITERIMA', 'DITOLAK'})
        self.assertTrue(math.isfinite(record.estimasi_gaji))
        self.assertIn('Berdasarkan nilai tes coding', record.penjelasan_ai)
        self.assertEqual(self.client.get(response.url).status_code, 200)

    @patch.dict(os.environ, {'COHERE_API_KEY': 'test-api-key'})
    @patch('seleksi_it.views.cohere.Client')
    def test_cohere_explanation_is_saved(self, cohere_client):
        cohere_client.return_value.chat.return_value = SimpleNamespace(
            text='  Kandidat menunjukkan kompetensi yang baik.  '
        )

        response = self.client.post(reverse('seleksi_it:index'), {
            'nama_pelamar': 'Siti Programmer',
            'tes_coding': '86',
            'wawancara': '84',
            'portofolio_uiux': '88',
            'pengalaman_tahun': '4',
        })

        self.assertEqual(response.status_code, 302)
        record = RiwayatSeleksi.objects.get(nama_pelamar='Siti Programmer')
        self.assertEqual(
            record.penjelasan_ai,
            'Kandidat menunjukkan kompetensi yang baik.',
        )
        cohere_client.return_value.chat.assert_called_once()

    @patch.dict(os.environ, {'COHERE_API_KEY': 'test-api-key'})
    @patch('seleksi_it.views.cohere.Client')
    def test_empty_cohere_text_uses_fallback_explanation(self, cohere_client):
        cohere_client.return_value.chat.return_value = SimpleNamespace(text='  ')

        response = self.client.post(reverse('seleksi_it:index'), {
            'nama_pelamar': 'Budi Empty',
            'tes_coding': '86',
            'wawancara': '84',
            'portofolio_uiux': '88',
            'pengalaman_tahun': '4',
        })

        self.assertEqual(response.status_code, 302)
        record = RiwayatSeleksi.objects.get(nama_pelamar='Budi Empty')
        self.assertIn('Berdasarkan nilai tes coding', record.penjelasan_ai)
        cohere_client.return_value.chat.assert_called_once()

    def test_invalid_score_does_not_create_history(self):
        response = self.client.post(reverse('seleksi_it:index'), {
            'nama_pelamar': 'Kandidat Invalid',
            'tes_coding': '101',
            'wawancara': '82',
            'portofolio_uiux': '90',
            'pengalaman_tahun': '3',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            RiwayatSeleksi.objects.filter(nama_pelamar='Kandidat Invalid').exists()
        )
        self.assertContains(response, 'Nilai harus berada di antara 0 dan 100.')

    def test_history_can_only_be_deleted_with_post(self):
        record = RiwayatSeleksi.objects.create(
            nama_pelamar='Kandidat Hapus',
            tes_coding=80,
            wawancara=80,
            portofolio_uiux=80,
            pengalaman_tahun=2,
            status_kelulusan='DITERIMA',
            estimasi_gaji=8,
            penjelasan_ai='Analisis',
        )
        delete_url = reverse('seleksi_it:hapus_riwayat', args=[record.pk])

        self.assertEqual(self.client.get(delete_url).status_code, 302)
        self.assertTrue(RiwayatSeleksi.objects.filter(pk=record.pk).exists())
        self.assertEqual(self.client.post(delete_url).status_code, 302)
        self.assertFalse(RiwayatSeleksi.objects.filter(pk=record.pk).exists())
