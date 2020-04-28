

"""
Main code for the alignement process. To be integrated in main rota-print code.
Written by Hélène Verhaeghe
"""

# import the necessary packages
# importing only compare_simm function/object within the whole libary
from skimage.metrics import structural_similarity
# import imutils
import cv2
import numpy as np
import statistics


#def control_system(status):


## turn on/off the laser,camera and lighting
#if status:
#    # do something to turn the system on
#    else:
#        # do something to turn the system off


#def take_picture(temp_file_path):
# take a picture with camera
# Return the data

#picture_data = cv2.imread(temp_file_path)

#return picture_data


def split_image(image):
    # split the image into separate R,G,B arrays.
    # return the 3 outputs
    B, G, R = cv2.split(image)

    # output["R"] = R
    # output["G"] = G
    # output["B"] = B

    return B, G, R

# for channel in ["R", "G", "B"]:
    # print(picture_data[channel])


def goto_angle(degrees):
    pass
# rotates the part degrees


def rotate_and_picture(y):  # y is the number of picture

    # Rotate the part in order to return ynumber for picture, taken every rotation
    # return an array of
    pictures_list = np.empty((0,3), int)
    angle_step = 360/y  # reference

    # if y=8: x=[0,45,90,135,180,225,270,315] - will need to return to 0/360 position
    for x in range(0, y):
        angle = 360/y*x
        goto_angle(angle)
        picture = take_picture(picture)
        B, G, R = cv2.split(picture)

        # record data in array with each R,G,B values associated to rotation (3 column: R,G,B) 0,1,2
        pictures_list = np.append(pictures_list, np.array([[R,G,B]]), axis=0)

        # index - [0,1,2,3,4,5,6,7]


    goto_angle(angle_step)

    return angle_step, pictures_list


def test_split(list_test):

    pictures_list = np.empty((0,3), int)

    for image in list_test:
        imageB = cv2.imread(image) #[b,g,r]
        B, G, R = cv2.split(imageB)
        #B = imageB[:,0,0]
        #G = imageB[0,:,0]
        #R = imageB[0,0,:]
        pictures_list = np.append(pictures_list, np.array([[R,G,B]]), axis=0)
    
    return pictures_list


"""Initial Alignement"""

# light up laser
"""control_system(True)"""


# here parts is being moved linearly to FOV of sensing position
# engineer manaually align the part to desired starting position in reference to laser.

# Record the y number of images of reference and store image data
"""angle_step_y, reference_image = rotate_and_picture(y)  # y to be chosen"""


"""Alignement of batch"""

# import dummy pictures for testing code
y = 4
ref_images = ["vision/img1.jpg", "vision/img4.jpg", "vision/img8.jpg", "vision/img10.jpg"]
angle_step_y = 360/y

reference_images = test_split(ref_images)

# test5
w = 14
com_images = ["vision/img1.jpg", "vision/img2.jpg", "vision/img3.jpg", "vision/img4.jpg", "vision/img5.jpg", "vision/img6.jpg", "vision/img7.jpg", "vision/img8.jpg", "vision/img9.jpg", "vision/img10.jpg", "vision/img11.jpg", "vision/img12.jpg", "vision/img13.jpg", "vision/img14.jpg"]
angle_step_w = 360/w


comparison_images = test_split(com_images)


# next part is moved linearly to sensing position

# record w number of inspection image to be compared with reference images

# w to be chosen for accuracy
"""angle_step_w, comparison_images = rotate_and_picture(w)"""

# compare the x number of images to the w compariosn images - as a set of y
score_list_R = []
score_list_G = []
score_list_B = []

ideal_step = angle_step_y / angle_step_w


# 1st loop for red
for j in range(0, w):
    for i in range(0, y):
        score_list = []
        # compute only R values - 1st column
        com_R = comparison_images[:, 0]
        ref_R = reference_images[:, 0]
        # find the index that is the closest to the desired angle by rounding it to the nearest image - index
        actual_index = round(ideal_step * i)
        # compute the Stuctural Similarity Indey (SSIM) - score - every x times
        (scoreR, _) = structural_similarity(ref_R[i], com_R[::actual_index], full=True)

        score_list.append(scoreR)
        score_list_R = np.mean(score_list)




# 2nd loop for Green
for j in range(0, w):
    for i in range(0, y):
        score_list = []
        # compute only G values - 2nd column
        com_G = comparison_images[:, 1]
        ref_G = reference_images[:, 1]
        # find the index that is the closest to the desired angle by rounding it to the nearest image - index
        actual_index = round(ideal_step * i)
        # compute the Stuctural Similarity Indey (SSIM) - score - every x times
        (scoreG, _) = structural_similarity(ref_G[i], com_G[::actual_index], full=True)

        score_list.append(scoreG)
        score_list_G = np.mean(score_list)


# 3rd loop for Blue
for j in range(0, w):
    for i in range(0, y):
        score_list = []
        # compute only R values - 1st column
        com_B = comparison_images[:, 2]
        ref_B = reference_images[:, 2]
        # find the index that is the closest to the desired angle by rounding it to the nearest image - index
        actual_index = round(ideal_step * i)
        # compute the Stuctural Similarity Indey (SSIM) - score - every x times
        (scoreB, _) = structural_similarity(ref_B[i], com_B[::actual_index], full=True)

        score_list.append(scoreB)
        score_list_B = np.mean(score_list)

        
score_list_RGB = np.column_stack((score_list_R, score_list_G, score_list_B))

# average the scores from R,G,B
score_list_avg = np.mean (score_list_RGB, axis=1)

# find the highest score
# return the index
i = score_list_avg.index(max(score_list_avg))

# print("Most similar image:" + comparison_list[i])

# the index indicate the image hence the rotation
goto_angle(angle_step_w*i)
