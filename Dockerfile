FROM python:3.9-slim

RUN apt-get update && apt-get install -y sshfs samba cifs-utils

WORKDIR /user/src/app

COPY sonar_compose.py .
COPY util/ util/
COPY cifs-credentials /etc/

# RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir /home/aris
