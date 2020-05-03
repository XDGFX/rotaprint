

"""
Main code for the alignement process. To be integrated in main rota-print code.
Written by Hélène Verhaeghe

INPUTS: 
r = db.settings["reference_images"] #number of reference images specified (default:4)
c = db.settings["comparison_images"] #number of comparison images specified (default:20)
qc = db.settings["qc_images"]  #number of comparison images for quality check specified (default:8)
camera_port = db.settings["video_device"] #device index  to specify which camera to use

OUTPUTS:
maxi = offset angle value

TERMS USED:
"score" is refering to the Similarity score obtained after computing OpenCV "structural_similarity" function.
"angle_step" ----
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



def take_picture(): 
    #Open webcam wanted
    #Take a picture 
    #Return the picture data
   
     
    log.debug("Activating the desired camera..." ) 

    cap = cv2.VideoCapture(db.settings["video_device"]) #activate the webcam of choice (0 usually is the default camera)
    
    #Check if camera opened successfully
    if (cap.isOpened()== False):
        log.error("Error opening video stream or file,")
     
    log.info("Camera successfully activated,")

    _ , picture_data = cap.read() # return a single frame in variable `picture_data` 
    #ret is a boolean variable that returns true if the frame is available.
    #picture_data is an image array vector captured based on the default frames per second defined explicitly or implicitly
       



    return picture_data 

def rotate_and_picture(n):
    # Rotate the part at desired angle steps
    # Take a picture at each rotation
    # return pictures data in a list 
    log.warning("Taking more than 360 pictures may slow down the image processing.")
    log.info(f"Rotating and taking a picture at each rotation until {n} pictures taken.")
    
    if n == 0:
        #if the desired number of pictures was set as zero, alert the user.
        log.error("The number of pictures specified must be above zero!")
        return

    #pictures_list = np.empty((0,3), int)
    pictures_list = []
    angle_step = 360 / n

    for x in range(n):
        angle = angle_step * x
        g.send([angle], True) # where  angle is  in degrees you want the part to go to
        picture_data = take_picture() 

        # record data in a list
        pictures_list.append(picture_data) 

    #go back to initial position
    g.send([angle_step], True) # where % is the angle in degrees you want the part to go to

    log.info("The {n} number of picture were sucessfully taken ")
    return angle_step, pictures_list


# def test_split(list_test):

#     pictures_list = []

#     for image in list_test:
#         imageB = cv2.imread(image) #[b,g,r]    
#         pictures_list.append(imageB)

#     return pictures_list


"""Initial Alignement"""

# light up laser
g.toggle_lighting(True)  # Turns lights on

# here parts is being moved linearly to FOV of sensing position
g.change_batch(0, True) # Move component 0 under scanner

# engineer manually align the part to desired starting position in reference to laser, using controls in interface.

# Record the "r" number of images of reference and store image data
angle_step_r, ref_image = rotate_and_picture(r)


"""Alignement of batch"""
#take c number of comparison images
#these should be compared against the reference images as set of "r"
#################################Explain here a bit better######################################

# next part of batch is moved linearly to sensing position
g.change_batch(1, True) # Move component 0 under scanner


# record "c" number of comparison images (to be compared against reference image as set of "r")
angle_step_c, com_images = rotate_and_picture(c)

#Initialisation of lists
temp_score = [] #temporary list to use within loop to collect SSIM scores of a comparison for each colour 
score_set = [] # list the scores of each comparison within a set
scores_per_sets = [] # Main list: list of the averages scores of each set 

#compute the ideal step size to compare 
ideal_step = c / r


for start in range(c):
    # Increment start comparison image
    
    for j, i  in zip(np.arange(start, start + c, ideal_step,int), range(r)): 
    # Compare the comparison image against its supposedly correct the reference images (in terms of angle)
    # Check the score of similarity between those two images
    # round j to nearest integer

        # If image index is greater than the number of images, 'wrap around' to the start - keeping the given angle step
        if j >= c:
            j = j - c
                
        for colour in range(3):
            #loop over B,G,R pixels - in that order
            (score, _) = structural_similarity(ref_images[i][:, :, colour], com_images[j][:, :, colour], full=True)

            temp_score.append(score)

        
        temp_score_avg= statistics.mean (temp_score)  #average the three colours scores for the given comparison
        score_set.append(temp_score_avg) #store that averaged score in score_set list
        temp_score.clear() #clear list for next comparison 

       
    score_set_avg = statistics.mean (score_set) #after a set, average all scores of set
    scores_per_sets.append (score_set_avg) #store that average set score in the main list
    score_set.clear() #clear list for next set

       

# find the highest score of all "c" sets
# return the index
maxi = scores_per_sets.index(max(scores_per_sets))


# the index indicates the offset angle to align part to desired priting position
g.send([angle_step_w*maxi], True) # where % is the angle in degrees you want the part to go to






   
