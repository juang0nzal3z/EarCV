.. highlight:: rst

=====
EarCV
=====

-----------
Descirption
-----------

A python-based tool for automated maize ear phenotyping. This tool allows the user to rapidly extract features from images containing maize ears against a uniform background. It was designed with the intention of facilitating analysis of thousands of images with a single command prompt. In the end, this tool creates a .csv with features for each ear found in the input image(s) and proof images to monitor tool performance. The application has optional modules on top of a default pipeline:

    * QR.py - Scans image for QR code and return found information.
    * Clrchk.py - Performs color correction on images using a color checker.
    * Ppm.py - Calculates the pixels per metric using a solid color square in the input image of known dimensions.
    * Find_ears.py - Segments ears in the input image.
    * Ear_features.py - Segments kernel from cob and shank, and measures ear features.


^^^^^^^^^^^^^^^^
Optional modules
^^^^^^^^^^^^^^^^
* QR code extraction -- Helps you keep track of who is what in what image in your experiment.
* Color correction -- If color analysis is important, you can include a color checker passport to standize colors across any number of images and make robust color comparisons. 
* Pixels per metric conversion -- Want your morphemetric measurements in inches? centimeters? Easiliy convert pixel measurements into any unit of length or area by providing a refference object in the image of know dimensions.

^^^^^^^^^^^^^
Main pipeline
^^^^^^^^^^^^^
* Segment ears photographed against a uniform background -- Background can be any color insofar it contrasts well with the ears. Algorithm can take any number of ears, in any configuration or arrangment. Ears may touch slightly in the image. Ears may have silk and other debri.

For each ear:
* Extract basic morphological features
* Segment cob and shank from kernels
* Extract kernel features
* (in development) Estimate Kernel Row Number
* (in development) Predict USDA quality Grade

------------
Installation
------------

Just download this repo and make sure you have all the dependencies installed on your python environment of choice.

^^^^^^^^^^^^^
Dependencies
^^^^^^^^^^^^^

* OpenCV 2
* numpy
* scipy
* pyzbar (optional, QR code module)
* plantcv (optional, Color correction module)

-----
Usage
-----

This tool uses any standard image format (.jpg, .jpeg, .png, or .tiff). We will asuume you are running this from the main ''EarCV/'' folder contianing this repo. Let's use images within the ''/test/'' folder as examples. To start, here is key info::

	    Required:

	    -i, --image         Path to input image file, required. Accepted formats: 'tiff', 'jpeg', 'bmp', 'png'
        
        Optional:

        -o, --OUTDIR        Provide directory to saves proofs, logfile, and output CSVs. Default: Will save in current directory if not provided.
        -ns, --no_save      Default saves proofs and output CSVs. Raise flag to stop saving.
        -np, --no_proof     Default prints proofs on screen. Raise flag to stop printing proofs.
        -D, --debug         Raise flag to print intermediate images throughout analysis. Useful for troubleshooting.

For complete usage documentation run::

	python ./src/main.py -h

The output structure is as follows::

	./OUT/
	|--- 01_Proofs/
	|--- 02_Ear_ROIs/
	|--- 03_Ear_Proofs/
	|--- EarCV.log
	|--- features.csv

Evey time you run the script, the terminal will print a log of what is happening under the hood. The log is always saved as ''EarCV.log'' within the output folder.

^^^^^^^^^^^^^^^^^^^^^^^^^^^
[Quick Start] The basics...
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Lets run the simplest case: an image only containing a single ear::

	python ./src/main.py -i ./test/IN/test_img_1.JPG -o ./test/OUT/

You get the following proofs under ''01_Proofs/'' and ''03_Ear_Proofs/'':

![Alt Text](/Users/mongo/Documents/OneDrive_University_of_Florida/PMCB/marcio/5.EAR_CV/10_EarCV_Final/EarCV/test/OUT/01_Proofs/test_img_1_proof.png)

![Alt Text](/Users/mongo/Documents/OneDrive_University_of_Florida/PMCB/marcio/5.EAR_CV/10_EarCV_Final/EarCV/test/OUT/03_Ear_Proofs/test_img_1_ear_1.png)

Now lets run the same image with default cob and shank segmentation::

	python ./src/main.py -i ./test/IN/test_img_1.JPG -o ./test/OUT/

You get the following cob/shank segmentation:

![Alt Text](/Users/mongo/Documents/OneDrive_University_of_Florida/PMCB/marcio/5.EAR_CV/10_EarCV_Final/EarCV/test/OUT/03_Ear_Proofs/test_img_1_ear_1_proof.png)

Let's run an image with all of the features using default settings::

	python ./src/main.py -i ./test/IN/test_img_2.png -o ./test/OUT/ -qr -clr ./test/IN/clrchr.png -ppm 10 -t 0 0 0 0 -b 0 0 0 0

You get this this proof:

![Alt Text](/Users/mongo/Documents/OneDrive_University_of_Florida/PMCB/marcio/5.EAR_CV/10_EarCV_Final/EarCV/test/OUT/01_Proofs/test_img_2_proof.png)


^^^^^
Usage
^^^^^



^^^^^^^^^^^^^^^^^^
QR code extraction
^^^^^^^^^^^^^^^^^^

Scans image for QR code and extracts information using pyzbar's decode function.

Parameters
----------
qr_img : array_like
	Valid file path to image to be scanned for QR code. Accepted formats: 'tiff', 'jpeg', 'bmp', 'png'.


qr_window_size: float
	Optional. Dimension of square window size to scan over original image.

overlap: float
	Optional. Amount of overlap between windows. Must be a decimal between 0 & 1. The higher the number the more overlap between windows and higher scanning resolution but longer analysis.

debug: bool
	If true, print images.

Returns
-------
QRcodeType
QRcodeData
QRcodeRect
qr_count
qr_proof

References
----------

Thank you zbar! http://zbar.sourceforge.net/index.html

Examples
--------

Example 1:

python qr.py W201432.JPG None None False

Example 2:

python qr.py W201432.JPG 2000 0.01 True




^^^^^^^^^^^^^^^^^^^^
Output: Ear features
^^^^^^^^^^^^^^^^^^^^

Anytime you use this tool you will get the following features:




