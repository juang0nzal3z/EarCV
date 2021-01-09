"""
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
##################################  Cob segmentation module  #############################
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

This script is a set of tools used in 'main.py' to segment the cob and shank.
This script requires that `OpenCV 2', 'numpy', and 'scipy' be installed within the Python environment you are running this script in.
This script imports the 'utility.py', module within the same folder.

"""

import numpy as np
import cv2
import argparse
import os
import utility
import sys
from statistics import stdev, mean
from scipy.spatial import distance as dist
#import args_log


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
##########################################TIP#############################################
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#	
def top_seg(ear, PixelsPerMetric, chnnl, mskd, tip_percent, contrast, threshold, close, extent):
	ymax = ear.shape[0]
	s_p = ear.copy()
	_,_,r = cv2.split(ear)											#Split into it channel constituents
	_,bw = cv2.threshold(r, 0, 255, cv2.THRESH_OTSU)
	
	chnnl = utility.apply_brightness_contrast(chnnl, brightness = 0, contrast = contrast)	#Split into it channel constituents
	
	if threshold is None and close is None:
		
		chnnl=cv2.bitwise_not(chnnl)
		vectorized = chnnl.reshape((-1,3))
		vectorized = np.float32(vectorized)
		criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
		K = 2
		attempts = 5
		ret,label,center=cv2.kmeans(vectorized,K,None,criteria,attempts,cv2.KMEANS_PP_CENTERS)
		center = np.uint8(center)
		res = center[label.flatten()]
		chnnl = res.reshape((chnnl.shape))
		
		chnnl = cv2.cvtColor(chnnl,cv2.COLOR_RGB2GRAY)
		_,chnnl = cv2.threshold(chnnl, 0, 255, cv2.THRESH_OTSU)


	else:	
		chnnl = cv2.cvtColor(chnnl,cv2.COLOR_RGB2GRAY)
		chnnl = cv2.threshold(chnnl, int(mskd*threshold),256, cv2.THRESH_BINARY_INV)[1]
		chnnl[int((ymax*(int(tip_percent)/100))):ymax, :] = 0 #FOR THE TIP
	
	bw[chnnl == 0] = 0		

	if close is not None:
		bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (int(close),int(close))), iterations=int(close))

	nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(bw, connectivity=4)

	tip = np.zeros(chnnl.shape, np.uint8)	

	for i in range (1, extent):
		tip[output == i] = 255

	return tip

def bottom_seg(ear, PixelsPerMetric, chnnl, mskd, bottom_percent, contrast, threshold, close, extent):
	ymax = ear.shape[0]
	s_p = ear.copy()
	_,_,r = cv2.split(ear)											#Split into it channel constituents
	_,bw = cv2.threshold(r, 0, 255, cv2.THRESH_OTSU)
	
	chnnl = utility.apply_brightness_contrast(chnnl, brightness = 0, contrast = contrast)	#Split into it channel constituents
	
	if threshold is None and close is None:
		
		chnnl=cv2.bitwise_not(chnnl)
		vectorized = chnnl.reshape((-1,3))
		vectorized = np.float32(vectorized)
		criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
		K = 2
		attempts = 5
		ret,label,center=cv2.kmeans(vectorized,K,None,criteria,attempts,cv2.KMEANS_PP_CENTERS)
		center = np.uint8(center)
		res = center[label.flatten()]
		chnnl = res.reshape((chnnl.shape))
		
		chnnl = cv2.cvtColor(chnnl,cv2.COLOR_RGB2GRAY)
		_,chnnl = cv2.threshold(chnnl, 0, 255, cv2.THRESH_OTSU)


	else:	
		chnnl = cv2.cvtColor(chnnl,cv2.COLOR_RGB2GRAY)
		chnnl = cv2.threshold(chnnl, int(mskd*threshold),256, cv2.THRESH_BINARY_INV)[1]
	

	chnnl[0:int((ymax*(int(bottom_percent)/100))), :] = 0 #FOR THE bottom
	
	bw[chnnl == 0] = 0		
	if close is not None:
		bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (int(close),int(close))), iterations=int(close))
	

	nb_components, output, stats, centroids = cv2.connectedComponentsWithStats(bw, connectivity=4)

	#print(nb_components, output, stats, centroids)

	bottom = np.zeros(chnnl.shape, np.uint8)			

	# extracts sizes vector for each connected component
	sizes = stats[:, -1]
	if len(sizes) > 1:
		for i in range(2, nb_components):
			if sizes[i] > ((r.shape[0]*r.shape[1])*0.001):
				bottom[output == i] = 255
	bottom[output == len(centroids)] = 255
	bottom[output == int(len(centroids)-1)] = 255

	#for i in range (1, extent):
	#	bottom[output == i] = 255

	return bottom
