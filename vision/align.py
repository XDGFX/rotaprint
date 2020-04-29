

"""
Main code for the alignement process. To be integrated in main rota-print code.
Written by Hélène Verhaeghe

INPUTS: 
r = db.settings["reference_images"] #number of reference images specified (default:4)
c = db.settings["comparison_images"] #number of comparison images specified (default:20)
qc = db.settings["qc_images"]  #number of comparison images for quality check specified (default:8)
camera_port = db.settings["video_device"] #device index  to specify which camera to use

OUTPUTS:
offset angle value
"""

# import the necessary packages
from skimage.metrics import structural_similarity 
import cv2
import numpy as np
import statistics

#Update varaible based on machine configuration
r = db.settings["reference_images"] #number of reference images specified (default:4)
c = db.settings["comparison_images"] #number of comparison images specified (default:20)
qc = db.settings["qc_images"]  #number of comparison images for quality check specified (default:8)
camera_port = db.settings["video_device"] #device index  to specify which camera to use


def take_picture(camera_port):
    #Take a picture with camera
    #Return the picture data
    
    cap = cv2.VideoCapture(camera) #open the webcam of choice (0 usually is the default camera)
    
    #Check if camera opened successfully
    if (cap.isOpened()== False):
        log.error("Error opening video stream or file"))
     
    ret, picture_data = cap.read() # return a single frame in variable `picture_data` 
    #ret is a boolean variable that returns true if the frame is available.
    #picture_data is an image array vector captured based on the default frames per second defined explicitly or implicitly
       
    # Default resolutions of the frame are obtained.The default resolutions are system dependent.
    # We convert the resolutions from float to integer.
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    # When everything done, release the video capture object
    cap.release()


    return picture_data 

def rotate_and_picture(r):  # r is the number of picture

    # Rotate the part in order to return ynumber for picture, taken every rotation
    # return an array of
    pictures_list = np.empty((0,3), int)
    angle_step = 360/r  # reference

    # if y=8: x=[0,45,90,135,180,225,270,315] - will need to return to 0/360 position
    for x in range(0, r):
        angle = 360/r*x
        g.send([angle], True) # where % is the angle in degrees you want the part to go to
        picture = take_picture(picture)
        B, G, R = cv2.split(picture)

        # record data in array with each R,G,B values associated to rotation (3 column: R,G,B) 0,1,2
        pictures_list = np.append(pictures_list, np.array([[R,G,B]]), axis=0)



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
g.toggle_lighting(True)  # Turns lights on

# here parts is being moved linearly to FOV of sensing position
g.change_batch(0, True) # Move component 0 under scanner

# engineer manually align the part to desired starting position in reference to laser, using controls in interface.

# Record the y number of images of reference and store image data
"""angle_step_y, ref_image = rotate_and_picture(r)  


"""Alignement of batch"""

# import dummy pictures for testing code
r = 4  # Reference
ref_images_upload = ["vision/img1.jpg", "vision/img4.jpg", "vision/img7.jpg", "vision/img10.jpg"]
angle_step_r = 360/r

ref_images = test_split(ref_images_upload)

# test5
c = 14  # Comparison
com_images_upload = ["vision/img1.jpg", "vision/img2.jpg", "vision/img3.jpg", "vision/img4.jpg", "vision/img5.jpg", "vision/img6.jpg", "vision/img7.jpg", "vision/img8.jpg", "vision/img9.jpg", "vision/img10.jpg", "vision/img11.jpg", "vision/img12.jpg", "vision/img13.jpg", "vision/img14.jpg"]
angle_step_c = 360/c


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
ideal_step = c / r

# Increment start comparison image
for start in range(c):

    # Determine y number of comparison images to test against the reference images
    # round j to nearest integer
    for j, i  in zip(np.arange(start, start + c, ideal_step,int), range(r)): 

        # If image index is greater than the number of images, 'wrap around' to the start
        if j >= c:
            j = j - c
                
        for colour in range(3):
            #loop over R,G,B pixels
            (score, _) = structural_similarity(ref_images[i][:, :, colour], com_images[j][:, :, colour], full=True)

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






   
