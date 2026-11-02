#!/usr/bin/env bash
# Auto-install & auto-config DVWA di Ubuntu (Apache + MariaDB + PHP).
# DVWA sengaja dibuat rentan: pakai hanya di VM lab, jangan di server publik.
#
# Opsi (lewat environment variable):
#   DVWA_SECURITY=low|medium|high|impossible   level keamanan awal (default: low)
#   DVWA_PASSWORD=0|1                          aktifkan password akses (default: 0)
#   DVWA_ALLOWED_NETS="..."                    jika DVWA_PASSWORD=1, IP/subnet yang
#                                              boleh masuk tanpa password
#
# Secara default DVWA terbuka dari IP mana pun, tanpa password akses.
set -euo pipefail

DVWA_DIR=/var/www/html/DVWA
DVWA_SECURITY="${DVWA_SECURITY:-low}"
DVWA_PASSWORD="${DVWA_PASSWORD:-0}"
DVWA_ALLOWED_NETS="${DVWA_ALLOWED_NETS:-127.0.0.1 ::1 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16}"
BASE_URL=http://127.0.0.1/DVWA
GATE_USER=dvwa
GATE_FILE=/etc/apache2/dvwa-gate.htpasswd
GATE_PASS_FILE=/root/.dvwa-gate-password

log()  { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[1;31m[x] %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Jalankan dengan sudo: sudo bash $0"
case "$DVWA_SECURITY" in low|medium|high|impossible) ;; *) die "DVWA_SECURITY tidak valid: $DVWA_SECURITY" ;; esac
case "$DVWA_PASSWORD" in 0|1) ;; *) die "DVWA_PASSWORD harus 0 atau 1, bukan: $DVWA_PASSWORD" ;; esac
. /etc/os-release
[ "${ID:-}" = ubuntu ] || warn "Skrip ini dibuat untuk Ubuntu, terdeteksi: ${PRETTY_NAME:-tidak diketahui}"

# Pakai systemd bila aktif, selain itu fallback ke perintah service.
svc() { # svc start|restart nama
  if [ -d /run/systemd/system ]; then
    systemctl enable -q "$2" 2>/dev/null || true
    systemctl "$1" "$2"
  else
    service "$2" "$1"
  fi
}

log "Menginstal paket"
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a
apt-get update -qq
apt-get install -y -qq apache2 apache2-utils mariadb-server mariadb-client php php-mysqli php-gd php-xml \
  php-mbstring php-curl libapache2-mod-php git curl unzip composer openssl >/dev/null

log "Mengunduh DVWA ke $DVWA_DIR"
if [ -d "$DVWA_DIR/.git" ]; then
  git -C "$DVWA_DIR" pull -q --ff-only || warn "git pull gagal, memakai versi yang sudah ada"
elif [ -e "$DVWA_DIR" ]; then
  die "$DVWA_DIR sudah ada tetapi bukan repo git. Pindahkan dulu, lalu jalankan ulang."
else
  git clone -q --depth 1 https://github.com/digininja/DVWA.git "$DVWA_DIR"
fi

log "Menyiapkan database"
svc start mariadb
for _ in $(seq 1 30); do mariadb -e 'SELECT 1' >/dev/null 2>&1 && break; sleep 1; done
mariadb -e 'SELECT 1' >/dev/null 2>&1 || die "MariaDB tidak bisa dihubungi"
DB_PASS="$(openssl rand -hex 16)"
mariadb <<SQL
CREATE DATABASE IF NOT EXISTS dvwa;
CREATE USER IF NOT EXISTS 'dvwa'@'localhost' IDENTIFIED BY '$DB_PASS';
CREATE USER IF NOT EXISTS 'dvwa'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';
ALTER USER 'dvwa'@'localhost' IDENTIFIED BY '$DB_PASS';
ALTER USER 'dvwa'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';
GRANT ALL ON dvwa.* TO 'dvwa'@'localhost';
GRANT ALL ON dvwa.* TO 'dvwa'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL

log "Menulis konfigurasi DVWA"
CONFIG="$DVWA_DIR/config/config.inc.php"
cp "$DVWA_DIR/config/config.inc.php.dist" "$CONFIG"
sed -i "s/?: 'p@ssw0rd'/?: '$DB_PASS'/; s/?: 'impossible'/?: '$DVWA_SECURITY'/" "$CONFIG"
grep -q "$DB_PASS" "$CONFIG" || die "Gagal menulis password database ke $CONFIG"
chown -R www-data:www-data "$DVWA_DIR/hackable/uploads" "$DVWA_DIR/config"
chmod 640 "$CONFIG"

log "Menginstal dependensi modul API"
# composer.lock DVWA bisa menuntut PHP lebih baru dari bawaan Ubuntu. Jika begitu,
# pilih versi paket yang cocok, lalu kembalikan lock file agar git pull tetap bersih.
export COMPOSER_ALLOW_SUPERUSER=1
(cd "$DVWA_DIR/vulnerabilities/api" &&
  { composer install -q --no-interaction --no-dev 2>/dev/null ||
    { composer update -q --no-interaction --no-dev && git checkout -q -- composer.lock; }; }) ||
  warn "composer gagal: lab API tidak akan berfungsi, lab lainnya tetap normal"

log "Mengonfigurasi Apache dan PHP"
if [ "$DVWA_PASSWORD" = 1 ]; then
  # Password dipertahankan selama opsi ini tetap aktif saat skrip dijalankan ulang.
  if [ ! -s "$GATE_PASS_FILE" ]; then
    (umask 077; openssl rand -hex 12 >"$GATE_PASS_FILE")
  fi
  GATE_PASS="$(cat "$GATE_PASS_FILE")"
  printf '%s\n' "$GATE_PASS" | htpasswd -ciB "$GATE_FILE" "$GATE_USER" 2>/dev/null
  chown root:www-data "$GATE_FILE"
  chmod 640 "$GATE_FILE"
  ACCESS_RULES="    AuthType Basic
    AuthName \"DVWA Lab\"
    AuthUserFile $GATE_FILE
    <RequireAny>
        Require ip $DVWA_ALLOWED_NETS
        Require valid-user
    </RequireAny>"
else
  rm -f "$GATE_FILE" "$GATE_PASS_FILE"
  ACCESS_RULES="    Require all granted"
fi

# Setting PHP yang rentan hanya berlaku untuk folder DVWA, bukan seluruh server.
cat >/etc/apache2/conf-available/dvwa.conf <<APACHE
<Directory $DVWA_DIR>
    AllowOverride All
$ACCESS_RULES
    php_admin_flag allow_url_fopen On
    php_admin_flag allow_url_include On
    php_admin_flag display_errors On
    php_admin_flag display_startup_errors On
</Directory>
APACHE
a2enmod -q rewrite auth_basic authn_file authz_user
a2enconf -q dvwa
apache2ctl configtest >/dev/null 2>&1 || die "Konfigurasi Apache tidak valid, cek: apache2ctl configtest"
svc restart apache2

if command -v ufw >/dev/null && ufw status 2>/dev/null | grep -q 'Status: active'; then
  log "Membuka port 80 di UFW"
  ufw allow 80/tcp >/dev/null
fi

log "Membuat tabel database DVWA"
COOKIES="$(mktemp)"
trap 'rm -f "$COOKIES"' EXIT
get_token() { curl -fsS -b "$COOKIES" -c "$COOKIES" "$1" | sed -n "s/.*name='user_token' value='\([^']*\)'.*/\1/p" | head -n 1; }

TOKEN="$(get_token "$BASE_URL/setup.php")"
[ -n "$TOKEN" ] || die "Halaman setup tidak merespons dengan benar: $BASE_URL/setup.php"
curl -fsS -o /dev/null -b "$COOKIES" -c "$COOKIES" \
  --data-urlencode "create_db=Create / Reset Database" --data-urlencode "user_token=$TOKEN" "$BASE_URL/setup.php"

log "Memverifikasi login"
: >"$COOKIES"
TOKEN="$(get_token "$BASE_URL/login.php")"
LOCATION="$(curl -sS -o /dev/null -w '%{redirect_url}' -b "$COOKIES" -c "$COOKIES" \
  -d "username=admin" -d "password=password" -d "Login=Login" \
  --data-urlencode "user_token=$TOKEN" "$BASE_URL/login.php")"
case "$LOCATION" in
  *index.php*) ;;
  *) die "Login admin gagal (redirect ke: ${LOCATION:-tidak ada}). Cek /var/log/apache2/error.log" ;;
esac

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
cat <<DONE

==================================================
 DVWA siap digunakan
 URL         : http://${IP:-127.0.0.1}/DVWA/
 Login DVWA  : admin / password
 Security    : $DVWA_SECURITY
==================================================
Jika VM punya IP publik, URL di atas mungkin menampilkan IP internal;
ganti dengan IP publik VM.
DONE

if [ "$DVWA_PASSWORD" = 1 ]; then
  cat <<DONE

Password akses aktif untuk IP di luar: $DVWA_ALLOWED_NETS
 Username : $GATE_USER
 Password : $GATE_PASS
Password bisa dilihat lagi dengan: sudo cat $GATE_PASS_FILE
DONE
else
  warn "DVWA terbuka dari IP mana pun tanpa password akses."
  warn "Jika VM punya IP publik, siapa pun bisa masuk dan menjalankan perintah di server."
  warn "Untuk mengaktifkan password: sudo DVWA_PASSWORD=1 bash $0"
fi
echo "DVWA sengaja dibuat rentan: jangan simpan data penting di VM ini dan matikan setelah selesai dipakai."
