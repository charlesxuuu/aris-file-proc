import os
import re
import json
import time
import logging
import subprocess
from datetime import datetime
from util.my_utils import *

SONAR_ARIS_FOLDER_PATH = '/home/aris/'
SONAR_GRB_FOLDER_PATH = '/home/sonar_rgb/'
SONAR_LOG_PATH = '/home/logs/'
settings = {}
mount_drive_command = ""
# subprocess.call(["sshfs", "netlabmedia@ip:/media/netlabmedia/LaCie/", "/user/src/pi_drive", "-o", "IdentityFile=/user/src/app/test_key", "-o", "StrictHostKeyChecking=no"])

def initialize_logger():
    current_date = time.strftime("%Y-%m-%d")
    logging.basicConfig(filename=os.path.join(SONAR_LOG_PATH, f'{current_date}.log'), 
                        format='%(asctime)s - %(message)s',
                        level=logging.INFO)

def get_date_from_folder_name_outer(folder_name):
    date_pattern = re.compile(r'[A-Za-z]+\s\d{4}')  
    match = date_pattern.search(folder_name)

    if match:
        return datetime.strptime(match.group(), '%B %Y')
    return None

def get_date_from_folder_name_inner(folder_name):
    date_pattern = re.compile(r'\d{4}_\d{2}_\d{2}')
    match = date_pattern.search(folder_name)

    if match:
        return datetime.strptime(match.group(), '%Y_%m_%d')
    return None

def get_date_from_file_name(file_name):
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}_\d{6}')
    match = date_pattern.search(file_name)

    if match:
        return datetime.strptime(match.group(), '%Y-%m-%d_%H%M%S')
    return None

def get_first_file(directory_path):
    outer_folders = [f for f in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, f))]
    outer_folders_with_dates = [(folder, get_date_from_folder_name_outer(folder)) for folder in outer_folders]
    outer_folders_with_dates = [fd for fd in outer_folders_with_dates if fd[1] is not None] # filter out folders without dates

    earliest_outer_folder = min(outer_folders_with_dates, key=lambda x: x[1])[0]

    inner_folders = [f for f in os.listdir(os.path.join(directory_path, earliest_outer_folder)) if os.path.isdir(os.path.join(directory_path, earliest_outer_folder, f))]
    inner_folders_with_dates = [(folder, get_date_from_folder_name_inner(folder)) for folder in inner_folders]
    inner_folders_with_dates = [fd for fd in inner_folders_with_dates if fd[1] is not None] # filter out folders without dates

    earliest_inner_folder = min(inner_folders_with_dates, key=lambda x: x[1])[0]

    files = [f for f in os.listdir(os.path.join(directory_path, earliest_outer_folder, earliest_inner_folder)) if os.path.isfile(os.path.join(directory_path, earliest_outer_folder, earliest_inner_folder, f))]
    files_with_dates = [(file, get_date_from_file_name(file)) for file in files]
    files_with_dates = [fd for fd in files_with_dates if fd[1] is not None] # filter out files without dates

    earliest_file = min(files_with_dates, key=lambda x: x[1])[0]

    print(earliest_outer_folder, earliest_inner_folder, earliest_file)
    # return earliest_folder

def initialize_settings():
    global settings
    global mount_drive_command

    with open('./settings/settings.json', 'r') as f:
        settings = json.load(f)

    mount_drive_command = f"mount -t cifs //{settings['drive_IP']}/{settings['drive_letter']} {SONAR_ARIS_FOLDER_PATH} -o credentials=/user/src/app/settings/cifs-credentials,uid=$(id -u),gid=$(id -g)"
    return settings

def initialize_drive():
    try:
        logging.info("Mounting drive")
        logging.info(mount_drive_command)
        result = subprocess.run(mount_drive_command, shell=True, text=True, 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logging.info("Command executed successfully")
    except subprocess.CalledProcessError as e:
        logging.info("Error output:", e.stderr, result.stdout)

if __name__ == '__main__':
    print(get_first_file("/mnt/d"))
    # initialize_settings()
    # initialize_logger()
    # initialize_drive()
    # logging.info("Sonar app started")

    # while True:
    #     time.sleep(5)

