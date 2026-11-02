<div align="center">

# 🛡️ DVWA Toolkit

**A complete toolkit for setting up and testing [DVWA](https://github.com/digininja/DVWA) (Damn Vulnerable Web Application).**

![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04_LTS-E95420?logo=ubuntu&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Bash](https://img.shields.io/badge/Bash-script-4EAA25?logo=gnubash&logoColor=white)
![Apache](https://img.shields.io/badge/Apache-2.4-D22128?logo=apache&logoColor=white)
![MariaDB](https://img.shields.io/badge/MariaDB-database-003545?logo=mariadb&logoColor=white)
![PHP](https://img.shields.io/badge/PHP-8.3-777BB4?logo=php&logoColor=white)

</div>

---

## 📦 Repository Structure

```
dvwa-toolkit/
├── auto-install/       # Bash script to install & configure DVWA on Ubuntu
│   └── install-dvwa.sh
└── auto-attack/        # Python 3 tool to automate security tests against DVWA
    └── dvwa_tester.py
```

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Security Notice](#-security-notice)
- [auto-install — Setup DVWA](#-auto-install--setup-dvwa)
  - [Requirements](#requirements)
  - [OS Support](#os-support)
  - [Quick Start](#quick-start)
  - [After Installation](#after-installation)
  - [What the Script Does](#what-the-script-does)
  - [Configuration](#configuration)
  - [Optional: IP Access Password](#optional-ip-access-password)
  - [Optional: Access via Domain](#optional-access-via-domain)
  - [Updating](#updating)
  - [Troubleshooting](#troubleshooting)
  - [Testing Notes](#testing-notes)
- [auto-attack — Security Tester](#-auto-attack--security-tester)
  - [Requirements](#requirements-1)
  - [Quick Start](#quick-start-1)
  - [Attack Modules](#attack-modules)
  - [Usage Examples](#usage-examples)
- [Credits](#-credits)

---

## 📖 Overview

This repository contains two tools that work together:

| Tool | Language | Purpose |
|------|----------|---------|
| `auto-install/install-dvwa.sh` | Bash | Install and configure DVWA on Ubuntu with one command |
| `auto-attack/dvwa_tester.py` | Python 3 | Automate security tests (SQLi, XSS, LFI, Command Injection) against a running DVWA instance |

**Typical workflow:** run `install-dvwa.sh` to set up DVWA on a lab VM, then run `dvwa_tester.py` against it to practice and observe the attack modules.

---

## ⚠️ Security Notice

> [!WARNING]
> DVWA is **intentionally vulnerable**. These tools are designed strictly for **educational use on systems you own or have explicit permission to test**.

- Use only on a dedicated lab VM with no important data.
- Take a VM snapshot before running anything.
- Shut the VM down when you are done.
- Never run these tools against systems without authorization.

---

## 🔧 auto-install — Setup DVWA

### Requirements

| Requirement | Details |
|-------------|---------|
| Operating system | Ubuntu 24.04 (a virtual machine is recommended) |
| Privileges | `sudo` / root access |
| Network | Internet connection to download packages and DVWA |

### OS Support

| OS | Status | Notes |
|----|--------|-------|
| Ubuntu 24.04 LTS | ✅ Tested | Primary target |
| Other Ubuntu versions | ⚠️ Untested | Same `apt` packages, different PHP version |
| Debian, Kali, Mint and other `apt`-based distros | ⚠️ Untested | Script prints a warning and continues |
| Non-`apt` distros (Fedora, Arch, etc.) | ❌ Not supported | Script stops because `apt-get` is unavailable |

### Quick Start

```bash
sudo apt update && sudo apt install -y git
git clone https://github.com/stillrg/dvwa-toolkit.git
cd dvwa-toolkit/auto-install
sudo bash install-dvwa.sh
```

When the script finishes, it prints a summary:

```
==================================================
 DVWA siap digunakan
 URL         : http://192.168.56.101/DVWA/
 Login DVWA  : admin / password
 Security    : low
==================================================
```

> The script's output messages are in Indonesian.

### After Installation

1. Open `http://<VM-IP>/DVWA/` in your browser:
   ```bash
   hostname -I
   ```
2. Log in with:

   | Username | Password |
   |----------|----------|
   | `admin` | `password` |

3. Default security level is `low`. Change it from the **DVWA Security** page or at install time (see [Configuration](#configuration)).

### What the Script Does

| Step | Action |
|:----:|--------|
| 1 | Pre-flight checks (root, valid env vars, OS warning) |
| 2 | Install Apache, MariaDB, PHP, Git, Composer, OpenSSL |
| 3 | Clone DVWA into `/var/www/html/DVWA` (or `git pull` if already there) |
| 4 | Create `dvwa` database and user with a random 32-char password |
| 5 | Write `config/config.inc.php` with DB credentials and security level |
| 6 | Install API lab dependencies via Composer |
| 7 | Optionally create an IP access password (only with `DVWA_PASSWORD=1`) |
| 8 | Write `/etc/apache2/conf-available/dvwa.conf` (scoped PHP settings) |
| 9 | Enable Apache modules, validate config, restart Apache |
| 10 | Open port 80 in UFW if active |
| 11 | Auto-submit DVWA's **Create / Reset Database** form |
| 12 | Verify the `admin` login works |

### Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DVWA_SECURITY` | Initial security level: `low`, `medium`, `high`, `impossible` | `low` |
| `DVWA_PASSWORD` | `0` or `1` — turn on an IP access password | `0` |
| `DVWA_ALLOWED_NETS` | IPs/subnets allowed without password when `DVWA_PASSWORD=1` | `127.0.0.1 ::1 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16` |

**Examples:**

```bash
# Start DVWA at medium security
sudo DVWA_SECURITY=medium bash install-dvwa.sh

# Enable access password, allow Tailscale range without it
sudo DVWA_PASSWORD=1 DVWA_ALLOWED_NETS="127.0.0.1 100.64.0.0/10" bash install-dvwa.sh
```

### Optional: IP Access Password

```bash
sudo DVWA_PASSWORD=1 bash install-dvwa.sh
```

- Public IPs must log in as `dvwa` with the generated password (view again with `sudo cat /root/.dvwa-gate-password`).
- Localhost and private networks bypass the password.
- Turn it off by running the script without `DVWA_PASSWORD=1`.

### Optional: Access via Domain

**1. Create the config file:**
```bash
sudo nano /etc/apache2/sites-available/dvwa-domain.conf
```

**2. Paste this config:**
```apache
<VirtualHost *:80>
    ServerName domain-anda.com
    DocumentRoot /var/www/html/DVWA
    <Directory /var/www/html/DVWA>
        Require all granted
    </Directory>
</VirtualHost>
```

**3. Enable it:**
```bash
sudo a2ensite dvwa-domain && sudo apache2ctl configtest && sudo service apache2 reload
```

**To remove:**
```bash
sudo a2dissite dvwa-domain && sudo service apache2 reload
```

### Updating

```bash
git pull && sudo bash auto-install/install-dvwa.sh
```

> [!NOTE]
> Re-running the script **resets the DVWA database**. Add `DVWA_PASSWORD=1` if you had the access password enabled.

### Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Browser asks for username/password | Access password is on | Log in as `dvwa`. View password: `sudo cat /root/.dvwa-gate-password` |
| API lab does not work | Conflict with `Authorization` header | Use a private network or run without `DVWA_PASSWORD=1` |
| Page does not open from host | VM network settings | Check VM network mode; NAT requires port 80 forwarding |
| Login fails | PHP/Apache/DB error | Check: `sudo tail -n 50 /var/log/apache2/error.log` |

### Testing Notes

| Component | Status |
|-----------|--------|
| Core installation on Ubuntu 24.04 + PHP 8.3 | ✅ Tested |
| Admin login | ✅ Tested |
| SQL Injection lab | ✅ Tested |
| File Upload lab | ✅ Tested |
| Access with and without the access password | ✅ Tested (simulated) |
| API lab dependency installation | ⚠️ Untested |
| Other Ubuntu versions | ⚠️ Untested |

---

## 🔫 auto-attack — Security Tester

A Python 3 script that automates common web vulnerability tests against a running DVWA instance. No browser required — works entirely via HTTP requests.

### Requirements

| Requirement | Details |
|-------------|---------|
| Python | 3.x |
| Libraries | `requests`, `beautifulsoup4` |
| Target | A running DVWA instance |

**Install dependencies:**
```bash
pip install requests beautifulsoup4
```

### Quick Start

```bash
cd auto-attack

# Interactive mode (prompts for URL, credentials, module)
python dvwa_tester.py

# Direct mode
python dvwa_tester.py http://192.168.56.101
```

### Attack Modules

| # | Module | Path | What it tests |
|---|--------|------|---------------|
| 1 | Command Injection | `/vulnerabilities/exec/` | OS command chaining via `;` — extracts `id`, `uname -a`, `/etc/passwd`, hostname |
| 2 | SQL Injection | `/vulnerabilities/sqli/` | Error-based, boolean bypass, UNION-based user/table dump |
| 3 | Cross-Site Scripting | `/vulnerabilities/xss_r/` & `xss_s/` | Reflected and stored XSS payload reflection |
| 4 | Local File Inclusion | `/vulnerabilities/fi/` | Path traversal to `/etc/passwd`, `/etc/issue`, `/proc/version` |
| 5 | All modules | — | Runs all of the above in sequence |

### Usage Examples

```bash
# Run all modules against local DVWA
python dvwa_tester.py http://127.0.0.1

# Run against DVWA on a VM
python dvwa_tester.py http://192.168.56.101

# Run against DVWA on a non-standard port
python dvwa_tester.py http://192.168.56.101:8080

# Run against DVWA installed via auto-install (path is /DVWA/)
python dvwa_tester.py http://192.168.56.101/DVWA
```

When started without arguments, the script prompts interactively:

```
  Masukkan URL target DVWA (contoh: http://127.0.0.1): http://192.168.56.101
  Username [admin]:
  Password [password]:

  Menu Serangan:
    1. Command Injection
    2. SQL Injection
    3. Cross-Site Scripting (XSS)
    4. File Inclusion (LFI)
    5. Semua modul
    0. Keluar

  Pilihan [5]:
```

---

## 🙏 Credits

DVWA is created and maintained by the [digininja/DVWA](https://github.com/digininja/DVWA) project. This repository contains only the toolkit scripts. DVWA itself is downloaded from the original repository when the install script runs.
