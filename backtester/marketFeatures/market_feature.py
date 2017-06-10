class MarketFeature(object):

    @classmethod
    def validateInputs(cls, featureParams, currentMarketFeatures, instrumentManager):
        return True

    '''
    override this method
    '''
    @classmethod
    def compute(cls, featureParams, featureKey, currentMarketFeatures, instrumentManager):
        raise NotImplementedError
        return None, None
