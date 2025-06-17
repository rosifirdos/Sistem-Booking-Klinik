# Sistem Booking Dokter Klinik Awan

![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat&logo=python)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green?style=flat&logo=qt)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?style=flat&logo=sqlite)
![Google Gemini API](https://img.shields.io/badge/AI-Google_Gemini_API-red?style=flat&logo=google)

Sebuah aplikasi desktop sederhana untuk manajemen booking janji temu dokter di Klinik Awan, dirancang untuk meningkatkan efisiensi operasional dan pengalaman pasien.

---

## Daftar Isi
- [Tentang Proyek](#tentang-proyek)
- [Fitur Unggulan](#fitur-unggulan)
- [Teknologi yang Digunakan](#teknologi-yang-digunakan)
- [Struktur Proyek](#struktur-proyek)
- [Cara Menginstal dan Menjalankan](#cara-menginstal-dan-menjalankan)
- [Penggunaan API Key (Penting!)](#penggunaan-api-key-penting)
- [Perancangan Class Diagram](#perancangan-class-diagram)
- [Kontribusi](#kontribusi)
- [Lisensi](#lisensi)
- [Kontak](#kontak)

---

## Tentang Proyek

Proyek ini adalah implementasi dari **Aplikasi Booking Sederhana** dengan variasi entitas **Dokter**, sesuai dengan tema proyek PBO. Sistem Booking Dokter Klinik Awan bertujuan untuk mengatasi tantangan dalam proses booking janji temu yang masih manual atau kurang efisien. Aplikasi ini menyediakan solusi digital yang intuitif, membantu pasien menemukan dokter yang tepat, mengelola jadwal secara *real-time*, dan bahkan mendapatkan bantuan instan melalui asisten virtual berbasis AI.

**Masalah yang Diatasi:**
- Ketidakefisienan proses booking manual.
- Kesulitan pasien dalam mencari informasi dokter dan ketersediaan jadwal.
- Potensi kesalahan pencatatan dan manajemen data.

**Solusi yang Ditawarkan:**
- Otomatisasi proses booking untuk efisiensi klinik.
- Peningkatan aksesibilitas informasi bagi pasien.
- Pengalaman pengguna yang lebih baik melalui UI interaktif dan asisten AI.

## Fitur Unggulan

Sistem Booking Dokter ini dilengkapi dengan beberapa fitur utama yang dirancang untuk kemudahan penggunaan dan efisiensi:

1.  **Daftar Dokter & Informasi Lengkap:**
    * Menyediakan akses mudah ke informasi lengkap setiap dokter di klinik.
    * Pengguna dapat dengan cepat **memfilter dokter berdasarkan spesialisasi**, menyederhanakan proses pencarian dokter yang sesuai (misalnya, untuk gigi, anak, umum).

2.  **Manajemen Booking Janji Temu yang Efisien:**
    * Memfasilitasi proses pembuatan janji temu dokter yang terstruktur, termasuk pemilihan tanggal dan jadwal yang tersedia.
    * Mencakup fitur **hapus booking** yang tidak hanya membatalkan janji temu tetapi juga secara otomatis mengosongkan kembali jadwal dokter agar tersedia untuk pasien lain, memastikan akurasi data jadwal.

3.  **Asisten Virtual Cerdas (MediBot):**
    * *Chatbot* interaktif berbasis AI yang siap memberikan informasi dan panduan.
    * Dengan **respon yang ramah dan informatif**, MediBot membantu pengguna menemukan data dokter, jadwal, atau rekomendasi dokter yang tepat, meningkatkan pengalaman interaksi secara signifikan dengan mengambil data langsung dari sistem klinik.

## Teknologi yang Digunakan

Proyek ini dibangun menggunakan teknologi-teknologi berikut:

-   **Python 3.x:** Bahasa pemrograman utama yang digunakan.
-   **PyQt5:** *Framework* GUI untuk membangun antarmuka aplikasi desktop yang intuitif dan *user-friendly*.
-   **SQLite:** Sistem manajemen basis data relasional yang ringan dan mandiri, digunakan untuk menyimpan data dokter, jadwal, dan booking secara efisien.
-   **Google Gemini API:** Digunakan untuk mengintegrasikan kemampuan AI generatif pada asisten virtual (MediBot), memungkinkan pemahaman bahasa alami dan respons cerdas. Implementasi menggunakan pendekatan **Retrieval-Augmented Generation (RAG)** untuk memberikan jawaban yang akurat dari data spesifik klinik.
-   **`python-dotenv`:** Digunakan untuk mengelola variabel lingkungan (terutama Gemini API Key) dengan aman.

## Struktur Proyek
aplikasi_dokter/
├── .venv/                         # Lingkungan virtual Python (dabaikan oleh Git)
├── .gitignore                     # File yang diabaikan oleh Git
├── config.py                      # File konfigurasi untuk API Key (diabaikan oleh Git)
├── database.py                    # Modul untuk manajemen koneksi dan tabel database SQLite
├── main.py                        # File utama yang menjalankan aplikasi GUI PyQt5
├── requirements.txt               # Daftar dependensi Python
└── services/                      # Direktori untuk modul layanan dan logika bisnis
├── init.py                # Menandakan direktori sebagai paket Python
├── app_tools.py               # Modul untuk fungsi-fungsi pembantu umum
├── booking_service.py         # Modul untuk logika bisnis terkait booking dokter
└── chatbot.py                 # Modul untuk implementasi asisten virtual MediBot (interaksi Gemini API)

## Cara Menginstal dan Menjalankan

Ikuti langkah-langkah di bawah ini untuk mengatur dan menjalankan proyek di komputer lokal Anda.

### Prasyarat

-   [Python 3.x](https://www.python.org/downloads/) terinstal.
-   Git terinstal (untuk mengkloning repositori).

### Instalasi

1.  **Kloning Repositori:**
    ```bash
    git clone [https://github.com/NamaPenggunaAnda/Sistem-Booking-Klinik-Awan.git](https://github.com/NamaPenggunaAnda/Sistem-Booking-Klinik-Awan.git)
    cd Sistem-Booking-Klinik-Awan
    ```
    *(Ganti `NamaPenggunaAnda/Sistem-Booking-Klinik-Awan` dengan URL repositori Anda yang sebenarnya)*

2.  **Buat dan Aktifkan Lingkungan Virtual:**
    ```bash
    python -m venv .venv
    ```
    * **Windows:**
        ```bash
        .venv\Scripts\activate
        ```
    * **Linux/macOS:**
        ```bash
        source .venv/bin/activate
        ```

3.  **Instal Dependensi:**
    ```bash
    pip install -r requirements.txt
    ```

### Menjalankan Aplikasi

Setelah semua dependensi terinstal dan lingkungan virtual aktif:

```bash
python main.py

Aplikasi Sistem Booking Dokter akan terbuka dalam jendela desktop.

Penggunaan API Key (Penting!)
Fitur asisten virtual (MediBot) menggunakan Google Gemini API. Untuk menjalankan fitur ini, Anda perlu mendapatkan dan mengatur API Key Anda sendiri.

Dapatkan API Key:

Kunjungi Google AI Studio dan buat API Key baru.
Atur API Key:

Buat file bernama .env di direktori akar proyek (sejajar dengan main.py).

Tambahkan baris berikut ke dalam file .env:

GEMINI_API_KEY="PASTE_API_KEY_ANDA_DI_SINI"
(Ganti PASTE_API_KEY_ANDA_DI_SINI dengan API Key Gemini Anda yang sebenarnya).

Alternatif (untuk pengembangan/debug): Anda juga bisa menempatkan API Key langsung di file config.py yang sudah disediakan, namun ini tidak disarankan untuk penggunaan jangka panjang atau produksi. Pastikan config.py memiliki baris GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" dan ganti placeholder tersebut.

Penting: File .env sudah masuk ke dalam .gitignore, sehingga API Key Anda tidak akan terunggah ke repositori publik.

Kontribusi
Kontribusi dipersilakan! Jika Anda memiliki saran atau menemukan bug, silakan buka issue atau buat pull request.

Lisensi
Proyek ini dilisensikan di bawah MIT License.

Kontak
Jika Anda memiliki pertanyaan, jangan ragu untuk menghubungi saya:
Nama: Awanda Rosi Firdaus
Email: awandarosifirdaus@gmail.com
GitHub: 
