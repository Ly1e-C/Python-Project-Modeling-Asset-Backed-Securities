'''
This script contains the FixedRateLoan and the VariableRateLoan classes, both of which are
derived from the Loan base class. They override the rate() function.
'''
# This imports the Loan base class using selective importing.
from loan.loan_base import Loan


# The FixedRateLoan class is derived from the Loan base class.
# It does not have its own __init__ because it has no new attribute.
class FixedRateLoan(Loan):
    # The rate() function overrides the abstract rate() function in Loan.
    # 'period' is a dummy parameter since the rate is fixed across all periods.
    def rate(self, period=1):
        return self._rate


# The VariableRateLoan class is derived from the Loan base class.
class VariableRateLoan(Loan):
    # This initializes _rateDict and calls for the Loan __init__ to initialize _face and _term.
    def __init__(self, asset, face, rateDict, term):
        self._rateDict = rateDict
        super(VariableRateLoan, self).__init__(asset, face, None, term)

    # This retrieves rate of a specific period.
    def rate(self, period):
        # This finds the last time rate was changed.
        last_rate_change = max([month for month in self._rateDict.keys() if month <= period])
        # This returns the rate of the last time rate was changed.
        return self._rateDict[last_rate_change]
