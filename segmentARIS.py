import cv2
import time
import pyARIS
import threading
import subprocess
import numpy as np
from myUtils import *
from PIL import Image
from tqdm import tqdm
import matplotlib.pyplot as plt
from multiprocessing import Process

outputDir = "./output/"
sonarDataDir = "./sonar/"

# Crops the left and right black borders of the image
# This function check the entire column of the image from both left and right
def cropBlackBorder(img):
    leftX = 0
    rightX = img.shape[1] - 1

    for i in range(img.shape[1]):
        # check if the pixel is black
        if np.all(img[:, i] == 0):
            leftX += 1
        else:
            break
    
    for i in range(img.shape[1]):
        if np.all(img[:, rightX] == 0):
            rightX -= 1
        else:
            break

    return img[:, leftX:rightX]

# Crops the left and right black borders of the image
# This function only check the first row of the image
def cropBlackBorderFirstRow(img):
    leftX = 0
    rightX = img.shape[1] - 1

    for i in range(img.shape[1]):
        # check if the pixel is black
        if np.all(img[0, i] == 0):
            leftX += 1
        else:
            break
    
    for i in range(img.shape[1]):
        if np.all(img[0, rightX] == 0):
            rightX -= 1
        else:
            break

    return img[:, leftX:rightX]

def saveCroppedImage(segment1, segment2, segment3, ARISfolderName, ARISFileName, i):
    folder_path = os.path.join(outputDir, ARISfolderName, ARISFileName[:-5])
    create_folder(folder_path)

    cv2.imwrite(os.path.join(folder_path, "%d_seg1.jpeg" %(i)), segment1)
    cv2.imwrite(os.path.join(folder_path, "%d_seg2.jpeg" %(i)), segment2)
    cv2.imwrite(os.path.join(folder_path, "%d_seg3.jpeg" %(i)), segment3)

def segmentARISFile(filePath, ARISfolderName, ARISFileName):
    ARISdata, _ = pyARIS.DataImport(filePath)
    time.sleep(0.5)

    for i in range(ARISdata.FrameCount):
        frameData = pyARIS.FrameRead(ARISdata, i).remap
        convertedFrame = cv2.cvtColor(frameData, cv2.COLOR_GRAY2BGR)

        # segment1 = convertedFrame[:462,:]
        # segment2 = convertedFrame[462:462+428,:]
        # segment3 = convertedFrame[890:,:]
        # plt.figure(figsize=(15, 6))
        # plt.tight_layout()
        # plt.subplot(131), plt.imshow(cropBlackBorder(segment1))
        # plt.subplot(132), plt.imshow(cropBlackBorder(segment2))
        # plt.subplot(133), plt.imshow(cropBlackBorderFirstRow(segment3))

        segment1 = cropBlackBorder(convertedFrame[:462,:])
        segment2 = cropBlackBorder(convertedFrame[462:462+428,:])
        segment3 = cropBlackBorderFirstRow(convertedFrame[890:,:])

        # output the cropped image
        saveCroppedImage(segment1, segment2, segment3, ARISfolderName, ARISFileName, i)

# process one day of sonar data
def processSonarData(folderName, count):
    print("Processing %s" %(folderName), flush=True)
    oneDaySonarDataFolder = os.path.join(sonarDataDir, folderName)

    progressBar = tqdm(total=len(os.listdir(oneDaySonarDataFolder)), position=count, desc=folderName)

    for item in os.listdir(oneDaySonarDataFolder):
        if os.path.isfile(os.path.join(oneDaySonarDataFolder, item)):
            if item.endswith(".aris"):
                segmentARISFile(os.path.join(oneDaySonarDataFolder, item), folderName, item)
            else:
                print("%s is not an ARIS file, skip" %(os.path.join(oneDaySonarDataFolder, item)))
            progressBar.update(1)
            progressBar.refresh()
    progressBar.close()

def processAllARISFiles():
    pList = []
    count = 0

    for item in os.listdir(sonarDataDir):
        if os.path.isdir(os.path.join(sonarDataDir, item)):
            p = Process(target=processSonarData, args=(item,count))
            count += 1
            pList.append(p)
            p.start()
    
    for p in pList:
        p.join()

    print("\n\nAll done!", flush=True)

if __name__ == "__main__":
    processAllARISFiles()
