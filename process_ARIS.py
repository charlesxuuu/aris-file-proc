# read .aris file and convert segment each frame into 3 parts and save them into output folder
import time
import pyARIS
import threading
import subprocess
import numpy as np
from my_utils import *
from PIL import Image
import matplotlib.pyplot as plt
from multiprocessing import Process

outputDir = "./output/processed_sonar/"
sonarDataDir = "./sonar/"

def covertARISToVideo(ARISFilePath, outputVideoPath, startFrame=1, endFrame=None):
    ARISdata, _ = pyARIS.DataImport(ARISFilePath)
    pyARIS.VideoExportOriginal_NoProgressBar(
        ARISdata,
        start_frame=startFrame,
        end_frame=endFrame,
        filename=outputVideoPath)

# process one day of sonar data
def processSonarData(folderName):
    print("Processing %s" %(folderName), flush=True)
    oneDaySonarDataFolder = os.path.join(sonarDataDir, folderName)
    videoOutputFolder = os.path.join(outputDir, folderName)
    create_folder(videoOutputFolder)

    for item in os.listdir(oneDaySonarDataFolder):
        if os.path.isfile(os.path.join(oneDaySonarDataFolder, item)):
            if item.endswith(".aris"):
                ARISdata, _ = pyARIS.DataImport(os.path.join(oneDaySonarDataFolder, item))
                pyARIS.VideoExportOriginal_NoProgressBar(
                    ARISdata,
                    start_frame=1,
                    end_frame=50,
                    filename=os.path.join(videoOutputFolder, "test.mp4"))
            else:
                print("%s is not an ARIS file, skip" %(os.path.join(oneDaySonarDataFolder, item)))
    
    time.sleep(3) # * so all the print statements can be printed
    print("Done processing %s" %(folderName), flush=True)

def processAllARISFiles():
    pList = []

    for item in os.listdir(sonarDataDir):
        if "ARIS" in item and os.path.isdir(os.path.join(sonarDataDir, item)):
            p = Process(target=processSonarData, args=(item,))
            pList.append(p)
            p.start()
        
            break
    
    for p in pList:
        p.join()
    
    print("\n\nAll done!", flush=True)

if __name__ == "__main__":
    processAllARISFiles()
