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



var bands = ['B1','B2', 'B3', 'B4', 'B5', 'B6','B7'];
var india = ee.FeatureCollection('users/chahatresearch/India_Boundary')
    .geometry();


var india_image = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR')
    .filterBounds(india)
    .filterDate('2019-01-01','2019-12-31')
    .filter(ee.Filter.lt('CLOUD_COVER',10))
    .map(cloudMaskL457)
    .select(bands)
    ;

var india_image_training_median = india_image.median();
var india_image_training_min = india_image.min();
var india_image_training_max = india_image.max();
  


//Training feature collection. Imported from assets (Its a shapefile)
var ft = ee.FeatureCollection('users/chahatresearch/IndiaSat');


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

var folder_name = 'Landsat7_5fold_accuracy'


var exportConfusionMatrix = ee.Feature(null, {matrix: errorMatrix1.array()})
Export.table.toDrive({
  collection: ee.FeatureCollection(exportConfusionMatrix),
  description: 'landsat7_training10_errorMatrix1',
  folder : folder_name,
  fileFormat: 'CSV'
});

var exportConfusionMatrix = ee.Feature(null, {matrix: errorMatrix2.array()})
Export.table.toDrive({
  collection: ee.FeatureCollection(exportConfusionMatrix),
  description: 'landsat7_training10_errorMatrix2',
  folder : folder_name,
  fileFormat: 'CSV'
});

var exportConfusionMatrix = ee.Feature(null, {matrix: errorMatrix3.array()})
Export.table.toDrive({
  collection: ee.FeatureCollection(exportConfusionMatrix),
  description: 'landsat7_training10_errorMatrix3',
  folder : folder_name,
  fileFormat: 'CSV'
});

var exportConfusionMatrix = ee.Feature(null, {matrix: errorMatrix4.array()})
Export.table.toDrive({
  collection: ee.FeatureCollection(exportConfusionMatrix),
  description: 'landsat7_training10_errorMatrix4',
  folder : folder_name,
  fileFormat: 'CSV'
});

var exportConfusionMatrix = ee.Feature(null, {matrix: errorMatrix5.array()})
Export.table.toDrive({
  collection: ee.FeatureCollection(exportConfusionMatrix),
  description: 'landsat7_training10_errorMatrix5',
  folder : folder_name,
  fileFormat: 'CSV'
});


