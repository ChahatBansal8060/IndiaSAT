# IndiaSAT - A datset for pixel-level LC classification of Landsat-7, Landsat-8 and Sentinel-2A imagery

This repo contains an open dataset for pixel-level LC classification of Landsat 7, Landsat 8, and Sentinel 2A Imagery along with the code for classification as well as the error correction methods on top of it.

## Methodology for pixel-level classification of Landsat 7, Landsat 8, and Sentinel 2 Imagery
![alt text](Images/LC_classification_methodology.png?raw=true)

## Step by step procedure to do classification of a selected area.
* **Step 1  : Run the GEE scripts for data download**

Run the corresponding GEE script to download prediction images of your region of interest (ROI). These are located at Scripts/GEE_scripts/Data_download_scripts. Use the script landsat7_classification.js or landsat8_classification.js or sentinel2_classification.js for Landsat 7, Landsat 8, and Sentinel 2 respectively.

The output of the GEE script will be three prediction images for your ROI for a given year. (2 half yearly images and 1 for the whole year)

> *Note - You should have the shapefiles of that particular area or you can draw the area by hand in GEE. The shapefiles used in our project can be found in Datasets/GEE_Assets.
Someone, who is new to Google earth engine, can find all the help from this [place](https://developers.google.com/earth-engine/getstarted)*

* **Step 2 : Run final_classification.py script for creating single yearly prediction maps**

It will make a different folder of each ROI in the Results directory and put all classification outputs for that ROI (for all the years) in that folder.


The command-line argument for the script: the path of root folder for the target ROI. (path of the unique folder which you just created).
For exmample if you are doing classification for an area name Delhi, then put all your downloaded classification outputs in a folder named <Delhi> and then run the following command from terminal.
    
        python3 Scripts/LC_classification/final_classification_processing.py Delhi

> The final classification result will be stored in the Results directory inside root folder. For above example the classification results of each year will be in Results/Delhi/results/combined_yearly_prediction_temp_corrected. We generate 3 sets of results: (1) Direct classification maps (using year median images), (2) Combined yearly mapping (with 3 images), and (3) Combined yearly mapping with temporal correction.
Please note that you have to edit the list of years under analysis in the script for processing. You can also choose if you want temporal correction to be done in a single batch, or in group of batches.


* **Optional- get_4_class_accuracy.py**

The command-line argument to be given while running the script - the path of root folder for a given area. (which you created in step 2), the path of folder storing groundtruth files, and the year for which groundtruth is created. 

        python3 Scripts/LC_classification/get_4_class_accuracy.py Results/Delhi/ Datasets/Groundtruth_4_categories_2018/ 2018

This script is to check the accuracy when the ground-truth is available in four categories (green, water, bareland and built-up).
This script will provide four options to the user to check the accuracy of outputs from four different methods/techniques. The output of this script will be saved in a .txt file in Results/Classification_4cat_Accuracy_2018s. 

* **Optional- get_BU_NBU_accuracy.py**

The command-line argument to be given while running the script - the path of root folder for a given area. (which you created in step 2), the path of folder storing groundtruth files, and the year for which groundtruth is created. 

        python3 Scripts/LC_classification/get_BU_NBU_accuracy.py Results/Delhi/ Datasets/Groundtruth_4_categories_2018/ 2018

This script is to check the BU/NBU accuracy when the ground-truth is available in four categories (green, water, bareland and built-up).
This script will provide four options to the user to check the accuracy of outputs from four different methods/techniques. The output of this script will be saved in a .txt file in Results/BU_NBU_Accuracy_2018. 


* **Step 3 : Run classify_builtup_change.py script for finding change in builtup pixels across multiple years**

The command-line argument to be given while running the script - the path of root folder for a given area. (which you created in step 2), the first year and the last year between which you wish to find the change in builtup pixels. 

        python3 Scripts/Builtup_change_classification/classify_builtup_change.py Results/Delhi/ 2016 2019

This script creates a single CBU_CNBU_Changing map for this interval, where the pixels which remained BU in both years were marked as constantly Builtup (CBU), NBU in both years as Constantly Non-Builtup (CNBU), and the ones which were NBU in first year and BU in the last year were marked as Changing Pixels. The output in grayscale and RGB is saved in Results/Builtup_change_classification_2016_2019/Delhi directory. 


* **Optional- get_builtup_change_accuracy.py**

The command-line argument to be given while running the script - the path of folder containing CBU/CNB/Changing map for a given area. (which you created in step 3), the path of folder storing CBU_CNBU_)Changing groundtruth files for this district, and a REFERENCE TIFFILE to create png prediction maps to tif files (this reference tiffile can be any tiffile of this district, like the ones downloaded from GEE in the very beginning). 

        python3 Scripts/Builtup_change_classification/get_builtup_change_accuracy.py Results/Builtup_change_classification_2016_2019/Delhi/ Datasets/CBU_CNBU_Changing_Groundtruth_2016_2019/Delhi/ Results/Delhi/2016/landsat8_Delhi_2016_1half.tif

This script is to check the CBU/CNBU/Changing accuracy when the ground-truth is available in these three categories.
This script will provide four options to the user to check the accuracy of outputs from four different methods/techniques. The output of this script will be saved in a .txt file in Results/CBU_CNBU_Changing_Accuracy_2016_2019. 
 

## Prerequisites
* Google Earth Engine(GEE) account to run the google earth engine scripts for downloading and images and run the classifier
* Following python libraries to run the python scripts
    * PIL (Pillow)
    * scipy
    * numpy
    * pandas
  
