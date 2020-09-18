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
from  methods_temporal_correction import *
from  methods_rules_based_approach import *
#-------------------------------------------------------------------------------
#year_list = ['1999','2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010','2011','2012','2013','2014','2015','2016','2017','2018','2019','2020']
#year_list = ['2010','2011','2012','2013','2014','2015','2016','2017','2018','2019']

#year_list = ['2017','2018','2019']
#year_list = ['2016','2017','2018','2019']
#year_list = ['2015','2016','2017','2018','2019']
#year_list = ['2014','2015','2016','2017','2018','2019']
#year_list = ['2013','2014','2015','2016','2017','2018','2019']
#year_list = ['2012','2013','2014','2015','2016','2017','2018','2019']
#year_list = ['2011','2012','2013','2014','2015','2016','2017','2018','2019']
#year_list = ['2010','2011','2012','2013','2014','2015','2016','2017','2018','2019']

year_list = ['2016','2017','2018','2019']
flag_overlapping_TempCorrection = False
batch_size_overlapping = 6
#temp_correction_list=['direct_application','combined_yearly_prediction']
temp_correction_list=['combined_yearly_prediction']

print(sys.argv[0])#
print()
input_folder = sys.argv[1]     #we have stored monthly predections in a folder named by district name
if input_folder.split('/')[-1]=='':
	input_folder = input_folder[:-1]
district_name = input_folder.split('/')[-1]
if (district_name==""): #if user has put extra "/" at the end of input folder path.
	district_name = input_folder.split('/')[-2]

print('Name of Area/District - ',district_name)

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
	Overlapping_TempCorrection_execution(input_folder, district_name, year_list, temp_correction_list, batch_size_overlapping)
else:
	print("Temporal correction is being done for all years together.")
	for folder_name in temp_correction_list:
		TempCorrection(input_folder, district_name, year_list, folder_name)		

print('''
	-------------------------------------------------------
	Making temporal corrected predictions colorful for you!
	-------------------------------------------------------
	''')  
#-----------------------------------------------------
for folder_name in temp_correction_list:
	temp_coorected_folder_name = folder_name + '_temp_corrected'
	make_images_colorful(input_folder, temp_coorected_folder_name)


print('''
	-----------------------------------------------
	 Congratulations! We are done with everything.
	-----------------------------------------------
	''')
