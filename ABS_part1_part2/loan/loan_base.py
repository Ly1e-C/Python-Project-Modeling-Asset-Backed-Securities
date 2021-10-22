'''
This module contains the Loan base class.
'''
# This imports Asset class, which is useful when checking if input is indeed an asset.
from asset.asset_base import Asset
import logging


# This is the Loan base class, from which specific loan types will be derived.
class Loan(object):
    # This initializes an instance of Loan based on inputs given.
    def __init__(self, asset, face, rate, term):
        # This checks if the first input is an Asset. Exception is raised otherwise.
        if not isinstance(asset, Asset):
            # An ERROR logging statement gets displayed before exception is raised.
            logging.error('The input is of {0}, but an instance of Asset class is '
                          'expected.'.format(type(asset)))
            raise TypeError('Exception: The input is not an asset.')
        else:
            self._asset = asset
            self._face = face
            self._rate = rate
            self._term = term

    # This is the getter function for _asset.
    @property
    def asset(self):
        return self._asset

    # This is the setter function for _asset.
    @asset.setter
    def asset(self, i_asset):
        self._asset = i_asset

    # This is the getter function for _face.
    @property
    def face(self):
        return self._face

    # This is the setter function for _face.
    @face.setter
    def face(self, i_face):
        self._face = i_face

    # This will be overridden by derived classes.
    # This also makes Loan an abstract base class.
    def rate(self, period):
        raise NotImplementedError()

    # This is the getter function for _term.
    @property
    def term(self):
        return self._term

    # This is the setter function for _term.
    @term.setter
    def term(self, i_term):
        self._term = i_term

    # This calculates the monthly payment.
    def monthlyPayment(self, period=1):
        # This returns 0 for edge cases.
        if period == 0 or period > self._term:
            return 0
        else:
            # The actual calculation is done here.
            monthly_rate = self.monthlyRate(self._rate)
            return monthly_rate * self._face / (1 - (1 + monthly_rate) ** (-self._term))

    # This calculates the sum of all payments across all periods.
    # The total payments is simply the number of months times the monthly payment.
    def totalPayments(self):
        return self._term * self.monthlyPayment()

    # This calculates the sum of all interest payments across all periods.
    # The total interest is simply the total payments minus the principal (face value).
    def totalInterest(self):
        return self.totalPayments() - self._face

    # This calculates the remaining balance.
    def balance(self, period):
        # This returns 0 for edge cases.
        if period >= self._term:
            return 0
        # In period 0, balance is just face value.
        elif period == 0:
            return self._face
        else:
            # The actual calculation is done here.
            monthly_rate = self.monthlyRate(self._rate)
            return self._face * (1 + monthly_rate) ** period - \
                   self.monthlyPayment(period) * ((1 + monthly_rate) ** period - 1) / monthly_rate

    # This calculates the interest due. It calls for the formula-based balance function.
    def interestDue(self, period):
        # This returns 0 for edge cases.
        if period == 0 or period > self._term:
            return 0
        else:
            # Interest due is period interest rate times last period's remaining balance.
            return self.monthlyRate(self._rate) * self.balance(period - 1)

    # This calculates the principal due. It calls for the formula-based interest due function.
    def principalDue(self, period):
        # This returns 0 for edge cases.
        if period == 0 or period > self._term:
            return 0
        else:
            # Principal due is this period's monthly payment minus this period's interest due.
            return self.monthlyPayment(period) - self.interestDue(period)

    # This calculates the remaining balance using recursion.
    def balanceRcr(self, period):
        # WARN level statement is displayed to encourage user to choose explicit version instead.
        logging.warning('Recursive methods can take long time. Using explicit versions is '
                        'recommended.')
        # The initial balance at period 0 is the face value.
        if period == 0:
            return self._face
        elif period >= self._term:
            return 0
        # Remaining balance is last period's remaining balance minus this period's principal due.
        else:
            return self.balanceRcr(period - 1) - self.principalDueRcr(period)

    # This is same as the first interest due function, but it calls for the recursion-based
    # balance function.
    def interestDueRcr(self, period):
        # WARN level statement is displayed to encourage user to choose explicit version instead.
        logging.warning('Recursive methods can take long time. Using explicit versions is '
                        'recommended.')
        if period == 0 or period > self._term:
            return 0
        else:
            return self.monthlyRate(self._rate) * self.balanceRcr(period - 1)

    # This is same as the first principal due function, but it calls for the recursion-based
    # interest due function.
    def principalDueRcr(self, period):
        # WARN level statement is displayed to encourage user to choose explicit version instead.
        logging.warning('Recursive methods can take long time. Using explicit versions is '
                        'recommended.')
        if period == 0 or period > self._term:
            return 0
        else:
            return self.monthlyPayment(period) - self.interestDueRcr(period)

    # This static method converts annual rate into monthly rate.
    @staticmethod
    def monthlyRate(annual_rate):
        return annual_rate / 12

    # This static method converts monthly rate into annual rate.
    @staticmethod
    def annualRate(monthly_rate):
        return monthly_rate * 12

    # This calculates the recovery value of the loan.
    def recoveryValue(self, period):
        # This returns 0 for edge cases.
        if period == 0 or period > self._term:
            return 0
        else:
            recovery_multiplier = 0.6
            # Interim step like the value of recovery multiplier is displayed in a DEBUG statement.
            logging.debug('The recovery multiplier is {0:.2f}.'.format(recovery_multiplier))
            # Formula is asset's current value times the recovery multiplier.
            return self._asset.currentVal(period) * recovery_multiplier

    # This calculates the owner's equity.
    def equity(self, period):
        # Formula is asset's current value minus the loan's remaining balance.
        return self._asset.currentVal(period) - self.balance(period)
