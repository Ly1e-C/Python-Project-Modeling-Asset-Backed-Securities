'''
This module includes the AutoLoan class, which is derived from the FixedRateLoan class.
'''
from loan.loans import FixedRateLoan
from asset.cars import Car
import logging


# Auto loan usually has fixed rate, but it is not a mortgage and does not have PMI.
# Therefore, it is set to derive from FixedRateLoan.
class AutoLoan(FixedRateLoan):
    # This calls for FixedRateLoan's __init__, but it also sets an attribute called '_secured'.
    def __init__(self, car, face, rate, term):
        # This checks to make sure the first input is a Car. Exception is raised otherwise.
        if not isinstance(car, Car):
            # An ERROR logging statement gets displayed before exception is raised.
            logging.error('The input is of {0}, but an instance of Car class is '
                          'expected.'.format(type(car)))
            raise TypeError('Exception: The input is not a car.')
        else:
            super(AutoLoan, self).__init__(car, face, rate, term)
