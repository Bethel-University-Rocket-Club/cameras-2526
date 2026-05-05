#!/usr/bin/env python3
import subprocess
import socket
import urllib.request
import urllib.error
import time
import sys
import os
IFACE = "wwu1i5"
WDM = "/dev/cdc-wdm0"

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode

def section(title):
    print(f"\n{'─'*40}")
    print(f"  {title}")
    print(f"{'─'*40}")

def ok(msg):   print(f"  ✓  {msg}")
def fail(msg): print(f"  ✗  {msg}")
def info(msg): print(f"  ·  {msg}")

# ── Interface ────────────────────────────────
section("Interface")
out, rc = run(f"ip link show {IFACE}")
if rc == 0:
    state = "UP" if "UP" in out else "DOWN"
    ok(f"{IFACE} exists — {state}")
else:
    fail(f"{IFACE} not found")
    sys.exit(1)

out, _ = run(f"ip addr show {IFACE}")
for line in out.splitlines():
    line = line.strip()
    if line.startswith("inet"):
        info(line)

# ── QMI Bearer ──────────────────────────────
section("QMI Bearer")
state_file = "/tmp/qmi-network-state-cdc-wdm0"
out, _ = run(f"ip addr show {IFACE}")
has_global = "scope global" in out
state_exists = os.path.exists(state_file)

if has_global and state_exists:
    ok("Bearer active (qmi-network connected)")
elif has_global:
    ok("Interface has address (bearer assumed active)")
else:
    fail("No global address on interface")

# ── Routing ─────────────────────────────────
section("Routing")
out, _ = run("ip -6 route show")
default_via_iface = any(IFACE in line and "default" in line for line in out.splitlines())
if default_via_iface:
    for line in out.splitlines():
        if "default" in line and IFACE in line:
            ok(f"Default route: {line.strip()}")
else:
    fail(f"No default route via {IFACE}")
    for line in out.splitlines():
        if "default" in line:
            info(f"Default route is via: {line.strip()}")

# ── Ping ────────────────────────────────────
section("Ping (Google DNS)")
out, rc = run(f"ping6 -c 4 -I {IFACE} 2001:4860:4860::8888")
if rc == 0:
    for line in out.splitlines():
        if "packets transmitted" in line or "rtt" in line:
            ok(line.strip())
else:
    fail("ping6 failed")
    for line in out.splitlines()[-5:]:
        info(line.strip())

# ── DNS ─────────────────────────────────────
section("DNS Resolution")
try:
    ip = socket.getaddrinfo("google.com", None, socket.AF_INET6)[0][4][0]
    ok(f"google.com resolved to {ip}")
except Exception as e:
    fail(f"DNS failed: {e}")

# ── HTTP ────────────────────────────────────
section("HTTP Connectivity")
try:
    start = time.time()
    req = urllib.request.urlopen("https://ipv6.icanhazip.com", timeout=10)
    elapsed = time.time() - start
    public_ip = req.read().decode().strip()
    ok(f"HTTP OK ({elapsed:.2f}s)")
    ok(f"Public IPv6: {public_ip}")
except urllib.error.URLError as e:
    fail(f"HTTP failed: {e}")

# ── Tailscale ───────────────────────────────
section("Tailscale")
out, rc = run("tailscale status 2>&1")
if rc == 0:
    lines = out.splitlines()
    ok(lines[0] if lines else "Tailscale up")
    for line in lines[1:6]:
        info(line)
else:
    if "not installed" in out.lower() or "command not found" in out.lower():
        info("Tailscale not installed")
    elif "stopped" in out.lower() or "not running" in out.lower():
        fail("Tailscale installed but not running — run: sudo tailscale up")
    else:
        fail(out.splitlines()[0] if out else "Tailscale error")

print(f"\n{'─'*40}\n")