'''
This module contains derived asset classes related to cars.
'''
# This imports the Asset base class.
from asset.asset_base import Asset


# This is the Car class. It is derived from the Asset base class.
# Different car types are derived from this class.
class Car(Asset):
    def annualDeprRate(self):
        return 0.12


# This is the MercedesBenz class, derived from Car class. Its depreciation rate is 5% per year.
class MercedesBenz(Car):
    def annualDeprRate(self):
        return 0.05


# This is the Porsche class, derived from Car class. Its depreciation rate is 8% per year.
class Porsche(Car):
    def annualDeprRate(self):
        return 0.08


# This is the Tesla class, derived from Car class. Its depreciation rate is 10% per year.
class Tesla(Car):
    def annualDeprRate(self):
        return 0.1


# This is the Honda class, derived from Car class. Its depreciation rate is 12% per year.
class Honda(Car):
    def annualDeprRate(self):
        return 0.12
