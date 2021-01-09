=====
EarCV
=====


Python-based tool for automted maize ear phenotyping


Description
===========

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
###################### Computer Vision for Maize Ear Analysis  ###########################
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
###################### By: Juan M. Gonzalez, University of Florida  ######################
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This tool allows the user to analyze images with maize ears in a uniform background.

This script accepts any standard image format (.jpg, .jpeg, .png, or .tiff).

This script requires that `OpenCV 2', 'numpy', 'scipy', 'pyzbar'(optional), and 'plantcv(optinal)' be installed within the Python
environment you are running this script in.

This file imports modules within the same folder:

    * QR.py - Scans image for QR code and return found information.
    * Clrchk.py - Performs color correction on images using a color checker.
    * Ppm.py - Calculates the pixels per metric using a solid color square in the input image of known dimensions.
    * Find_ears.py - Segments ears in the input image.
    * Ear_features.py - Segments kernel from cob and shank, and measures ear features.
    
This script returns a .csv with features for each ear found in the input image and a proof image to monitor tool performance.
