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
- [Requirements](#-requirements)
- [OS Support](#-os-support)
- [Quick Start](#-quick-start)
- [After Installation](#-after-installation)
- [What the Script Does](#%EF%B8%8F-what-the-script-does)
- [Configuration](#-configuration)
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
- **IP allow-list:** access is limited to localhost and private networks by default, and you can change it.
- **Configurable security level:** start DVWA at `low`, `medium`, `high` or `impossible`.
- **Self-verifying:** the script creates the database tables and then checks that the `admin` login actually works.
- **Safe to re-run:** running it again updates DVWA and rebuilds the configuration.

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
 URL      : http://192.168.56.101/DVWA/
 Login    : admin / password
 Security : low
 Akses    : 127.0.0.1 ::1 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16
==================================================
```

> The script's own output messages are in Indonesian.

## 🎯 After Installation

1. Find the VM's IP address:
   ```bash
   hostname -I
   ```
2. Open `http://<VM-IP>/DVWA/` in your browser.
3. Log in with:

   | Username | Password |
   |----------|----------|
   | `admin` | `password` |

4. The initial security level is `low`. You can change it from the **DVWA Security** page, or set it at install time (see [Configuration](#-configuration)).

## ⚙️ What the Script Does

| Step | Action | Details |
|:----:|--------|---------|
| 1 | Pre-flight checks | Makes sure it runs as root, validates `DVWA_SECURITY`, and warns if the OS is not Ubuntu |
| 2 | Install packages | Apache, MariaDB, PHP (with `mysqli`, `gd`, `xml`, `mbstring`, `curl`), Git, cURL, Composer and OpenSSL |
| 3 | Download DVWA | Clones DVWA into `/var/www/html/DVWA`, or runs `git pull` if it is already there |
| 4 | Set up the database | Creates the `dvwa` database and a `dvwa` user with a random password |
| 5 | Write the config | Creates `config/config.inc.php` with the database password and the chosen security level |
| 6 | Install API lab dependencies | Runs `composer install` for the API lab, falling back to `composer update` if the lock file needs a newer PHP |
| 7 | Configure Apache and PHP | Writes `/etc/apache2/conf-available/dvwa.conf`, which enables `allow_url_fopen`, `allow_url_include` and `display_errors` for the DVWA folder only and applies the IP allow-list |
| 8 | Enable modules | Enables `mod_rewrite` and the DVWA config, checks the Apache config, then restarts Apache |
| 9 | Open the firewall | Allows port 80/tcp if UFW is active |
| 10 | Create the tables | Submits DVWA's **Create / Reset Database** form automatically |
| 11 | Verify the login | Logs in as `admin` and stops with an error if the login fails |

## 🔧 Configuration

You can customize the installation with environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DVWA_SECURITY` | Initial security level: `low`, `medium`, `high` or `impossible` | `low` |
| `DVWA_ALLOWED_NETS` | Space-separated IPs or subnets that are allowed to access DVWA | `127.0.0.1 ::1 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16` |

**Examples**

Start DVWA at the `medium` security level:

```bash
sudo DVWA_SECURITY=medium bash install-dvwa.sh
```

Allow localhost and the `100.64.0.0/10` range (for example, Tailscale):

```bash
sudo DVWA_ALLOWED_NETS="127.0.0.1 100.64.0.0/10" bash install-dvwa.sh
```

## 🔄 Updating

```bash
git pull && sudo bash install-dvwa.sh
```

> [!NOTE]
> Re-running the script **resets the DVWA database** and generates a new database password. Any data you created in DVWA will be lost.

## 🩺 Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| **403 Forbidden** | Your client IP is not in `DVWA_ALLOWED_NETS` | Add your subnet to `DVWA_ALLOWED_NETS` and run the script again |
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
| Other labs | ⚠️ Untested |
| API lab dependency installation | ⚠️ Untested |
| Other Ubuntu versions | ⚠️ Untested |

## 🙏 Credits

DVWA is created and maintained by the [digininja/DVWA](https://github.com/digininja/DVWA) project. This repository contains only the installation script. DVWA itself is downloaded from the original repository when the script runs.
