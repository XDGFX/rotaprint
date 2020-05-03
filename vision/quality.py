
"""
Main code for the quality check process. To be integrated in main rota-print code.
Written by Hélène Verhaeghe
"""

# import the necessary packages
# importing only compare_simm function/object within the whole libary
from skimage.metrics import structural_similarity #import imutils
import cv2
import numpy as np
import statistics