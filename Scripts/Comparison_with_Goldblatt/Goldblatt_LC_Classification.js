var cloud_masks = require('users/fitoprincipe/geetools:cloud_masks');
var maskClouds = cloud_masks.landsatTOA();

var year_list = ['2014','2015','2016','2017','2018','2019'];
var district_list =['Delhi','Mumbai','Kolkata','Chennai','Hyderabad','Chandigarh','Bangalore'];

//Loading India image, the extracting data for Haryana (a state in India) and then subsequently Ambala (a district in Haryana)
var bands = ['B1','B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B10', 'B11'];
var india = ee.FeatureCollection('users/mtpictd/world_boundary')
    .filter(ee.Filter.eq('Name','India'))
    .geometry();
print(india);
var india_image = ee.ImageCollection('LANDSAT/LC08/C01/T1_TOA')
    .filterBounds(india)
    .filterDate('2014-03-01','2014-09-01')
    .filter(ee.Filter.lt('CLOUD_COVER',5))
    .sort('CLOUD_COVER')
    // .limit(500)
    .map(maskClouds)
    .median();
print(india_image);    
//india_image = addBands(india_image);

//Loading the points from the fusion table and training the classifier
var ft = ee.FeatureCollection('users/mtpictd/goldblatt_2');
var ft_builtup = ft.filter(ee.Filter.eq('class_int2',1));
print(ft_builtup);
var ft_nonbuiltup = ft.filter(ee.Filter.eq('class_int2',2));
print(ft_nonbuiltup);
ft = ft_builtup.merge(ft_nonbuiltup);
var new_bands = ['B1','B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B10', 'B11'];//,'NDVI','NDBI'];
// function addBands(image){
//   var ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI');
//   var ndbi = image.normalizedDifference(['B6', 'B5']).rename('NDBI');
//   //var ndwi = image.normalizedDifference(['B6', 'B6']).rename('NDWI');
//   return image.addBands(ndvi).addBands(ndbi);
// }

// Load a Landsat 8 image to be used for prediction.
var training = india_image.sampleRegions(ft,['class_int2'],30);
var trained = ee.Classifier.randomForest(10).train(training, 'class_int2', new_bands);


for (var i in district_list) {
  var district_name = district_list[i];
  print(district_name);
  for (var j in year_list)
  {
    var year = year_list[j];
    var district = ee.FeatureCollection('users/mtpictd/ind_Adm2_edited_InUse')
    .filter(ee.Filter.eq('Name',district_name));
    print(district);
    var district_image = ee.ImageCollection('LANDSAT/LC08/C01/T1_TOA')
    .filterBounds(district)
    .filterDate(year + '-03-01',year + '-09-01')
    .filter(ee.Filter.lt('CLOUD_COVER',5))
    .sort('CLOUD_COVER')
    .map(maskClouds)
    .median();  
   
    print(district_image);
    var input = district_image;
    //input.select(bands);  //to check if image is present
    //input = addBands(input.select(bands));
    input = input.clip(district);
    input = input.classify(trained);
    input = input.expression('LC==1?1:2',{'LC':input.select('classification')});
   
    var str = district_name.replace(/\s/g,'');
   
    Export.image.toDrive({
  image: input.clip(district),
  description: str + '_' + year,
  maxPixels: 499295920080,
  scale: 30,
  folder: 'testing',
  region: district.geometry().bounds()
});
  }
 
}


