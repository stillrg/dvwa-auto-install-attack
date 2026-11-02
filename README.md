<div align="center">

# 🛡️ DVWA Auto Install

**Install and configure [DVWA](https://github.com/digininja/DVWA) (Damn Vulnerable Web Application) on Ubuntu with a single command.**

![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04_LTS-E95420?logo=ubuntu&logoColor=white)
![Bash](https://img.shields.io/badge/Bash-script-4EAA25?logo=gnubash&logoColor=white)
![Apache](https://img.shields.io/badge/Apache-2.4-D22128?logo=apache&logoColor=white)
![MariaDB](https://img.shields.io/badge/MariaDB-database-003545?logo=mariadb&logoColor=white)
![PHP](https://img.shields.io/badge/PHP-8.3-777BB4?logo=php&logoColor=white)

</div>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Security Notice](#%EF%B8%8F-security-notice)
- [Requirements](#-requirements)
- [OS Support](#-os-support)
- [Quick Start](#-quick-start)
- [After Installation](#-after-installation)
- [What the Script Does](#%EF%B8%8F-what-the-script-does)
- [Configuration](#-configuration)
- [Optional: IP Access Password](#-optional-ip-access-password)
- [Optional: Access via Domain](#-optional-access-via-domain)
- [Updating](#-updating)
- [Troubleshooting](#-troubleshooting)
- [Testing Notes](#-testing-notes)
- [Credits](#-credits)

## 📖 Overview

Setting up DVWA by hand means installing a web server, a database and PHP, creating a database user, editing the config file, loosening specific PHP settings, and clicking through the setup page. `install-dvwa.sh` does all of that for you. Run it once and you get a working DVWA instance you can log in to straight away.

## ✨ Features

- **One command:** packages, database, configuration and first-time setup are all handled.
- **Random database password:** a new 32-character password is generated for the `dvwa` database user on every run.
- **Scoped PHP settings:** the vulnerable PHP options are enabled only for the DVWA folder, not for the whole web server.
- **Optional access password:** with `DVWA_PASSWORD=1`, localhost and private networks get in directly, while any other IP must enter an auto-generated password first.
- **Configurable security level:** start DVWA at `low`, `medium`, `high` or `impossible`.
- **Self-verifying:** the script creates the database tables and then checks that the `admin` login actually works.
- **Safe to re-run:** running it again updates DVWA and rebuilds the configuration.

## ⚠️ Security Notice

> [!WARNING]
> DVWA is **intentionally vulnerable**. By default, it can be accessed from **any IP without a password**. If your VM has a public IP, internet bots can find it, log in with `admin` / `password`, and then run commands on the server.

- Use it only on a dedicated lab VM with no important data.
- Take a VM snapshot first.
- Shut the VM down when you are done.
- You can turn on an access password with `DVWA_PASSWORD=1` (see [Optional: IP Access Password](#-optional-ip-access-password)).
- Only test systems you own or have permission to test.

## 📋 Requirements

| Requirement | Details |
|-------------|---------|
| Operating system | Ubuntu 24.04 (a virtual machine is recommended) |
| Privileges | `sudo` / root access |
| Network | Internet connection to download packages, DVWA and Composer dependencies |

## 🐧 OS Support

| OS | Status | Notes |
|----|--------|-------|
| Ubuntu 24.04 LTS | ✅ Tested | Primary target of this script |
| Other Ubuntu versions | ⚠️ Untested | Uses the same `apt` packages, but ships a different PHP version |
| Debian, Kali, Linux Mint and other `apt`-based distros | ⚠️ Untested | The script prints a warning and then continues |
| Fedora, RHEL, CentOS, Arch, openSUSE and other non-`apt` distros | ❌ Not supported | The script stops because `apt-get` is not available, so it needs to be adapted first |

Want to try it on another Linux distribution? Go ahead. Take a VM snapshot first so you can roll back easily if something goes wrong. Whether it works or fails, feel free to share your results in the [Issues](https://github.com/stillrg/dvwa-auto-install/issues) tab.

## 🚀 Quick Start

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/stillrg/dvwa-auto-install.git
cd dvwa-auto-install
sudo bash install-dvwa.sh
```

When the script finishes, it prints a summary like this:

```text
==================================================
 DVWA siap digunakan
 URL         : http://192.168.56.101/DVWA/
 Login DVWA  : admin / password
 Security    : low
==================================================
Jika VM punya IP publik, URL di atas mungkin menampilkan IP internal;
ganti dengan IP publik VM.
[!] DVWA terbuka dari IP mana pun tanpa password akses.
[!] Jika VM punya IP publik, siapa pun bisa masuk dan menjalankan perintah di server.
[!] Untuk mengaktifkan password: sudo DVWA_PASSWORD=1 bash install-dvwa.sh
DVWA sengaja dibuat rentan: jangan simpan data penting di VM ini dan matikan setelah selesai dipakai.
```

> The script's own output messages are in Indonesian.

## 🎯 After Installation

1. Open `http://<VM-IP>/DVWA/` in your browser. You can find the VM's IP address with:
   ```bash
   hostname -I
   ```
   If this shows an internal IP, use the VM's public IP instead.
2. Log in to DVWA with:

   | Username | Password |
   |----------|----------|
   | `admin` | `password` |

3. The initial security level is `low`. You can change it from the **DVWA Security** page, or set it at install time (see [Configuration](#-configuration)).

## ⚙️ What the Script Does

| Step | Action | Details |
|:----:|--------|---------|
| 1 | Pre-flight checks | Makes sure it runs as root, validates `DVWA_SECURITY` and `DVWA_PASSWORD`, and warns if the OS is not Ubuntu |
| 2 | Install packages | Apache (with `apache2-utils`), MariaDB, PHP (with `mysqli`, `gd`, `xml`, `mbstring`, `curl`), Git, cURL, Composer and OpenSSL |
| 3 | Download DVWA | Clones DVWA into `/var/www/html/DVWA`, or runs `git pull` if it is already there |
| 4 | Set up the database | Creates the `dvwa` database and a `dvwa` user with a random password |
| 5 | Write the config | Creates `config/config.inc.php` with the database password and the chosen security level |
| 6 | Install API lab dependencies | Runs `composer install` for the API lab, falling back to `composer update` if the lock file needs a newer PHP |
| 7 | Access password (only with `DVWA_PASSWORD=1`) | Generates an access password for IPs outside `DVWA_ALLOWED_NETS`, saves it to `/root/.dvwa-gate-password`, and creates the `dvwa` user in `/etc/apache2/dvwa-gate.htpasswd`. Without `DVWA_PASSWORD=1`, no password is created and any existing password files are removed |
| 8 | Configure Apache and PHP | Writes `/etc/apache2/conf-available/dvwa.conf`, which enables `allow_url_fopen`, `allow_url_include` and `display_errors` for the DVWA folder only. By default every IP is allowed. With `DVWA_PASSWORD=1`, `DVWA_ALLOWED_NETS` gets in directly and every other IP is asked for the password |
| 9 | Enable modules | Enables `mod_rewrite`, the Basic Auth modules and the DVWA config, checks the Apache config, then restarts Apache |
| 10 | Open the firewall | Allows port 80/tcp if UFW is active |
| 11 | Create the tables | Submits DVWA's **Create / Reset Database** form automatically |
| 12 | Verify the login | Logs in as `admin` and stops with an error if the login fails |

## 🔧 Configuration

You can customize the installation with environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DVWA_SECURITY` | Initial security level: `low`, `medium`, `high` or `impossible` | `low` |
| `DVWA_PASSWORD` | `0` or `1`. Set to `1` to turn on the access password | `0` |
| `DVWA_ALLOWED_NETS` | When `DVWA_PASSWORD=1`: space-separated IPs or subnets that can get in without a password | `127.0.0.1 ::1 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16` |

**Examples**

Start DVWA at the `medium` security level:

```bash
sudo DVWA_SECURITY=medium bash install-dvwa.sh
```

Turn on the access password and let localhost and the `100.64.0.0/10` range (for example, Tailscale) in without it:

```bash
sudo DVWA_PASSWORD=1 DVWA_ALLOWED_NETS="127.0.0.1 100.64.0.0/10" bash install-dvwa.sh
```

## 🔐 Optional: IP Access Password

This step is optional. To turn it on, run:

```bash
sudo DVWA_PASSWORD=1 bash install-dvwa.sh
```

After that:
- Public IPs must enter the username `dvwa` and the random password shown at the end of the installation. You can view the password again with `sudo cat /root/.dvwa-gate-password`.
- Localhost and private networks still get in directly. You can change this list with `DVWA_ALLOWED_NETS`.

To turn it off, run `sudo bash install-dvwa.sh` without that option.

## 🌐 Optional: Access via Domain

This step is optional. DVWA still works over its IP address without a domain.

Before you start, make sure the DNS for your domain or subdomain (an `A` record) points to the VM's IP. Replace `domain-anda.com` in the examples below with your own domain.

**1. Create the config file:**

```bash
sudo nano /etc/apache2/sites-available/dvwa-domain.conf
```

**2. Fill the file with the following configuration, then save it with `Ctrl+O`, `Enter`, `Ctrl+X`:**

```apache
<VirtualHost *:80>
    ServerName domain-anda.com
    DocumentRoot /var/www/html/DVWA
    <Directory /var/www/html/DVWA>
        Require all granted
    </Directory>
    ErrorLog ${APACHE_LOG_DIR}/dvwa-error.log
    CustomLog ${APACHE_LOG_DIR}/dvwa-access.log combined
</VirtualHost>
```

**3. Enable it:**

```bash
sudo a2ensite dvwa-domain
sudo apache2ctl configtest
sudo service apache2 reload
```

Make sure you see `Syntax OK`, then open `http://domain-anda.com/`.

> **Warning:** the configuration above makes DVWA open to anyone without a password. Anyone can also reset the database through `setup.php`.

### Optional: Password for the Domain

With this step, the browser asks for a username and password before showing DVWA through the domain.

**1. Create a password.** You will be asked to type it:

```bash
sudo htpasswd -cB /etc/apache2/dvwa.htpasswd dvwa
sudo chown root:www-data /etc/apache2/dvwa.htpasswd
sudo chmod 640 /etc/apache2/dvwa.htpasswd
```

**2. Open `/etc/apache2/sites-available/dvwa-domain.conf` again, then replace the `Require all granted` line with:**

```apache
        AuthType Basic
        AuthName "DVWA Lab"
        AuthUserFile /etc/apache2/dvwa.htpasswd
        Require valid-user
```

**3. Apply it:**

```bash
sudo apache2ctl configtest
sudo service apache2 reload
```

Notes:
- The domain password only protects access through the domain. The `http://VM-IP/DVWA/` address stays open, unless the IP access password is also turned on with `DVWA_PASSWORD=1`.
- The domain password and the IP access password are two separate passwords.
- As long as you are using HTTP, the password is sent without encryption.

### Turning Off Domain Access

```bash
sudo a2dissite dvwa-domain && sudo service apache2 reload
```

### If Something Goes Wrong

- The domain shows the default Apache page: make sure `ServerName` exactly matches the domain you are opening, then make sure the site is enabled with `sudo a2ensite dvwa-domain`.
- The domain does not open at all: check the DNS record and make sure port 80 is open in the VM's firewall.
- The password pop-up still appears after you removed it: try opening the page in an Incognito window, because the browser may have saved the previous login.

## 🔄 Updating

```bash
git pull && sudo bash install-dvwa.sh
```

> [!NOTE]
> Re-running the script **resets the DVWA database** and generates a new database password. Any data you created in DVWA will be lost.
>
> If you use the access password, keep `DVWA_PASSWORD=1` when you update, because without that option the password is turned off and deleted:
>
> ```bash
> git pull && sudo DVWA_PASSWORD=1 bash install-dvwa.sh
> ```

## 🩺 Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| **Browser asks for a username and password** | This only happens when the access password is turned on | Log in as `dvwa`. View the password with `sudo cat /root/.dvwa-gate-password` |
| **API lab does not work** | The API lab and the access password both use the `Authorization` header, so they will likely conflict | Use a private network, add your IP to `DVWA_ALLOWED_NETS`, or run the script without `DVWA_PASSWORD=1` |
| **Composer warning** during install | The API lab dependencies could not be installed | Only the API lab is affected, the other labs work normally. The dependencies need access to Packagist, so check your internet connection and re-run |
| **Page does not open from the host computer** | VM network settings | Check your VM's network mode. For example, NAT mode needs port forwarding for port 80 |
| **Error page or login fails** | PHP, Apache or database error | Check the Apache error log: `sudo tail -n 50 /var/log/apache2/error.log` |
| **`/var/www/html/DVWA` already exists but is not a git repository** | A previous manual install | Move or delete that folder, then run the script again |

## 🧪 Testing Notes

| Component | Status |
|-----------|--------|
| Core installation on Ubuntu 24.04 with PHP 8.3 | ✅ Tested |
| Admin login | ✅ Tested |
| SQL Injection lab | ✅ Tested |
| File Upload lab | ✅ Tested |
| Access with and without the access password | ✅ Tested (simulated) |
| Domain guide | ✅ Tested (simulated) |
| Other labs | ⚠️ Untested |
| API lab dependency installation | ⚠️ Untested |
| Access across real networks | ⚠️ Untested |
| Other Ubuntu versions | ⚠️ Untested |

## 🙏 Credits

DVWA is created and maintained by the [digininja/DVWA](https://github.com/digininja/DVWA) project. This repository contains only the installation script. DVWA itself is downloaded from the original repository when the script runs.
