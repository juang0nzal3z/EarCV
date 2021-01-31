#krn.py

import sys, traceback, os, re
import numpy as np
import pandas as pd
import math
import cv2
from scipy.spatial import distance as dist
from scipy import stats
from scipy.signal import savgol_filter
from scipy.signal import argrelextrema
from statsmodels.nonparametric.smoothers_lowess import lowess
#from matplotlib import pyplot as plt
#import plotly.graph_objects as go
#from plotly.subplots import make_subplots
import utility

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#################################DEFINE MAIN FUNCTION#####################################
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def krn(img, debug):

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#################################### Slice Horizontally ##################################
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
	ear = img.copy()		
	ear = cv2.rotate(ear, cv2.cv2.ROTATE_90_CLOCKWISE) 											#Make copy of original image
	wid = ear.copy()
	wid2 = ear.copy()

#grab lower half of the ear
	sect = utility.ranges(ear.shape[1], 6)
	see1 = sect[0].split (",")
	see2 = sect[4].split (",")
	wid[:, int(see1[1]):int(see2[0])] = 0
	wid2[wid != 0] = 0
	wid3 = wid2.copy()
	wid4 = wid3.copy()
	widk = img.copy()

#grab middle of the ear
	sect = utility.ranges(ear.shape[0], 3)
	see = sect[1].split (",")
	wid2[int(see[0]):int(see[1]), :] = 0
	wid3[wid2 != 0] = 0

#remove the rest
	gray = cv2.cvtColor(wid3, cv2.COLOR_BGR2GRAY)
	grayk = cv2.cvtColor(widk, cv2.COLOR_BGR2GRAY)
	thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)[1]
	threshk = cv2.threshold(grayk, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)[1]
	cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cnts = cnts[0] if len(cnts) == 2 else cnts[1]
	cntsk = cv2.findContours(threshk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cntsk = cntsk[0] if len(cntsk) == 2 else cntsk[1]
	cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
	cntsk = sorted(cntsk, key=cv2.contourArea, reverse=True)
	for c in cnts:
		x,y,w,h = cv2.boundingRect(c)    ###CHECJ THIS MIGHT AFFECT THE RESULTS
		wid3 = wid3[0:ear.shape[0], x:x+w, ] 		#CUT IMAGE		
		wid4 = wid4[0:ear.shape[0], x:x+w, ] 		#CUT IMAGE				
		wid3 = wid3[y:y+h, 0:ear.shape[1]]

		break
	for c in cntsk:
		x, y, w, h = cv2.boundingRect(c)  ###CHECJ THIS MIGHT AFFECT THE RESULTS
		widk = widk[y:y+h, x:x+w]  # CUT IMAGE
		break

#~~~~~~~~~~~~~~~~~~~~~~~~Force signal into 2D and call valleys
#split colors
	_,g1,_ = cv2.split(wid3)
#mean intestines (1D)	
	x = np.sum(g1,axis=0)

#smooth
	window_len=15   #### <-------THIS IS HOW HARD YOU SMOOTH, AFFECTS PEAK CALLING
	window='flat'
	s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
	w=np.ones(window_len,'d')
	if w.size != 0:
		#cols=np.convolve(w/w.sum(),s,mode='valid')
		cols = savgol_filter(x, window_len, 5)

#find valleys
	cols = utility.rescale_linear(cols, 0, wid3.shape[0])
	b = argrelextrema(cols, np.less)
	kk = b[0]
	b = b[0]

#SUMMARY STATS
	dif = np.diff(b)

##append slices to make each slice wider

	a = utility.ranges(wid3.shape[1], 6)
	a = [int(a[i].split(",")[0]) for i in range(len(a))]
	a = a[1:len(a)-1]
	b = a

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#################################### Slice Vertically ##################################
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

###now you have where to make the slices      ##### TEMPORARILY ONLY DOING THREE SLICES....MUST EXTRAPOLATE TO ALL SLICES
	j = 1
	peaks = []
	dis_kernel = []
	all_peaks = []

	for i in range(len(b)-1):
	#for i in range(0,5):
		j = j + 1
		#print(j)
		#bb = b[i].split(",")
		wid5 = wid4.copy()
		wid5[:,0:int(b[i])] = 0
		wid5[:,int(b[i+1]):wid5.shape[1]] = 0
		wid5 = cv2.rotate(wid5, cv2.cv2.ROTATE_90_COUNTERCLOCKWISE)
######### HERE IS WHERE YOU DO THE THING TO EACH SECTION###############
		gray = cv2.cvtColor(wid5, cv2.COLOR_BGR2GRAY)
		thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)[1]
		cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		cnts = cnts[0] if len(cnts) == 2 else cnts[1]
		cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
		for c in cnts:
			x,y,w,h = cv2.boundingRect(c)    ###CHECJ THIS MIGHT AFFECT THE RESULTS
			rects = cv2.minAreaRect(c)		###CHECJ THIS MIGHT AFFECT THE RESULTS
			boxs = cv2.boxPoints(rects)
			boxs = np.array(boxs, dtype="int")			
			boxs = utility.order_points(boxs)
			(tls, trs, brs, bls) = boxs
			(tlblXs, tlblYs) = ((tls[0] + bls[0]) * 0.5, (tls[1] + bls[1]) * 0.5)
			(trbrXs, trbrYs) = ((trs[0] + brs[0]) * 0.5, (trs[1] + brs[1]) * 0.5)
			thmp = dist.euclidean((tlblXs, tlblYs), (trbrXs, trbrYs)) #pixel width 
			
		#CUT IMAGE				
			wid5 = wid5[y:y+h, 0:wid5.shape[1]]
			wid5 = wid5[0:wid5.shape[0], x:x+w,] 		#CUT IMAGE	
			break
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Resize image
		wid6 = wid5.copy()
		_,g1,_ = cv2.split(wid6)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Find peaks
#sum intestines (1D)
		x = np.sum(g1,axis=0)
#find valleys
		c = argrelextrema(x, np.less)
		c = c[0]
		u = 19
		while len(c) > 9:					#smooth
			window_len=u  #### <-------THIS IS HOW HARD YOU SMOOTH, AFFECTS PEAK CALLING
			s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
			w=np.ones(window_len,'d')
			#w = eval('np.' + window + '(window_len)')
			if w.size != 0:
				#cols=np.convolve(w/w.sum(),s,mode='valid')
				cols = savgol_filter(x, window_len, 4)
			cols = utility.rescale_linear(cols, 0, wid5.shape[0])
			c = argrelextrema(cols, np.less)
			c = c[0]
			u = 2 + u

		#stats
		dif = np.diff(c)
		median_dif = np.median(dif, axis=0)
		dis_kernel.append(median_dif)
		all_peaks.extend(c)


	''' ------------------------------------------------------------------
		Report median difference between peaks pre consensus
	------------------------------------------------------------------ '''
	diff_pre_consensus = np.median(dis_kernel)
	#print("Median difference between peaks pre consensus =  ", diff_pre_consensus)


	''' ------------------------------------------------------------------
		Flatten all the peaks in 1 array and then cluster based on 
		median of the diff. All the peaks in the flattened array with
		difference from the previous peak less than the median diff are
		clustered as a single peak
		Median of each peak is taken as representative 
	------------------------------------------------------------------ '''

	all_peaks = np.sort(all_peaks)
	all_peaks_diff = np.diff(all_peaks)
	all_peaks_diff_med = np.median(all_peaks_diff)
	cur_list = []
	prev_ele = all_peaks[0]
	clustered_list = []
	for i in range(len(all_peaks)):
		if (abs(all_peaks[i]-prev_ele) <= (all_peaks_diff_med)):
			cur_list.append(all_peaks[i])
		else:
			clustered_list.append(cur_list)
			cur_list = [all_peaks[i]]
		prev_ele = all_peaks[i]
	clustered_list.append(cur_list)
	all_peaks_final = []
	for i in range(len(clustered_list)):
		all_peaks_final.append(np.median(clustered_list[i]))

	''' ------------------------------------------------------------------
		Further process the peaks to eliminate some of the erroneous peak
		based on adaptive threshold
	------------------------------------------------------------------ '''

	all_peaks_final_temp = all_peaks_final.copy()
	num_peaks_iter = 0
	threshold = 0.9
	num_exec = 0
	while num_peaks_iter < 6:
		all_peaks_final = all_peaks_final_temp.copy()
		all_peaks_final_diff = np.diff(all_peaks_final)
		all_peaks_final_diff_max = np.max(all_peaks_final_diff)
		prev_ele = all_peaks_final[0]
		i = 1
		while(i < len(all_peaks_final)):
			if (all_peaks_final[i]-prev_ele < (threshold*all_peaks_final_diff_max)):
				all_peaks_final.remove(all_peaks_final[i])
			else:
				prev_ele = all_peaks_final[i]
				i = i+1
		num_peaks_iter = len(all_peaks_final)
		#print("num peaks = ", num_peaks_iter, " threshold = ", threshold)
		threshold = threshold - 0.1
		num_exec = num_exec + 1
		if num_exec > 6:
			break
	''' ------------------------------------------------------------------
		Plot
	------------------------------------------------------------------ '''
	#widk = cv2.cvtColor(widk, cv2.COLOR_BGR2RGB)
	#fig = make_subplots(rows=1, cols=2)
	#fig.add_trace(go.Image(z=widk), row=1, col=1)
	#fig.add_trace(go.Image(z=widk), row=1, col=2)
	# lines to add, specified by x-position
	lines = all_peaks_final
	line_thickness = 7
	
	for i in range (0, len(lines)):
		x1, y1 = int(lines[i]), 100
		x2, y2 = int(lines[i]), widk.shape[0]-50
		cv2.line(widk, (x1, y1), (x2, y2), (219, 112, 147), thickness=line_thickness)

	krn_proof = widk.copy()

	# add lines using absolute references
	#for k in range(len(lines)):
	#	fig.add_shape(type='line', yref="y", xref="x", x0=lines[k], y0=0,
	#				  x1=lines[k], y1=img.shape[0], line=dict(color='red', width=3), row=1, col=2)

	diff_post_consensus = np.median(np.diff(all_peaks_final))
	num_peaks = len(all_peaks_final)

#	''' ------------------------------------------------------------------
#		Report median difference between peaks post consensus#
#	------------------------------------------------------------------ '''
#	print("Median difference between peaks post consensus = ", diff_post_consensus)
#	print("Num of peaks post consensus = ", num_peaks)


# End ---
	#fig.layout.update(showlegend=False)
	#fig.show()

	return diff_pre_consensus, diff_post_consensus, num_peaks, krn_proof