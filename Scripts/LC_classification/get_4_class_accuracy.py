from osgeo import gdal
import numpy as np
from PIL import Image
import json
import rasterio
from rasterio.mask import mask
from json import loads
import os, sys
from os import listdir, path
from os.path import isfile, join
import shutil
from groundtruth_preprocessing import *
import kml2geojson


#######################################################################################################################
'''
Method to convert .png into .tif files
.tiff files need to have WGS84 coordinate system
'''
def CovertPNGtoTIFF(mainFolder, inputFolder, year):
	# load GDAL (Geospatial Data Abstraction Library) driver for tiff files
	driver = gdal.GetDriverByName('GTiff')
	# Get one tif file of this district for reference. This can be the initial tif files downloaded from GEE 
	for infile in os.listdir(mainFolder+'/'+year):
		if (infile[-4:] == ".tif"):
			filepath = mainFolder+"/"+year+"/"+infile
			#print(filepath)
			break
	reference_image = gdal.Open(filepath)
	#1 because we have information in a single band (prediction classes) 
	pixel_predictions = (reference_image.GetRasterBand(1)).ReadAsArray()
	[cols, rows] = pixel_predictions.shape
	#print("Rows: ",rows," Cols: ",cols)
	path_for_final_prediction_pngs = inputFolder
	#print(path_for_final_prediction_pngs)
	#print(os.getcwd())
	os.makedirs(path_for_final_prediction_pngs+'/tifs',exist_ok=True)

	for infile in os.listdir(path_for_final_prediction_pngs):
		#print(infile)
		if infile[-4:] == ".png":
			#print(infile)

			pngImage = np.array( Image.open( path_for_final_prediction_pngs+'/'+infile ))
			#print("The unique labels in png image are: ", np.unique(pngImage) )
			#print("The shape of png image is: ", pngImage.shape )
            
			destination_filename = path_for_final_prediction_pngs+'/tifs/'+infile[:-4]+'.tif'
            
            #Setting the structure for the destination tif file
			dst_ds = driver.Create(destination_filename, rows, cols, 1, gdal.GDT_UInt16)
			dst_ds.SetGeoTransform(reference_image.GetGeoTransform())
			dst_ds.SetProjection(reference_image.GetProjection())
			dst_ds.GetRasterBand(1).WriteArray(pngImage)
			dst_ds.FlushCache()
            
            ##Checking the validity of created tif file
			# tiffImage = np.asarray( Image.open(destination_filename) )
			# print("The unique labels in png image are: ", np.unique(tiffImage) )
			# print("The shape of png image is: ", tiffImage.shape )


##############################################################################################################################
'''
Method to crop groundtruth polygons out of prediction tiffiles
'''
def CutTifffile(folder_tifffiles, folder_groundtruth_shapefiles, year):
    print("In cutfiles folder for tiffiles= ",folder_tifffiles)
    print("In cutfiles folder for groundtruth= ",folder_groundtruth_shapefiles)
    
    for infile in listdir(folder_tifffiles):
        if year in infile:
            tiff_file_name = infile

    i = 0
    for shapefile in listdir(folder_groundtruth_shapefiles):
        if shapefile[-3:]=='kml':
            #print(shapefile)

            kml2geojson.main.convert(folder_groundtruth_shapefiles+'/'+shapefile, folder_groundtruth_shapefiles)
            
            json_filepath = folder_groundtruth_shapefiles+'/'+shapefile[:-3]+'geojson'

            json_data = json.loads(open(json_filepath).read())
            #print(json_data)
            output_directory = folder_tifffiles+'/'+shapefile[:-4]	
            os.makedirs(output_directory, exist_ok=True)
           
            for currFeature in json_data["features"]:
                #print(currFeature)
                i += 1
                try:
                    geoms = [currFeature["geometry"]]
                    #print(geoms)
                    with rasterio.open(folder_tifffiles+'/'+tiff_file_name) as src:
                        #print(src)
                        out_image, out_transform = mask(src, geoms, crop = True)
                        out_meta = src.meta
                        # save the resulting raster
                        out_meta.update({ "driver": "GTiff", "height": out_image.shape[1], "width": out_image.shape[2], "transform": out_transform})
                        saveFileName = output_directory+"/"+str(i)+".tif"
                        with rasterio.open(saveFileName, "w", **out_meta) as dest:
                            dest.write(out_image)
                except:
                    continue

    landcover_classes = ['Greenery','Water','Builtup','Barrenland']
    i = 0
    for cat in landcover_classes:	
        for infile in os.listdir(folder_tifffiles+'/'+cat):
            i=i+1
            if infile[-4:] == ".tif":
                os.makedirs(folder_tifffiles+"/4cat/"+cat,exist_ok=True)
                shutil.copy(folder_tifffiles+'/'+cat+'/'+infile, folder_tifffiles+"/4cat/"+cat+"/"+str(i)+'_'+infile)




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
	# specifying integer code of land cover classes
	green = 1
	water = 2
	builtup = 3
	barrenland = 4
	landcover_classes = ['Greenery','Water','Builtup','Barrenland']
	confusion_matrix = []
	for landcover in landcover_classes:
		landcover_predicted_class_count = [0, 0, 0, 0] # [bu, nbu (Greenery + Water + Barrenland)]

		tif_files_path = cropped_images_folder+'/'+landcover
		for tif_file in os.listdir(tif_files_path):
			tif_image = np.asarray(Image.open(tif_files_path+'/'+tif_file))
			if green in np.unique(tif_image, return_counts=True)[0]:
				landcover_predicted_class_count[0] += np.unique(tif_image, return_counts=True)[1][np.where(np.unique(tif_image,return_counts=True)[0]==green)[0][0]]
			if water in np.unique(tif_image, return_counts=True)[0]:
				landcover_predicted_class_count[1] += np.unique(tif_image, return_counts=True)[1][np.where(np.unique(tif_image,return_counts=True)[0]==water)[0][0]]
			if builtup in np.unique(tif_image, return_counts=True)[0]:
				landcover_predicted_class_count[2] += np.unique(tif_image, return_counts=True)[1][np.where(np.unique(tif_image,return_counts=True)[0]==builtup)[0][0]]
			if barrenland in np.unique(tif_image, return_counts=True)[0]:
				landcover_predicted_class_count[3] += np.unique(tif_image, return_counts=True)[1][np.where(np.unique(tif_image,return_counts=True)[0]==barrenland)[0][0]]
		confusion_matrix.append(landcover_predicted_class_count)
	cm = np.array(confusion_matrix)

	write_to_file(text_file,'Confusion Matrix (Greenery, Waterbody, Builtup, Barrenland): \n')
	write_listoflist_to_file(text_file,confusion_matrix)

	print("Confusion Matrix (Greenery, Waterbody, Builtup, Barrenland): \n",confusion_matrix,"\n")		

	print("label precision  recall avg_precision avg_recall")
	write_to_file(text_file,'label precision recall avg_precision avg_recall')
	for label in range(len(landcover_classes)):
		s = f"{label:5d} {precision(label, cm):9.3f}  {recall(label, cm):6.3f}   {precision_macro_average(cm):6.3f}      {recall_macro_average(cm):6.3f}"
		write_to_file(text_file,s)
		print(s)


						
######################################## main method #########################################################################
def main():
    input_folder = sys.argv[1]     #input folder path with final predictions in a folder named by district
    folder_groundtruth_shapefiles = sys.argv[2]
    year = sys.argv[3]
    
    if input_folder.split('/')[-1]=='':
        input_folder = input_folder[:-1]
        district_name = input_folder.split('/')[-1]
    else:
        district_name = input_folder.split('/')[-1]

    print('Name of Area/District - ',district_name)
    folder_groundtruth_shapefiles = folder_groundtruth_shapefiles+district_name

    if path.isdir(folder_groundtruth_shapefiles) == False:
        print("OOPS!! Looks like you don't have groundtruth for this district!! Can't compute accuracy for this!")
        sys.exit()

    choice = input(
        '''
        Please enter one of the following choices(1,2,3 or 4) :
        Enter 1 - For Direct Classification using Year Median Images
        Enter 2 - For Temporally Corrected Direct Classification
        Enter 3 - For Rule-based Combined Yearly Prediction
        Enter 4 - For Temporally Corrected Rule-based Combined Yearly Prediction
        ''') 
    if choice == '1':
        chosen_folder = input_folder + '/results/'+'direct_application'
        heading = '''
        ----------------------------------------------
        Direct Classification using Year Median Images
        ----------------------------------------------
        '''
    elif choice == '2':
        chosen_folder = input_folder + '/results/'+'direct_application_temp_corrected'
        heading = '''
        ------------------------------------------
        Temporally Corrected Direct Classification
        ------------------------------------------
        '''
    elif choice == '3':
        chosen_folder = input_folder + '/results/'+'combined_yearly_prediction'
        heading = '''
        -------------------------------------
        Rule-based Combined Yearly Prediction
        -------------------------------------
        '''
    elif choice =='4':
        chosen_folder = input_folder + '/results/'+'combined_yearly_prediction_temp_corrected'
        heading = '''
        -----------------------------------------------------------
         Temporally Corrected Rule-based Combined Yearly Prediction
        -----------------------------------------------------------
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
    CovertPNGtoTIFF(input_folder, chosen_folder, year)

    print('''
        Step2 - Cut district/area .tif files(classification) using groundtruth shapefiles.
        ''')
    folder_tifffiles = chosen_folder + '/tifs'
    # print("Folder path with tiffiles: ",folder_tifffiles)
    # print("Folder path for groundtruth: ",folder_groundtruth_shapefiles)

    CutTifffile(folder_tifffiles, folder_groundtruth_shapefiles, year)

    print('''
        Step3 - Calulate accuracy for all classes.
        ''')

    # Name of the containing folder of cropped_images where the cropped tif files of predictions are stored
    cropped_images_folder = chosen_folder + '/tifs/4cat'
    accuracy_result_folder = 'Results/Classification_4cat_Accuracy_'+year
    os.makedirs(accuracy_result_folder, exist_ok=True)

    text_file_path = accuracy_result_folder+'/'+district_name+'_accuracy_4cat.txt'
    text_file_heading = "District - " + district_name
    write_to_file(text_file_path,text_file_heading) 
    write_to_file(text_file_path,heading)

    groundtruth_preprocessing(cropped_images_folder)
    ComputeAccuracy(cropped_images_folder+'_cropped',text_file_path)


if __name__ == '__main__':
	main()


