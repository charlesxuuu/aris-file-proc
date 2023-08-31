import re
import cv2
import csv
import json
import time
import pyARIS
import threading
import subprocess
import numpy as np
import datumaro as dm
from my_utils import *
from PIL import Image
from tqdm import tqdm
from dateutil import parser
import matplotlib.pyplot as plt
from multiprocessing import Process

sonarDataDir = "./sonar/"
outputDir = "./output/"

def preprocess_data_and_generate_csv_file():
    output_video_folder_path = os.path.join(outputDir, "video")
    create_folder(output_video_folder_path)
    r = "(.+)_(.+)\.zip"

    with open(os.path.join(outputDir, "fileInfo.csv"), "w") as f:
        csvWriter = csv.writer(f)
        csvWriter.writerow(["filename", "vid_path", "anno_path"])

        for item in os.listdir(os.path.join(sonarDataDir, "annotation")):
            match = re.match(r, item)
            date = parser.parse(match[1])
            time = match[2]

            ARISfolderName = "ARIS_%s" %(date.strftime("%Y_%m_%d"))
            ARISFolderPath = os.path.join(sonarDataDir, "ARIS", ARISfolderName)
            ARISFilePath = os.path.join(ARISFolderPath, "%s_%s.aris" %(date.strftime("%Y-%m-%d"), time))
            
            # From annotation folder, find the corresponding ARIS file and preprocess
            if os.path.exists(ARISFolderPath) and os.path.exists(ARISFilePath):
                print("Processing %s" %(ARISFilePath))
                ARISFileName = os.path.splitext(os.path.basename(ARISFilePath))[0]
                videoFolderPath = os.path.join(output_video_folder_path, ARISfolderName)
                create_folder(videoFolderPath)

                ARISdata, _ = pyARIS.DataImport(ARISFilePath)
                pyARIS.VideoExportOriginal(ARISdata, filename=os.path.join(videoFolderPath, "%s.mp4" %(ARISFileName)))

                csvWriter.writerow([ARISFileName, os.path.join(videoFolderPath, "%s.mp4" %(ARISFileName)), os.path.join(sonarDataDir, "annotation", item)])

def annotation_converter_helper(datum_proj_path, coco_output_proj_path):
    dataset = dm.Dataset.import_from(datum_proj_path, 'datumaro')
    dataset.export(coco_output_proj_path, 'coco')

def convert_annotation_to_coco():
    datum_proj_path = os.path.join(outputDir, "datum_proj")
    datum_anno_path = os.path.join(outputDir, "annotation")
    coco_proj_path = os.path.join(outputDir, "coco_proj")

    subprocess.run(["python3", "datum_create_dataset.py", os.path.join(outputDir, "fileInfo.csv"), 
                    "--proj-path", datum_proj_path,
                    "--anno-path", datum_anno_path])
    pList = []
    for item in os.listdir(datum_proj_path):
        if os.path.isdir(os.path.join(datum_proj_path, item)):
            datum_input_proj_path = os.path.join(datum_proj_path, item)
            coco_output_proj_path = os.path.join(coco_proj_path, item)

            p = Process(target=annotation_converter_helper, args=(datum_input_proj_path, coco_output_proj_path))
            pList.append(p)
            p.start()
    
    for p in pList:
        p.join()
    
    print("\n\nDone!")

# bounding box format: [top left x position, top left y position, width, height]
# crop_boundaries = [[0:462], [462:890], [890:]]
# Go though the annotation file and split the annotation into 3 files according to the crop_boundaries
# If the bounding box is in between segments, the bounding box is simply discarded
def reconstruct_coco_annotation(file_path, folder_path):
    with open(file_path, "r") as f:
        data = json.load(f)
        temp_annotation_list = []
        for _ in range(3):
            temp_annotation_list.append([])

        for idx, obj in enumerate(data["annotations"]):
            ymin = obj["bbox"][1]
            ymax = obj["bbox"][1] + obj["bbox"][3]
            # print(obj["bbox"])
            # print("ymin: %d, ymax: %d" %(ymin, ymax))

            if ymax < 462:
                temp_annotation_list[0].append(obj)
            elif ymin >= 462 and ymax < 890:
                temp_annotation_list[1].append(obj)
            elif ymin >= 890:
                temp_annotation_list[2].append(obj)

        for i in range(3):
            tempJson = data.copy()
            # ! after converting the annotation file to COCO format, some of the annotation id is duplicated for same reason
            # ! Manually reassign the id to avoid this problem
            for idx, obj in enumerate(temp_annotation_list[i]):
                obj["id"] = idx + 1
            tempJson["annotations"] = temp_annotation_list[i]

            with open(os.path.join(folder_path, "instances_default_%d.json" %(i)), "w") as json_file:
                json.dump(tempJson, json_file)

def segment_coco_annotation():
    coco_proj_path = os.path.join(outputDir, "coco_proj")

    for item in os.listdir(coco_proj_path):
        if os.path.isdir(os.path.join(coco_proj_path, item)):
            annotation_folder_path = os.path.join(coco_proj_path, item, "annotations")
            annotation_file_path = os.path.join(annotation_folder_path, "instances_default.json")

            reconstruct_coco_annotation(annotation_file_path, annotation_folder_path)

if __name__ == "__main__":
    # preprocess_data_and_generate_csv_file()
    # convert_annotation_to_coco()
    segment_coco_annotation()
