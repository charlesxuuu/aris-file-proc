import os
import platform
import yaml
import pyARISupdated
import logging


def load_config():
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return config['aris_drive_path'], config['mp4_drive_path']


def convert_aris_to_video(aris_file_path, mp4_file_path, start_frame=1, end_frame=None, fps=5):
    ARISdata, _ = pyARISupdated.DataImport(aris_file_path)
    pyARISupdated.VideoExportOriginal_NoProgressBar(
        ARISdata,
        start_frame=start_frame,
        end_frame=end_frame,
        filename=mp4_file_path,
        fps=fps,
        osPlatform=platform.system())


def bytes_to_mb(size_in_bytes):
    return size_in_bytes / (1024 * 1024)


def process_directory(aris_drive_path, mp4_drive_path):
    exclude_pattern = "\\$RECYCLE.BIN\\"
    aris_files = []

    for root, dirs, files in os.walk(aris_drive_path):
        if exclude_pattern in root:
            continue  # Skip processing any files in or below the $RECYCLE.BIN directory
        for file in files:
            if file.endswith('.aris'):
                aris_files.append(os.path.join(root, file))

    total_aris_files = len(aris_files)
    files_processed = 0

    for aris_file_path in aris_files:
        aris_file_size = bytes_to_mb(os.path.getsize(aris_file_path))
        relative_path = os.path.relpath(os.path.dirname(aris_file_path), aris_drive_path)
        mp4_directory = os.path.join(mp4_drive_path, relative_path)
        if not os.path.exists(mp4_directory):
            os.makedirs(mp4_directory)
        mp4_file_path = os.path.join(mp4_directory, os.path.basename(aris_file_path).replace('.aris', '.mp4'))

        convert_aris_to_video(aris_file_path, mp4_file_path)

        mp4_file_size = bytes_to_mb(os.path.getsize(mp4_file_path))
        files_processed += 1

        logging.info(
            f"Converted: {aris_file_path} ({aris_file_size:.2f} MB) to {mp4_file_path} ({mp4_file_size:.2f} MB)")
        logging.info(f"Progress: {files_processed}/{total_aris_files} files converted.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    aris_drive_path, mp4_drive_path = load_config()
    process_directory(aris_drive_path, mp4_drive_path)