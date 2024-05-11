import os
import time
import logging
import subprocess
from util.my_utils import *

SONAR_ARIS_FOLDER_PATH = '/home/aris/'
SONAR_GRB_FOLDER_PATH = '/home/sonar_rgb/'
SONAR_LOG_PATH = '/home/logs/'
mount_drive_command = f"mount -t cifs //ip/d {SONAR_ARIS_FOLDER_PATH} -o credentials=/etc/cifs-credentials,uid=$(id -u),gid=$(id -g)"
# subprocess.call(["sshfs", "netlabmedia@ip:/media/netlabmedia/LaCie/", "/user/src/pi_drive", "-o", "IdentityFile=/user/src/app/test_key", "-o", "StrictHostKeyChecking=no"])

def initialize_logger():
    current_date = time.strftime("%Y-%m-%d")
    logging.basicConfig(filename=os.path.join(SONAR_LOG_PATH, f'{current_date}.log'), 
                        format='%(asctime)s - %(message)s',
                        level=logging.INFO)

def initialize_drive():
    try:
        logging.info("Mounting drive")
        print(mount_drive_command)
        result = subprocess.run(mount_drive_command, shell=True, text=True, 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logging.info("Command executed successfully, output:\n", result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error("Error output:", e.stderr)

# TODO: use a config json file and read in IP address and other parameters
if __name__ == '__main__':
    initialize_logger()
    initialize_drive()
    logging.info("Sonar app started")

    print(os.listdir(SONAR_ARIS_FOLDER_PATH))

    count = 0
    while True:
        time.sleep(5)
        logging.info(count)
        count += 1

