

"""
Main code for the alignement process. To be integrated in main rota-print code.
Written by Hélène Verhaeghe
"""

# import the necessary packages
# importing only compare_simm function/object within the whole libary
from skimage.metrics import structural_similarity #import imutils
import cv2
import numpy as np
import statistics

#Update varaible based on machine configuration
#y = db.settings["video_device"] 
#w = db.settings["comparison_images"]
#qc = db.settings["qc_images"]


def take_picture():
    #take a picture with camera
    #Return the data

    cap = cv2.VideoCapture(db.settings["video_device"]) # video capture source camera (webcam choice in interface) 
    _,picture_data = cap.read() # return a single frame in variable `frame`
    
    return picture_data


def split_image(image):
    # split the image into separate R,G,B arrays.
    # return the 3 outputs
    B, G, R = cv2.split(image)

    return B, G, R

def rotate_and_picture(y):  # y is the number of picture

    # Rotate the part in order to return ynumber for picture, taken every rotation
    # return an array of
    pictures_list = np.empty((0,3), int)
    angle_step = 360/y  # reference

    # if y=8: x=[0,45,90,135,180,225,270,315] - will need to return to 0/360 position
    for x in range(0, y):
        angle = 360/y*x
        g.send([angle], True) # where % is the angle in degrees you want the part to go to
        picture = take_picture(picture)
        B, G, R = cv2.split(picture)

        # record data in array with each R,G,B values associated to rotation (3 column: R,G,B) 0,1,2
        pictures_list = np.append(pictures_list, np.array([[R,G,B]]), axis=0)

        # index - [0,1,2,3,4,5,6,7]


    g.send([angle_step], True) # where % is the angle in degrees you want the part to go to

    return angle_step, pictures_list


def test_split(list_test):

    pictures_list = []

    for image in list_test:
        imageB = cv2.imread(image) #[b,g,r]
        
               
        pictures_list.append(imageB)
    
    return pictures_list


"""Initial Alignement"""

# light up laser
## g.toggle_lighting(True)  # Turns lights on


#g.change_batch(0) # Move component 0 under print head
#g.change_batch(0, True) # Move component 0 under scanner
#g.change_batch(1) # Move component 1 under print head
#g.change_batch(1, True) # Move component 1 under scanner


# here parts is being moved linearly to FOV of sensing position
# engineer manaually align the part to desired starting position in reference to laser.

# Record the y number of images of reference and store image data
"""angle_step_y, ref_image = rotate_and_picture(y)  # y to be chosen"""


"""Alignement of batch"""

# import dummy pictures for testing code
y = 4  # Reference
ref_images_upload = ["vision/img1.jpg", "vision/img4.jpg", "vision/img7.jpg", "vision/img10.jpg"]
angle_step_y = 360/y

ref_images = test_split(ref_images_upload)

# test5
w = 14  # Comparison
com_images_upload = ["vision/img1.jpg", "vision/img2.jpg", "vision/img3.jpg", "vision/img4.jpg", "vision/img5.jpg", "vision/img6.jpg", "vision/img7.jpg", "vision/img8.jpg", "vision/img9.jpg", "vision/img10.jpg", "vision/img11.jpg", "vision/img12.jpg", "vision/img13.jpg", "vision/img14.jpg"]
angle_step_w = 360/w


com_images = test_split(com_images_upload)


# next part is moved linearly to sensing position

# record w number of inspection image to be compared with reference images

# w to be chosen for accuracy
"""angle_step_w, com_images = rotate_and_picture(w)"""

# initialise the lists
scores_per_sets = [] #
temp_score = []
score_set = []

# Step size for W wrt Y
ideal_step = w / y

# Increment start comparison image
for start in range(w):

    # Determine y number of comparison images to test against the reference images
    # round j to nearest integer
    for j, i  in zip(np.arange(start, start + w, ideal_step,int), range(y)): 

        # If image index is greater than the number of images, 'wrap around' to the start
        if j >= w:
            j = j - w
                
        for c in range(3):
            #loop over R,G,B pixels
            (score, _) = structural_similarity(ref_images[i][:, :, c], com_images[j][:, :, c], full=True)

            temp_score.append(score)

        # average the R,G,B scores of that comparison and assign to one list 
        temp_score_avg= statistics.mean (temp_score) 
        score_set.append(temp_score_avg)
        temp_score.clear() 
    score_set_avg = statistics.mean (score_set)
    scores_per_sets.append (score_set_avg)
    score_set.clear()

       

# find the highest score of all y sets
# return the index
maxi = scores_per_sets.index(max(scores_per_sets))

print("Most similar set:" + com_images[maxi])

# the index indicate the image hence the rotation
##g.send([angle_step_w*maxi], True) # where % is the angle in degrees you want the part to go to










################################################
# Increment start test image
#for start in range(w):

    ## Determine y images to test against the reference images
    #for i in range(y):
       # j = round(ideal_step * y)

        #(scoreB, _) = structural_similarity(
      #      ref_images[i][:, :, 0], com_images[j][:, :, 0], full=True)
#
      #  temp_score.append(scoreB)
      #  score_list_B.append

        # for j in np.arange(start, start + w, ideal_step):
        # If value is greater than the number of images, 'wrap around' to the start
       # if j > w:
       #     j = j - w

        # Round to nearest integer
       # j = round(j)

       # for c in range [:,:,3]
        


       # # Loop over reference images
       # for i in range(y):

       #     score_list_B.append(scoreB)

##################################




# j = [0, 3.5, 7, 10.5]
# j = [1, 4.5, 8, 11.5]
# j = [0, 1, 2, 3, 4]

# for start in range(0, w):
#     print(range(start, start + w, ideal_step))

# # 1st loop for Blue
#     for j in range(start, start + w, ideal_step):

#         print(j)

#         for i in range(start, y):
            
#             # compute only B values - 1st column
#             #com_B = comparison_images[:,:, 0]
#             #ref_B = reference_images[:,:, 0]
#             # find the index that is the closest to the desired angle by rounding it to the nearest image - index
#             actual_index = round(ideal_step * j)
#             # compute the Stuctural Similarity Indey (SSIM) - score - every x times
#             #(scoreB, _) = structural_similarity(ref_images[i][:,:,0], com_images[::actual_index][:,:,0], full=True)
#             (scoreB, _ )= structural_similarity(ref_images[i][:,:,0], com_images[actual_index][:,:,0], full=True)

#             score_list_B.append(scoreB)
            


  #  # 2nd loop for Green
   # for j in range(start, ideal_step):
   #     for i in range(start, y):
  #          
  #          # compute only G values - 2nd column
            # find the index that is the closest to the desired angle by rounding it to the nearest image - index
  #          actual_index = round(ideal_step * j)
            # compute the Stuctural Similarity Indey (SSIM) - score - every x times
   #         (scoreG, _) = structural_similarity(ref_images[i][:,:,1], com_images[actual_index][:,:,1], full=True)

  #          score_list_G.append(scoreG)
            

    # 3rd loop for red
  #  for j in range(start, ideal_step):
   #     for i in range(start, y):
            
            # compute only R values - 3rd column
            # find the index that is the closest to the desired angle by rounding it to the nearest image - index
            #actual_index = round(ideal_step * j)
            # compute the Stuctural Similarity Indey (SSIM) - score - every x times
           # (scoreR, _) = structural_similarity(ref_images[i][:,:,2], com_images[actual_index][:,:,2], full=True)

           # score_list_R.append(scoreR)
        
   # score_list_RGB = np.column_stack((score_list_R, score_list_G, score_list_B))

# average the scores from R,G,B
#score_list_avg = np.mean (score_list_RGB, axis=1)

# find the highest score
# return the index
#maxi = score_list_avg.index(max(score_list_avg))

# print("Most similar image:" + comparison_list[i])

# the index indicate the image hence the rotation
#goto_angle(angle_step_w*maxi)

