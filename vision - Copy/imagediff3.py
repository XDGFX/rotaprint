# import the necessary packages
from skimage.metrics import structural_similarity #importing only compare_simm function/object within the whole libary
#import imutils
import cv2



# load the image of reference
imageREF = cv2.imread("vision/img1.jpg")
# convert the image to grayscale
grayREF = cv2.cvtColor(imageREF, cv2.COLOR_BGR2GRAY)

#load a list of images
#imageList=["vision/Picture 3.2.jpg","vision/Picture 3.2.jpg","vision/Picture 3.3.jpg","vision/Picture 3.4.jpg","vision/Picture 3.5.jpg","vision/Picture 3.6.jpg","vision/Picture 3.7.jpg"]


#test1
#imageList=["vision/imgd2.jpg","vision/imgd3.jpg","vision/imgd4.jpg","vision/imgd5.jpg","vision/imgd6.jpg","vision/imgd7.jpg","vision/imgd8.jpg","vision/imgd9.jpg","vision/imgd10.jpg","vision/imgd11.jpg","vision/imgd12.jpg","vision/imgd13.jpg","vision/imgd14.jpg"]
#test2
#imageList=["vision/imgs2.jpg","vision/imgs3.jpg","vision/imgs4.jpg","vision/imgs5.jpg","vision/imgs6.jpg","vision/imgs7.jpg","vision/imgs8.jpg","vision/imgs9.jpg","vision/imgs10.jpg","vision/imgs11.jpg","vision/imgs12.jpg","vision/imgs13.jpg","vision/imgs14.jpg"]
#test3
#imageList=["vision/imgc2.jpg","vision/imgc3.jpg","vision/imgc4.jpg","vision/imgc5.jpg","vision/imgc6.jpg","vision/imgc7.jpg","vision/imgc8.jpg","vision/imgc9.jpg","vision/imgc10.jpg","vision/imgc11.jpg","vision/imgc12.jpg","vision/imgc13.jpg","vision/imgc14.jpg"]
#test5
imageList=["vision/img2.jpg","vision/img3.jpg","vision/img4.jpg","vision/img5.jpg","vision/img6.jpg","vision/img7.jpg","vision/img8.jpg","vision/img9.jpg","vision/img10.jpg","vision/img11.jpg","vision/img12.jpg","vision/img13.jpg","vision/img14.jpg"]
#test6
#imageList=["vision/imga2.jpg","vision/imga3.jpg","vision/imga4.jpg","vision/imga5.jpg","vision/imga6.jpg","vision/imga7.jpg","vision/imga8.jpg","vision/imga9.jpg","vision/imga10.jpg","vision/imga11.jpg","vision/imga12.jpg","vision/imga1.jpg","vision/imga14.jpg"]
#test7
#imageList=["vision/imgb2.jpg","vision/imgb3.jpg","vision/imgb4.jpg","vision/imgb5.jpg","vision/imgb6.jpg","vision/imgb7.jpg","vision/imgb8.jpg","vision/imgb9.jpg","vision/imgb10.jpg","vision/imgb11.jpg","vision/imgb12.jpg","vision/imgb13.jpg","vision/imgb14.jpg"]
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
