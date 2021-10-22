'''
This module contains the MortgageMixin class, as well as its derived FixedMortgage class and
VariableMortgage class.
'''
from loan.loans import VariableRateLoan, FixedRateLoan
from asset.houses import House
import logging


# The MortgageMixin class contains functionalities that are specific to a mortgage.
class MortgageMixin(object):
    # MortgageMixin's __init__ delegates to the loan class to initialize attributes.
    def __init__(self, home, face, rate, term):
        # This checks to make sure the first input is a House. Exception is raised otherwise.
        if not isinstance(home, House):
            # An ERROR logging statement gets displayed before exception is raised.
            logging.error('The input is of {0}, but an instance of House class is '
                          'expected.'.format(type(home)))
            raise TypeError('Exception: The input is not a house.')
        else:
            # 'rate' is a fixed rate for FixedMortgage and a rate dict for VariableMortgage.
            super(MortgageMixin, self).__init__(home, face, rate, term)

    # This calculates the PMI of a mortgage.
    def PMI(self, period):
        # This gets the remaining balance using the Loan base class's balance function.
        balancePMI = super(MortgageMixin, self).balance(period)
        # This gets the asset's initial value.
        valuePMI = super(MortgageMixin, self).asset.initialVal
        # If the remaining balance is greater than 80% of the initial value, then a 0.0075% monthly
        # PMI payment is applied.
        if balancePMI > (valuePMI * 0.8):
            return 0.000075 * valuePMI
        else:
            return 0
    
    # Monthly payment now must add in the PMI payment.
    # This gets the original monthly payment using the Loan base class's monthlyPayment() function.
    def monthlyPayment(self, period=1):
        return super(MortgageMixin, self).monthlyPayment(period) + self.PMI(period)
    
    # Principal due now must subtract the PMI payment.
    def principalDue(self, period):
        return super(MortgageMixin, self).principalDue(period) - self.PMI(period)


# This is the FixedMortgage class. It does not have its own __init__ because that is delegated to
# the __init__ of MortgageMixin, which then delegates to FixedRateLoan.
# It also does not have any FixedMortgage specific functionalities yet.
class FixedMortgage(MortgageMixin, FixedRateLoan):
    pass


# This is the VariableMortgage class. It does not have its own __init__ because that is delegated
# to the __init__ of MortgageMixin, which then delegates to VariableRateLoan.
# It also does not have any VariableMortgage specific functionalities yet.
class VariableMortgage(MortgageMixin, VariableRateLoan):
    pass
