import math
import os
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from django.test import TestCase
from django.urls import reverse

from .models import RiwayatSeleksi


class SeleksiPelamarTests(TestCase):
    @patch.dict(os.environ, {'COHERE_API_KEY': ''})
    def test_chatbot_api_returns_fallback_json(self):
        response = self.client.post(
            reverse('seleksi_it:chatbot_api'),
            data={
                'message': 'Bagaimana cara kerja penilaian sistem ini?',
                'context': {
                    'nama_pelamar': 'Andi Pratama',
                    'tes_coding': 70,
                    'wawancara': 80,
                    'portofolio_uiux': 90,
                    'pengalaman_tahun': 2,
                    'status_kelulusan': 'DITOLAK',
                    'estimasi_gaji': 8.5,
                },
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('reply', payload)
        self.assertFalse(payload['used_ai'])
        self.assertIn('75', payload['reply'])

    @patch.dict(os.environ, {'COHERE_API_KEY': ''})
    def test_chatbot_api_personalizes_rejected_result(self):
        response = self.client.post(
            reverse('seleksi_it:chatbot_api'),
            data={
                'message': 'Analisis hasil seleksi saya',
                'context': {
                    'tes_coding': 70,
                    'wawancara': 80,
                    'portofolio_uiux': 90,
                    'status_kelulusan': 'DITOLAK',
                },
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('tes coding 70/100', response.json()['reply'])

    @patch.dict(os.environ, {'COHERE_API_KEY': 'test-api-key'})
    @patch('seleksi_it.views.cohere.Client')
    def test_chatbot_api_uses_cohere_text_and_preamble(self, cohere_client):
        cohere_client.return_value.chat.return_value = SimpleNamespace(
            text='  Saran karier yang kontekstual.  '
        )

        response = self.client.post(
            reverse('seleksi_it:chatbot_api'),
            data={
                'message': 'Apa saran untuk hasil saya?',
                'context': {
                    'nama_pelamar': 'Rahasia Kandidat',
                    'tes_coding': 78,
                    'status_kelulusan': 'DITERIMA',
                },
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {'reply': 'Saran karier yang kontekstual.', 'used_ai': True},
        )
        _, call = cohere_client.return_value.chat.call_args
        self.assertIn('Asisten Virtual Konsultan Rekrutmen & Karier IT', call['preamble'])
        self.assertNotIn('Rahasia Kandidat', call['message'])

    @patch.dict(os.environ, {'COHERE_API_KEY': 'test-api-key'})
    @patch('seleksi_it.views.cohere.Client')
    def test_chatbot_api_falls_back_when_cohere_is_unavailable(self, cohere_client):
        cohere_client.return_value.chat.side_effect = httpx.ConnectError('offline')

        response = self.client.post(
            reverse('seleksi_it:chatbot_api'),
            data={'message': 'Tips wawancara IT?'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['used_ai'])
        self.assertIn('wawancara IT', response.json()['reply'])

    def test_chatbot_api_rejects_empty_message(self):
        response = self.client.post(
            reverse('seleksi_it:chatbot_api'),
            data={'message': '  '},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_dashboard_renders_form_and_visualizations(self):
        response = self.client.get(reverse('seleksi_it:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Input data pelamar')
        self.assertContains(response, 'Asisten Konsultasi IT')
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
