import cv2
import numpy as np
import time

# Video Capture
capture = cv2.VideoCapture("D:/sonar/2020-05-27_071000.mp4")
#capture = cv2.VideoCapture("./output/Haida_2020-05-24/2020-05-24_000000_-8-62.mp4")
#capture = cv2.VideoCapture("D:/sonar/2020-05-25_020000.mp4")
capture = cv2.VideoCapture("./Haida_2020/2020-05-24_000000_-58-82.mp4")
capture = cv2.VideoCapture("./Haida_2020/2020-05-24_005000_2230-2370.mp4")
capture = cv2.VideoCapture("./Haida_2020/2020-05-24_081000_1102-1242.mp4")
capture = cv2.VideoCapture("./Haida_2020/denoised_2020-05-24_230000_323-463.mp4")
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
gmgSubtractor = cv2.bgsegm.createBackgroundSubtractorGMG(10, .8)    #
knnSubtractor = cv2.createBackgroundSubtractorKNN(100, 400, False)   # 2
cntSubtractor = cv2.bgsegm.createBackgroundSubtractorCNT(5, True)   #

# Keeps track of what frame we're on
frameCount = 0

# Determine how many pixels do you want to detect to be considered "movement"
movementCount = 1000
movementText = "pixels > 1000"
textColor = (255, 255, 255)

while True:
    # Return Value and the current frame
    ret, frame = capture.read()
    #  Check if a current frame actually exist
    if not ret:
        break
    frameCount += 1
    print("FrameCount: " + str(frameCount))

    # Resize the frame
    resizedFrame = cv2.resize(frame, (0, 0), fx=0.64, fy=0.64)

    # Get the foreground masks using all the subtractors
    mogMask = mogSubtractor.apply(resizedFrame)
    mog2Mask = mog2Subtractor.apply(resizedFrame)
    knnMask = knnSubtractor.apply(resizedFrame)

    countMOG2Mask = mog2Mask.copy()
    morphMOGMaskOpen = cv2.morphologyEx(countMOG2Mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)))
    morphMOGMaskClose = cv2.morphologyEx(morphMOGMaskOpen, cv2.MORPH_CLOSE,
                                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)))

    ret, thresh = cv2.threshold(morphMOGMaskOpen, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)
    print("n_labels: " + str(n_labels))

    morphMOGMaskOpen = cv2.cvtColor(morphMOGMaskOpen, cv2.COLOR_GRAY2RGB)
    size_thresh = 30
    for i in range(1, n_labels):
        if stats[i, cv2.CC_STAT_AREA] >= size_thresh:
            #print(stats[i, cv2.CC_STAT_AREA])
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            print("loc: " + str(x) + " " +str(y) + " " + str(w) + " " + str(h))
            cv2.rectangle(morphMOGMaskOpen, (x, y), (x + w, y + h), (0, 255, 0), thickness=1)


    mog2mask = mog2Subtractor.apply(resizedFrame)
    gmgMask = gmgSubtractor.apply(resizedFrame)
    gmgMask = cv2.morphologyEx(gmgMask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)))

    cntMask = cntSubtractor.apply(resizedFrame)


    # Count all the non zero pixels within the masks
    mogCount = np.count_nonzero(mogMask)
    mog2Count = np.count_nonzero(mog2mask)
    gmgCount = np.count_nonzero(gmgMask)
    knnCount = np.count_nonzero(knnMask)
    cntCount = np.count_nonzero(cntMask)

    #print('mog Frame: %d, Pixel Count: %d' % (frameCount, mogCount))
    #print('mog2 Frame: %d, Pixel Count: %d' % (frameCount, mog2Count))
    #print('gmg Frame: %d, Pixel Count: %d' % (frameCount, gmgCount))
    #print('knn Frame: %d, Pixel Count: %d' % (frameCount, knnCount))
    #print('cnt Frame: %d, Pixel Count: %d' % (frameCount, cntCount))

    titleTextPosition = (100, 40)
    titleTextSize = 1.2
    cv2.putText(mogMask, 'MOG', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)
    cv2.putText(mog2mask, 'MOG2', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)
    cv2.putText(gmgMask, 'GMG', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)
    cv2.putText(knnMask, 'KNN', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)
    cv2.putText(cntMask, 'CNT', titleTextPosition, cv2.FONT_HERSHEY_SIMPLEX, titleTextSize, textColor, 2, cv2.LINE_AA)

    countTextPosition = (100, 100)
    # if (frameCount > 1):
    #     if (mogCount > movementCount):
    #         cv2.putText(mogMask, 'count:' + str(1), countTextPosition, cv2.FONT_HERSHEY_SIMPLEX, .5,
    #                     textColor, 2, cv2.LINE_AA)
    #     if (mog2MCount > movementCount):
    #         cv2.putText(mog2Mmask, 'count:' + str(1), countTextPosition, cv2.FONT_HERSHEY_SIMPLEX, .5,
    #                     textColor, 2, cv2.LINE_AA)
    #     if (gmgCount > movementCount):
    #         cv2.putText(gmgMask, 'count:' + str(1), countTextPosition, cv2.FONT_HERSHEY_SIMPLEX, .5,
    #                     textColor, 2, cv2.LINE_AA)
    #     if (knnCount > movementCount):
    #         cv2.putText(knnMask, 'count:' + str(1), countTextPosition, cv2.FONT_HERSHEY_SIMPLEX, .5,
    #                     textColor, 2, cv2.LINE_AA)
    #     if (cntCount > movementCount):
    #         cv2.putText(cntMask, 'count:' + str(1), countTextPosition, cv2.FONT_HERSHEY_SIMPLEX, .5,
    #                     textColor, 2, cv2.LINE_AA)

    cv2.imshow('Original', resizedFrame)
    cv2.imshow('MOG', mogMask)
    cv2.imshow('MOG2', mog2mask)
    cv2.imshow('GMG', gmgMask)
    cv2.imshow('KNN', knnMask)
    cv2.imshow('CNT', cntMask)

    cv2.imshow('countMOGMask', countMOG2Mask)
    cv2.imshow('morphMOGMaskOpen', morphMOGMaskOpen)
    cv2.imshow('morphMOGMaskClose', morphMOGMaskClose)
    cntCount = np.count_nonzero(cntMask)

    cv2.moveWindow('Original', 0, 0)
    cv2.moveWindow('MOG', 400, 0)
    cv2.moveWindow('KNN', 800, 0)
    cv2.moveWindow('GMG', 1200, 0)
    cv2.moveWindow('MOG2', 1600, 0)
    cv2.moveWindow('CNT', 2000, 0)

    cv2.moveWindow('countMOGMask', 400, 700)
    cv2.moveWindow('morphMOGMaskOpen', 800, 700)
    cv2.moveWindow('morphMOGMaskClose', 1200, 700)

    k = cv2.waitKey(0) & 0xff
    # Enter for next frame and Esc for break the loop
    print(k)

    if k == 27:
        break

time.sleep(3)

capture.release()
cv2.destroyAllWindows()
