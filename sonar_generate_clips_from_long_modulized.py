import cv2
import numpy as np
from cv2.ximgproc import guidedFilter

def change_surrounding_region(mask, size):
    white_pixels = np.where(mask == 255)
    result_mask = np.copy(mask)
    for y, x in zip(*white_pixels):
        y_min = max(0, y - size)
        y_max = min(mask.shape[0], y + size)
        x_min = max(0, x - size)
        x_max = min(mask.shape[1], x + size)
        result_mask[y_min:y_max, x_min:x_max] = 255
    return result_mask

def process_frame(frame, mog_subtractor, frame_count):
    resized_frame = cv2.resize(frame, (0, 0), fx=0.6, fy=0.6)
    mog_mask = mog_subtractor.apply(resized_frame)
    guided_img = guidedFilter(resized_frame, mog_mask, 10, 0.01)
    guided_mog = guidedFilter(resized_frame, mog_mask, 10, 0.01)
    edge_original = cv2.Canny(guided_img, 200, 255)
    edge_mog = cv2.Canny(guided_mog, 200, 255)
    M_edge_mog = change_surrounding_region(edge_mog, 2)
    result = resized_frame.copy()
    condition = (edge_original == 255) & (M_edge_mog == 255)
    result[condition] = [0, 0, 255]
    mask = np.zeros_like(edge_original, dtype=np.uint8)
    mask[condition] = 255
    mask = change_surrounding_region(mask, 1)
    ret, thresh = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)
    convert_image = np.dstack([
        cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY),
        guided_img,
        guided_mog
    ]).astype(np.uint8)
    return resized_frame, mog_mask, guided_img, guided_mog, edge_original, edge_mog, result, n_labels, stats, convert_image

def count_fish(stats, guided_img, size_thresh=30):
    fish_count = 0
    fish_count_small = 0
    fish_count_big = 0
    for i in range(1, stats.shape[0]):
        if stats[i, cv2.CC_STAT_AREA] >= size_thresh:
            x, y, w, h = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            if np.mean(guided_img[y:y + h, x:x + w]) > 80:
                fish_count += 1
                if stats[i, cv2.CC_STAT_AREA] >= 50:
                    fish_count_big += 1
                else:
                    fish_count_small += 1
    return fish_count, fish_count_small, fish_count_big

def display_frames(frames):
    titles = ['original', 'mog_mask', 'convert', 'result', 'guided_img', 'guided_mog', 'edge_original', 'edge_mog']
    for i, (title, frame) in enumerate(zip(titles, frames)):
        cv2.imshow(title, frame)
        cv2.moveWindow(title, (i % 4) * 450, (i // 4) * 600)

def process_video(input_path, output_path):
    capture = cv2.VideoCapture(input_path)
    mog_subtractor = cv2.bgsegm.createBackgroundSubtractorMOG(100)
    frame_count = 0
    clips, items_record, items_record_small, items_record_big = [], [], [], []
    items_record_clips, items_record_clips_small, items_record_clips_big = [], [], []
    temp, temp_small, temp_big = [], [], []
    interval = 0

    while True:
        ret, frame = capture.read()
        if not ret:
            break
        frame_count += 1

        resized_frame, mog_mask, guided_img, guided_mog, edge_original, edge_mog, result, n_labels, stats, convert_image = process_frame(frame, mog_subtractor, frame_count)
        fish_count, fish_count_small, fish_count_big = count_fish(stats, guided_img)

        items_record.append(fish_count)
        items_record_small.append(fish_count_small)
        items_record_big.append(fish_count_big)
        if temp:
            temp.append(fish_count)
            temp_small.append(fish_count_small)
            temp_big.append(fish_count_big)

        if fish_count != 0:
            interval = 0
            if not clips or len(clips) % 2 == 0:
                clips.append(max(0, frame_count - 40))
                temp = items_record[-40:] if frame_count > 40 else items_record
                temp_small = items_record_small
                temp_big = items_record_big
        else:
            interval += 1
        if interval > 80 and len(clips) % 2 == 1:
            clips.append(frame_count - 40)
            items_record_clips.append(temp[:-40])
            temp = []
            items_record_clips_big.append(temp_big[:-40])
            temp_big = []
            items_record_clips_small.append(temp_small[:-40])
            temp_small = []

        frames = [resized_frame, mog_mask, convert_image, result, guided_img, guided_mog, edge_original, edge_mog]
        display_frames(frames)

    if len(clips) % 2 == 1:
        clips.append(frame_count)
    items_record_clips.append(temp)
    items_record_clips_big.append(temp_big)
    items_record_clips_small.append(temp_small)

    print("起始帧和终止帧")
    print(clips)
    print("二维矩阵: 不同clips的fish count")
    print(items_record_clips)
    print("一维矩阵: 整个视频的fish count")
    print(items_record)
    print("二维矩阵: 不同clips的fish count(小)")
    print(items_record_clips_small)
    print("一维矩阵: 整个视频的fish count(小)")
    print(items_record_small)
    print("二维矩阵: 不同clips的fish count(大)")
    print(items_record_clips_big)
    print("一维矩阵: 整个视频的fish count(大)")
    print(items_record_big)

    save_clips(capture, clips, output_path)
    capture.release()
    cv2.destroyAllWindows()

def save_clips(capture, clips, output_path):
    fps = capture.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    for i in range(0, len(clips), 2):
        start_frame = clips[i]
        end_frame = clips[i + 1]
        output_filename = f"{output_path}/clip_{i // 2 + 1}.mp4"
        out = cv2.VideoWriter(output_filename, fourcc, fps, (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))))
        capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        while capture.isOpened() and start_frame <= end_frame:
            ret, frame = capture.read()
            if ret:
                out.write(frame)
            else:
                break
            start_frame += 1
        out.release()

if __name__ == "__main__":
    input_video_path = "sonar_mp4/ARIS_2020_05_24/2020-05-24_000000.mp4"
    output_video_path = "output_clips"
    process_video(input_video_path, output_video_path)
