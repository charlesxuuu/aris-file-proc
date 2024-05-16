import cv2
import numpy as np
import time
from cv2.ximgproc import guidedFilter


def change_surrounding_region(mask,size):
    """
    expand white pixels 2 px
    """
    white_pixels = np.where(mask == 255)
    result_mask = np.copy(mask)
    
    for y, x in zip(*white_pixels):
        y_min = max(0, y - size)
        y_max = min(mask.shape[0], y + size)
        x_min = max(0, x - size)
        x_max = min(mask.shape[1], x + size)
        
        result_mask[y_min:y_max, x_min:x_max] = 255
    
    return result_mask

capture = cv2.VideoCapture("./output/denoised_MNLM_caltech1.mp4")
# capture = cv2.VideoCapture("Haida_2020-05-24/2020-05-24_230000_2027-2097.mp4")
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

mogSubtractor = cv2.bgsegm.createBackgroundSubtractorMOG(100)       # 1

# Keeps track of what frame we're on
frameCount = 0

while True:
    # return Value and the current frame
    ret, frame = capture.read()
    # check if a current frame actually exist
    if not ret:
        break
    frameCount += 1
    # print("FrameCount: " + str(frameCount))

    resized_frame = cv2.resize(frame, (0, 0), fx=1, fy=1)
    height, weight, _ = resized_frame.shape
    mogMask = mogSubtractor.apply(resized_frame)
    copy_of_mog_mask = mogMask.copy()

    copy_of_mog_mask = cv2.cvtColor(copy_of_mog_mask, cv2.COLOR_GRAY2RGB)

    # here use guided filter
    #

    guided_img = guidedFilter(copy_of_mog_mask, resized_frame, 10, 0.01)
    guided_mog = guidedFilter(resized_frame, copy_of_mog_mask, 10, 0.01)
    
    convert_image = np.dstack([
            cv2.cvtColor(resized_frame, cv2.COLOR_RGB2GRAY),
            cv2.cvtColor(guided_img, cv2.COLOR_RGB2GRAY),
            cv2.cvtColor(guided_mog, cv2.COLOR_RGB2GRAY)
        ]).astype(np.uint8)
    print(resized_frame.shape,guided_img.shape,convert_image.shape)
    #canny edge detection on guided img and guided_mog

    edge_original = cv2.Canny(guided_img, 200, 255)
    edge_mog = cv2.Canny(guided_mog, 200, 255)


    M_edge_mog = change_surrounding_region(edge_mog,2)
    
    result = resized_frame.copy()
    condition = (edge_original == 255) & (M_edge_mog == 255)
    result[condition] = [0, 0, 255]
    
    mask = np.zeros_like(edge_original, dtype=np.uint8)
    mask[condition] = 255
    mask = change_surrounding_region(mask,1)
    # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv3, 3)))2.getStructuringElement(cv2.MORPH_ELLIPSE, (
    ret, thresh = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)
    
    size_thresh = 15
    for i in range(1, n_labels):
        if stats[i, cv2.CC_STAT_AREA] >= size_thresh:
            #print(stats[i, cv2.CC_STAT_AREA])
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]            
            # print("loc: " + str(x) + " " +str(y) + " " + str(w) + " " + str(h))
            # print(y)
            cv2.rectangle(resized_frame, (x, y), (x + w, y + h), (0, 255, 0), thickness=1)
    
    cv2.imshow('original', resized_frame)
    cv2.imshow('mog_mask', mogMask)
    cv2.imshow('convert',convert_image)

    cv2.imshow('guided_img', guided_img)
    cv2.imshow('guided_mog', guided_mog)
    cv2.imshow('result', result)
    cv2.imshow('edge_original', edge_original)
    cv2.imshow('edge_mog', edge_mog)

    cv2.moveWindow('original', 0, 0)
    cv2.moveWindow('mog_mask', 450, 0)
    cv2.moveWindow('convert',450,500)
    cv2.moveWindow('result', 900, 0)

    cv2.moveWindow('guided_img', 1600, 0)
    cv2.moveWindow('guided_mog', 2050, 0)
    cv2.moveWindow('edge_original', 1600, 600)
    cv2.moveWindow('edge_mog', 2050, 600)

    k = cv2.waitKey(0) & 0xff

    if k == 27:
        # cv2.imwrite("1.jpg", resized_frame)
        # cv2.imwrite("2.jpg", mogMask)
        # cv2.imwrite("3.jpg", guided_img)
        # cv2.imwrite("4.jpg", guided_mog)
        # cv2.imwrite("5.jpg", edge_original)
        # cv2.imwrite("6.jpg", edge_mog)
        # cv2.imwrite('7.jpg', result)
        break

time.sleep(5)

capture.release()
cv2.destroyAllWindows()
