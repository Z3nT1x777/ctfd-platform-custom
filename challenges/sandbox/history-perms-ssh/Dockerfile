FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server sudo ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/run/sshd

# Challenge user
RUN useradd -m -s /bin/bash player \
    && echo 'player:player2026' | chpasswd

# Misconfiguration path: privileged helper executable
RUN mkdir -p /opt/secret /opt/ops/notes
RUN echo 'CTF{history_leak_plus_sudo_misconfig}' > /opt/secret/flag.txt \
    && chmod 600 /opt/secret/flag.txt \
    && chown root:root /opt/secret/flag.txt

RUN printf '#!/bin/bash\ncat /opt/secret/flag.txt\n' > /usr/local/bin/readflag \
    && chmod 750 /usr/local/bin/readflag \
    && chown root:root /usr/local/bin/readflag

RUN echo 'player ALL=(root) NOPASSWD:/usr/local/bin/readflag' > /etc/sudoers.d/player-readflag \
    && chmod 440 /etc/sudoers.d/player-readflag

# Breadcrumb in history
RUN echo 'cat /opt/ops/notes/incident.txt' > /home/player/.bash_history \
    && chown player:player /home/player/.bash_history \
    && chmod 600 /home/player/.bash_history

RUN printf 'Incident note:\n- Investigate sudo rule drift\n- test helper: sudo /usr/local/bin/readflag\n' > /opt/ops/notes/incident.txt \
    && chmod 644 /opt/ops/notes/incident.txt \
    && chown root:root /opt/ops/notes/incident.txt

# Keep root login off; password auth on for challenge user
RUN sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D", "-e"]