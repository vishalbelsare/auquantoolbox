from feature import Feature
import numpy as np

class FeesFeature(Feature):

    @classmethod
    def computeForLookbackData(cls, featureParams, featureKey, currentFeatures, lookbackDataDf):
        raise NotImplementedError
        return None

    @classmethod
    def computeForInstrument(cls, featureParams, featureKey, currentFeatures, instrument, instrumentManager):
        positionDict = instrument.getDataDf()['position']
        if len(positionDict) < 1:
            return 0
        currentPrice = currentFeatures[featureParams['price']]
        feesDict = featureParams['feesDict']
        currentPosition = instrument.getCurrentPosition()
        previousPosition = positionDict.iloc[-1]
        changeInPosition = currentPosition - previousPosition
        fees = np.abs(changeInPosition) * feesDict[np.sign(changeInPosition)] * currentPrice
        return fees

    @classmethod
    def computeForMarket(cls, featureParams, featureKey, currentMarketFeatures, instrumentManager):
    	raise NotImplementedError
        return None
        