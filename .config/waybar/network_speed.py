#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# waybar network speed module
#
# Save as ~/.config/waybar/network_speed.py and make executable:
# chmod +x ~/.config/waybar/network_speed.py

import argparse
import json
import os
import re
import subprocess
import sys
import time
from signal import signal, SIGINT, SIGTERM

RUNNING = True
def _handle_sig(signum, frame):
    global RUNNING
    RUNNING = False

signal(SIGINT, _handle_sig)
signal(SIGTERM, _handle_sig)


def get_default_iface():
    """Try to detect the default (internet) interface."""
    try:
        out = subprocess.check_output(
            ['ip', 'route', 'get', '1.1.1.1'],
            stderr=subprocess.DEVNULL
        ).decode(errors='ignore')
        m = re.search(r'dev\s+(\S+)', out)
        if m:
            return m.group(1)
    except Exception:
        pass
    # fallback: first 'up' interface (skip lo)
    try:
        for iface in os.listdir('/sys/class/net'):
            if iface == 'lo':
                continue
            try:
                with open(f'/sys/class/net/{iface}/operstate') as f:
                    if f.read().strip() == 'up':
                        return iface
            except Exception:
                continue
    except Exception:
        pass
    # final fallback: any non-loopback
    for iface in os.listdir('/sys/class/net'):
        if iface != 'lo':
            return iface
    return 'lo'


def read_stats(iface):
    """Return (rx_bytes, tx_bytes) for iface or (None, None) on error."""
    try:
        base = f'/sys/class/net/{iface}/statistics'
        with open(base + '/rx_bytes') as f:
            rx = int(f.read().strip())
        with open(base + '/tx_bytes') as f:
            tx = int(f.read().strip())
        return rx, tx
    except Exception:
        return None, None


def format_speed(bps, si=False):
    """Format bytes/sec to human readable string (SI or IEC)."""
    if bps is None:
        return '—'
    base = 1000 if si else 1024
    units = ['B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s'] if si \
            else ['B/s', 'KiB/s', 'MiB/s', 'GiB/s', 'TiB/s']
    neg = bps < 0
    bps = abs(bps)
    unit = 0
    while bps >= base and unit < len(units) - 1:
        bps /= base
        unit += 1
    if bps >= 100:
        s = f"{bps:.0f} {units[unit]}"
    elif bps >= 10:
        s = f"{bps:.1f} {units[unit]}"
    else:
        s = f"{bps:.2f} {units[unit]}"
    return ('-' + s) if neg else s


def main():
    p = argparse.ArgumentParser(
        description='Waybar network speed module (prints JSON lines).'
    )
    p.add_argument('-i', '--iface', help='network interface to monitor')
    p.add_argument('-t', '--interval', type=float, default=1.0,
                   help='refresh interval in seconds (default 1)')
    p.add_argument('--si', action='store_true',
                   help='use SI units (1000) instead of 1024')
    args = p.parse_args()

    iface = args.iface or os.getenv('WAYBAR_NETWORK_IFACE') or \
            get_default_iface()

    down_arrow = '↓'
    up_arrow = '↑'

    prev_rx, prev_tx = read_stats(iface)
    prev_time = time.monotonic()

    # initial placeholder so Waybar shows something immediately
    initial = f"{down_arrow} —   {up_arrow} —"
    sys.stdout.write(json.dumps({'text': initial}) + "\n")
    sys.stdout.flush()

    while RUNNING:
        time.sleep(max(0.01, args.interval))
        now = time.monotonic()
        rx, tx = read_stats(iface)

        if rx is None or tx is None or prev_rx is None:
            text = f"{down_arrow} —   {up_arrow} —"
            out = {'text': text, 'class': 'disconnected',
                   'tooltip': f'iface={iface}'}
            sys.stdout.write(json.dumps(out) + "\n")
            sys.stdout.flush()
            prev_rx, prev_tx = rx, tx
            prev_time = now
            continue

        dt = now - prev_time if now > prev_time else 1.0
        drx = rx - prev_rx
        dtx = tx - prev_tx
        down_bps = drx / dt
        up_bps = dtx / dt

        down_txt = format_speed(down_bps, args.si)
        up_txt = format_speed(up_bps, args.si)
        text = f"{down_arrow} {down_txt}   {up_arrow} {up_txt}"

        peak = max(down_bps, up_bps)
        if peak > 10 * 1024 * 1024:
            cls = 'critical'
        elif peak > 1 * 1024 * 1024:
            cls = 'high'
        elif peak > 100 * 1024:
            cls = 'medium'
        else:
            cls = 'normal'

        tooltip = (f'iface: {iface}\\nrx: {rx} tx: {tx}\\n'
                   f'interval: {dt:.2f}s')
        out = {'text': text, 'class': cls, 'tooltip': tooltip}
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()

        prev_rx, prev_tx, prev_time = rx, tx, now


if __name__ == '__main__':
    main()
