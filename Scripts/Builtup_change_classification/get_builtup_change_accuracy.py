from osgeo import gdal
import imageio
import numpy as np
from PIL import Image
import json
import rasterio
from rasterio.mask import mask
from json import loads
import os, sys
from os import listdir
from os.path import isfile, join
import shutil
import kml2geojson
from groundtruth_preprocessing import *


#######################################################################################################################
'''
Method to convert .png into .tif files
.tiff files need to have WGS84 coordinate system
'''
def CovertPNGtoTIFF(reference_tiffile_path, inputFolder, file_name):
	# load GDAL (Geospatial Data Abstraction Library) driver for tiff files
	driver = gdal.GetDriverByName('GTiff')
	# Get one tif file of this district for reference. This can be the initial tif files downloaded from GEE 
	reference_image = gdal.Open(reference_tiffile_path)
	#1 because we have information in a single band (prediction classes) 
	pixel_predictions = (reference_image.GetRasterBand(1)).ReadAsArray()
	[cols, rows] = pixel_predictions.shape
	
	path_for_final_prediction_pngs = inputFolder
	os.makedirs(path_for_final_prediction_pngs+'/tifs', exist_ok=True)

	pngImage = np.array( Image.open( path_for_final_prediction_pngs+'/'+file_name ))
	destination_filename = path_for_final_prediction_pngs+'/tifs/'+file_name[:-4]+'.tif'
	
	#Setting the structure for the destination tif file
	dst_ds = driver.Create(destination_filename, rows, cols, 1, gdal.GDT_UInt16)
	dst_ds.SetGeoTransform(reference_image.GetGeoTransform())
	dst_ds.SetProjection(reference_image.GetProjection())
	dst_ds.GetRasterBand(1).WriteArray(pngImage)
	dst_ds.FlushCache()


#####################################################################################################
def CutTifffile(folder_tifffiles, folder_groundtruth_shapefiles, tiffile_name):
    final_output_directory = folder_tifffiles+'/Trimmed_tiffiles'
    for shapefile in listdir(folder_groundtruth_shapefiles):
        if shapefile[-3:] == 'kml':
            kml2geojson.main.convert(folder_groundtruth_shapefiles+'/'+shapefile, folder_groundtruth_shapefiles)
            
            json_filepath = folder_groundtruth_shapefiles+'/'+shapefile[:-3]+'geojson'
            json_data = json.loads( open(json_filepath).read() )
            
            output_directory = final_output_directory+'/'+shapefile[:-4]
            os.makedirs(output_directory, exist_ok=True)
            
            i = 0            
            for currFeature in json_data["features"]:
                i += 1
                try:
                    geoms = [currFeature["geometry"]]

                    with rasterio.open(folder_tifffiles+'/'+tiffile_name) as src:
                        out_image, out_transform = mask(src, geoms, crop = True)
                        out_meta = src.meta

                        # save the resulting raster
                        out_meta.update({ "driver": "GTiff", "height": out_image.shape[1], "width": out_image.shape[2], "transform": out_transform})

                        saveFileName = output_directory+"/"+str(i)+".tif"
                        with rasterio.open(saveFileName, "w", **out_meta) as dest:
                            dest.write(out_image)
                except:
                    continue
    return final_output_directory
    

######################################################Methods for calculating Accuracy##############################################
def precision(label, confusion_matrix):
	col = confusion_matrix[:, label]
	return (confusion_matrix[label, label] / col.sum())*100
    
def recall(label, confusion_matrix):
	row = confusion_matrix[label, :]
	return (confusion_matrix[label, label] / row.sum())*100

def precision_macro_average(confusion_matrix):
	rows, columns = confusion_matrix.shape
	sum_of_precisions = 0
	for label in range(rows):
		sum_of_precisions += precision(label, confusion_matrix)
	return sum_of_precisions / rows

def recall_macro_average(confusion_matrix):
	rows, columns = confusion_matrix.shape
	sum_of_recalls = 0
	for label in range(columns):
		sum_of_recalls += recall(label, confusion_matrix)
	return sum_of_recalls / columns

def write_to_file(file_name, text_to_append):
	"""Append given text as a new line at the end of file"""
	# Open the file in append & read mode ('a+')
	with open(file_name, "a+") as file_object:
		# Move read cursor to the start of file.
		file_object.seek(0)
		# If file is not empty then append '\n'
		data = file_object.read(100)
		if len(data) > 0:
			file_object.write("\n")
		# Append text at the end of file
		file_object.write(text_to_append)

def write_listoflist_to_file(file_name,input_list):
	with open(file_name, 'a+') as f:
		for _list in input_list:
			for _string in _list:
				#f.seek(0)
				f.write(str(_string) + ', ')
			f.write('\n')	


def ComputeAccuracy(cropped_images_folder, text_file):
	# specifying integer code of change classification classes
	CBU = 65
	CNBU = 130
	Changing = 195 
	# green = 1
	# water = 2
	# builtup = 3
	# barrenland = 4
	landcover_classes = ['CBU','CNBU','Changing']
	confusion_matrix = []
	for landcover in landcover_classes:
		landcover_predicted_class_count = [0, 0, 0]

		tif_files_path = cropped_images_folder+'/'+landcover
		for tif_file in os.listdir(tif_files_path):
			tif_image = np.asarray(Image.open(tif_files_path+'/'+tif_file))
			if CBU in np.unique(tif_image, return_counts=True)[0]:
				landcover_predicted_class_count[0] += np.unique(tif_image, return_counts=True)[1][np.where(np.unique(tif_image,return_counts=True)[0]==CBU)[0][0]]
			if CNBU in np.unique(tif_image, return_counts=True)[0]:
				landcover_predicted_class_count[1] += np.unique(tif_image, return_counts=True)[1][np.where(np.unique(tif_image,return_counts=True)[0]==CNBU)[0][0]]
			if Changing in np.unique(tif_image, return_counts=True)[0]:
				landcover_predicted_class_count[2] += np.unique(tif_image, return_counts=True)[1][np.where(np.unique(tif_image,return_counts=True)[0]==Changing)[0][0]]
		confusion_matrix.append(landcover_predicted_class_count)
	cm = np.array(confusion_matrix)

	write_to_file(text_file,'Confusion Matrix (CBU, CNBU, Changing): \n')
	write_listoflist_to_file(text_file,confusion_matrix)

	print("Confusion Matrix (CBU, CNBU, Changing): \n",confusion_matrix,"\n")		

	print("label precision  recall avg_precision avg_recall")
	write_to_file(text_file,'label precision recall avg_precision avg_recall')
	for label in range(3):
		s = f"{label:5d} {precision(label, cm):9.3f}  {recall(label, cm):6.3f}   {precision_macro_average(cm):6.3f}      {recall_macro_average(cm):6.3f}"
		write_to_file(text_file,s)
		print(s)



						
######################################## main method #########################################################################
def main():
	input_folder = sys.argv[1]     #path of CBU/CNBU/Changing prediction map
	folder_groundtruth_shapefiles = sys.argv[2]
	reference_tiffile_path = sys.argv[3]

	if input_folder.split('/')[-1]=='':
		input_folder = input_folder[:-1]
		district_name = input_folder.split('/')[-1]
	else:
		district_name = input_folder.split('/')[-1]

	print('Name of Area/District - ',district_name)

	choice = input(
		'''
		Please enter one of the following choices(1,2,3 or 4) :
		Enter 1 - For Change Classification of Direct LC Classification using Year Median Images
        Enter 2 - For Change Classification of Temporally Corrected Direct Classification
        Enter 3 - For Change Classification of Rule-based Combined Yearly Prediction
        Enter 4 - For Change Classification of Temporally Corrected Rule-based Combined Yearly Prediction
		''') 
	if choice == '1':
		chosen_folder = input_folder + '/direct_application'
		heading = '''
		--------------------------------------------------------------------------
		Change Classification of Direct LC Classification using Year Median Images
		--------------------------------------------------------------------------
		'''
	elif choice == '2':
		chosen_folder = input_folder + '/direct_application_temp_corrected'
		heading = '''
		-------------------------------------------------------------------
		Change Classification of Temporally Corrected Direct Classification
		-------------------------------------------------------------------
		'''
	elif choice == '3':
		chosen_folder = input_folder + '/combined_yearly_prediction'
		heading = '''
		--------------------------------------------------------------
		Change Classification of Rule-based Combined Yearly Prediction
		--------------------------------------------------------------
		'''
	elif choice =='4':
		chosen_folder = input_folder + '/combined_yearly_prediction_temp_corrected'
		heading = '''
		-----------------------------------------------------------------------------------
		Change Classification of Temporally Corrected Rule-based Combined Yearly Prediction
		-----------------------------------------------------------------------------------
		'''
	else:
		print('''
			Wrong choice entered!
			Please try again.
			''')
		sys.exit("Wrong Input")	

	print ('''
		Step1 - Converting png files into tif files with WGS84 coordinated system
		''')
	
	chosen_file_name = 'CBU_CNBU_Changing.png'
	CovertPNGtoTIFF(reference_tiffile_path, chosen_folder, chosen_file_name)

	print('''
		Step2 - Cut district/area .tif files(classification) using groundtruth shapefiles.
		''')
	folder_tifffiles = chosen_folder + '/tifs'
	tiffile_name = 'CBU_CNBU_Changing.tif'
	cropped_images_folder = CutTifffile(folder_tifffiles, folder_groundtruth_shapefiles, tiffile_name)

	print('''
		Step3 - Calulate accuracy for all classes.
		''')

	# Folder name containing cropped tiffiles of prediction map
	
	# cropped_images_folder=chosen_folder + '/tifs/2cat'
	accuracy_result_file_folder = 'Results/CBU_CNBU_Changing_Accuracy_2016_2019'
	os.makedirs(accuracy_result_file_folder, exist_ok=True)
	text_file_path = accuracy_result_file_folder+'/'+district_name+'_accuracy_cbu_cnbu_changing.txt'
	
	# input_folder+'/'+district_name+'_accuracy_2cat.txt'
	text_file_heading = "CBU/CNBU/Changing Accuracy for District- " + district_name
	write_to_file(text_file_path, text_file_heading) 
	write_to_file(text_file_path, heading)
	groundtruth_preprocessing(cropped_images_folder)
	ComputeAccuracy(cropped_images_folder+'_cropped',text_file_path)





if __name__ == '__main__':
	main()


