FROM python:3.9-slim

WORKDIR /user/src/app

COPY . .
# RUN pip install --no-cache-dir -r requirements.txt

# RUN python3 sonar_compose.py
RUN apt-get update && apt-get install -y sshfs
RUN mkdir /user/src/pi_drive
RUN sshfs netlabmedia@142.58.48.145:/media/netlabmedia/LaCie/ /user/src/pi_drive -o IdentityFile=./test_key.pub
