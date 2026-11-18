from pathlib import Path

import joblib
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeClassifier, plot_tree

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / 'ml_models'
IMAGE_DIR = BASE_DIR / 'static' / 'images'

APPLICANT_DATA_URL = (
    'https://raw.githubusercontent.com/aylanurramadhani8-dot/'
    'data-modul-03-sistem-cerdas/refs/heads/main/data_pelamar_it.csv'
)
SALARY_DATA_URL = (
    'https://raw.githubusercontent.com/aylanurramadhani8-dot/'
    'data-modul-03-sistem-cerdas/refs/heads/main/data_gaji_progammer.csv'
)


def train_classification_model():
    data = pd.read_csv(APPLICANT_DATA_URL)
    features = ['tes_coding', 'wawancara', 'portofolio_uiux']
    missing_columns = set(features).difference(data.columns)
    if missing_columns:
        raise ValueError(f'Kolom dataset pelamar tidak ditemukan: {missing_columns}')

    data['skor_akhir'] = 0.6 * data['tes_coding'] + 0.4 * data['wawancara']
    data['status'] = (data['skor_akhir'] >= 75).map({
        True: 'DITERIMA',
        False: 'DITOLAK',
    })
    model = DecisionTreeClassifier(max_depth=2, random_state=42)
    model.fit(data[features], data['status'])
    joblib.dump(model, MODEL_DIR / 'model_rekrutmen.joblib')

    figure, axis = plt.subplots(figsize=(13, 7))
    plot_tree(
        model,
        feature_names=features,
        class_names=model.classes_,
        filled=True,
        rounded=True,
        ax=axis,
    )
    axis.set_title('Pohon Keputusan Seleksi Pelamar Programmer IT')
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'decision_tree.png', dpi=180)
    plt.close(figure)
    return model


def train_salary_model():
    data = pd.read_csv(SALARY_DATA_URL)
    features = ['pengalaman_tahun', 'skor_tes']
    missing_columns = set(features + ['gaji_juta']).difference(data.columns)
    if missing_columns:
        raise ValueError(f'Kolom dataset gaji tidak ditemukan: {missing_columns}')

    model = LinearRegression()
    model.fit(data[features], data['gaji_juta'])
    joblib.dump(model, MODEL_DIR / 'model_gaji.joblib')

    figure, axis = plt.subplots(figsize=(10, 6))
    points = axis.scatter(
        data['pengalaman_tahun'],
        data['gaji_juta'],
        c=data['skor_tes'],
        cmap='viridis',
        s=75,
        edgecolor='white',
        linewidth=0.7,
        label='Data aktual',
    )
    experience_range = pd.Series(
        [data['pengalaman_tahun'].min(), data['pengalaman_tahun'].max()],
        name='pengalaman_tahun',
    )
    regression_features = pd.DataFrame({
        'pengalaman_tahun': experience_range,
        'skor_tes': data['skor_tes'].mean(),
    })
    axis.plot(
        experience_range,
        model.predict(regression_features),
        color='#ef4444',
        linewidth=2.5,
        label='Garis regresi (skor tes rata-rata)',
    )
    figure.colorbar(points, ax=axis, label='Skor tes')
    axis.set_title('Regresi Estimasi Gaji Programmer')
    axis.set_xlabel('Pengalaman kerja (tahun)')
    axis.set_ylabel('Gaji (juta rupiah per bulan)')
    axis.grid(alpha=0.2)
    axis.legend()
    figure.tight_layout()
    figure.savefig(IMAGE_DIR / 'regresi_gaji.png', dpi=180)
    plt.close(figure)
    return model


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    train_classification_model()
    train_salary_model()
    print(f'Model tersimpan di: {MODEL_DIR}')
    print(f'Grafik tersimpan di: {IMAGE_DIR}')


if __name__ == '__main__':
    main()
