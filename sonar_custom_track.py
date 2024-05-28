from collections import defaultdict
import cv2
import numpy as np
import time
from ultralytics import YOLO

# Load your YOLOv8 model
model = YOLO("yolov8m_our_converted.pt")

# Define video path and parameters
video_path = "F:/sonar-data-train/2/clip_convert_up_1_1-3063.mp4"
# video_path = "F:/sonar-data-train/2/clip_convert_up_1_1-3063.mp4"  # Uncomment if you want to use this video instead

cap = cv2.VideoCapture(video_path)
img_size = 640
conf_level = 0.001

# Get video properties
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Define the codec and create VideoWriter object
output_path = 'output_annotated_video.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' codec for .mp4 file
out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

if __name__ == '__main__':
    # Store the track history
    track_history = defaultdict(list)

    # Loop through the video frames
    while cap.isOpened():
        # Read a frame from the video
        success, frame = cap.read()

        if success:
            # Run YOLOv8 tracking on the frame, persisting tracks between frames
            results = model.track(frame, imgsz=img_size, persist=True, conf=conf_level)

            # Check if there are any detections
            if results[0].boxes is not None and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                confidences = results[0].boxes.conf.cpu().numpy()

                # Visualize the results on the frame
                annotated_frame = results[0].plot()

                # Plot the tracks
                for box, track_id in zip(boxes, track_ids):
                    x1, y1, x2, y2 = box
                    track = track_history[track_id]
                    track.append(((x1 + x2) / 2, (y1 + y2) / 2))  # Append the center point

                    if len(track) > 30:  # Retain 30 points for 30 frames
                        track.pop(0)

                    # Draw the tracking lines
                    points = np.array(track, dtype=np.int32).reshape((-1, 1, 2))
                    cv2.polylines(annotated_frame, [points], isClosed=False, color=(230, 230, 230), thickness=2)

                # Write the frame to the video file
                out.write(annotated_frame)

                # Display the annotated frame
                cv2.imshow("YOLOv8 Tracking", annotated_frame)
                time.sleep(0.0001)

                # Break the loop if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        else:
            # Break the loop if the end of the video is reached
            break

    # Release the video capture and writer objects and close the display window
    cap.release()
    out.release()
    cv2.destroyAllWindows()