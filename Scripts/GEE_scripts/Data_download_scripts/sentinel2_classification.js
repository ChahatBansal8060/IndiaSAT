// Input imagery is a cloud-free Sentinel .
function maskS2clouds(image) {
  var qa = image.select('QA60');

 // Bits 10 and 11 are clouds and cirrus, respectively.
 var cloudBitMask = 1 << 10;
 var cirrusBitMask = 1 << 11;

 // Both flags should be set to zero, indicating clear conditions.
 var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
    .and(qa.bitwiseAnd(cirrusBitMask).eq(0));

 return image.updateMask(mask);
}

//-------------------------------------------------------------------------


var year_list = ['2015','2016','2017','2018','2019','2020'];

var month_list = ['1half','2half','year_median'];

var aoi_list =['Hyderabad','Gurgaon','Mumbai','Chandigarh','Delhi'];

var bands = ['B1','B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8','B9', 'B10', 'B11','B12','B8A'];

//var bands = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11','B12','B8A']; // resolution 10 and 20 mtr
//var bands = ['B2', 'B3', 'B4'];

var india = ee.FeatureCollection('users/chahatresearch/India_Boundary')
    .geometry();

var india_image = ee.ImageCollection('COPERNICUS/S2') // searches all sentinel 2 imagery pixels...
  .filterBounds(india)
  .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 1)) // ...filters on the metadata for pixels less than 10% cloud
  .filterDate('2019-01-1' ,'2019-05-30') //... chooses only pixels between the dates you define here
  .sort('CLOUD_COVER')
  .map(maskS2clouds)
  .select(bands)  

//print(india_image);   
var india_image_training_median = india_image.median();
var india_image_training_min = india_image.min();
var india_image_training_max = india_image.max();

//Loading the training dataset
var ft = ee.FeatureCollection('users/chahatresearch/IndiaSat');


function add_normalized_bands(image){
  var ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI'); //vegetaion index
  var ndwi = image.normalizedDifference(['B8', 'B12']).rename('NDWI'); //water index
  var ndbi = image.normalizedDifference(['B11', 'B8']).rename('NDBI'); //built-up index
  //var ndmi = image.normalizedDifference(['B8', 'B11']).rename('NDMI'); //moisture index
  return image.addBands(ndvi).addBands(ndwi).addBands(ndbi);
}

function add_all_bands(median_image, min_image, max_image){
  return median_image.select('B1','B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8','B9', 'B10', 'B11','B12','B8A','NDVI','NDWI','NDBI')
  .addBands(min_image.select('B2','B3','B4','NDVI','NDWI','NDBI'))
  .addBands(max_image.select('B2','B3','B4','NDVI','NDWI','NDBI'));
  
}
india_image_training_median = add_normalized_bands(india_image_training_median)
india_image_training_min = add_normalized_bands(india_image_training_min)
india_image_training_max = add_normalized_bands(india_image_training_max)

var india_image_training = add_all_bands(india_image_training_median,
                                          india_image_training_min,
                                          india_image_training_max);

// Training the RF model.

var new_bands = ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11','B12','B8A','NDVI','NDWI','NDBI',
                'B2_1','B3_1','B4_1', 'NDVI_1','NDWI_1',
                'B2_2','B3_2','B4_2','NDVI_2','NDWI_2'
                ];


var training = india_image_training.sampleRegions(ft,['class'],30);
var trained = ee.Classifier.randomForest(100).train(training, 'class', new_bands);



//--------------Running the classifier for Area of Interest-----------------------------------------------

for (var i in aoi_list) {
var aoi_name = aoi_list[i];
  for (var j in year_list)
  {
    for (var k in month_list)
    {  
      var month = month_list[k]
      var start_month;
      var end_month;
      var start_date = '01';
      var end_date;
      
      if (month == '1half')
      {
        start_month = '01';
        end_date = '30';
        end_month = '06';
      }
      else if (month == '2half')
      {
        start_month = '07';
        end_date = '31';
        end_month = '12';
      }
      
      else if (month == 'year_median')
      {
        start_month = '01';
        end_date = '31';
        end_month = '12';
        
      }
      else
      {
        start_month = month;
        end_date = '30';
        end_month = month;
      }
      
    var year = year_list[j];
      
    var aoi = aoi_list[j];
    var aoi = ee.FeatureCollection('users/chahatresearch/india_district_boundaries')
    .filter(ee.Filter.eq('Name',aoi_name));
 
      var aoi_image_toa = ee.ImageCollection('COPERNICUS/S2')
      .filterBounds(aoi)
      .filterDate(year + '-'+ start_month +'-'+ start_date,  year + '-'+ end_month +'-'+ end_date)
      .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))
      .sort('CLOUD_COVER')
      .map(maskS2clouds)
      .select(bands);
     
   
    var aoi_image_median = aoi_image_toa.median();
    var aoi_image_min = aoi_image_toa.min();
    var aoi_image_max = aoi_image_toa.max();
    
   
   
    aoi_image_median = add_normalized_bands(aoi_image_median)
    aoi_image_min = add_normalized_bands(aoi_image_min)
    aoi_image_max = add_normalized_bands(aoi_image_max)
    
    var aoi_image = add_all_bands(aoi_image_median,
                                  aoi_image_min,
                                  aoi_image_max)
   
   
    print(aoi_name + ' - ' + year);
    print(aoi_image);
    
    var input = aoi_image;
    input = input.clip(aoi);
    input = input.classify(trained);
    input = input.expression('LC',{'LC':input.select('classification')});
   
    var str = aoi_name.replace(/\s/g,'');	//remove spaces in the aoi name for naming the downloaded image
    var misc = '_'+month 
      
    Export.image.toDrive({
    image: input.clip(aoi),
    description: 'sentinel2a_'+str+'_'+year+misc,
    maxPixels: 1e9,
    scale: 30,
    folder: 'Sentinel2a_'+str,
    region: aoi.geometry().bounds()
    });
      
  }  
}
}
