import re
import cv2
import time
import pyARIS
import threading
import subprocess
import numpy as np
from my_utils import *
from PIL import Image
from tqdm import tqdm
import matplotlib.pyplot as plt
from multiprocessing import Process

sonarDataDir = "./sonar/ARIS/"

def create_csv_file():
    r = "(.+)_(.+)\.zip"
    for item in os.listdir(os.path.join(sonarDataDir, "annotation")):
        match = re.match(r, item)
        print(match)
        break
        # if os.path.isdir(os.path.join(sonarDataDir, item)):


if __name__ == "__main__":
    create_csv_file()