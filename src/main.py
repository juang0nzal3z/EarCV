# -*- coding: utf-8 -*-
"""--------------------------------------------------------------------------------------------------

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
###################### Computer Vision for Maize Ear Analysis  ###########################
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
###################### By: Juan M. Gonzalez, University of Florida  ######################
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This tool allows the user to rapidly extract features from images containing maize ears against a uniform background.
This tool requires that `OpenCV 2', 'numpy', 'scipy', 'pyzbar'(optional), and 'plantcv(optinal)' be installed within the Python
environment you are running this script in.

This file imports modules within the same folder:

	* args_log.py - Cpntains the arguments and log settings for the main script.
    * qr.py - Scans image for QR code and returns found information.
    * ColorCorrection.py - Performs color correction on images using a color checker.
    * ppm.py - Calculates the pixels per metric using a solid color square in the input image of known dimensions.
    * find_ears.py - Segments ears in the input image.
    * features.py - Measures basic ear morphological features and kernel features.
    * cob_chank_segmentation.py - Segments kernel from cob and shank.
	* utilities.py - Helper functions needed thorughout the analysis.

--------------------------------------------------------------------------------------------------"""

import sys
import traceback
import os
import re
import string
import csv
import imghdr
import numpy as np
import cv2
from statistics import stdev, mean
from scipy.spatial import distance as dist
from plantcv import plantcv as pcv

import utility
import args_log
import qr
import colorcorrection
import ppm
import find_ears
import features
import cob_shank_segmentation


#import entropy

#from earcv import __version__

__author__ = "Juan M. Gonzalez"
__copyright__ = "Juan M. Gonzalez"
__license__ = "mit"

def main():

	"""Full pipeline for automated maize ear phenotyping.

    This tool allows the user to rapidly extract ear features from images containing maize ears against a uniform background.

    Parameters
    ----------
    **kwargs : iterable
        [-h] -i IMAGE [-o OUTDIR] [-ns] [-np] [-D] [-qr] [-r]
        [-qr_scan [Window size of x pixels by x pixels]
        [Amount of overlap 0 < x < 1]] [-clr COLOR_CHECKER]
        [-ppm [Refference length]]
        [-filter [Min area as % of total image area]
        [Max Area as % of total image area] [Max Aspect Ratio]
        [Max Solidity]] [-clnup [Max area COV] [Max iterations]]
        [-slk [Min delta convexity change] [Max iterations]]
        [-t [Tip percent] [Contrast] [Threshold] [Close]]
        [-b [Bottom percent] [Contrast] [Threshold] [Close]]
       
        Required:

        -i, --image         Path to input image file, required. Accepted formats: 'tiff', 'jpeg', 'bmp', 'png'
        
        Optional:

        -o, --OUTDIR        Provide directory to saves proofs, logfile, and output CSVs. Default: Will save in current directory if not provided.
        -ns, --no_save      Default saves proofs and output CSVs. Raise flag to stop saving.
        -np, --no_proof     Default prints proofs on screen. Raise flag to stop printing proofs.
        -D, --debug         Raise flag to print intermediate images throughout analysis. Useful for troubleshooting.
        
        -qr, --qrcode                          Raise flag to scan entire image for QR code.
        -r, --rename                           Default renames images with found QRcode. Raise flag to stop renaming images with found QR code.
        -qr_scan, --qr_window_size_overlap     Advanced QR code scanning by breaking the image into subsections. [Window size of x pixels by x pixels] [Amount of overlap (0 < x < 1)] Provide the pixel size of square window to scan through image for QR code and the amount of overlap between sections (0 < x < 1).
        -clr, --color_checker COLOR_CHECKER    Path to input image file with refference color checker.
        -ppm, --pixelspermetric                [Refference length] Calculate pixels per metric using either a color checker or the largest uniform color square. Provide refference length.
        

        -filter, --ear_filter       [Min area as % of total image area] [Max Area as % of total image area] [Max Aspect Ratio] [Max Solidity] Ear segmentation filter, filters each segmented object based on area, aspect ratio, and solidity. Default: Min Area--1 percent, Max Area--x percent, Max Aspect Ratio: x < 0.6, Max Solidity: 0.98. Flag with three arguments to customize ear filter.
        -clnup, --ear_cleanup       [Max area COV] [Max iterations] Ear clean-up module. Default: Max Area Coefficient of Variation threshold: 0.2, Max number of iterations: 10. Flag with two arguments to customize clean up module.
        -slk, --silk_cleanup        [Min delta convexity change] [Max iterations] Silk decontamination module. Default: Min change in covexity: 0.04, Max number of iterations: 10. Flag with two arguments to customize silk clean up module.
        

        -t, --tip [Tip percent] [Contrast] [Threshold] [Close] Tip segmentation module. Tip percent, Contrast, Threshold, Close. Flag with four arguments to customize tip segmentation module. Use module defaults by providing '0' for all arguments.
        -b, --bottom [Bottom percent] [Contrast] [Threshold] [Close] Bottom segmentation module. Bottom percent, Contrast, Threshold, Close. Flag with four arguments to customize tip segmentation module. Use module defaults module by providing '0' for all arguments.
    
    Returns
    -------
    qrcode.csv
        .csv file with the file name and the corresponding information found in QR code.
    color_check.csv
        .csv file with color correction preformance metrics based on root mean squared differences in color.
    features.csv
        .csv file with the ear features as columns and ears as rows.
    proof
        proooooooooofs

   
    Other Parameters
    ----------------
    **kwargs : iterable
        -h, --help          Show help message and exit

    Raises
    ------
    Exception
        Invalid file type. Only accepts: 'tiff', 'jpeg', 'bmp', 'png'.

    Notes
    -----
    Notes about the implementation algorithm (if needed).

    References
    ----------
    .. [1] O. McNoleg, "The integration of GIS, remote sensing,
       expert systems and adaptive co-kriging for environmental habitat
       modelling of the Highland Haggis using object-oriented, fuzzy-logic
       and neural-network techniques," Computers & Geosciences, vol. 22,
       pp. 585-588, 1996.

    Examples
    --------

    python etc...

    """


	args = args_log.options()											# Get options
	log = args_log.get_logger("logger")									# Create logger
	log.info(args)														# Print expanded arguments
	
	if args.outdir is not None:											# If out dir is provided, else use current dir
		out = args.outdir
	else:
		out = "./"
	
	fullpath, root, filename, ext = utility.img_parse(args.image)		# Parse provided path
	
	if imghdr.what(fullpath) is None:									# Is the image path valid?
		log.warning("[ERROR]--{}--Invalid image file provided".format(fullpath)) # Log
		raise Exception										

	log.info("[START]--{}--Starting analysis pipeline...".format(filename)) # Log
	img=cv2.imread(fullpath)											# Read img in
	img_h = img.shape[0]
	img_w = img.shape[1] 
	if img.shape[0] > img.shape[1]:										# Rotate the image in case it is saved vertically  
		img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
		img_h = img.shape[0]
		img_w = img.shape[1]

	log.info("[START]--{}--Image is {} by {} pixels".format(filename, img.shape[0], img.shape[1])) # Log
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	##################################  QR code module  ######################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

	if args.qrcode is True or args.qr_window_size_overlap is not None:	# Turn module on
		QRcodeType = QRcodeData = QRcodeRect = qr_window_size = overlap = qr_proof = None 	# Empty variables
		log.info("[QR]--{}--Starting QR code extraction module...".format(filename))		# Log

		if args.qr_window_size_overlap is not None:								# Turn flag on to break image into subsections and flag each sub section and read in each variable
			qr_window_size =  args.qr_window_size_overlap[0]
			overlap = args.qr_window_size_overlap[1]
			log.info("[QR]--{}--Dividing image into windows of {} by {} pixels with overlap {}".format(filename, qr_window_size, qr_window_size, overlap))
			
		QRcodeType, QRcodeData, QRcodeRect, qr_count, qr_proof = qr.qr_scan(img, qr_window_size, overlap, args.debug)	# Run the qr.py module

		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~QRCODE output~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~		
		if QRcodeData is None:										
			log.warning("[QR]--{}--Error: QR code not found".format(filename))	# Print error if no QRcode found
		else:
			log.info("[QR]--{}--Found {}: {} on the {}th iteration".format(filename, QRcodeType, QRcodeData, qr_count))	# Log
			cv2.putText(qr_proof, "Found: {}".format(QRcodeData), (int(qr_proof.shape[0]/10), int(qr_proof.shape[1]/2)), cv2.FONT_HERSHEY_SIMPLEX,7, (222, 201, 59), 12)	# Print Text into proof
			(x, y, w, h) = QRcodeRect											# Pull coordinates for barcode location
			cv2.rectangle(qr_proof, (x, y), (x + w, y + h), (0, 0, 255), 20)	#Draw a box around the found QR code
			
			if args.qr_window_size_overlap is None:
				cv2.rectangle(img, (x-40, y-40), (x + w + 320, y + h + 40), (0, 0, 0), -1)		# Remove qr code from image if you used the entire image

			if args.debug is True:											# Print proof with QR code
				cv2.namedWindow('[QR][PROOF] Found QRcode', cv2.WINDOW_NORMAL)
				cv2.resizeWindow('[QR][PROOF] Found QRcode', 1000, 1000)
				cv2.imshow('[QR][PROOF] Found QRcode', qr_proof); cv2.waitKey(3000); cv2.destroyAllWindows()
				
			if args.rename is True:												# Rename image with QR code
				os.rename(args.image, root + QRcodeData + ext)
				filename = QRcodeData
				log.info("[QR]--{}--Renamed with QRCODE info: {}".format(filename, filename, QRcodeData))

			if args.no_save is False:								
				csvname = out + 'QRcodes' +'.csv'								# Create CSV and store barcode info
				file_exists = os.path.isfile(csvname)
				with open (csvname, 'a') as csvfile:
					headers = ['Filename', 'QR Code']
					writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)
					if not file_exists:
						writer.writeheader()
					writer.writerow({'Filename': filename, 'QR Code': QRcodeData})
				log.info("[QR]--{}--Saved filename and QRcode info to: {}QRcodes.csv".format(filename, out))
			
	else:
		log.info("[QR]--{}--QR module turned off".format(filename))
		qr_proof = mask = np.zeros_like(img)
		cv2.putText(qr_proof, "QR module off", (int(500), int(500)), cv2.FONT_HERSHEY_SIMPLEX, 7, (0, 0, 255), 15)	

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	##############################  Color correction module  #################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	if args.color_checker is not None:
		reff_fullpath, reff_root, reff_filename, reff_ext = utility.img_parse(args.color_checker[0])		# Parse provided path for refference color checker image

		if imghdr.what(reff_fullpath) is None:
			log.warning("[ERROR]--{}--Invalid refference image file provided".format(reff_fullpath)) 		# RUN A TEST HERE IF IMAGE IS REAL
			raise Exception										

		log.info("[COLOR]--{}--Starting color correction module...".format(filename)) # Log
		reff=cv2.imread(reff_fullpath)	
		
		color_proof, tar_chk, corrected, avg_tar_error, avg_trans_error, csv_field = colorcorrection.color_correct(filename, img, reff, args.debug)	#Run the color correction module
		
		log.info("[COLOR]--{}--Before correction - {} After correction - {}".format(filename, avg_tar_error, avg_trans_error)) # Log

		img[tar_chk != 0] = 0															# Mask out found color checker

		csvname = out + 'color_correction' +'.csv'										# Save results into csv
		file_exists = os.path.isfile(csvname)
		with open (csvname, 'a') as csvfile:
			headers = ['Filename', 'Overall improvement', 'Square1', 'Square1', 'Square3', 'Square4', 'Square5', 'Square6',
               'Square7', 'Square8', 'Square9', 'Square10', 'Square11', 'Square12', 'Square13',
               'Square14', 'Square15', 'Square16', 'Square17', 'Square18', 'Square19', 'Square20',
               'Square21', 'Square22', 'Square23', 'Square24']
			writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)
			if not file_exists:
				writer.writeheader()  													# file doesn't exist yet, write a header	

			writer.writerow({headers[i]: csv_field[i] for i in range(26)})
	
		log.info("[COLOR]--{}--Saved features to: {}color_correction.csv".format(filename, out)) # Log


		if args.debug is True:
			cv2.namedWindow('Pixels Per Metric: FOUND', cv2.WINDOW_NORMAL)
			cv2.resizeWindow('Pixels Per Metric: FOUND', 1000, 1000)
			cv2.imshow('Pixels Per Metric: FOUND', img); cv2.waitKey(3000); cv2.destroyAllWindows()

	else:
		log.info("[COLOR]--{}--Color correction module turned off".format(filename))
		color_proof = mask = np.zeros_like(img)
		color_proof = mask = np.zeros_like(img)
		cv2.putText(color_proof, "Color correction module off", (int(500), int(500)), cv2.FONT_HERSHEY_SIMPLEX, 7, (0, 0, 255), 15)	
		 

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	##############################  PIXELS PER METRIC MODULE  ################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	if args.pixelspermetric is not None:
		PixelsPerMetric = None
		log.info("[PPM]--{}--Calculating pixels per metric...".format(filename))
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~PPM module Output
		if args.color_checker is not None:
			log.info("[PPM]--{}--Using color checker to calculate pixels per metric...".format(filename))
			PixelsPerMetric, ppm_proof = ppm.ppm_square(tar_chk, args.pixelspermetric[0])	#Run the pixels per metric module using color checker
		else:
			log.info("[PPM]--{}--Looking for solid color square to calculate pixels per metric...".format(filename))
			PixelsPerMetric, ppm_proof = ppm.ppm_square(img, args.pixelspermetric[0])	#Run the pixels per metric module without color checker
		if PixelsPerMetric is not None:
			log.info("[PPM]--{}--Found {} pixels per metric".format(filename, PixelsPerMetric))	
			
			if args.debug is True:
				cv2.namedWindow('Pixels Per Metric: FOUND', cv2.WINDOW_NORMAL)
				cv2.resizeWindow('Pixels Per Metric: FOUND', 1000, 1000)
				cv2.imshow('Pixels Per Metric: FOUND', ppm_proof); cv2.waitKey(3000); cv2.destroyAllWindows()

		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ pixels per metric csv			
			if args.no_save is False:		
				csvname = out + 'pixelspermetric' +'.csv'
				file_exists = os.path.isfile(csvname)
				with open (csvname, 'a') as csvfile:
					headers = ['Filename', 'Pixels Per Metric']
					writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)
					if not file_exists:
						writer.writeheader()  # file doesn't exist yet, write a header	
					writer.writerow({'Filename': filename, 'Pixels Per Metric': PixelsPerMetric})
				log.info("[PPM]--{}--Saved pixels per metric to: {}pixelspermetric.csv".format(filename, out))			
		else:
			log.warning("[PPM]--{}--No size refference found for pixel per metric calculation".format(filename))
			PixelsPerMetric = None

	else:
		log.info("[PPM]--{}--Pixels per Metric module turned off".format(filename))
		PixelsPerMetric = None
		ppm_proof = np.zeros_like(img)
		cv2.putText(ppm_proof, "PPM module off", (int(500), int(500)), cv2.FONT_HERSHEY_SIMPLEX, 7, (0, 0, 255), 15)	
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	##################################  Find ears module  ####################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	log.info("[EARS]--{}--Looking for ears...".format(filename))
	ears_proof = img.copy()
	bkgrnd = find_ears.kmeans(img)									# Use kmeans to segment everything from the background
	img_area = img_w*img_h
	
	if args.debug is True:
		cv2.namedWindow('Pixels Per Metric: FOUND', cv2.WINDOW_NORMAL)
		cv2.resizeWindow('Pixels Per Metric: FOUND', 1000, 1000)
		cv2.imshow('Pixels Per Metric: FOUND', bkgrnd); cv2.waitKey(3000); cv2.destroyAllWindows()

	if args.ear_filter is not None:
		log.info("[EARS]--{}--Segmenting ears with custom settings: Min Area: {}%, Max Area: {}%, 0.19 < Aspect Ratio < {}, Solidity < {}".format(filename, args.ear_filter[0], args.ear_filter[1], args.ear_filter[2], args.ear_filter[3]))
		min_area = img_area*((args.ear_filter[0])/100)
		max_area = img_area*((args.ear_filter[1])/100)
		aspect_ratio = args.ear_filter[2]
		solidity = args.ear_filter[3]
	else:
		min_area = img_area*0.010
		max_area = img_area*0.100
		aspect_ratio = 0.6
		solidity = 0.983
		log.info("[EARS]--{}--Segmenting ears with default settings: Min Area: 1%, Max Area: 10%, 0.19 < Aspect Ratio < {}, Solidity < {}".format(filename, aspect_ratio, solidity))
	
	filtered, ear_number = find_ears.filter(filename, bkgrnd, min_area, max_area, aspect_ratio, solidity)		# Run the filter module
	log.info("[EARS]--{}--Found {} Ear(s) before clean up".format(filename, ear_number))

	cov = None
	cov = find_ears.calculate_area_cov(filtered, cov)																#Calculate area coeficient of variance
	log.info("[CLNUP]--{}--Area Coefficent of Variance: {}".format(filename, cov))


	if cov is None:
		log.info("[CLNUP]--{}--Cannot calculate Coefficent of Variance on single ear".format(filename))
	
	elif cov > 0.35:
		log.warning("[CLNUP]--{}--COV above 0.35 has triggered default ear clean-up module".format(filename))
		max_cov = 0.35
		max_iterations = 10
		i = 1
		while cov > max_cov  and i <= max_iterations:
			log.info("[CLNUP]--{}--Ear clean-up module: Iterate up to {} times or until area COV < {}. Current COV: {} and iteration {}".format(filename, max_iterations, max_cov, round(cov, 3), i))
			mask = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (i,i)), iterations=i)
			filtered, ear_number = find_ears.filter(filename, mask, min_area, max_area, aspect_ratio, solidity)		# Run the filter module
			cov = find_ears.calculate_area_cov(filtered)																# Calculate area coeficient of variance			
			i = i+1
		log.info("[CLNUP]--{}--Ear clean-up module finished. Final Area COV--{}".format(filename, cov))

	elif args.ear_cleanup is not None:
		log.info("[CLNUP]--{}--Ear clean-up module with custom settings".format(filename))
		max_cov = args.ear_cleanup[0]	
		max_iterations = args.ear_cleanup[1]
		i = 1
		while cov > max_cov  and i <= max_iterations:
			log.info("[CLNUP]--{}--Ear clean-up module: Iterate up to {} times or until area COV < {}. Current COV: {} and iteration {}".format(filename, max_iterations, max_cov, round(cov, 3), i))
			mask = cv2.morphologyEx(filtered, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (i,i)), iterations=i)
			filtered, ear_number = find_ears.filter(filename, mask, min_area, max_area, aspect_ratio, solidity)		# Run the filter module
			cov = find_ears.calculate_area_cov(filtered)																# Calculate area coeficient of variance			
			i = i+1
		log.info("[CLNUP]--{}--Ear clean-up module finished. Final Area COV--{}".format(filename, cov))
	else:
		log.info("[CLNUP]--{}--Area COV under threshold. Ear clean-up module turned off.".format(filename))

	ears = img.copy()
	ears[filtered == 0] = 0

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	###################################  Sort ears module ####################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	cnts = cv2.findContours(filtered, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cnts = cnts[0] if len(cnts) == 2 else cnts[1]
	boundingBoxes = [cv2.boundingRect(c) for c in cnts]
#Sort left to right
	(cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes), key=lambda b:b[1][0], reverse= False))
#Count the number of ears and number them on proof
	number_of_ears = 0
	ear_masks = []
	for c in cnts:
		number_of_ears = number_of_ears+1
#Find centroid
		M = cv2.moments(c)
		cX = int(M["m10"] / M["m00"])
		cY = int(M["m01"] / M["m00"])
#Create ROI and find tip
		rects = cv2.minAreaRect(c)
		width_i = int(rects[1][0])
		height_i = int(rects[1][1])
		boxs = cv2.boxPoints(rects)
		boxs = np.array(boxs, dtype="int")
		src_pts_i = boxs.astype("float32")
		dst_pts_i = np.array([[0, height_i-1],[0, 0],[width_i-1, 0],[width_i-1, height_i-1]], dtype="float32")
		M_i = cv2.getPerspectiveTransform(src_pts_i, dst_pts_i)
		ear = cv2.warpPerspective(ears, M_i, (width_i, height_i))
		height_i = ear.shape[0]
		width_i = ear.shape[1]
		if height_i > width_i:
			rat = round(width_i/height_i, 2)
		else:
			rat = round(height_i/width_i, 2)
			ear = cv2.rotate(ear, cv2.ROTATE_90_COUNTERCLOCKWISE) 				#This rotates the image in case it is saved vertically

		ear = cv2.copyMakeBorder(ear, 30, 30, 30, 30, cv2.BORDER_CONSTANT)
		ear_area = cv2.contourArea(c)
		hulls = cv2.convexHull(c); hull_areas = cv2.contourArea(hulls)
		ear_solidity = float(ear_area)/hull_areas	
		ear_percent = (ear_area/img_area)*100
		log.info("[EARS]--{}--Ear #{}: Min Area: {}% Aspect Ratio: {} Solidity score: {}".format(filename, number_of_ears, round(ear_percent, 3), rat, round(ear_solidity, 3)))
		#Draw the countour number on the image
		ear_masks.append(ear)
		cv2.drawContours(ears_proof, [c], -1, (134,22,245), -1)
		cv2.putText(ears_proof, "#{}".format(number_of_ears), (cX - 80, cY), cv2.FONT_HERSHEY_SIMPLEX,4.0, (255, 255, 0), 10)


	cv2.putText(ears_proof, "Found {} Ear(s)".format(number_of_ears), (int((img.shape[0]/1.5)), img.shape[0]-100), cv2.FONT_HERSHEY_SIMPLEX, 5.0, (200, 255, 255), 17)
	
	if args.debug is True:
		cv2.namedWindow('[EARS][DEBUG] Segmentation after Filter', cv2.WINDOW_NORMAL)
		cv2.resizeWindow('[EARS][DEBUG] Segmentation after Filter', 1000, 1000)
		cv2.imshow('[EARS][DEBUG] Segmentation after Filter', ears_proof); cv2.waitKey(2000); cv2.destroyAllWindows()


	log.info("[EARS]--{}--Found {} Ear(s) after clean up".format(filename, number_of_ears))

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	##################################  Create Found_ears_proof  #############################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	axis = ears_proof.shape[1]
	axis = int(axis/3)
	tall_ratio = ears_proof.shape[1]/ears_proof.shape[1]
	
	img_list = []
	img_list.append(qr_proof)
	img_list.append(color_proof)
	img_list.append(ppm_proof)
	
	montages = utility.build_montages(img_list, (axis, int(axis*tall_ratio)), (3, 1))
	dim = (ears_proof.shape[1], int(axis*tall_ratio))
	montages[0] = cv2.resize(montages[0], dim, interpolation = cv2.INTER_AREA)

	ears_proof = cv2.vconcat([montages[0], ears_proof])

	if args.no_proof is False or arg.debug is True:											# Print proof with QR code
		cv2.namedWindow('[PROOF]', cv2.WINDOW_NORMAL)
		cv2.resizeWindow('[PROOF]', 1000, 1000)
		cv2.imshow('[PROOF]', ears_proof); cv2.waitKey(3000); cv2.destroyAllWindows()

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Save proofs
	if args.no_save is False:		
		destin = "{}".format(out) + "01_Proofs/"
		if not os.path.exists(destin):
			try:
				os.mkdir(destin)
			except OSError as e:
				if e.errno != errno.EEXIST:
					raise
		destin = "{}".format(out) + "01_Proofs/" + filename + "_proof.png"
		log.info("[EARS]--{}--Proof saved to: {}".format(filename, destin))
		cv2.imwrite(destin, ears_proof)

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	##################################  Clean silks module  ##################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

	log.info("[SILK]--{}--Cleaning up silks...".format(filename))
	final_ear_masks = []
	n = 1 #Counter
	for r in range(number_of_ears):
		ear = ear_masks[r]
		
		if args.debug is True:
			cv2.namedWindow('[SILK CLEAN UP]', cv2.WINDOW_NORMAL)
			cv2.resizeWindow('[SILK CLEAN UP]', 1000, 1000)
			cv2.imshow('[SILK CLEAN UP]', ear); cv2.waitKey(2000); cv2.destroyAllWindows() 

		_,_,r = cv2.split(ear)											# Split into it channel constituents
		_,r = cv2.threshold(r, 0, 255, cv2.THRESH_OTSU)
		r = utility.cnctfill(r)
		ear[r == 0] = 0
		lab = cv2.cvtColor(ear, cv2.COLOR_BGR2LAB)
		lab[r == 0] = 0
		_,_,b_chnnl = cv2.split(lab)									# Split into it channel constituents

		convexity = find_ears.calculate_convexity(b_chnnl)
		log.info("[SILK]--{}--Ear #{}: Convexity: {}".format(filename, n, round(convexity, 3)))

		if convexity < 0.87:
			i = 1
			conv_var = 0.04
			i_var = 10	
			log.warning("[SILK]--{}--Ear #{}: Convexity under 0.87 has triggered default ear clean-up module".format(filename, n))
	
		elif args.silk_cleanup is not None:
			log.info("[SILK]--{}--Ear #{}: Convexity clean up module with custom settings")
			conv_var = args.silk_cleanup[0]	
			i_var = args.silk_cleanup[1]	
		
		if convexity < 0.87 or args.silk_cleanup is not None:
			
			delta_conv = 0.001
			log.info("[SILK]--{}--Ear #{}: Min delta convexity: {}, Max interations: {}".format(filename, n, round(conv_var, 3), i_var))
			
			while delta_conv < conv_var  and i <= i_var:
				b_chnnl = cv2.morphologyEx(b_chnnl, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (2+i,2+i)    ), iterations=1+i) #Open to get rid of the noise
				convexity2 = find_ears.calculate_convexity(b_chnnl)
				delta_conv = convexity2-convexity
				log.info("[SILK]--{}--Ear #{}: Convexity: {}, delta convexity: {}, iteration: {}".format(filename, n, round(convexity2, 3), round(delta_conv, 3), i))
				i = i + 1
	
		ear[b_chnnl == 0] = 0

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	##################################  Orient ears module  ##################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
		log.info('[EAR]--{}--Ear #{}: Checking ear orientation...'.format(filename, n))
		ori_width = find_ears.rotate_ear(ear)
		if ori_width[2] < ori_width[0]:
			log.warning('[EAR]--{}--Ear #{}: Ear rotated'.format(filename, n))
			ear = cv2.rotate(ear, cv2.ROTATE_180)	
		else:
			log.info('[EAR]--{}--Ear #{}: Ear orientation is fine.'.format(filename, n))	

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	##################################  Save final ear masks  ################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
		if args.no_save is False:
			destin = "{}".format(out) + "02_Ear_ROIs/"
			if not os.path.exists(destin):
				try:
					os.mkdir(destin)
				except OSError as e:
					if e.errno != errno.EEXIST:
						raise			
			destin = "{}02_Ear_ROIs/{}_ear_{}".format(out, filename, n) + ".png"
			log.info("[EAR]--{}--Ear #{}: ROI saved to: {}".format(filename, n, destin))			
			cv2.imwrite(destin, ear)

		if args.debug is True:
			cv2.namedWindow('[SILK CLEAN UP]', cv2.WINDOW_NORMAL)
			cv2.resizeWindow('[SILK CLEAN UP]', 1000, 1000)
			cv2.imshow('[SILK CLEAN UP]', ear); cv2.waitKey(2000); cv2.destroyAllWindows() 

		final_ear_masks.append(ear)
		n = n + 1

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	############################# BASIC FULL EAR FEATURES ####################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	log.info('[EAR]--{}--Extracting features from {} ears...'.format(filename, number_of_ears))
	n = 1 #Counter
	for r in range(number_of_ears):
		ear = final_ear_masks[r]
		log.info('[EAR]--{}--Ear #{}: Extracting basic morphological features...'.format(filename, n))
		#Ear_Area = Convexity = Solidity = Ellipse = Ear_Box_Width = Ear_Box_Length = Ear_Box_Area = Ear_Extreme_Length = Ear_Area_DP = Solidity_PolyDP = Solidity_Box = Taper_PolyDP = Taper_Box = Widths = Widths_Sdev = Cents_Sdev = Ear_area = Tip_Area = Bottom_Area = Krnl_Area = Tip_Fill = Blue = Green = Red = Hue = Sat = Vol = Light = A_chnnl = B_chnnl = second_width = mom1 = None
		Ear_Area, Ear_Box_Area, Ear_Box_Length, Ear_Box_Width, newWidths, max_Width, perimeters, Convexity, Solidity, Convexity_polyDP, Taper, Taper_Convexity, Taper_Solidity, Taper_Convexity_polyDP, Widths_Sdev, Cents_Sdev, ear_proof, canvas, wid_proof = features.extract_feats(ear, PixelsPerMetric)
		log.info('[EAR]--{}--Ear #{}: Done extracting basic morphological features'.format(filename, n))

		_,_,r = cv2.split(ear)											#Split into it channel constituents
		_,r = cv2.threshold(r, 0, 255, cv2.THRESH_OTSU)
		hsv = cv2.cvtColor(ear, cv2.COLOR_BGR2HSV)						#Convert into HSV color Space	
		hsv[r == 0] = 0
		_,s,_ = cv2.split(hsv)											#Split into it channel constituents	
		chnnl = cv2.cvtColor(s,cv2.COLOR_GRAY2RGB)
		mskd,_ = cv2.threshold(chnnl[chnnl !=  0],1,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU); 
		pixels = np.float32(chnnl[chnnl !=  0].reshape(-1, 3))
		Blue, Red, Green, Hue, Sat, Vol, Light, A_chnnl, B_chnnl = features.dominant_cols(chnnl, pixels)


		uncob = ear.copy()
		bw = r.copy()
		tip = r.copy()
		bottom = r.copy()
		cob = r.copy()
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	############################# Cob Segemntation Module ####################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
		if args.tip is not None:
			#[Tip percent]", "[Contrast]", "[Threshold]", "[Close]"
			tip_percent = args.tip[0]
			contrast = args.tip[1]
			threshold = args.tip[2]
			close = args.tip[3]
		
			if args.tip[0] == 0 and args.tip[1] == 0 and args.tip[2] == 0 and args.tip[3] == 0:
				if mskd < 80 and Blue > 140:
					log.warning("[EAR]--{}--Ear #{}: Detected white ear...segmenting ear tip with special white ear settings...".format(filename, n))
					#white ear automatic trigger
					tip = cob_shank_segmentation.top_seg(ear, PixelsPerMetric, chnnl, mskd, 50, 10, 0.95, 3, 5) 
				else:
					log.info("[EAR]--{}--Ear #{}: Segmenting ear tip with default settings...".format(filename, n))
					#k means default	
					tip = cob_shank_segmentation.top_seg(ear, PixelsPerMetric, chnnl, mskd, 50, 15, None, None, 5) 
			else:
				log.info("[EAR]--{}--Ear #{}: Segmenting eat tip with custom settings...".format(filename, n))
				tip = cob_shank_segmentation.top_seg(ear, PixelsPerMetric, chnnl, mskd, tip_percent, contrast, threshold, close, 5) 
		else:
			log.info("[EAR]--{}--Ear #{}: Ear tip segmentation turned off".format(filename, n))
	
		if args.bottom is not None:
			#[bottom percent]", "[Contrast]", "[Threshold]", "[Close]"
			bottom_percent = args.bottom[0]
			contrast = args.bottom[1]
			threshold = args.bottom[2]
			close = args.bottom[3]

			if args.bottom[0] == 0 and args.bottom[1] == 0 and args.bottom[2] == 0 and args.bottom[3] == 0:
				if mskd < 80 and Blue > 140:
					log.warning("[EAR]--{}--Ear #{}: Detected white ear...segmenting ear bottom with special white ear settings...".format(filename, n))
					#white ear automatic trigger
					bottom = cob_shank_segmentation.bottom_seg(ear, PixelsPerMetric, chnnl, mskd, 75, 5, 0.85, None, 5) 
				else:
					log.info("[EAR]--{}--Ear #{}: Segmenting ear bottom with default settings...".format(filename, n))
					#k means default	
					bottom = cob_shank_segmentation.bottom_seg(ear, PixelsPerMetric, chnnl, mskd, 75, 15, None, None, 5)					 
			else:
				log.info("[EAR]--{}--Ear #{}: Segmenting eat bottom with custom settings...".format(filename, n))
				bottom = cob_shank_segmentation.bottom_seg(ear, PixelsPerMetric, chnnl, mskd, bottom_percent, contrast, threshold, close, 5) 
		else:
			log.info("[EAR]--{}--Ear #{}: Ear bottom segmentation turned off".format(filename, n))

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	############################# Cob/shank/kernel Analysis Module ###########################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

		if cv2.countNonZero(bottom) != cv2.countNonZero(tip):
			log.info("[EAR]--{}--Ear #{}: Extracting kernel features...".format(filename, n))

			Tip_Area, Bottom_Area, Krnl_Area, Kernel_Length, Krnl_Convexity, Tip_Fill, Bottom_Fill, Krnl_Fill, krnl_proof, cob, uncob, Blue, Red, Green, Hue, Sat, Vol, Light, A_chnnl, B_chnnl = features.krnl_feats(ear, tip, bottom, PixelsPerMetric)

			log.info("[EAR]--{}--Ear #{}: Done extracting kernel features".format(filename, n))
			
			Krnl_proof = ear.copy()

			Krnl_proof[uncob == 0] = [0,0,255]
			Krnl_proof[r == 0] = [0,0,0]

		else:
			Krnl_proof = ear.copy()
			Tip_Area = Bottom_Area = Krnl_Area = Kernel_Length = Krnl_Convexity =  Tip_Fill = Bottom_Fill = Krnl_Fill = None 
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	################################## KRN Module ###########################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	################################## Grading Module ########################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	##################################### Proofs  ############################################
	#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
		canvas = cv2.cvtColor(canvas,cv2.COLOR_GRAY2RGB)
		ear_proof = cv2.hconcat([canvas, ear_proof, wid_proof, Krnl_proof])

		if args.no_save is False:
			destin = "{}".format(out) + "03_Ear_Proofs/"
			if not os.path.exists(destin):
				try:
					os.mkdir(destin)
				except OSError as e:
					if e.errno != errno.EEXIST:
						raise			
			destin = "{}03_Ear_Proofs/{}_ear_{}_proof".format(out, filename, n) + ".png"
			log.info("[EAR]--{}--Ear #{}: Ear proof saved to: {}".format(filename, n, destin))			
			cv2.imwrite(destin, ear_proof)

		if args.no_proof is False or arg.debug is True:
			cv2.namedWindow('[SILK CLEAN UP]', cv2.WINDOW_NORMAL)
			cv2.resizeWindow('[SILK CLEAN UP]', 1000, 1000)
			cv2.imshow('[SILK CLEAN UP]', ear_proof); cv2.waitKey(2000); cv2.destroyAllWindows()

		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
		##################################### Features CSV  ######################################
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
		#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Create CSV
		if args.no_save is False:			
			csvname = out + 'features' +'.csv'
			file_exists = os.path.isfile(csvname)
			with open (csvname, 'a') as csvfile:
				headers = ['Filename', 'Ear Number', 'Ear_Area', 'Ear_Box_Area', 'Ear_Box_Length', 'Ear_Box_Width', 'Max_Width', 'perimeters', 
							'Convexity', 'Solidity', 'Convexity_polyDP', 'Taper', 'Taper_Convexity', 'Taper_Solidity', 'Taper_Convexity_polyDP', 
							'Widths_Sdev', 'Cents_Sdev', 'Tip_Area', 'Bottom_Area', 'Krnl_Area', 'Kernel_Length', 'Krnl_Convexity', 'Tip_Fill', 
							'Bottom_Fill', 'Krnl_Fill', 'Blue', 'Red', 'Green', 'Hue', 'Sat', 'Vol', 'Light', 'A_chnnl', 'B_chnnl']  


				writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=headers)
				if not file_exists:
					writer.writeheader()  # file doesn't exist yet, write a header	

				writer.writerow({'Filename': filename,'Ear Number': n, 'Ear_Area': Ear_Area, 'Ear_Box_Area': Ear_Box_Area,
								 'Ear_Box_Length': Ear_Box_Length, 'Ear_Box_Width': Ear_Box_Width, 'Max_Width': max_Width, 'perimeters': perimeters,
								 'Convexity': Convexity , 'Solidity': Solidity, 'Convexity_polyDP': Convexity_polyDP, 'Taper': Taper,
								 'Taper_Convexity': Taper_Convexity, 'Taper_Solidity': Taper_Solidity, 'Taper_Convexity_polyDP': Taper_Convexity_polyDP, 
							     'Widths_Sdev': Widths_Sdev, 'Cents_Sdev': Cents_Sdev, 'Tip_Area': Tip_Area, 'Bottom_Area': Bottom_Area, 
							     'Krnl_Area': Krnl_Area, 'Kernel_Length': Kernel_Length , 'Krnl_Convexity': Krnl_Convexity, 'Tip_Fill': Tip_Fill, 
								 'Bottom_Fill': Bottom_Fill, 'Krnl_Fill': Krnl_Fill , 'Blue':Blue , 'Red':Red , 'Green':Green , 'Hue': Hue, 'Sat':Sat,
								 'Vol':Vol , 'Light':Light , 'A_chnnl':A_chnnl , 'B_chnnl':B_chnnl})

		log.info("[EAR]--{}--Ear #{}: Saved features to: {}features.csv".format(filename, n, out))
		n = n + 1
	log.info("[EAR]--{}--Collected all ear features.".format(filename))		



#def run():
#    """Entry point for console_scripts"""
#    main(sys.argv[1:])


#if __name__ == "__main__":
#    run()
main()