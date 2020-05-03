# import the necessary packages
# importing only compare_simm function/object within the whole libary
from skimage.metrics import structural_similarity
#import imutils
import cv2
import numpy as np
import statistics


#b = np.array([0, a, a, a])
# pictures_list=[]
# print(b)
# load the image of reference
#imageREF = cv2.imread("vision/imgCfront.jpg")

#B,G,R = cv2.split(imageREF)


"""Stack test"""
#a = np.array((1,2,3))
#b = np.array((8,9,10))
#c = np.zeros(3)
#pictures_list = np.empty((1,3), int)
#pictures_list = np.append(pictures_list, np.array([1,2,3]), axis=0)

#pictures_list = np.append(pictures_list, np.array([4,5,6]), axis=0)
#pictures_list = np.append(c[2,3,4], axis=0)

#print(b)
#N = 2
#result = np.column_stack((a, b))

#print(result)

#avg = np.mean(result, axis=1)

#print(avg)

"""Loop data storage"""

#ref_images_upload = ["vision/img1.jpg", "vision/img4.jpg", "vision/img8.jpg", "vision/img10.jpg"]
#com_images_upload = ["vision/img1.jpg", "vision/img2.jpg", "vision/img3.jpg", "vision/img4.jpg", "vision/img5.jpg", "vision/img6.jpg", "vision/img7.jpg", "vision/img8.jpg", "vision/img9.jpg", "vision/img10.jpg", "vision/img11.jpg", "vision/img12.jpg", "vision/img13.jpg", "vision/img14.jpg"]

"""angle step"""
#angle_step_w=52
#angle_step_y=8

#ideal_step = round(angle_step_w / angle_step_y)
#print(ideal_step)

#(scoreB, _ )= structural_similarity(ref_images[i][:,:,0], com_images[actual_index][:,:,0], full=True)
#temp_score=[0.9,0.8,0.9,0.5]

#score_list = statistics.mean (temp_score)
#print(score_list)

def truncate(n, decimals=0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


j=0.0

b = np.around(j, decimals=1)
print (b)