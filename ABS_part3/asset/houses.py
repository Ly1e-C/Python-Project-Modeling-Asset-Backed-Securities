'''
This module contains derived asset classes related to houses.
'''
# This imports the Asset base class.
from asset.asset_base import Asset


# This is the House class. It is derived from the Asset base class.
# Different house types are derived from this class, but it does not do anything by itself for now.
class House(Asset):
    pass


# This is the PrimaryHome class, derived from House class. Its depreciation rate is 7% per year.
class PrimaryHome(House):
    def annualDeprRate(self):
        return 0.07


# This is the VacationHome class, derived from House class. Its depreciation rate is 3% per year.
class VacationHome(House):
    def annualDeprRate(self):
        return 0.03
