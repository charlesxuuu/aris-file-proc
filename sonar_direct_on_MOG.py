import cv2
import numpy as np
import time
import math

# Video Capture
capture = cv2.VideoCapture("./output/Haida_2020-05-24/2020-05-24_015000_503-573.mp4")
#capture = cv2.VideoCapture("./output/Haida_2020-05-24/2020-05-24_230000_373-443.mp4")
capture = cv2.VideoCapture("./output/Haida_2020-05-24/wuikinuxv23.mp4")

#capture = cv2.VideoCapture("./output/Haida_2020-05-24/2020-05-24_000000_-8-62.mp4")
#capture = cv2.VideoCapture("D:/sonar/2020-05-25_020000.mp4")
#capture = cv2.VideoCapture("D:/sonar/2020-05-24_000000.mp4")
"""

MOG algorithm brief introduction (in chinese) https://blog.csdn.net/weixin_53598445/article/details/124093067

history is the number of frames used to build the statistic model of the background. 
The smaller the value is, the faster changes in the background will be taken into account 
by the model and thus be considered as background. And vice versa.

dist2Threshold is a threshold to define whether a pixel is different from the background or not. 
The smaller the value is, the more sensitive movement detection is. And vice versa.

detectShadows : If set to true, shadows will be displayed in gray on the generated mask. (Example bellow)

count: https://stackoverflow.com/questions/52087533/how-to-find-number-of-clusters-in-a-image
"""

# Subtractors
# history = 300, nmixtures = 5, backgroundRatio = 0.001
mogSubtractor = cv2.bgsegm.createBackgroundSubtractorMOG(100)       # 1
# history = 300, varThreshold = 16, detectShadows = true
mog2Subtractor = cv2.createBackgroundSubtractorMOG2(100, 40, True) # 3

# Keeps track of what frame we're on
frameCount = 0

# Determine how many pixels do you want to detect to be considered "movement"
movementCount = 1000
movementText = "pixels > 1000"
textColor = (255, 255, 255)
previous_x = []
previous_y = []

while True:
    # Return Value and the current frame
    ret, frame = capture.read()
    #  Check if a current frame actually exist
    if not ret:
        break
    frameCount += 1
    print("FrameCount: " + str(frameCount))

    # Resize the frame
    resizedFrame = cv2.resize(frame, (0, 0), fx=0.7, fy=0.7)
    height, weight, _ = resizedFrame.shape

    # Get the foreground masks using all the subtractors
    mogMask = mogSubtractor.apply(resizedFrame)
    countMOGMask = mogMask.copy()
    morphMOGMask = cv2.morphologyEx(countMOGMask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)))

    ret, thresh = cv2.threshold(countMOGMask, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)
    print("n_labels: " + str(n_labels))

    countMOGMask = cv2.cvtColor(countMOGMask, cv2.COLOR_GRAY2RGB)
    size_thresh = 3
    for i in range(1, n_labels):
        if stats[i, cv2.CC_STAT_AREA] >= size_thresh:
            #print(stats[i, cv2.CC_STAT_AREA])
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            print("loc: " + str(x) + " " +str(y) + " " + str(w) + " " + str(h))
            region = resizedFrame[y:y+h, x:x+w]
            mean_color = np.mean(region, axis=(0, 1))
            print(y)
            if np.mean(mean_color)*y/height > 60 and w*h > 10:
                cv2.rectangle(countMOGMask, (x, y), (x + w, y + h), (0, 255, 0), thickness=1)
                cv2.rectangle(resizedFrame, (x, y), (x + w, y + h), (0, 255, 0), thickness=1)

    mog2Mmask = mog2Subtractor.apply(resizedFrame)

    # Count all the non zero pixels within the masks
    mogCount = np.count_nonzero(mogMask)
    mog2MCount = np.count_nonzero(mog2Mmask)

    print('mog Frame: %d, Pixel Count: %d' % (frameCount, mogCount))
    print('mog2 Frame: %d, Pixel Count: %d' % (frameCount, mog2MCount))

    titleTextPosition = (100, 40)
    titleTextSize = 1.2
    cv2.putText(mogMask, 'MOG', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)
    cv2.putText(mog2Mmask, 'MOG2', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)

    countTextPosition = (100, 100)

    cv2.imshow('Original', resizedFrame)
    cv2.imshow('MOG', mogMask)
    cv2.imshow('MOG2', mog2Mmask)

    cv2.imshow('countMOGMask', countMOGMask)
    cv2.imshow('morphMOGMask', morphMOGMask)

    cv2.moveWindow('Original', 100, 0)
    cv2.moveWindow('MOG', 500, 0)
    cv2.moveWindow('countMOGMask', 900, 0)
    cv2.moveWindow('morphMOGMask', 1300, 0)

    k = cv2.waitKey(0) & 0xff
    # Enter for next frame and Esc for break the loop
    print(k)

    if k == 27:
        break

time.sleep(5)

capture.release()
cv2.destroyAllWindows()
