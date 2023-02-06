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

https://docs.opencv.org/3.4.0/db/d5c/tutorial_py_bg_subtraction.html

"""

import numpy as np
import cv2 as cv

algo = 'MOG'

#create Background Subtractor objects
if algo == 'MOG2':
    backSub = cv.createBackgroundSubtractorMOG2()
else:
    backSub = cv.createBackgroundSubtractorKNN()

capture = cv.VideoCapture('D:/sonar/2020-05-27_071000.mp4')

if not capture.isOpened():
    print('Unable to open')
    exit(0)


while 1:
    ret, frame = capture.read()

    fgmask = backSub.apply(frame)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
    fgmask = cv.morphologyEx(fgmask, cv.MORPH_OPEN, kernel)

    cv.imshow('frame',fgmask)
    k = cv.waitKey(30) & 0xff
    if k == 27:
        break

capture.release()
cv.destroyAllWindows()