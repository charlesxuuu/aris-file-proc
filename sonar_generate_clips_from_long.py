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
# capture = cv2.VideoCapture("1.mp4")
capture = cv2.VideoCapture("1.mp4")
# capture = cv2.VideoCapture("caltech.mp4")
# capture = cv2.VideoCapture("Haida_2020-05-24/2020-05-24_230000_2027-2097.mp4")


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

clips = []
interval = 0 # 没鱼的时长
while True:
    # return Value and the current frame
    ret, frame = capture.read()
    # check if a current frame actually exist
    if not ret:
        break
    frameCount += 1
    # print("FrameCount: " + str(frameCount))

    resized_frame = cv2.resize(frame, (0, 0), fx=0.6, fy=0.6)
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
    # print(resized_frame.shape,guided_img.shape,convert_image.shape)
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
    
    size_thresh = 30
    Fish_count = 0
    for i in range(1, n_labels):
        if stats[i, cv2.CC_STAT_AREA] >= size_thresh:
            #print(stats[i, cv2.CC_STAT_AREA])
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]            
            # print("loc: " + str(x) + " " +str(y) + " " + str(w) + " " + str(h))
            # print(y)
            if np.mean(guided_img[y:y+h,x:x+w])>80:
                Fish_count += 1 # 计算单个frame的鱼的数量
                cv2.rectangle(resized_frame, (x, y), (x + w, y + h), (0, 255, 0), thickness=1)
    if Fish_count != 0:
        interval = 0
        if len(clips) == 0 or len(clips)%2 ==0:  # 如果 检测到有鱼 且没有clip正在录制
            clips.append(max(0,frameCount-10)) # 添加clip开始时间
    else:
        interval += 1
    # print(interval)
    if interval > 80 and len(clips)%2 == 1: # 如果空余时长超过 80 帧
        clips.append(frameCount-10) # 添加 clip 结束时间
        
            
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
    cv2.moveWindow('convert',900,600)
    cv2.moveWindow('result', 900, 0)

    cv2.moveWindow('guided_img', 1400, 0)
    cv2.moveWindow('guided_mog', 1850, 0)
    cv2.moveWindow('edge_original', 1400, 600)
    cv2.moveWindow('edge_mog', 1850, 600)

    # k = cv2.waitKey(0) & 0xff

    # if k == 27:
    #     # cv2.imwrite("1.jpg", resized_frame)
    #     # cv2.imwrite("2.jpg", mogMask)
    #     # cv2.imwrite("3.jpg", guided_img)
    #     # cv2.imwrite("4.jpg", guided_mog)
    #     # cv2.imwrite("5.jpg", edge_original)
    #     # cv2.imwrite("6.jpg", edge_mog)
    #     # cv2.imwrite('7.jpg', result)
    #     break

# time.sleep(5)
if len(clips)%2 == 1:
    clips.append(frameCount)

print(clips)


fps = capture.get(cv2.CAP_PROP_FPS)

fourcc = cv2.VideoWriter_fourcc(*'mp4v')

for i in range(0, len(clips), 2):
    start_frame = clips[i]
    end_frame = clips[i + 1]

    output_filename = f"clip_{i//2 + 1}.mp4"

    out = cv2.VideoWriter(output_filename, fourcc, fps, (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                                        int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))))

    capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    while capture.isOpened() and start_frame <= end_frame:
        ret, frame = capture.read()
        if ret:
            out.write(frame)
        else:
            break
        start_frame += 1

    out.release()

capture.release()
cv2.destroyAllWindows()