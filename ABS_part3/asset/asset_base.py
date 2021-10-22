'''
This module contains the Asset abstract base class.
'''


class Asset(object):
    # This initializes an instance of Asset based on input given.
    def __init__(self, initialVal):
        self._initialVal = initialVal

    # This is the getter function for _initialVal.
    @property
    def initialVal(self):
        return self._initialVal

    # This is the setter function for _initialVal.
    @initialVal.setter
    def initialVal(self, i_initialVal):
        self._initialVal = i_initialVal

    # This is an abstract method to be overridden by derived classes.
    def annualDeprRate(self):
        raise NotImplementedError()

    # This is a static method that converts annual depreciation rate into monthly depreciation rate.
    @staticmethod
    def getMonthlyDeprRate(i_annualDeprRate):
        return 1 - (1 - i_annualDeprRate) ** (1 / 12)

    # This calculates the value of an asset after a given period of depreciation.
    def currentVal(self, period):
        return self._initialVal * (1 - self.getMonthlyDeprRate(self.annualDeprRate())) ** period
