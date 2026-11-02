# DVWA Auto Install

Skrip ini menginstal dan mengonfigurasi DVWA (Damn Vulnerable Web Application) di Ubuntu dengan satu perintah.

## ⚠️ Peringatan Keamanan

- DVWA **sengaja dibuat rentan**. Gunakan hanya untuk belajar di VM lab.
- **Jangan** memasangnya di server yang terhubung ke internet.
- Hanya uji sistem milik sendiri atau sistem yang sudah memberi izin.
- Gunakan mode jaringan VM **Host-only** atau **NAT**. Mode **Bridged** membuat DVWA bisa diakses oleh perangkat lain di jaringan yang sama.

## Kebutuhan

- VM Ubuntu 24.04
- Akses `sudo`
- Koneksi internet

## Dukungan OS

| OS | Status | Keterangan |
|----|--------|------------|
| Ubuntu 24.04 LTS | Sudah diuji | Target utama skrip ini |
| Ubuntu versi lain | Belum diuji | Memakai `apt` yang sama, tetapi versi PHP berbeda |
| Debian, Kali, Linux Mint, dan distro berbasis `apt` lainnya | Belum diuji | Skrip menampilkan peringatan, lalu tetap berjalan |
| Fedora, RHEL, CentOS, Arch, openSUSE, dan distro non-`apt` lainnya | Belum didukung | Skrip akan berhenti karena `apt-get` tidak tersedia, jadi perlu disesuaikan dulu |

Ingin mencoba di versi Linux lain? Silakan saja dicoba. Sebaiknya buat snapshot VM terlebih dahulu supaya mudah kembali jika ada masalah. Hasilnya, baik berhasil maupun gagal, bisa dibagikan lewat tab Issues di repo ini.

## Cara Menjalankan

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/stillrg/dvwa-auto-install.git
cd dvwa-auto-install
sudo bash install-dvwa.sh
```

## Setelah Instalasi

- Buka `http://IP-VM/DVWA/` di browser.
- Login dengan `admin` / `password`.
- Level keamanan awal adalah `low`.
- IP VM bisa dilihat dengan perintah `hostname -I`.

## Yang Dilakukan Skrip

1. Menginstal Apache, MariaDB, dan PHP.
2. Meng-clone DVWA ke `/var/www/html/DVWA`.
3. Membuat database dan user `dvwa` dengan password acak.
4. Menulis konfigurasi DVWA.
5. Mengaktifkan setting PHP yang rentan hanya untuk folder DVWA.
6. Mengaktifkan `mod_rewrite`.
7. Menginstal dependensi lab API.
8. Membuka port 80 jika UFW aktif.
9. Membuat tabel database.
10. Memverifikasi login.

## Opsi

| Environment variable | Keterangan | Default |
|----------------------|------------|---------|
| `DVWA_SECURITY` | Level keamanan awal: `low`, `medium`, `high`, atau `impossible` | `low` |
| `DVWA_ALLOWED_NETS` | IP atau subnet yang boleh mengakses DVWA | `127.0.0.1 ::1 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16` |

Contoh:

```bash
sudo DVWA_SECURITY=medium bash install-dvwa.sh
sudo DVWA_ALLOWED_NETS="127.0.0.1 100.64.0.0/10" bash install-dvwa.sh
```

## Update

```bash
git pull && sudo bash install-dvwa.sh
```

> **Catatan:** menjalankan ulang skrip akan mereset database DVWA.

## Troubleshooting

- **Error 403:** IP klien tidak termasuk dalam `DVWA_ALLOWED_NETS`. Tambahkan subnetnya, lalu jalankan ulang skrip.
- **Peringatan composer:** lab API tidak berfungsi, tetapi lab lain tetap normal. Dependensinya butuh akses ke Packagist.
- **Halaman tidak terbuka dari komputer host:** periksa pengaturan jaringan VM, misalnya mode NAT yang belum diberi port forwarding.
- **Halaman error atau login gagal:** cek `/var/log/apache2/error.log`.

## Catatan Pengujian

Instalasi inti, login, lab SQL Injection, dan lab File Upload sudah diuji di Ubuntu 24.04 dengan PHP 8.3. Lab lain, instalasi dependensi lab API, dan Ubuntu versi lain belum diuji.

## Kredit

DVWA dibuat oleh proyek [digininja/DVWA](https://github.com/digininja/DVWA). Repo ini hanya berisi skrip instalasi dan mengunduh DVWA dari repo aslinya saat dijalankan.
