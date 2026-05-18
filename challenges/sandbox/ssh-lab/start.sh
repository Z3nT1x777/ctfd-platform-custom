#!/bin/bash
# Start monitoring agent in background (root), then SSH daemon in foreground
python3 /opt/ctf/app.py &
exec /usr/sbin/sshd -D -e
