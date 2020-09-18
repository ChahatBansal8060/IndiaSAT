var cloud_masks = require('users/fitoprincipe/geetools:cloud_masks');
var maskClouds = cloud_masks.landsatTOA();


// Use these bands for prediction.
//var bands = ['B2', 'B3', 'B4'];
var bands = ['B1','B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B10', 'B11'];

//boundary for India
// Make sure that India_Boundary shapefiles are uploaded as assets in GEE and then change the path of that asset accordingly.
var india = ee.FeatureCollection('users/chahatresearch/India_Boundary')
    .geometry();

var india_image = ee.ImageCollection('LANDSAT/LC08/C01/T1_TOA')
    .filterBounds(india)
    .filterDate('2019-01-01','2019-12-31')
    .filter(ee.Filter.lt('CLOUD_COVER',1))
    .sort('CLOUD_COVER')
    // .limit(500)
    .map(maskClouds)
    .select(bands)
    ;

var india_image_training_median = india_image.median();
var india_image_training_mean = india_image.mean();
var india_image_training_min = india_image.min();
var india_image_training_max = india_image.max();

//Training feature collection. Imported from assets (Its a shapefile)
var ft = ee.FeatureCollection('users/chahatresearch/IndiaSat');

function add_normalized_bands(image){
  var ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI'); //vegetaion index
  var ndmi = image.normalizedDifference(['B5', 'B6']).rename('NDMI'); //moisture index
  var ndwi = image.normalizedDifference(['B3', 'B6']).rename('NDWI'); //water index
  var ndbi = image.normalizedDifference(['B6', 'B5']).rename('NDBI'); //water index
  return image.addBands(ndvi).addBands(ndwi).addBands(ndbi).addBands(ndmi);
}

function add_all_bands(median_image, min_image, max_image){
  return median_image.select('B1','B2','B3','B4','B5','B6','NDVI','NDWI','NDBI','NDMI')
  .addBands(min_image.select('B1','B2','B3','B4','B5','B6','NDVI','NDMI','NDWI','NDBI'))
  .addBands(max_image.select('B1','B2','B3','B4','B5','B6','NDWI','NDVI','NDMI'));  
}


india_image_training_median = add_normalized_bands(india_image_training_median)
india_image_training_min = add_normalized_bands(india_image_training_min)
india_image_training_max = add_normalized_bands(india_image_training_max)

var india_image_training = add_all_bands(india_image_training_median,
                                          india_image_training_min,
                                          india_image_training_mean,
                                          india_image_training_max)

// Training the RF model.

var new_bands = ['B1','B2', 'B3', 'B4','B5','B6','NDVI','NDBI','NDWI','NDMI',
                'B2_1', 'B3_1', 'B4_1','NDVI_1','NDBI_1','NDWI_1','NDMI_1',
                'B2_2', 'B3_2', 'B4_2','NDVI_2','NDWI_2','NDMI_2',
                ];


// Get the values for all pixels in each polygon in the training.
var training = india_image_training.sampleRegions(ft,['class'],30);


//######################### Partition the data into Testing and Training #######################################################

// Optionally, do some accuracy assessment.  Fist, add a column of random uniforms to the training dataset.
var withRandom = training.randomColumn('random');

// We want to reserve some of the data for testing, to avoid overfitting the model.
// var split = 0.7;  // Roughly 70% training, 30% testing.
// var trainingPartition = withRandom.filter(ee.Filter.lt('random', split));
// var testingPartition = withRandom.filter(ee.Filter.gte('random', split));

var fold1 = withRandom.filter(ee.Filter.lt('random',0.2));
var fold2 = withRandom.filter(ee.Filter.lt('random',0.4)).filter(ee.Filter.gt('random',0.2));
var fold3 = withRandom.filter(ee.Filter.lt('random',0.6)).filter(ee.Filter.gt('random',0.4));
var fold4 = withRandom.filter(ee.Filter.lt('random',0.8)).filter(ee.Filter.gt('random',0.6));
var fold5 = withRandom.filter(ee.Filter.gt('random',0.8));




var fold1Size=fold1.size();
var fold2Size=fold2.size();
var fold3Size=fold3.size();
var fold4Size=fold4.size();
var fold5Size=fold5.size();
var mergeFold1=fold2.merge(fold3).merge(fold4).merge(fold5);
var mergeFold2=fold1.merge(fold3).merge(fold4).merge(fold5);
var mergeFold3=fold2.merge(fold1).merge(fold4).merge(fold5);
var mergeFold4=fold2.merge(fold3).merge(fold1).merge(fold5);
var mergeFold5=fold2.merge(fold3).merge(fold4).merge(fold1);



var trainingClassifier1 = ee.Classifier.randomForest(100).train(mergeFold1, 'class', new_bands);
var validation1 = fold1.classify(trainingClassifier1);
var errorMatrix1 = validation1.errorMatrix('class', 'classification');
var accuracy1=errorMatrix1.accuracy();
//print(errorMatrix1)

var trainingClassifier2 = ee.Classifier.randomForest(100).train(mergeFold2, 'class', new_bands);
var validation2 = fold2.classify(trainingClassifier2);
var errorMatrix2 = validation2.errorMatrix('class', 'classification');
var accuracy2=errorMatrix2.accuracy();

var trainingClassifier3 = ee.Classifier.randomForest(100).train(mergeFold3, 'class', new_bands);
var validation3 = fold3.classify(trainingClassifier3);
var errorMatrix3 = validation3.errorMatrix('class', 'classification');
var accuracy3=errorMatrix3.accuracy();

var trainingClassifier4 = ee.Classifier.randomForest(100).train(mergeFold4, 'class', new_bands);
var validation4 = fold4.classify(trainingClassifier4);
var errorMatrix4 = validation4.errorMatrix('class', 'classification');
var accuracy4=errorMatrix4.accuracy();

var trainingClassifier5 = ee.Classifier.randomForest(100).train(mergeFold5, 'class', new_bands);
var validation5 = fold5.classify(trainingClassifier5);
var errorMatrix5 = validation5.errorMatrix('class', 'classification');



// var accuracy1 = ee.Feature(null, {matrix: accuracy1})

var folder_name = 'Landsat8_5fold_accuracy'


var exportConfusionMatrix = ee.Feature(null, {matrix: errorMatrix1.array()})
Export.table.toDrive({
  collection: ee.FeatureCollection(exportConfusionMatrix),
  description: 'landsat_training10_errorMatrix1',
  folder : folder_name,
  fileFormat: 'CSV'
});

var exportConfusionMatrix = ee.Feature(null, {matrix: errorMatrix2.array()})
Export.table.toDrive({
  collection: ee.FeatureCollection(exportConfusionMatrix),
  description: 'landsat_training10_errorMatrix2',
  folder : folder_name,
  fileFormat: 'CSV'
});

var exportConfusionMatrix = ee.Feature(null, {matrix: errorMatrix3.array()})
Export.table.toDrive({
  collection: ee.FeatureCollection(exportConfusionMatrix),
  description: 'landsat_training10_errorMatrix3',
  folder : folder_name,
  fileFormat: 'CSV'
});

var exportConfusionMatrix = ee.Feature(null, {matrix: errorMatrix4.array()})
Export.table.toDrive({
  collection: ee.FeatureCollection(exportConfusionMatrix),
  description: 'landsat_training10_errorMatrix4',
  folder : folder_name,
  fileFormat: 'CSV'
});

var exportConfusionMatrix = ee.Feature(null, {matrix: errorMatrix5.array()})
Export.table.toDrive({
  collection: ee.FeatureCollection(exportConfusionMatrix),
  description: 'landsat_training10_errorMatrix5',
  folder : folder_name,
  fileFormat: 'CSV'
});


