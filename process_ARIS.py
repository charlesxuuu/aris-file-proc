# read .aris file and convert segment each frame into 3 parts and save them into output folder
import re
import csv
import time
import platform
import pyARIS
import threading
import subprocess
import multiprocessing
import numpy as np
import pandas as pd
from my_utils import *
from PIL import Image
from tqdm import tqdm
from datetime import datetime
from dateutil import parser
import matplotlib.pyplot as plt
from multiprocessing import Process

arisFolderPath = "./sonar/"
salmonNoteFolderPath = "./sonar/notes2/"
outputVideoPath = "./output/"
numFramesBefore = 10
numFramesAfter = 50
numFramesToBeConsideredTogether = 20

# * Deprecated
outputDir = "./output/processed_sonar/"
sonarDataDir = "./sonar/"

def covertARISToVideo(ARISFilePath, outputVideoPath, startFrame=1, endFrame=None, fps=24):
    ARISdata, _ = pyARIS.DataImport(ARISFilePath)
    pyARIS.VideoExportOriginal_NoProgressBar(
        ARISdata,
        start_frame=startFrame,
        end_frame=endFrame,
        filename=outputVideoPath,
        fps=fps,
        osPlatform=platform.system())

def date_convert_helper(date):
    if "-" not in date:
        return datetime.strptime(date, "%B %d", ).replace(year=2020)
    else:
        return datetime.strptime(date, "%d-%B", ).replace(year=2020)

# read and concatenate all fish notes
def read_salmon_note():
    allSalmonNote = pd.DataFrame()

    for item in os.listdir(salmonNoteFolderPath):
        filePath = os.path.join(salmonNoteFolderPath, item)
        print(filePath)
        if os.path.isfile(filePath) and item.endswith(".csv"):
            # # ! Ignore LF Haida Sonar file for now
            # if "LF" not in item:
            if True: # * use this if LF Haida Sonar file is fixed
                salmonNote = pd.read_csv(filePath)[["Date","Timefile","Time","Frame"]].dropna()
                allSalmonNote = pd.concat([allSalmonNote, salmonNote])
    
    allSalmonNote = allSalmonNote.reset_index(drop=True)
    allSalmonNote["frameNumber"] = allSalmonNote["Frame"].apply(lambda x: int(re.findall(r"^-?\d+", x)[0])) # extract frame number
    allSalmonNote["convertedTime"] = allSalmonNote["Time"].apply(lambda x: datetime.strptime(x, "%H:%M:%S"))
    allSalmonNote["convertedDate"] = allSalmonNote["Date"].apply(date_convert_helper)
    allSalmonNote["combinedDate"] = pd.to_datetime(allSalmonNote["convertedDate"].astype(str) + " " + allSalmonNote["convertedTime"].astype(str), format="mixed")
    
    # * group all notes by date and frame number, and only keep the first note
    allSalmonNote = allSalmonNote.groupby(["convertedDate",  "frameNumber"]).first()
    allSalmonNote = allSalmonNote.sort_values(by=["convertedDate", "convertedTime"]).reset_index()

    # * calculate time difference between each annotation
    allSalmonNote["timeDiff"] = allSalmonNote["combinedDate"].diff()
    # * convert time difference to seconds
    allSalmonNote["timeDiff"] = allSalmonNote["timeDiff"].apply(lambda x: x.seconds)
    
    # * combine rows where time difference is less than 20 seconds
    # TODO: update this number if necessary
    allSalmonNote["group"] = (allSalmonNote["timeDiff"] > numFramesToBeConsideredTogether).cumsum()
    allSalmonNote.to_csv("allSalmonNote.csv", index=False)

    allSalmonNote["fileNameTimePrefix"] = allSalmonNote["Timefile"].apply(lambda x: datetime.strptime(x, "%H:%M").strftime("%H%M%S"))
    allSalmonNote["fileNameDatePrefix"] = allSalmonNote["convertedDate"].apply(lambda x: x.strftime("%Y-%m-%d"))
    allSalmonNote["folderName"] = allSalmonNote["convertedDate"].apply(lambda x: x.strftime("ARIS_%Y_%m_%d"))
    allSalmonNote.to_csv("allSalmonNote.csv", index=False)
    
    return allSalmonNote

def process_salmon_note(start, end, allSalmonNote, fps):
    currentRow = start
    totalRows = allSalmonNote.shape[0]

    while currentRow <= end:
        row = allSalmonNote.iloc[currentRow]
        startFrame = row["frameNumber"] - numFramesBefore # ! This might be less than 0
        endFrame = row["frameNumber"] + numFramesAfter # ! This might be greater than the total number of frames
        group = row["group"]
        fileName = "{}_{}.aris".format(row["fileNameDatePrefix"], row["fileNameTimePrefix"])
        folderName = row["folderName"]
        arisFilePath = "%s%s/%s" % (arisFolderPath, folderName, fileName)
        videoPathFolder = outputVideoPath + "Haida_%s/" % (row["fileNameDatePrefix"])
        videoPath = outputVideoPath + "Haida_%s/%s_%s_%s-%s.mp4" % (row["fileNameDatePrefix"], 
                                                                    row["fileNameDatePrefix"], 
                                                                    row["fileNameTimePrefix"], 
                                                                    startFrame, 
                                                                    endFrame)
        tempRow = currentRow
        for _, row in allSalmonNote.iloc[tempRow+1:totalRows].iterrows():
            if row["group"] == group:
                endFrame = row["frameNumber"] + numFramesAfter
                currentRow += 1
            else:
                break
        currentRow += 1

        if os.path.isfile(arisFilePath):
            if startFrame < 0 or endFrame < 0:
                create_folder(videoPathFolder)
                covertARISToVideo(arisFilePath, videoPath,startFrame=-1, endFrame=-1, fps=fps)
        else:
            # print("File %s does not exist" %(arisFilePath))
            pass
    
    print("Done processing %s to %s" %(start, end), flush=True)

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

# ! LF Haida Sonar Data 2020 - LF not processed
if __name__ == "__main__":
    pList = []
    fps = 5
    num_cores = multiprocessing.cpu_count() # get number of cores
    allSalmonNote = read_salmon_note()

    # * get number of rows in the dataframe
    num_rows = allSalmonNote.shape[0]
    print("num_rows: %s" %(num_rows))
    for i in range(num_cores):
        start = int(i * num_rows / num_cores)
        end = int((i+1) * num_rows / num_cores)

        if i == num_cores - 1:
            end = num_rows - 1
        p = Process(target=process_salmon_note, args=(start, end, allSalmonNote, fps))
        p.start()
        pList.append(p)
    
    for p in pList:
        p.join()

    # process_salmon_note(3510, 3530, allSalmonNote, fps)
    
    time.sleep(3) # * so all the print statements can be printed
    print("\n\nAll done!", flush=True)
