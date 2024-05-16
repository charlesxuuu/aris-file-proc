import cv2
import numpy as np


origin =  cv2.imread("1.jpg")
origin = cv2.cvtColor(origin,cv2.COLOR_RGB2GRAY)
mogSubtractor = cv2.bgsegm.createBackgroundSubtractorMOG(origin.shape[1]) 

##########
####方法一
##########
median = np.median(origin,axis=1)
repetitions = (1280, 1)  # Repeat 3 times along rows, 2 times along columns
result = np.tile(median, repetitions).T
result = np.abs(origin - result)
cv2.imwrite('2_1.jpg', result)


##########
####方法二
##########
mask = np.zeros((origin.shape[0], origin.shape[1]), dtype=np.uint8)
for x in range(origin.shape[1]):
    mogMask = mogSubtractor.apply(origin[:,x])
    copy_of_mog_mask = mogMask.copy()
    mask[:,x] = copy_of_mog_mask.T


cv2.imwrite('2_2.jpg', mask)
