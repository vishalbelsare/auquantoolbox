import pandas as pd
try:        # Python 3.x
    import _pickle as pickle
except ImportError:
    try:    # Python 2.x
        import cPickle as pickle
    except ImportError:
        import pickle
from backtester.constants import *
from backtester.logger import *

class TrainingModelManager(object):
    """
    Base training model manager class to read, write, fit, predict and re-train
    """
    # TODO: process multiple model fit parallely

    def __init__(self, systemParams):
        self.systemParams = systemParams
        self._features = None
        self._targetVariable = None
        self._trainingModel = {}

    def getFeaures(self):
        return self._features

    def getTargetVariable(self):
        return self._targetVariable

    def setFeaures(self, features):
        self._features = features

    def setTargetVariable(self, targetVariable):
        self._targetVariable = targetVariable

    def getModel(self):
        return self._trainingModel

    def getModelByConfig(self, modelConfig):
        return self._trainingModel[modelConfig.getKey()]

    def readModel(self, fileName):
        with open(fileName, 'rb') as f:
            self._trainingModel = pickle.load(f)

    def writeModel(self, fileName):
        with open(fileName, 'wb') as f:
            pickle.dump(self._trainingModel, f)

    def computeWorkingTimestamps(self, data):
        timestamps = None
        if isinstance(data, dict):
            for key in data:
                if timestamps is None:
                    timestamps = data[key].index
                else:
                    timestamps = data[key].index.intersection(timestamps)
        elif isinstance(data, pd.DataFrame) or isinstance(data, pd.Series):
            timestamps = data.index
        else:
            raise ValueError
        return timestamps

    def modelConfigWrapper(func):
        def wrapper(self, *args, modelConfigs=None):
            outputDict = {}
            if modelConfigs is None:
                modelConfigs = self.systemParams.getModelConfigsForInstrumentType(INSTRUMENT_TYPE_STOCK)
            elif not isinstance(modelConfigs, list):
                modelConfigs = [modelConfigs]
            for modelConfig in modelConfigs:
                outputDict[modelConfig.getKey()] = func(self, *args, modelConfig=modelConfig)
            return outputDict
        return wrapper

    # fit multiple models on the same dataset
    @modelConfigWrapper
    def fitModel(self, features, targetVariable, modelConfig):
        self._targetVariable = targetVariable
        self._features = features.loc[self.computeWorkingTimestamps(targetVariable)]
        modelKey = modelConfig.getKey()
        modelId = modelConfig.getId()
        modelParams = modelConfig.getParams()
        modelCls = modelConfig.getClassForModelId(modelId)
        self._trainingModel[modelKey] = modelCls(modelParams)
        return self._trainingModel[modelKey].fit(self)

    @modelConfigWrapper
    def predict(self, features, modelConfig):
        self._features = features
        return self._trainingModel[modelConfig.getKey()].predict(self)

    @modelConfigWrapper
    def reTrain(self, features, targetVariable, modelConfig):
        self._targetVariable = targetVariable
        self._features = features.loc[self.computeWorkingTimestamps(targetVariable)]
        return self._trainingModel[modelConfig.getKey()].reTrain(self)

    @modelConfigWrapper
    def evaluateModel(self, features, targetVariable, modelConfig):
        self._targetVariable = targetVariable
        self._features = features.loc[self.computeWorkingTimestamps(targetVariable)]
        return self._trainingModel[modelConfig.getKey()].evaluate(self)

    def dumpModel(self, modelConfig):
        modelKey = modelConfig.getKey()
        del self._trainingModel[modelKey]
