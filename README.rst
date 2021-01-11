.. highlight:: rst

=====
EarCV
=====

-------------------------------------------------------
A python-based tool for automated maize ear phenotyping
-------------------------------------------------------

This tool allows the user to rapidly extract features from images containing maize ears against a uniform background. It was designed with the intention of facilitating analysis of thousands of images with a single command prompt. As output, this tool creates a .csv with features for each ear found in the input image(s) and prints several proofs to monitor tool performance.

-----------
Quick Start
-----------

Assuming you are in the root folder of this repo, lets run the simplest case -- an image only containing a single ear::

	python ./src/main.py -i ./test/IN/test_img_1.JPG -o ./test/OUT/

Output:

.. image:: ./test/OUT/01_Proofs/test_img_1_proof.png
    :width: 100px
    :align: center
    :height: 100px
    :alt: alternate text

.. image:: ./test/OUT/03_Ear_Proofs/test_img_1_ear_1.png
    :width: 100px
    :align: center
    :height: 100px
    :alt: alternate text

Now lets run the same image with default cob and shank segmentation::

	python ./src/main.py -i ./test/IN/test_img_1.JPG -o ./test/OUT/ -t 0 0 0 0 -b 0 0 0 0 

Output:

.. image:: ./test/OUT/03_Ear_Proofs/test_img_1_ear_1_proof.png
    :width: 100px
    :align: center
    :height: 100px
    :alt: alternate text

Let's run an image with all of the features using default settings::

	python ./src/main.py -i ./test/IN/test_img_2.png -o ./test/OUT/ -qr -clr ./test/IN/clrchr.png -ppm 10 -t 0 0 0 0 -b 0 0 0 0

Output:

.. image:: ./test/OUT/01_Proofs/test_img_2_proof.png
    :width: 100px
    :align: center
    :height: 100px
    :alt: alternate text

-----
Usage
-----

^^^^^^^^^^^^^^^^^^^^^^^^^^^
Installation & Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Just download this repo and make sure you have all the dependencies installed on your python environment of choice. This tool uses the folowing packages:

* OpenCV 2
* numpy
* scipy
* pyzbar (optional, QR code module)
* plantcv (optional, Color correction module)

^^^^^^^^^^^^^
Main pipeline
^^^^^^^^^^^^^
This tool uses any standard image format (.jpg, .jpeg, .png, or .tiff). We will asuume you are running this from the main ''EarCV/'' folder contianing this repo. Let's use images within the ''/test/'' folder as examples. To start, here is key info:

* Segments ears photographed against a uniform background
	- Background can be any color insofar it contrasts well with the ears.
	- Algorithm can take any number of ears, in any configuration or arrangment.
	- Ears may touch slightly in the image.
	- Ears may have silk and other debri.

* For each ear:
	- Extracts basic morphological features
	- Segments cob and shank from kernels
	- Extracts kernel features
	- (in development) Estimates Kernel Row Number
	- (in development) Predicts USDA quality Grade
 
Input

	Required:

	-i, --image         Path to input image file, required. Accepted formats: 'tiff', 'jpeg', 'bmp', 'png'.

	Optional:

	-o, --OUTDIR        Provide path to directory to save proofs, logfile, and output CSVs. Default: Will save in current directory if not provided.

	-ns, --no_save      Default saves proofs and output CSVs. Raise flag to stop saving.

	-np, --no_proof     Default prints proofs on screen. Raise flag to stop printing proofs.

	-D, --debug         Raise flag to print intermediate images throughout analysis. Useful for troubleshooting.

For complete usage documentation run::

	python ./src/main.py -h

Output
	The output structure is as follows::

	./OUT/
	|--- 01_Proofs/
	|--- 02_Ear_ROIs/
	|--- 03_Ear_Proofs/
	|--- EarCV.log
	|--- qrcode.csv
	|--- color_check.csv
	|--- features.csv

Proofs
    Use proofs to minotor performance. ''01_Proofs'' documents qr code extraction, color correction, pixels per metric calculation, and ear segmentation. ''02_Ear_ROIs'' contains the region of interest for each segmented ear. ''03_Ear_Proofs'' conatins a proof for each individual ear showing various feature extraction results. 
EarCV.log
	Evey time you run the script, the terminal prints a log of what is happening under the hood.
qrcode.csv
	File with the image name and the corresponding information found in QR code.
color_check.csv
    File with color correction preformance metrics based on root mean squared differences in color.
features.csv
    File with the ear features as columns and ears as rows.

^^^^^^^^^^^^^^^^
Optional modules
^^^^^^^^^^^^^^^^
* QR code extraction
	- Helps you keep track of who is what in what image in your experiment.
	- Scans image for QR code and returns found information.
* Color correction
	- Standizes colors across any number of images to make robust color comparisons.
	- Performs color correction on images using a color checker.

* Pixels per metric conversion
	- Want your morphemetric measurements in inches? centimeters?
	- Converts pixel measurements into any unit of length or area.
	- Calculates the pixels per metric using a solid color square in the input image of known dimensions.

^^^^^^^^^^^^^^^^^^
QR code extraction
^^^^^^^^^^^^^^^^^^

#.. literalinclude:: filename
#    :linenos:
#    :language: python
#    :lines: 1, 3-5
#    :start-after: 3
#    :end-before: 5

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




