# import the necessary packages
# importing only compare_simm function/object within the whole libary
from skimage.metrics import structural_similarity
#import imutils
import cv2
import numpy as np


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
pictures_list = np.empty((1,3), int)
pictures_list = np.append(pictures_list, np.array([1,2,3]), axis=0)

pictures_list = np.append(pictures_list, np.array([4,5,6]), axis=0)
#pictures_list = np.append(c[2,3,4], axis=0)

print(b)
N = 2
result = np.column_stack((a, b))

print(result)

avg = np.mean(result, axis=1)

print(avg)
