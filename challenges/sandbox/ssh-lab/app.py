#!/usr/bin/env python3
"""Internal monitoring agent — do not expose externally."""

from flask import Flask
import os
import socket
import datetime

app = Flask(__name__)


@app.route("/")
def index():
    return (
        "monitoring-agent v0.3\n"
        "routes: /health  /status  /metrics\n"
    ), 200, {"Content-Type": "text/plain"}


@app.route("/health")
def health():
    return '{"status":"ok"}\n', 200, {"Content-Type": "application/json"}


@app.route("/status")
def status():
    hostname = socket.gethostname()
    return (
        f'{{"hostname":"{hostname}","uptime":"ok","checks":3}}\n'
    ), 200, {"Content-Type": "application/json"}


@app.route("/metrics")
def metrics():
    try:
        secret = open("/root/flag.txt").read().strip()
    except Exception:
        secret = "unavailable"
    ts = datetime.datetime.utcnow().isoformat()
    return (
        f"# monitoring-agent internal metrics — {ts}\n"
        f"process_status 1\n"
        f"checks_passed 3\n"
        f"memory_ok 1\n"
        f"# internal_token: {secret}\n"
    ), 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=False)
