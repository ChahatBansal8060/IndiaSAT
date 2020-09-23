# import all required packages
from PIL import Image
import math
from scipy import misc
from scipy import ndimage
import pandas as pd
import os, sys
import shutil #for copying files
import numpy as np
import tqdm as tqdm
from methods_temporal_correction import *
from methods_rules_based_approach import *
#-------------------------------------------------------------------------------

flag_overlapping_TempCorrection = False
batch_size_overlapping = 6
temp_correction_list=['direct_application','combined_yearly_prediction']
# temp_correction_list=['combined_yearly_prediction']
year_list = ['2015','2016','2017','2018','2019','2020']
#year_list = ['2014','2015','2016','2017','2018','2019','2020']
#year_list = ['2010','2011','2012','2013','2014','2015','2016','2017','2018','2019']
#year_list = ['1999','2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010','2011','2012','2013','2014','2015','2016','2017','2018','2019','2020']



print(sys.argv[0])
print()
input_folder = sys.argv[1]     #we have stored monthly predections in a folder named by district name
if input_folder.split('/')[-1]=='':
	input_folder = input_folder[:-1]
district_name = input_folder.split('/')[-1]
if (district_name==""): #if user has put extra "/" at the end of input folder path.
	district_name = input_folder.split('/')[-2]

print('Name of Area/District - ',district_name)

output_folder = 'Results/'+input_folder
os.makedirs(output_folder,exist_ok=True)

##==========================================Sub folder structure creation ======================================================

print('''
        -------------------------------------------------------
        Creating sub-folders structure and
        Converting .tif files into .png for further processing.  
        -------------------------------------------------------
	''')

total_count=0
for infile in os.listdir(input_folder):
    if infile[-4:] == ".tif":
        total_count = total_count+1
        for year in year_list:
            os.makedirs(output_folder+"/"+year,exist_ok=True)
            if (year in infile):
                #shutil.move(input_folder+'/'+infile, output_folder+'/'+year+'/'+infile)
                shutil.copy(input_folder+'/'+infile, output_folder+'/'+year+'/'+infile)
print("Total .tif files found in the root folder - ", total_count)


for year in year_list:
	main_folder = output_folder + '/' + year
	os.makedirs(main_folder+"/pngs",exist_ok=True)
	count = 0
	for infile in os.listdir(main_folder):
		if infile[-4:] == ".tif":                   #reading all tif files in given folder
			im = Image.open(main_folder+"/"+infile)
			im.save(main_folder+"/pngs/"+infile[:-4]+'.png')
			count=count+1
	print(count, ' images found and converted for year ',year )		
print('.tif to .png conversion completed.')

print('''
	-----------------------------------------------
	Segregating yearly median prediction 
	and making them colorful.
	-----------------------------------------------
	''')
'''
Make a year_median folder and copy all the yearly_median_prediction for all years in that folder.

'''
os.makedirs(output_folder+"/results/direct_application",exist_ok=True)
for year in year_list:
	src_dir = output_folder + '/' + year + '/pngs'
	dest_dir = output_folder+"/results/direct_application"
	for infile in os.listdir(src_dir):
		if ('year_median' in infile):
			shutil.copyfile(src_dir+'/'+infile, dest_dir+'/'+district_name+'_prediction_'+year+'.png')

make_images_colorful(output_folder, "direct_application")

##=========================================Rule based approach =======================================================

print('''
	-----------------------------------------------
	Processing for final_year_prediction started.
	 (Please wait. This might take few minutes.)
	-----------------------------------------------
	''')

os.makedirs(output_folder+"/results/combined_yearly_prediction",exist_ok=True)
for year in year_list:
	main_folder = output_folder + '/' + year
	#Find the minimum number of background pixels in the images of all months for this year
	dataset = [ np.asarray(Image.open(main_folder+"/pngs/"+infile)) for infile in os.listdir(main_folder+"/pngs/") ]
	image_dimension = dataset[0].shape
	#print(image_dimension)

	#Initializing the results prediction matrix for a particular year
	results_prediction = np.zeros(image_dimension[0] * image_dimension[1]).reshape(image_dimension)
	#print(results_prediction)

	for i in tqdm.tqdm(range(image_dimension[0]), desc='Progress : '):
	    for j in range(image_dimension[1]):
	        x = [ dataset[k][i][j] for k in range(len(dataset)) ]
	        results_prediction[i,j] = merge_prediction(x)

	print("final_prediction "+year +" - ",np.unique(results_prediction,return_counts=True))
	results_prediction = (Image.fromarray(results_prediction)).convert("L")
	results_prediction.save(output_folder+'/results/combined_yearly_prediction/'+district_name+'_prediction_'+year+'.png')        
print('done!')

print('''
	-----------------------------------------------
	final_year_prediction done.
	Making final_year_prediction colorful for you!
	-----------------------------------------------
	''')   


make_images_colorful(output_folder, "combined_yearly_prediction")

##========================================= Temp Correction procedure =========================================================			

print('''
	---------------------------------------------------
	Combined_yearly_prediction for all years completed.
	Temporal correction begins...
	---------------------------------------------------
	''')  


if flag_overlapping_TempCorrection==True:
	print("Temporal correction is being done with overlapping of two years with batches of "
		+ batch_size_overlapping + ' years')
	Overlapping_TempCorrection_execution(output_folder, district_name, year_list, temp_correction_list, batch_size_overlapping)
else:
	print("Temporal correction is being done for all years together.")
	for folder_name in temp_correction_list:
		TempCorrection(output_folder, district_name, year_list, folder_name)		

print('''
	-------------------------------------------------------
	Making temporal corrected predictions colorful for you!
	-------------------------------------------------------
	''')  
#-----------------------------------------------------
for folder_name in temp_correction_list:
	temp_coorected_folder_name = folder_name + '_temp_corrected'
	make_images_colorful(output_folder, temp_coorected_folder_name)


print('''
	-----------------------------------------------
	 Congratulations! We are done with everything.
	-----------------------------------------------
	''')
