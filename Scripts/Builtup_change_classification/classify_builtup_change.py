from PIL import Image
import numpy as np
import pandas as pd
import os, sys

# define color coding used in prediction images
Background = 0
Green = 1
Water = 2
Builtup = 3
Barrenland = 4

def Create_BU_NBU_Images(first_year_image_path, last_year_image_path, output_folder):
    first_image = np.array( Image.open(first_year_image_path) )
    last_image = np.array( Image.open(last_year_image_path) )

    #keep built-up pixels as it is i.e. BU with color code (1 * 65)
    first_image[ first_image == 3 ] = 65
    last_image[ last_image == 3 ] = 65
    # keep green, water, and barrenland pixels as non-built-up i.e. NBU with color code (2 x 65)
    first_image[ first_image == 1 ] = 130
    first_image[ first_image == 2 ] = 130
    first_image[ first_image == 4 ] = 130
    last_image[ last_image == 1 ] = 130
    last_image[ last_image == 2 ] = 130
    last_image[ last_image == 4 ] = 130

    first_image = ( Image.fromarray(first_image) ).convert("L")
    first_image.save( output_folder+'/first_year_bu_nbu.png' )

    last_image = ( Image.fromarray(last_image) ).convert("L")
    last_image.save( output_folder+'/last_year_bu_nbu.png' )

    print('''
    BU/NBU maps created for the first and last year
    ''')

    return output_folder+'/first_year_bu_nbu.png', output_folder+'/last_year_bu_nbu.png'
         
def Create_colored_change_maps(image_changing, chosen_output_folder):
    image_3d = np.zeros( [image_changing.shape[0], image_changing.shape[1],3], dtype=np.uint8 )
 
    for i in range(image_changing.shape[0]):
        for j in range(image_changing.shape[1]):
            if image_changing[i][j] == 195:
                image_3d[i][j] = [255,0,0]
            else:
                if image_changing[i][j] == 0: #background
                    image_3d[i][j] = [0,0,0]
                elif image_changing[i][j] == 65: #BU
                    image_3d[i][j] = [160,160,160]
                elif image_changing[i][j] == 130: #NBU
                    image_3d[i][j] = [0,255,0]                  

    image_3d = Image.fromarray(image_3d)
    image_3d.save(chosen_output_folder+'/Colored_CBU_CNBU_Changing.png')

    print('''
    Your CBU/CNBU/Changing maps are successfully color-coded!!
    Background (black), CBU (gray), CNBU (green), and Changing (red)
    ''')


def Create_change_maps(first_bu_nbu_image_path, last_bu_nbu_image_path, chosen_output_folder):
    first_bu_nbu_image = np.array( Image.open(first_bu_nbu_image_path) )
    last_bu_nbu_image = np.array( Image.open(last_bu_nbu_image_path) )

    image_changing = np.array( Image.open(first_bu_nbu_image_path) ) #initializing with base image

    for i in range(first_bu_nbu_image.shape[0]):
        for j in range(first_bu_nbu_image.shape[1]):
            if first_bu_nbu_image[i][j] == 130 and last_bu_nbu_image[i][j] == 65:
                image_changing[i][j] = 195
            else:
                image_changing[i][j] = first_bu_nbu_image[i][j]                  

    image_changing_array = Image.fromarray(image_changing)
    image_changing_array.save(chosen_output_folder+'/CBU_CNBU_Changing.png')
    Create_colored_change_maps(image_changing, chosen_output_folder)
    print('''
    Both Grayscale and Colored CBU/CNBU/Changing Maps Created!!
    ''')


######################################## main method #########################################################################
def main():
    input_folder = sys.argv[1]
    first_year = sys.argv[2]
    last_year = sys.argv[3] 

    if input_folder.split('/')[-1]=='':
        input_folder = input_folder[:-1]
        district_name = input_folder.split('/')[-1]
    else:
        district_name = input_folder.split('/')[-1]

    print('Name of Area/District - ',district_name)
    output_folder = 'Results/Builtup_change_classification_'+first_year+'_'+last_year+'/'+district_name
    os.makedirs(output_folder, exist_ok=True)

    choice = input(
        '''
        Please enter one of the following choices(1,2,3 or 4) :
        Enter 1 - For Change Classification of Direct LC Classification using Year Median Images
        Enter 2 - For Change Classification of Temporally Corrected Direct Classification
        Enter 3 - For Change Classification of Rule-based Combined Yearly Prediction
        Enter 4 - For Change Classification of Temporally Corrected Rule-based Combined Yearly Prediction
        ''') 
    if choice == '1':
        chosen_input_folder = input_folder + '/results/'+'direct_application'
        chosen_output_folder = output_folder+'/direct_application'

    elif choice == '2':
        chosen_input_folder = input_folder + '/results/'+'direct_application_temp_corrected'
        chosen_output_folder = output_folder+'/direct_application_temp_corrected'

    elif choice == '3':
        chosen_input_folder = input_folder + '/results/'+'combined_yearly_prediction'
        chosen_output_folder = output_folder+'/combined_yearly_prediction'

    elif choice =='4':
        chosen_input_folder = input_folder + '/results/'+'combined_yearly_prediction_temp_corrected'
        chosen_output_folder = output_folder+'/combined_yearly_prediction_temp_corrected'

    else:
        print('''
        	Wrong choice entered!
        	Please try again.
        	''')
        sys.exit("Wrong Input")	
	
    #Create output folder
    os.makedirs(chosen_output_folder, exist_ok=True)

    first_year_image_path = chosen_input_folder+'/'+district_name+'_prediction_'+first_year+'.png'
    last_year_image_path = chosen_input_folder+'/'+district_name+'_prediction_'+last_year+'.png'
    first_bu_nbu_image_path, last_bu_nbu_image_path = Create_BU_NBU_Images(first_year_image_path, last_year_image_path, chosen_output_folder)

    Create_change_maps(first_bu_nbu_image_path, last_bu_nbu_image_path, chosen_output_folder)

if __name__ == '__main__':
	main()
