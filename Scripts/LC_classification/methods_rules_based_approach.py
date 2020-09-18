# import all required packages
from PIL import Image
import math
from PIL import Image
from scipy import misc
from scipy import ndimage
import pandas as pd
import unittest
import os, sys
import shutil #for copying files
import numpy as np
import shutil

#-------------------------------------------------------------------------------


'''
Rule-based post-classification correction

merge the monthly predictions and overall median prediction to get a single prediction for year
Pixel value 0 denotes Background, 1 denotes greenery, 2 denotes water, 3 benotes Built-Up, 4 denotes Barren land
Input-
1) monthly_pixel_predictions = list of predicted value of a particular pixel in the best 5 months of a particular year
2) median_pixel_prediction = predicted value of the above pixel over the year median image
'''  
def merge_prediction(monthly_pixel_predictions):    
    total_predictions = len(monthly_pixel_predictions)
    
    #find the count of each kind of pixel value for a pixel across all the given years
    background_count = monthly_pixel_predictions.count(0)
    green_count = monthly_pixel_predictions.count(1) 
    water_count = monthly_pixel_predictions.count(2) 
    builtup_count = monthly_pixel_predictions.count(3) 
    barrenland_count = monthly_pixel_predictions.count(4) 
    
    #Applying different rules for post-classification error correction
    
    # Rule1: If pixel is predicted as background in all selected predictions, consider it background for the entire year
    if (background_count == total_predictions):
        return '0'
    # Rule2: If a pixel is predicted same in all predictions keep it as it is.
    elif (green_count>=1 and max([barrenland_count,builtup_count,water_count])==0):
    	return '1'
    elif (water_count>=1 and max([green_count,barrenland_count,builtup_count])==0):
    	return '2'
    elif (barrenland_count>=1 and max([green_count,water_count,builtup_count])==0):
    	return '4'
    elif (builtup_count>=1 and max([green_count,barrenland_count,water_count])==0):
    	return '3'    
    
    # Rule3: (pixel has been predicted as water and green atleast once)
    #If pixel is predicted as water more times than green in quarterly predictions, 
    # consider it water for the entire year
    elif (water_count > 0 and green_count > 0):
        return '2' if (water_count >= 2 * green_count) else '1'

    #Rule3: (pixel has been predicted as bareland and green atleast once)
    # that means that area has grass at some point of time. Classify it as green area.
    # Choose green between barrenland and green	
    elif (green_count >0 or barrenland_count>0):
    	return '1'
    	#return '1' if(green_count>=barrenland_count) else '4'


    # Rule3: majority based rule  for remaining (builtup, bareland, green, water)
    elif (green_count >= max([green_count,water_count,builtup_count,barrenland_count])):
        return '1' 
    elif (barrenland_count >= max([green_count,water_count,builtup_count,barrenland_count])):
        return '4' 
    elif (water_count >= max([green_count,water_count,builtup_count,barrenland_count])):
        return '2'         
    else:
    	return '3'

 


#method to make grayscale images(.png) into colorful images. Input is the folder name containing grayscale images.
def make_images_colorful(input_folder, greyscale_folder):
	print(greyscale_folder)
	src_folder_path = input_folder+'/results/'+greyscale_folder
	colored_folder = greyscale_folder+'_colored'
	colored_folder_path = input_folder + '/results/' + colored_folder 
	os.makedirs(colored_folder_path, exist_ok=True)
	for infile in os.listdir(src_folder_path):
		if infile[-4:]=='.png':
			image_path = src_folder_path+'/'+infile
			img = Image.open(image_path)
			img = img.convert("RGBA")
			pixdata = img.load()
			for y in range(img.size[1]):
				for x in range(img.size[0]):
					if pixdata[x, y] == (0, 0, 0, 255):      # background 
						pixdata[x, y] = (0,0,0,0)            # black color
					elif pixdata[x, y] == (1, 1, 1, 255):    # green
						pixdata[x, y] = (34,139,34, 255)     # green color
					elif pixdata[x, y] == (2, 2, 2, 255):    # water
						pixdata[x, y] = (2, 4, 251, 255)     # blue color
					elif pixdata[x, y] == (3, 3, 3, 255):    # built-up 
						pixdata[x, y] = (255, 255, 102, 255) # yellow color
					elif pixdata[x, y] == (4, 4, 4, 255):    # bareland
						pixdata[x, y] = (255, 80, 80, 255)   # red color

			img.save(colored_folder_path+"/"+infile[:-4]+'_colored.png')
			print(infile + ' - colors filled.')
