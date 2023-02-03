"""Test read write and some shallow operations on image frames.

Leave one blank line.  The rest of this docstring should contain an
overall description of the module or program.  Optionally, it may also
contain a brief description of exported classes and functions and/or usage
examples.

Typical usage example:

foo = ClassFoo()
bar = foo.FunctionBar()

Image Denoising https://docs.opencv.org/3.4/d5/d69/tutorial_py_non_local_means.html
cv.fastNlMeansDenoising()
cv.fastNlMeansDenoisingColored()
cv.fastNlMeansDenoisingMulti()

Metric
Scikit Image has an estimate sigma function that works pretty well:

http://scikit-image.org/docs/dev/api/skimage.restoration.html#skimage.restoration.estimate_sigma

it also works with color images, you just need to set multichannel=True and average_sigmas=True:

import cv2
from skimage.restoration import estimate_sigma

def estimate_noise(image_path):
    img = cv2.imread(image_path)
    return estimate_sigma(img, multichannel=True, average_sigmas=True)

"""


import pyARIS

import matplotlib.pyplot as plt
from PIL import Image
import cv2

filename = "D:/sonar/2020-05-27_071000.aris"


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

    out_file_name = filename[0 : len(filename) - 4] + "mp4"
    print("Output File: " + out_file_name)
    # chix: change from frame to ARISdata
    pyARIS.VideoExport(ARISdata, out_file_name, start_frame=10, end_frame=2500, timestamp=True, fontsize=30, ts_pos=(10, 1200))
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