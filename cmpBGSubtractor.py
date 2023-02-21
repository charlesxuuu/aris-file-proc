import cv2
import numpy as np
import time

# Video Capture
capture = cv2.VideoCapture("D:/sonar/2020-05-27_071000.mp4")
capture = cv2.VideoCapture("D:/sonar/2020-05-25_020000.mp4")
#capture = cv2.VideoCapture("D:/sonar/caltech_2018-05-27_180004_1295_1895.mp4")

#capture = cv2.VideoCapture("D:/sonar/2020-05-24_000000.mp4")
"""
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
mog2Subtractor = cv2.createBackgroundSubtractorMOG2(100, 40, False) # 3
gmgSubtractor = cv2.bgsegm.createBackgroundSubtractorGMG(10, .8)    #
knnSubtractor = cv2.createBackgroundSubtractorKNN(100, 400, False)   # 2
cntSubtractor = cv2.bgsegm.createBackgroundSubtractorCNT(5, True)   #

# Keeps track of what frame we're on
frameCount = 0

# Determine how many pixels do you want to detect to be considered "movement"
movementCount = 1000
movementText = "pixels > 1000"
textColor = (255, 255, 255)

while (1):
    # Return Value and the current frame
    ret, frame = capture.read()

    #  Check if a current frame actually exist
    if not ret:
        break

    frameCount += 1

    # Resize the frame
    resizedFrame = cv2.resize(frame, (0, 0), fx=0.64, fy=0.64)



    # Get the foreground masks using all of the subtractors
    mogMask = mogSubtractor.apply(resizedFrame)
    knnMask = knnSubtractor.apply(resizedFrame)

    countKnnMask = mogMask.copy()

    morphKnnMask = cv2.morphologyEx(countKnnMask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)))

    ret, thresh = cv2.threshold(morphKnnMask, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)
    print("n_labels: " + str(n_labels))

    morphKnnMask = cv2.cvtColor(morphKnnMask, cv2.COLOR_GRAY2RGB)
    size_thresh = 30
    for i in range(1, n_labels):
        if stats[i, cv2.CC_STAT_AREA] >= size_thresh:
            #print(stats[i, cv2.CC_STAT_AREA])
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            print("loc: " + str(x) + " " +str(y) + " " + str(w) + " " + str(h))
            cv2.rectangle(morphKnnMask, (x, y), (x + w, y + h), (0, 255, 0), thickness=1)


    mog2Mmask = mog2Subtractor.apply(resizedFrame)
    gmgMask = gmgSubtractor.apply(resizedFrame)
    gmgMask = cv2.morphologyEx(gmgMask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)))

    cntMask = cntSubtractor.apply(resizedFrame)


    # Count all the non zero pixels within the masks
    mogCount = np.count_nonzero(mogMask)
    mog2MCount = np.count_nonzero(mog2Mmask)
    gmgCount = np.count_nonzero(gmgMask)
    knnCount = np.count_nonzero(knnMask)
    cntCount = np.count_nonzero(cntMask)

    print('mog Frame: %d, Pixel Count: %d' % (frameCount, mogCount))
    print('mog2M Frame: %d, Pixel Count: %d' % (frameCount, mog2MCount))
    print('gmg Frame: %d, Pixel Count: %d' % (frameCount, gmgCount))
    print('knn Frame: %d, Pixel Count: %d' % (frameCount, knnCount))
    print('cnt Frame: %d, Pixel Count: %d' % (frameCount, cntCount))

    titleTextPosition = (100, 40)
    titleTextSize = 1.2
    cv2.putText(mogMask, 'MOG', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)
    cv2.putText(mog2Mmask, 'MOG2', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)
    cv2.putText(gmgMask, 'GMG', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)
    cv2.putText(knnMask, 'KNN', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)
    cv2.putText(cntMask, 'CNT', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)

    countTextPosition = (100, 100)
    if (frameCount > 1):
        if (mogCount > movementCount):
            cv2.putText(mogMask, 'count:' + str(1), countTextPosition, cv2.FONT_HERSHEY_SIMPLEX, .5,
                        textColor, 2, cv2.LINE_AA)
        if (mog2MCount > movementCount):
            cv2.putText(mog2Mmask, 'count:' + str(1), countTextPosition, cv2.FONT_HERSHEY_SIMPLEX, .5,
                        textColor, 2, cv2.LINE_AA)
        if (gmgCount > movementCount):
            cv2.putText(gmgMask, 'count:' + str(1), countTextPosition, cv2.FONT_HERSHEY_SIMPLEX, .5,
                        textColor, 2, cv2.LINE_AA)
        if (knnCount > movementCount):
            cv2.putText(knnMask, 'count:' + str(1), countTextPosition, cv2.FONT_HERSHEY_SIMPLEX, .5,
                        textColor, 2, cv2.LINE_AA)
        if (cntCount > movementCount):
            cv2.putText(cntMask, 'count:' + str(1), countTextPosition, cv2.FONT_HERSHEY_SIMPLEX, .5,
                        textColor, 2, cv2.LINE_AA)


    cv2.imshow('Original', resizedFrame)
    cv2.imshow('MOG', mogMask)
    cv2.imshow('MOG2', mog2Mmask)
    cv2.imshow('GMG', gmgMask)
    cv2.imshow('KNN', knnMask)
    cv2.imshow('CNT', cntMask)

    cv2.imshow('countKnnMask', countKnnMask)
    cv2.imshow('morphKnnMask', morphKnnMask)

    cv2.moveWindow('Original', 0, 0)
    cv2.moveWindow('MOG', 400, 0)
    cv2.moveWindow('KNN', 800, 0)
    cv2.moveWindow('GMG', 1200, 0)
    cv2.moveWindow('MOG2', 1600, 0)
    cv2.moveWindow('CNT', 2000, 0)

    cv2.moveWindow('countKnnMask', 400, 700)
    cv2.moveWindow('morphKnnMask', 800, 700)

    k = cv2.waitKey(0) & 0xff
    print(k)
    if k == 27:
        break

time.sleep(5)

capture.release()
cv2.destroyAllWindows()