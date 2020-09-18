import sys,os
from os import listdir
from os.path import isfile, join
import numpy as np
from PIL import Image
import statistics 
import math
import shutil

# method to calculate total images, total no of pixels, mean and median of image size for each category
def image_statistics(input_folder):
	x = []
	y = []
	total_pixels = 0
	total_images = 0
	for tif in os.listdir(input_folder):
		total_images += 1
		tif_image_path = input_folder + '/' + tif
		tif_image = np.asarray(Image.open(tif_image_path))
		image_size_x = tif_image.shape[0]
		image_size_y = tif_image.shape[1]
		x.append(image_size_x)
		y.append(image_size_y)
		for i in range(image_size_x):
			for j in range(image_size_y):
				if tif_image[i][j] != 0:
					total_pixels += 1
	x_mean = statistics.mean(x)
	y_mean = statistics.mean(y)
	x_median = statistics.median(x)
	y_median = statistics.median(y)	
	return total_pixels, total_images, x_mean, y_mean, x_median, y_median

# method to calculate crop dimensions
def crop_dimensions(image_statistics_dict):
	print('''
		--------- Original Groundtruth Statistics-----------
		''')
	print('Category -> ','total_pixels | ', 'total_images | ', 'x_mean | ', 'y_mean | ', 'x_median | ', 'y_median | ')
	for key,value in image_statistics_dict.items():
		print(key, '->', value)
 
	temp = min(image_statistics_dict.values()) 
	min_cat = [key for key in image_statistics_dict if image_statistics_dict[key] == temp] 	
	min_cat = min_cat[0]
	min_cat_pixels = image_statistics_dict[min_cat][0]
	min_cat_x_mean = int(image_statistics_dict[min_cat][2])
	min_cat_y_mean = int(image_statistics_dict[min_cat][3])

	crop_size = {}
	for key,value in image_statistics_dict.items():
		if key != min_cat:
			xy = int(math.sqrt((min_cat_pixels)/(image_statistics_dict[key][1]))) + 2
			crop_size[key]=xy

	return crop_size, min_cat		
	print(min_cat_pixels, min_cat_x_mean, min_cat_y_mean)

def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))

# methos to crop the images
def crop_images(input_folder, output_folder, crop_size):
 

	if not os.path.exists(output_folder): os.makedirs(output_folder)

	onlyfiles = [f for f in listdir(input_folder) if isfile(join(input_folder, f))]


	for currImageName in onlyfiles:
		# currImageName='Landsat7_MedianAndhraPradesh_2011-0000000000-0000000000@80200@569751.png'
		path_currImageName = input_folder + '/' + currImageName
		out_image = currImageName
		path_out_image = output_folder + '/' + out_image
		im = Image.open(path_currImageName)
		im_new = crop_center(im, crop_size, crop_size)
		im_new.save(path_out_image, quality=100)

# main method
def groundtruth_preprocessing(tif_folder_path):
	#tif_folder_path = sys.argv[1]
	if tif_folder_path.split('/')[-1]=='':
		tif_folder_path = tif_folder_path[:-1]

	categories = [os.path.join(tif_folder_path, sub_dir) for sub_dir in os.listdir(tif_folder_path) 
		if os.path.isdir(os.path.join(tif_folder_path,sub_dir))]
	
	image_stats = {}
	for cat in categories:
		#print(cat)
		category_name = cat.split('/')[-1]
		#print(category_name)
		image_stats[category_name] = image_statistics(cat)

	crop_size, min_cat = crop_dimensions(image_stats)

	print('''
		------- calculated crop size----------------
		''')
	for key, value in crop_size.items():
		print(key, '->', value)
		input_folder = tif_folder_path + '/'+key	
		output_folder = tif_folder_path +'_cropped' + '/'+key
		crop_images(input_folder,output_folder, value)	

	for infile in os.listdir(tif_folder_path+'/'+min_cat):
		if infile[-4:] == ".tif":
			os.makedirs(tif_folder_path+"_cropped/"+min_cat,exist_ok=True)
			source_folder = tif_folder_path+'/'+min_cat
			dest_folder = tif_folder_path+'_cropped/'+min_cat
			shutil.copy(source_folder+'/'+infile, dest_folder+'/'+infile)


	cropped_tifs = 	[os.path.join(tif_folder_path+'_cropped', sub_dir) for sub_dir in os.listdir(tif_folder_path+'_cropped') 
		if os.path.isdir(os.path.join(tif_folder_path+'_cropped',sub_dir))]

	image_stats_cropped = {}
	for cat in cropped_tifs:
		category_name = cat.split('/')[-1]
		image_stats_cropped[category_name] = image_statistics(cat)	
	
	print('''
		---------- Crpped groundtrth Statistices-------------- 
		''')
	print('Category -> ', 'total_pixels | ', 'total_images | ', 'x_mean | ', 'y_mean | ', 'x_median | ', 'y_median | ')

	for key,value in image_stats_cropped.items():
		print(key, '->', value)
			

# if __name__ == '__main__':
# 		main()	