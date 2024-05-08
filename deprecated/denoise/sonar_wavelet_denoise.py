import cv2
import pywt
import numpy as np

# Function to perform wavelet denoising on an image
def wavelet_denoise(image, wavelet='db1', level=1):
    coeffs = pywt.wavedec2(image, wavelet, level=level)
    coeffs_H = list(coeffs)
    threshold = 2 * np.median(np.abs(coeffs[-1][-1]))
    for i in range(1, len(coeffs_H)):
        coeffs_H[i] = tuple([pywt.threshold(j, value=threshold, mode='soft') for j in coeffs_H[i]])
    return pywt.waverec2(coeffs_H, wavelet)

# Load the video
cap = cv2.VideoCapture('./output/Haida_2020-05-24/2020-05-24_230000_373-443.mp4')

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('output_denoised.mp4', fourcc, 20.0, (int(cap.get(3)), int(cap.get(4))))

while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        # Convert frame to grayscale
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Apply wavelet denoising
        denoised_frame = wavelet_denoise(gray_frame)
        # Convert back to BGR
        denoised_frame_bgr = cv2.cvtColor(denoised_frame.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        # Write the frame
        out.write(denoised_frame_bgr)
    else:
        break

# Release everything if job is finished
cap.release()
out.release()
cv2.destroyAllWindows()