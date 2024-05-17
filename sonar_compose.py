import os
import re
import json
import time
import logging
import subprocess
from datetime import datetime
from util.my_utils import *

SONAR_ARIS_FOLDER_PATH = '/home/aris/'
SONAR_RGB_FOLDER_PATH = '/home/sonar_rgb/'
SONAR_LOG_PATH = '/home/logs/'
settings = {}
mount_drive_command = ""
logger_current_date = ""
# subprocess.call(["sshfs", "netlabmedia@ip:/media/netlabmedia/LaCie/", "/user/src/pi_drive", "-o", "IdentityFile=/user/src/app/test_key", "-o", "StrictHostKeyChecking=no"])

def initialize_logger():
    global logger_current_date
    current_date = time.strftime("%Y-%m-%d")
    logger_current_date = current_date
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

    return earliest_outer_folder, earliest_inner_folder, earliest_file
    # return earliest_folder

def record_current_processing_file(earliest_outer_folder, earliest_inner_folder, earliest_file):
    with open(f"{SONAR_ARIS_FOLDER_PATH}/processing_file.json", "w") as f:
        json.dump({'earliest_outer_folder': earliest_outer_folder, 'earliest_inner_folder': earliest_inner_folder, 'earliest_file': earliest_file}, f)

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
        subprocess.run(mount_drive_command, shell=True, text=True, 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logging.info("Command executed successfully")
        create_folder(os.path.join(SONAR_ARIS_FOLDER_PATH, 'motion_detected'))
    except subprocess.CalledProcessError as e:
        logging.info(f"Error executing command: {e.stderr}")
        if (e.stderr.find("Device or resource busy") != -1):
            logging.info("Drive already mounted")
            return True
        return False
    
    return True

def process_file(out_folder, in_folder, file):
    pass

def get_next_file():
    pass

need_init = True

if __name__ == '__main__':
    while True:
        if need_init:
            initialize_settings()
            initialize_logger()
            initialize_drive()
            logging.info("Sonar app started")
        
        if time.strftime("%Y-%m-%d") != logger_current_date:
            initialize_logger()
        
        if "ARIS" not in os.listdir(SONAR_ARIS_FOLDER_PATH):
            logging.info("Folder is empty")
            time.sleep(900)
            continue

        if not os.path.exists(f"{SONAR_ARIS_FOLDER_PATH}/processing_file.json"):
            try:
                outer_folder, inner_folder, file = get_first_file("/mnt/d")
                record_current_processing_file(outer_folder, inner_folder, file)
            except Exception as e:
                logging.info(f"Error getting first file: {e}")
                time.sleep(900)
                continue
        else:
            with open(f"{SONAR_ARIS_FOLDER_PATH}/processing_file.json", "r") as f:
                data = json.load(f)
                outer_folder = data['earliest_outer_folder']
                inner_folder = data['earliest_inner_folder']
                file = data['earliest_file']
        
        if need_init:
            need_init = False
        else:
            next_outer_folder, next_inner_folder, next_file = get_next_file()
        
        process_file(next_outer_folder, next_inner_folder, next_file)
