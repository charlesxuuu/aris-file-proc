import cv2

def process_video(input_path, output_path, kernel_size=(5, 5)):
    # Open the video
    cap = cv2.VideoCapture(input_path)
    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # or 'XVID'
    out = cv2.VideoWriter(output_path, fourcc, 20.0, (int(cap.get(3)), int(cap.get(4))))

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # Apply Gaussian Blur to frame
            blurred_frame = cv2.GaussianBlur(frame, kernel_size, 0)
            # Write the frame into the file 'output_path'
            out.write(blurred_frame)
        else:
            break

    # Release everything if job is finished
    cap.release()
    out.release()
    cv2.destroyAllWindows()

# Set your video path and output path
input_video_path = './Haida_2020/2020-05-24_230000_323-463.mp4'
output_video_path = './Haida_2020/blurred_2020-05-24_230000_323-463.mp4'

# Apply Gaussian Blur to the video
process_video(input_video_path, output_video_path)
# Set your video path and output path