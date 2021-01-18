import argparse
import logging
import sys
import traceback
import os
import re
import string

def options():
	parser = argparse.ArgumentParser(description="Full pipeline for automted maize ear phenotyping")

	#Required main input
	parser.add_argument("-i", "--image",  help="Path to input image file", required=True)

	#Optional main arguments
	parser.add_argument("-o", "--outdir", help="Provide directory to saves proofs, logfile, and output CSVs. Default: Will save in current directory if not provided.")
	parser.add_argument("-ns", "--no_save", default=False, action='store_true', help="Default saves proofs and output CSVs. Raise flag to stop saving.")
	parser.add_argument("-np", "--no_proof", default=False, action='store_true', help="Default prints proofs on screen. Raise flag to stop printing proofs.")
	parser.add_argument("-D", "--debug", default=False, action='store_true', help="Raise flag to print intermediate images throughout analysis. Useful for troubleshooting.")	

	#QR code options
	parser.add_argument("-qr", "--qrcode", default=False, action='store_true', help="Raise flag to scan entire image for QR code.")	
	parser.add_argument("-r", "--rename", default=True, action='store_false', help="Default renames images with found QRcode. Raise flag to stop renaming images with found QRcode.")	
	parser.add_argument("-qr_scan", "--qr_window_size_overlap", metavar=("[Window size of x pixels by x pixels]", "[Amount of overlap (0 < x < 1)]"), nargs=2, type=float, help="Provide the size of window to scan through image for QR code and the amount of overlap between sections(0 < x < 1).")

	#Color Checker options
	parser.add_argument("-clr", "--color_checker", default="None", help="Path to input image file with refference color checker. If none provided will use default values.", nargs='?', const='', required=False)
	
	#Pixels Per Metric options
	parser.add_argument("-ppm", "--pixelspermetric", metavar=("[Refference length]"), nargs=1, type=float, help="Calculate pixels per metric using either a color checker or the largest uniform color square. Provide refference length.")
	
	#Find Ears options
	parser.add_argument("-thresh", "--threshold", metavar=("[channel]", "[intensity threshold]", "[invert]"), help="Manueal ear esgmentation module. Use if K fails", nargs=3, required=False)
	parser.add_argument("-filter", "--ear_filter", metavar=("[Min area as % of total image area]", "[Max Area as % of total image area]", "[Max Aspect Ratio]", "[Max Solidity]"), nargs=4, type=float, help="Ear segmentation filter. Default: Min Area--1 percent, Max Area--x percent, Max Aspect Ratio: x < 0.6,  Max Solidity: 0.98. Flag with three arguments to customize ear filter.")
	parser.add_argument("-clnup", "--ear_cleanup", metavar=("[Max area COV]", "[Max iterations]"), help="Ear clean-up module. Default: Max Area Coefficient of Variation threshold: 0.2, Max number of iterations: 10. Flag with two arguments to customize clean up module.", nargs=2, type=float, required=False)
	parser.add_argument("-slk", "--silk_cleanup", metavar=("[Min delta convexity change]", "[Max iterations]"), nargs=2, type=float, help="Silk decontamination module. Default: Min change in covexity: 0.04, Max number of iterations: 10. Flag with two arguments to customize silk clean up module")

	#Cob and shank segmentation options
	parser.add_argument("-t", "--tip", nargs=4, metavar=("[Tip percent]", "[Contrast]", "[Threshold]", "[Close]"), type=float, help="Tip segmentation module. Tip percent, Contrast, Threshold, Close. Flag with four arguments to customize tip segmentation module. Turn of module by providing '0' for all arguments")
	parser.add_argument("-b", "--bottom", nargs=4, metavar=("[Bottom percent]", "[Contrast]", "[Threshold]", "[Close]"), type=float, help="Bottom segmentation module. Bottom percent, Contrast, Threshold, Close. Flag with four arguments to customize tip segmentation module. Turn of module by providing '0' for all arguments")

	args = parser.parse_args()
	return args

def get_logger(logger_name):
	args = options()
	
	if args.outdir is not None:
		out = args.outdir
	else:
		out = "./"

	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setFormatter(logging.Formatter("%(asctime)s — %(levelname)s — %(message)s"))
	logger = logging.getLogger(logger_name)
	logger.setLevel(logging.DEBUG) # better to have too much log than not enough
	logger.addHandler(console_handler)
	
	destin = "{}".format(out)
	if not os.path.exists(destin):
		try:
			os.mkdir(destin)
		except OSError as e:
			if e.errno != errno.EEXIST:
				raise
		LOG_FILE = ("{}EarCV.log".format(out))
	else:
		LOG_FILE = ("{}EarCV.log".format(out))
		
	file_handler = logging.FileHandler(LOG_FILE)
	
	file_handler.setFormatter(logging.Formatter("%(asctime)s — %(levelname)s — %(message)s"))
	
	logger.addHandler(file_handler)
	# with this pattern, it's rarely necessary to propagate the error up to parent
	logger.propagate = False
	return logger