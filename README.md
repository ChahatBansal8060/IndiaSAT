# IndiaSat - A datset for pixel-level classification of Landsat-7, Landsat-8 and Sentinel-2A imagery

This repo contains an open dataset for pixel-level classification of Landsat 7, Landsat 8, and Sentinel 2A Imagery along with the code for classification as well as the error correction methods on top of it.

## Methodology for pixel-level classification of Landsat 7 and Landsat 8 Imagery
![alt text](images/landsat_classification.png?raw=true)

## Step by step procedure to do classification of a selected area.
* **Step 1  : Run the GEE script**

Run the corresponding GEE script for Landsat 7 or Landsat 8. (landsat7_classification.js or landsat8_classification.js or sentinel2_classification.js).
The output of the GEE script will be three images for your area of interest (selected area) for each year.

> *Note - You should have the shapefile of that particular area or you can draw the area by hand in GEE.
Someone, who is new to Google earth engine, can find all the help from this [place](https://developers.google.com/earth-engine/getstarted)*

* **Step 2 : Run final_classification.py script**

It will make a different folder of each area and put all classification outputs for that area (for all the years) in that folder.


The command-line argument for the script - the path of root folder for a given area. (path of the unique folder which you just created).
For exmample if you are doing classification for an area name Delhi, then put all you classification outputs in a folder named <Delhi> and then run the following command from terminal.
    
        python3 final_classification.py Delhi

> The final classification result will be stored in a folder inside root folder. For above example the classification results of each year will be in Delhi/results/combined_yearly_prediction_temp_corrected. 

* **Optional- only_temporal_correction.py (for developers use)**


the command-line argument to be given while running the script - the path of root folder for a given area. (which you created in step 2)

        python3 only_temporal_correction.py Delhi

> This script is for experimentation with temporal correction technique. This performs only the temporal correction.

* **Optional- check_accuracy_2cat_landsat.py**

The command-line argument to be given while running the script - the path of root folder for a given area. (which you created in step 2)

        ptyhon3 check_accuracy_2cat_landsat.py Delhi

This script is to check the BU/NBU accuracy when the ground-truth is available in four categories (green, water, bareland and built-up).
This script will provide four options to the user to check the accuracy of outputs from four different methods/techniques. The output of this script will be saved in a .txt file. 

## Prerequisites
* Google Earth Engine(GEE) account to run the google earth engine scripts for downloading and images and run the classifier
* Following python libraries to run the python scripts
    * PIL (Pillow)
    * scipy
    * numpy
    * pandas
  
