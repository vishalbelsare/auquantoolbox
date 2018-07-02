import sys, os
parentPath = os.path.abspath("..")
if parentPath not in sys.path:
    sys.path.insert(0, parentPath)
import pandas as pd
from backtester.model_learning_system_parameters import ModelLearningSystemParamters
from backtester.modelLearningManagers.target_variable_manager import TargetVariableManager
from backtester.modelLearningManagers.feature_selection_manager import FeatureSelectionManager
from backtester.modelLearningManagers.feature_transformation_manager import FeatureTransformationManager
from backtester.modelLearningManagers.regression_model import RegressionModel
from backtester.constants import *

class ModelLearningSystem:

    # This chunksize is different from chunkSize defined in mlsParams
    # This is useful to do training in chunks
    def __init__(self, mlsParams, chunkSize=None):
        self.mlsParams = mlsParams
        self.__trainingDataSource = mlsParams.getTrainingDataSource()
        self.__chunkSize = chunkSize
        self.__targetVariableManager = TargetVariableManager(mlsParams, instrumentIds=mlsParams.instrumentIds, chunkSize=self.__chunkSize)
        self.__featureSelectionManager = FeatureSelectionManager(mlsParams)
        self.__featureTransformationManager = FeatureTransformationManager(mlsParams)
        self.__trainingModelManager = RegressionModel(mlsParams)

    def getTrainingInstrurmentData(self, instrumentId):
        return self.__trainingDataSource.getInstrumentUpdates(instrumentId, self.__chunkSize)

    def getTargetVariables(self, targetVariableConfigs):
        targetVariableConfigs = targetVariableConfigs if isinstance(targetVariableConfigs, list) else [targetVariableConfigs]
        targetVariableKeys = map(lambda x: x.getFeatureKey(), targetVariableConfigs)
        targetVariable = {}
        for key in targetVariableKeys:
            targetVariable[key] = self.__targetVariableManager.getTargetVariableByKey(key)
        return targetVariable

    def computeTargetVariables(self, instrumentData, instrumentId, targetVariableConfigs, useTimeFrequency=True):
        timeFrequency = instrumentData.getTimeFrequency() if useTimeFrequency else None
        if self.__chunkSize is None:
            self.__targetVariableManager.computeTargetVariables(0, instrumentData.getBookData(), instrumentId,
                                                                targetVariableConfigs, timeFrequency)
            targetVariable = self.getTargetVariables(targetVariableConfigs)
            print(targetVariable)
            return
        for chunkNumber, instrumentDataChunk in instrumentData.getBookDataChunk():
            self.__targetVariableManager.computeTargetVariables(chunkNumber, instrumentDataChunk, instrumentId,
                                                                targetVariableConfigs, timeFrequency)
            targetVariable = self.getTargetVariables(targetVariableConfigs)
            print(chunkNumber, targetVariable)
        targetVariable = self.__targetVariableManager.getLeftoverTargetVariableChunk()
        print(chunkNumber+1, targetVariable)

    def getFeatureSet(self):
        return self.mlsParams.features

    def findBestModel(self, instrumentId, useTimeFrequency=True):
        instrumentData = self.getTrainingInstrurmentData(instrumentId)[instrumentId]
        targetVariableConfigs = self.mlsParams.getTargetVariableConfigsForInstrumentType(INSTRUMENT_TYPE_STOCK)
        modelConfigs = self.mlsParams.getModelConfigsForInstrumentType(INSTRUMENT_TYPE_STOCK)
        self.computeTargetVariables(instrumentData, instrumentId, targetVariableConfigs, useTimeFrequency)
        targetVariablesData = self.getTargetVariables(targetVariableConfigs)
        self.__featureSelectionManager.pruneFeatures(instrumentData.getBookData(), targetVariablesData,
                                                     aggregationMethod='intersect')
        selectedFeatures = self.__featureSelectionManager.getAllSelectedFeatures()
        print(selectedFeatures)
        selectedInstrumentData = {}
        transformedInstrumentData = {}
        for targetVariableConfig in targetVariableConfigs:
            key = targetVariableConfig.getFeatureKey()
            selectedInstrumentData[key] = instrumentData.getBookData()[selectedFeatures[key]]
            self.__featureTransformationManager.transformFeatures(selectedInstrumentData[key])
            columns = selectedInstrumentData[key].columns
            transformedInstrumentData[key] = pd.DataFrame(index=selectedInstrumentData[key].index, columns=columns)
            transformedInstrumentData[key][columns] = self.__featureTransformationManager.getTransformedData()
            print(transformedInstrumentData[key])
            # self.__featureTransformationManager.writeTransformers('transformersss.pkl')
            # for modelConfig in modelConfigs:
            self.__trainingModelManager.fitModel(transformedInstrumentData[key], targetVariablesData[key])
            print(self.__trainingModelManager.predict(transformedInstrumentData[key]))
            print(self.__trainingModelManager.evaluateModel(transformedInstrumentData[key], targetVariablesData[key]))


        print(self.__trainingModelManager.getModel())

    def getFinalMetrics(self):
        pass

if __name__ == '__main__':
    instrumentIds = ['IBM', 'AAPL']
    startDateStr = '2014/07/10'
    endDateStr = '2017/10/07'
    chunkSize = 100
    mlsParams = ModelLearningSystemParamters(instrumentIds, 'XYZ', chunkSize=chunkSize)
    params = dict(cachedFolderName='yahooData/',
                 dataSetId='testTrading',
                 instrumentIds=instrumentIds,
                 startDateStr=startDateStr,
                 endDateStr=endDateStr,
                 liveUpdates=False)
    mlsParams.initializeDataSource('YahooStockDataSource', **params)

    system1 = ModelLearningSystem(mlsParams, chunkSize=None)
    # print(system1.getTrainingInstrurmentData('IBM')['IBM'].getBookData())
    system1.findBestModel('AAPL')
