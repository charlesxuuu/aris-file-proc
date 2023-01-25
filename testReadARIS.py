


import pyARIS

import matplotlib.pyplot as plt
from PIL import Image
import cv2

filename = "D:/sonar/2020-05-27_071000.aris"
ARISdata, frame = pyARIS.DataImport(filename)

frame = pyARIS.FrameRead(ARISdata, 2)


tmp = frame.remap
#print(frame.remap.type)

# gate threadhold

# print (" " + str(frame.remap.size) + " " + str(frame.remap[0].size))
# for i in range(1, int(frame.remap.size / frame.remap[0].size) - 1 ):
#     for j in range(1, frame.remap[0].size - 1):
#         #print(str(i) + " " + str(j))
#         if 80 >= frame.remap[i][j] > 0:
#             frame.remap[i][j] = 1
#         if 170 <= frame.remap[i][j] < 255:
#             frame.remap[i][j] = 254
#
img = cv2.cvtColor(frame.remap, cv2.COLOR_GRAY2BGR)

dst = cv2.fastNlMeansDenoisingColored(img,None,10,10,7,21)

plt.subplot(121),plt.imshow(img)
plt.subplot(122),plt.imshow(dst)
plt.show()

#for i in range(ARISdata.FrameCount):
#        frame = FrameRead(ARISdata, i)

#im = Image.fromarray(frame.remap)
#im.show()

#cv2.imshow('data', frame.remap)
#cv2.waitKey(5000)
#cv2.destroyAllWindows()


out_file_name = filename[0 : len(filename) - 4] + "mp4"
print(out_file_name)
pyARIS.VideoExport(frame, out_file_name, start_frame=10, end_frame=50, timestamp=True, fontsize=30, ts_pos=(10, 1200))
