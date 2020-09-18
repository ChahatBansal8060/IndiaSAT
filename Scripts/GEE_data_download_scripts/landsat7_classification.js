/**
 * Function to mask clouds based on the pixel_qa band of Landsat SR data.
 * @param {ee.Image} image Input Landsat SR image
 * @return {ee.Image} Cloudmasked Landsat image
 */
var cloudMaskL457 = function(image) {
  var qa = image.select('pixel_qa');
  // If the cloud bit (5) is set and the cloud confidence (7) is high
  // or the cloud shadow bit is set (3), then it's a bad pixel.
  var cloud = qa.bitwiseAnd(1 << 5)
                  .and(qa.bitwiseAnd(1 << 7))
                  .or(qa.bitwiseAnd(1 << 3));
  // Remove edge pixels that don't occur in all bands
  var mask2 = image.mask().reduce(ee.Reducer.min());
  return image.updateMask(cloud.not()).updateMask(mask2);
};


//var year_list = ['2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010']
// var year_list = ['1999','2000','2001','2002','2003','2004','2005','2006','2007','2008','2009','2010',
//                 '2011','2012','2013','2014','2015','2016','2017','2018','2019','2020'];
var year_list = ['2015','2016','2017','2018','2019','2020']
var month_list = ['year_median','1half','2half'];

//var aoi_list =['Chandigarh','Hyderabad','Mumbai','Gurgaon','Delhi','Chennai','Bangalore','Kolkata'];
//var aoi_list =['Bangalore','Bangalore Rural','Panchkula','Delhi','Faridabad'];
var aoi_list = ['Kolkata']


var bands = ['B1','B2', 'B3', 'B4', 'B5', 'B6','B7'];
var india = ee.FeatureCollection('users/hariomahlawat/India_Boundary')
    .geometry();


var india_image = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR')
    .filterBounds(india)
    .filterDate('2019-01-01','2019-12-31')
    .filter(ee.Filter.lt('CLOUD_COVER',1))
    .map(cloudMaskL457)
    .select(bands)
    ;

var india_image_training_median = india_image.median();
var india_image_training_min = india_image.min();
var india_image_training_max = india_image.max();
  


//Loading the training dataset and training the classifier
var ft = ee.FeatureCollection('users/hariomahlawat/IndiaSat');

function add_normalized_bands(image){
  var ndvi = image.normalizedDifference(['B4', 'B3']).rename('NDVI'); //vegetaion index
  var ndwi = image.normalizedDifference(['B2', 'B4']).rename('NDWI'); //water index
  var ndbi = image.normalizedDifference(['B5', 'B4']).rename('NDBI'); //water index
  return image.addBands(ndvi).addBands(ndwi).addBands(ndbi);
}

function add_all_bands(median_image, min_image, max_image){
  return median_image.select('B1','B2','B3','B4','B5','B6','B7','NDVI','NDWI','NDBI')
  .addBands(min_image.select('B1','B2','B3','NDVI','NDWI','NDBI'))
  .addBands(max_image.select('B1','B2','B3','NDVI','NDWI','NDBI'));
  
}
india_image_training_median = add_normalized_bands(india_image_training_median)
india_image_training_min = add_normalized_bands(india_image_training_min)
india_image_training_max = add_normalized_bands(india_image_training_max)

var india_image_training = add_all_bands(india_image_training_median,
                                          india_image_training_min,
                                          india_image_training_max);

// Training the RF model.

var new_bands = ['B1','B2','B3','B4','B5','B6','B7','NDVI','NDWI','NDBI',
                'B1_1','B2_1','B3_1','NDVI_1','NDWI_1',
                'B1_2','B2_2','B3_2','NDVI_2','NDWI_2'
                ];
                

var training = india_image_training.sampleRegions(ft,['class'],30);
var trained = ee.Classifier.randomForest().train(training, 'class', new_bands);

//--------------Running the classifier for Area of Interest-----------------------------------------------

for (var i in aoi_list) {
var aoi_name = aoi_list[i];
  for (var j in year_list)
  {
    for (var k in month_list)
    {  
      var year = year_list[j];
      var month = month_list[k]
      var start_month = month;
      var end_month = month;
      var start_date = '01';
      var end_date= '30';
      
      if (month == '1half')
      {
        start_month = '01';
        end_date = '30';
        end_month = '06';
        
        if (year == '1999')
        {
          start_month = '02';
        }
        else if (year == '2020')
        {
          end_month == '05'
        }
        
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
        if (year == '1999')
        {
          start_month = '02';
        } else if (year == '2020')
        {
          end_month == '05'
        }
        
      }
      else
      {
        start_month = month;
        end_date = '30';
        end_month = month;
      }
      
    
      
    var aoi = aoi_list[j];
    var aoi = ee.FeatureCollection('users/hariomahlawat/india_district_boundaries')
    .filter(ee.Filter.eq('Name',aoi_name));
    
    var aoi_image_sr = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR')
    .filterBounds(aoi)
    .filterDate(year + '-'+ start_month +'-'+ start_date,  year + '-'+ end_month +'-'+ end_date)
    .filter(ee.Filter.lt('CLOUD_COVER',10))
    .map(cloudMaskL457)
    .select(bands)
    ;  
   
    var aoi_image_median = aoi_image_sr.median();
    var aoi_image_min = aoi_image_sr.min();
    var aoi_image_mean = aoi_image_sr.mean();
    var aoi_image_max = aoi_image_sr.max();
    
   
   
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
    description: 'landsat7_'+str + '_' + year+misc,
    maxPixels: 1e9,
    scale: 30,
    folder: 'Landsat7_'+str,
    region: aoi.geometry().bounds()
    });
      
  }  
}
}
