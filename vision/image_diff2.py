# import the necessary packages
from skimage.metrics import structural_similarity #importing only compare_simm function/object within the whole libary
#import imutils
import cv2



# load the image of reference
imageREF = cv2.imread("vision/Picture 3.1.jpg")
# convert the image to grayscale
grayREF = cv2.cvtColor(imageREF, cv2.COLOR_BGR2GRAY)

#load a list of images
imageList=["vision/Picture 3.2.jpg","vision/Picture 3.2.jpg","vision/Picture 3.3.jpg","vision/Picture 3.4.jpg","vision/Picture 3.5.jpg","vision/Picture 3.6.jpg","vision/Picture 3.7.jpg"]

#create list of the SSIM indexes 
scoreList=[]

# compute the Structural Similarity Index (SSIM) (score) between the image of reference and each of the images in "images" list
# and store each score to the scoreList - do that for each image of the list
for image in imageList:
    imageB = cv2.imread(image)
    grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    (score,_) = structural_similarity(grayREF, grayB, full=True)
    scoreList.append(score)

#print(scoreList)


i= scoreList.index(max(scoreList))

print("Most similar image:" + imageList[i])
