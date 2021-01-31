import sys
import traceback
import os
import re
import string
import csv
import imghdr
import numpy as np
import cv2
import utility
import cv2
from matplotlib import pyplot as plt

def thresh(img, channel, threshold, inv, debug):

	"""basic thersholding technique

	b = 
	g =
	r =
	h =
	s =
	v =
	l =
	a =
	b_chnl =

	threshold out be any number from 1< x < 254 or 'otsu'

	'inv' to invert (use for white backgrounds)

	"""
	ears = img.copy()
	b,g,r = cv2.split(ears)											#Split into it channel constituents
	hsv = cv2.cvtColor(ears, cv2.COLOR_BGR2HSV)
	hsv[img == 0] = 0
	h,s,v = cv2.split(hsv)											#Split into it channel constituents
	lab = cv2.cvtColor(ears, cv2.COLOR_BGR2LAB)
	lab[img == 0] = 0
	l,a,b_chnl = cv2.split(lab)										#Split into it channel constituents
	
	if channel == 'b':
		channel = b
	elif channel == 'g':
		channel = g
	elif channel == 'r':
		channel = r
	elif channel == 'h':
		channel = h
	elif channel == 's':
		channel = s
	elif channel == 'v':
		channel = v
	elif channel == 'l':
		channel = l
	elif channel == 'a':
		channel = a
	elif channel == 'b_chnl':
		channel = b_chnl

	if debug is True:
		cv2.namedWindow('Pixels Per Metric: FOUND', cv2.WINDOW_NORMAL)
		cv2.resizeWindow('Pixels Per Metric: FOUND', 1000, 1000)
		cv2.imshow('Pixels Per Metric: FOUND', channel); cv2.waitKey(3000); cv2.destroyAllWindows()
		plt.hist(channel.ravel(),256,[0,256]); plt.show()

	if threshold == 'otsu':
		otsu,bkgrnd = cv2.threshold(channel, 0, 255, cv2.THRESH_OTSU)
		print("otsu found {} threshold".format(otsu))
	else:
		bkgrnd = cv2.threshold(channel, int(threshold),256, cv2.THRESH_BINARY)[1]


	if inv == "inv":
		bkgrnd=cv2.bitwise_not(bkgrnd)

	if debug is True:
		cv2.namedWindow('Pixels Per Metric: FOUND', cv2.WINDOW_NORMAL)
		cv2.resizeWindow('Pixels Per Metric: FOUND', 1000, 1000)
		cv2.imshow('Pixels Per Metric: FOUND', bkgrnd); cv2.waitKey(3000); cv2.destroyAllWindows()

	return bkgrnd

