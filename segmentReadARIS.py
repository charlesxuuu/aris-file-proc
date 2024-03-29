"""Test read write and some shallow operations on image frames.

Leave one blank line.  The rest of this docstring should contain an
overall description of the module or program.  Optionally, it may also
contain a brief description of exported classes and functions and/or usage
examples.

Code for extract a raw video file from aris file.
Notable parameters
fps aris data provided was 5 fps

currently output 10 fps  - similar as Caltech dataset
segment into three regions

"""


import pyARIS

import matplotlib.pyplot as plt
from PIL import Image
import cv2

filename = r"D:/sonar/segment/2020-05-27_071000.aris"

def cutoff_gate(mapped_frame, low, high):
    for i in range(1, int(mapped_frame.size / mapped_frame[0].size) - 1 ):
        for j in range(1, mapped_frame[0].size - 1):
            #print(str(i) + " " + str(j))
            if 80 >= mapped_frame[i][j] > 0:
                mapped_frame[i][j] = 1
            if 170 <= mapped_frame[i][j] < 255:
                mapped_frame[i][j] = 254
    return mapped_frame


def main():

    ARISdata, frame = pyARIS.DataImport(filename)


    out_folder_name_seg1 = filename[0 : len(filename) - 5] + "-seg1"
    out_file_name_seg1 = filename[0 : len(filename) - 5] + "-seg1.mp4"
    out_folder_name_seg2 = filename[0 : len(filename) - 5] + "-seg2"
    out_file_name_seg2 = filename[0 : len(filename) - 5] + "-seg2.mp4"
    out_folder_name_seg3 = filename[0 : len(filename) - 5] + "-seg3"
    out_file_name_seg3 = filename[0 : len(filename) - 5] + "-seg3.mp4"

    print("Output Folder: " + out_folder_name_seg2)
    print("Output File: " + out_file_name_seg2)

    # chix: change from frame to ARISdata
    pyARIS.VideoSegExport(ARISdata, out_folder_name_seg1, out_file_name_seg1, start_frame=1, timestamp=False, fontsize=30, ts_pos=(10, 1200), x=208 ,y=890, w=206, h=392)
    pyARIS.VideoSegExport(ARISdata, out_folder_name_seg2, out_file_name_seg2, start_frame=1, timestamp=False, fontsize=30, ts_pos=(10, 1200), x=107 ,y=462, w=408, h=428)
    pyARIS.VideoSegExport(ARISdata, out_folder_name_seg3, out_file_name_seg3, start_frame=1, timestamp=False, fontsize=30, ts_pos=(10, 1200), x=5 ,y=0, w=612, h=462)
    print("Output Finished")


    frame = pyARIS.FrameRead(ARISdata, 2)
    original_frame = frame.remap     # frame.remap is a ndarray, whose size is the total number of elements
    cutoff_frame = original_frame.copy()

    # gate threadhold
    cutoff_gate(cutoff_frame, 40, 254)

    # print (" " + str(frame.remap.size) + " " + str(frame.remap[0].size))

    original_cvt = cv2.cvtColor(original_frame, cv2.COLOR_GRAY2BGR)
    cutoff_cvt = cv2.cvtColor(cutoff_frame, cv2.COLOR_GRAY2BGR)
    denoise_cvt = cv2.fastNlMeansDenoisingColored(original_cvt, None, 10, 10, 7, 21)

    plt.subplot(131), plt.imshow(original_cvt)
    plt.subplot(132), plt.imshow(cutoff_cvt)
    plt.subplot(133), plt.imshow(denoise_cvt)
    plt.show()

    #for i in range(ARISdata.FrameCount):
    #        frame = FrameRead(ARISdata, i)

    #im = Image.fromarray(frame.remap)
    #im.show()

    #cv2.imshow('data', frame.remap)
    #cv2.waitKey(5000)
    #cv2.destroyAllWindows()
    return

if __name__ == '__main__':
    main()