import os
import cv2
import numpy as np
import pandas as pd
import csv
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
    copy_of_mog_mask = cv2.cvtColor(mog_mask, cv2.COLOR_GRAY2RGB)

    guided_img = guidedFilter(copy_of_mog_mask, resized_frame, 10, 0.01)
    guided_mog = guidedFilter(resized_frame, copy_of_mog_mask, 10, 0.01)

    edge_original = cv2.Canny(guided_img, 200, 255)
    edge_mog = cv2.Canny(guided_mog, 200, 255)
    M_edge_mog = change_surrounding_region(edge_mog, 2)

    result = resized_frame.copy()
    condition = (edge_original == 255) & (M_edge_mog == 255)
    result[condition] = [0, 255, 0]

    mask = np.zeros_like(edge_original, dtype=np.uint8)
    mask[condition] = 255
    mask = change_surrounding_region(mask, 1)
    ret, thresh = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)

    convert_image = np.dstack([
        cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY),
        cv2.cvtColor(guided_img, cv2.COLOR_BGR2GRAY),
        cv2.cvtColor(guided_mog, cv2.COLOR_BGR2GRAY)
    ]).astype(np.uint8)

    # Debugging: Print shapes and types of processed frames
    # print(f"Frame {frame_count}:")
    # print(f"resized_frame shape: {resized_frame.shape}, dtype: {resized_frame.dtype}")
    # print(f"mog_mask shape: {mog_mask.shape}, dtype: {mog_mask.dtype}")
    # print(f"guided_img shape: {guided_img.shape}, dtype: {guided_img.dtype}")
    # print(f"guided_mog shape: {guided_mog.shape}, dtype: {guided_mog.dtype}")
    # print(f"edge_original shape: {edge_original.shape}, dtype: {edge_original.dtype}")
    # print(f"edge_mog shape: {edge_mog.shape}, dtype: {edge_mog.dtype}")
    # print(f"result shape: {result.shape}, dtype: {result.dtype}")
    # print(f"convert_image shape: {convert_image.shape}, dtype: {convert_image.dtype}")
    #
    # cv2.imwrite(f'debug_frames/frame_{frame_count}_resized.jpg', resized_frame)
    # cv2.imwrite(f'debug_frames/frame_{frame_count}_mog_mask.jpg', mog_mask)
    # cv2.imwrite(f'debug_frames/frame_{frame_count}_guided_img.jpg', guided_img)
    # cv2.imwrite(f'debug_frames/frame_{frame_count}_guided_mog.jpg', guided_mog)
    # cv2.imwrite(f'debug_frames/frame_{frame_count}_edge_original.jpg', edge_original)
    # cv2.imwrite(f'debug_frames/frame_{frame_count}_edge_mog.jpg', edge_mog)
    # cv2.imwrite(f'debug_frames/frame_{frame_count}_result.jpg', result)
    # cv2.imwrite(f'debug_frames/frame_{frame_count}_convert_image.jpg', convert_image)

    return resized_frame, mog_mask, guided_img, guided_mog, edge_original, edge_mog, result, n_labels, stats, convert_image


def count_fish(stats, guided_img, size_thresh=30):
    fish_count = 0
    fish_count_small = 0
    fish_count_large = 0
    for i in range(1, stats.shape[0]):
        if stats[i, cv2.CC_STAT_AREA] >= size_thresh:
            x, y, w, h = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[
                i, cv2.CC_STAT_HEIGHT]
            if np.mean(guided_img[y:y + h, x:x + w]) > 80:
                fish_count += 1
                if stats[i, cv2.CC_STAT_AREA] >= 50:
                    fish_count_large += 1
                else:
                    fish_count_small += 1
    return fish_count, fish_count_small, fish_count_large


def display_frames(frames):
    titles = ['original', 'mog_mask', 'convert', 'result', 'guided_img', 'guided_mog', 'edge_original', 'edge_mog']
    for i, (title, frame) in enumerate(zip(titles, frames)):
        cv2.imshow(title, frame)
        cv2.moveWindow(title, (i % 6) * 400, (i // 8) * 800)
    cv2.waitKey(1)  # Wait for a short period to allow the windows to update


def process_video(input_path, output_path):
    capture = cv2.VideoCapture(input_path)
    mog_subtractor = cv2.bgsegm.createBackgroundSubtractorMOG(100)
    frame_count = 0
    clips, items_record, items_record_small, items_record_large = [], [], [], []
    items_record_clips, items_record_clips_small, items_record_clips_large = [], [], []
    temp, temp_small, temp_large = [], [], []
    interval = 0

    while True:
        ret, frame = capture.read()
        if not ret:
            break
        frame_count += 1

        resized_frame, mog_mask, guided_img, guided_mog, edge_original, edge_mog, result, n_labels, stats, convert_image = process_frame(
            frame, mog_subtractor, frame_count)
        fish_count, fish_count_small, fish_count_large = count_fish(stats, guided_img)

        items_record.append(fish_count)
        items_record_small.append(fish_count_small)
        items_record_large.append(fish_count_large)
        if temp:
            temp.append(fish_count)
            temp_small.append(fish_count_small)
            temp_large.append(fish_count_large)

        if fish_count != 0:
            interval = 0
            if not clips or len(clips) % 2 == 0:
                clips.append(max(0, frame_count - 40))
                temp = items_record[-40:] if frame_count > 40 else items_record
                temp_small = items_record_small
                temp_large = items_record_large
        else:
            interval += 1
        if interval > 80 and len(clips) % 2 == 1:
            clips.append(frame_count - 40)
            items_record_clips.append(temp[:-40])
            temp = []
            items_record_clips_large.append(temp_large[:-40])
            temp_large = []
            items_record_clips_small.append(temp_small[:-40])
            temp_small = []

        frames = [resized_frame, mog_mask, convert_image, result, guided_img, guided_mog, edge_original, edge_mog]
        display_frames(frames)

    if len(clips) % 2 == 1:
        clips.append(frame_count)
    items_record_clips.append(temp)
    items_record_clips_large.append(temp_large)
    items_record_clips_small.append(temp_small)

    print("起始帧和终止帧")
    print(clips)
    print("二维矩阵: 不同clips的fish count")
    print("不同clips fish count list长度是")
    print_2d_list_with_lengths(items_record_clips)
    print(items_record_clips)
    print("一维矩阵: 整个视频的fish count")
    print("准确值是2761，整个视频fish count list长度是" + str(len(items_record)))
    print(items_record)
    print("二维矩阵: 不同clips的fish count(小)")
    print(items_record_clips_small)
    print("一维矩阵: 整个视频的fish count(小)")
    print(items_record_small)
    print("二维矩阵: 不同clips的fish count(大)")
    print(items_record_clips_large)
    print("一维矩阵: 整个视频的fish count(大)")
    print(items_record_large)

    save_clips(capture, clips, output_path)
    save_long_summary_csv(clips, items_record_clips, items_record_clips_large, items_record_clips_small, output_path)
    capture.release()
    cv2.destroyAllWindows()


def print_2d_list_with_lengths(two_d_list):
    for i, one_d_list in enumerate(two_d_list):
        print(f"List {i + 1} (length {len(one_d_list)}): {one_d_list}")


def save_clips(capture, clips, output_path):
    fps = capture.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # Create the directory if it does not exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for i in range(0, len(clips), 2):
        start_frame = clips[i]
        end_frame = clips[i + 1]
        output_filename = f"{output_path}/clip_{i // 2 + 1}_{start_frame}-{end_frame}.mp4"
        out = cv2.VideoWriter(output_filename, fourcc, fps,
                              (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))))
        capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        while capture.isOpened() and start_frame <= end_frame:
            ret, frame = capture.read()
            if ret:
                out.write(frame)
            else:
                break
            start_frame += 1
        out.release()


def save_long_summary_csv(clips, items_record_clips, items_record_clips_large,
                          items_record_clips_small, output_path):
    long_summary = []
    #for i, clip in enumerate(items_record_clips):
    #    start_frame = sum(len(c) for c in items_record_clips[:i])
    #    end_frame = start_frame + len(clip) - 1

    for i in range(len(clips / 2)):
        # TODO: some bugs here
        start_frame = clips[2 * i]
        end_frame = clips[2 * i + 1]
        clip = items_record_clips[i]
        max_count = max(clip) if clip else 0
        total_sum = sum(clip)

        small_clip = items_record_clips_small[i]
        large_clip = items_record_clips_large[i]
        max_small_count = max(small_clip) if small_clip else 0
        max_large_count = max(large_clip) if large_clip else 0

        long_summary.append([i + 1, start_frame, end_frame, max_count, max_large_count, max_small_count, total_sum])

    # Create a DataFrame for the results
    df = pd.DataFrame(long_summary, columns=['clip_no', 'start_frame', 'end_frame', 'max_count_a_frame',
                                             'max_large_count_a_frame', 'max_small_count_a_frame',
                                             'total_count_a_clip'])

    # Save the results to a CSV file
    csv_file_path = 'long_summary.csv'
    txt_file_path = 'long_summary.txt'
    csv_joined_file_path = os.path.join(output_path, csv_file_path)
    txt_joined_file_path = os.path.join(output_path, txt_file_path)
    df.to_csv(csv_joined_file_path, index=False)
    generate_aligned_txt_summary(csv_joined_file_path, txt_joined_file_path)


def generate_aligned_txt_summary(input_csv, output_txt):
    with open(input_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        # Determine the max length of each column
        column_widths = {column: max(len(column), max(len(str(row[column])) for row in reader)) for column in
                         reader.fieldnames}

        csvfile.seek(0)  # Reset the reader to the beginning of the file
        reader = csv.DictReader(csvfile)  # Re-read the CSV file

        with open(output_txt, 'w') as txtfile:
            # Write the header
            headers = [column.ljust(column_widths[column]) for column in reader.fieldnames]
            txtfile.write(" | ".join(headers) + "\n")
            txtfile.write("-" * (sum(column_widths.values()) + len(headers) * 3 - 1) + "\n")

            # Write each row
            for row in reader:
                line = [str(row[column]).ljust(column_widths[column]) for column in reader.fieldnames]
                txtfile.write(" | ".join(line) + "\n")


if __name__ == "__main__":
    input_video_path = "sonar_mp4/ARIS_2020_05_24/2020-05-24_000000.mp4"
    base_output_path = "sonar_mp4/ARIS_2020_05_24"
    clip_folder_name = os.path.basename(input_video_path).split('.')[0]
    output_video_path = os.path.join(base_output_path, clip_folder_name)
    process_video(input_video_path, output_video_path)
