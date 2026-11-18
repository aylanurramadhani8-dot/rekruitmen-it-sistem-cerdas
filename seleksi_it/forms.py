from django import forms

from .models import RiwayatSeleksi


class SeleksiPelamarForm(forms.ModelForm):
    class Meta:
        model = RiwayatSeleksi
        fields = [
            'nama_pelamar',
            'tes_coding',
            'wawancara',
            'portofolio_uiux',
            'pengalaman_tahun',
        ]
        labels = {
            'nama_pelamar': 'Nama pelamar',
            'tes_coding': 'Nilai tes coding',
            'wawancara': 'Nilai wawancara',
            'portofolio_uiux': 'Skor portofolio UI/UX',
            'pengalaman_tahun': 'Pengalaman kerja (tahun)',
        }
        widgets = {
            'nama_pelamar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Andi Pratama',
                'autocomplete': 'name',
            }),
            'tes_coding': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0–100',
                'min': 0,
                'max': 100,
                'step': 'any',
            }),
            'wawancara': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0–100',
                'min': 0,
                'max': 100,
                'step': 'any',
            }),
            'portofolio_uiux': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0–100',
                'min': 0,
                'max': 100,
                'step': 'any',
            }),
            'pengalaman_tahun': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: 2',
                'min': 0,
                'step': 'any',
            }),
        }

    def clean_tes_coding(self):
        return self._validate_score('tes_coding')

    def clean_wawancara(self):
        return self._validate_score('wawancara')

    def clean_portofolio_uiux(self):
        return self._validate_score('portofolio_uiux')

    def _validate_score(self, field_name):
        score = self.cleaned_data[field_name]
        if not 0 <= score <= 100:
            raise forms.ValidationError('Nilai harus berada di antara 0 dan 100.')
        return score

    def clean_pengalaman_tahun(self):
        years = self.cleaned_data['pengalaman_tahun']
        if years < 0:
            raise forms.ValidationError('Pengalaman kerja tidak boleh kurang dari 0.')
        return years
