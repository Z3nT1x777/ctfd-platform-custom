FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssh-server curl python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /opt/ctf/requirements.txt
RUN pip3 install -r /opt/ctf/requirements.txt --quiet --no-cache-dir

RUN useradd -m -s /bin/bash ctf \
    && echo 'ctf:ctf2026' | chpasswd \
    && mkdir -p /var/run/sshd

RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config \
    && printf '\nBanner /etc/issue.net\n' >> /etc/ssh/sshd_config

# Flag only readable by root — exposed via the monitoring agent
COPY flag.txt /root/flag.txt
RUN chmod 400 /root/flag.txt

# Monitoring agent — readable by ctf so player can inspect the source
COPY app.py /opt/ctf/app.py
RUN chmod 644 /opt/ctf/app.py

RUN printf 'monitoring-agent — internal system\n' > /etc/issue.net

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 22
CMD ["/start.sh"]
