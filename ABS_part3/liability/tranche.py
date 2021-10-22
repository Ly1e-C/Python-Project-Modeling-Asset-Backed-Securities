'''
This module includes the Tranche base class and the StandardTranche derived class.
'''


# This is the tranche base class, from which StandardTranche is derived.
class Tranche(object):
    # Inputs for constructor include notional value, rate, and subordination level.
    def __init__(self, notional, rate, subordination='A'):
        self._notional = notional
        self._rate = rate
        self._subordination = subordination
    
    # This is the getter function for _notional.
    @property
    def notional(self):
        return self._notional

    # This is the setter function for _notional.
    @notional.setter
    def notional(self, i_notional):
        self._notional = i_notional
        
    # This is the getter function for _rate.
    @property
    def rate(self):
        return self._rate

    # This is the setter function for _rate.
    @rate.setter
    def rate(self, i_rate):
        self._rate = i_rate
        
    # This is the getter function for _subordination.
    @property
    def subordination(self):
        return self._subordination

    # This is the setter function for _subordination.
    @subordination.setter
    def subordination(self, i_subordination):
        self._subordination = i_subordination


# This is the StandardTranche class, from which investors receive both interest and principal.
class StandardTranche(Tranche):
    def __init__(self, notional, rate, subordination):
        # This calls for the base class constructor.
        super(StandardTranche, self).__init__(notional, rate, subordination)
        # This calls for reset(), which sets the other data members.
        self.reset()

    # reset() may be called by StandardTranche's constructor or by StructuredSecurities when
    # resetting a tranche.
    def reset(self):
        self._period = 0
        self._interestDue = [0]
        self._interestPaid = [0]
        self._interestShortfall = [0]
        self._principalDue = [0]
        self._principalPaid = [0]
        self._principalShortfall = [0]
        self._balance = [self._notional]
        self._cashFlow = [-self._notional]

    # This is the getter function for _interestDue.
    @property
    def interestDue(self):
        return self._interestDue
    
    # This is the getter function for _interestPaid.
    @property
    def interestPaid(self):
        return self._interestPaid

    # This is the getter function for _interestShortfall.
    @property
    def interestShortfall(self):
        return self._interestShortfall
        
    # This is the getter function for _principalDue.
    @property
    def principalDue(self):
        return self._principalDue
    
    # This is the getter function for _principalPaid.
    @property
    def principalPaid(self):
        return self._principalPaid
    
    # This is the getter function for _principalShortfall.
    @property
    def principalShortfall(self):
        return self._principalShortfall
    
    # This is the getter function for _balance.
    @property
    def balance(self):
        return self._balance
    
    # This is the getter function for _cashFlow.
    @property
    def cashFlow(self):
        return self._cashFlow

    # This increases period by 1.
    def increaseTimePeriod(self):
        self._period += 1

    # This returns the amount of interest that is due in current period.
    def getInterestDue(self):
        self._interestDue.append(self._balance[self._period - 1] * self._rate / 12 +
                                 self._interestShortfall[self._period - 1])
        return self._interestDue[self._period]

    # This takes the interest payment and records interest shortfall.
    def makeInterestPayment(self, interest_pmt):
        if self._period in self._interestPaid:
            raise IndexError('Interest payment has already been made.')
        elif self._balance[self._period - 1] == 0 and interest_pmt != 0:
            raise ValueError('Tranche is fully paid off. It should not receive interest payment.')
        else:
            # This records the interest payment.
            self._interestPaid.append(interest_pmt)
            # This records any interest shortfall.
            self._interestShortfall.append(self._interestDue[self._period] - interest_pmt)

    # Since principal due is partly determined by the amount of principal received from loans,
    # the amount is given by StructuredSecurities instead of calculated here.
    def setPrincipalDue(self, tranche_principal_due):
        self._principalDue.append(tranche_principal_due)

    # This takes the principal payment and records principal shortfall, remaining balance,
    # and total periodic cash flow.
    def makePrincipalPayment(self, principal_pmt):
        if self._period in self._principalPaid:
            raise IndexError('Principal payment has already been made.')
        elif self._balance[self._period - 1] == 0 and principal_pmt != 0:
            raise ValueError('Tranche is fully paid off. It should not receive principal payment.')
        else:
            # This records the principal payment.
            self._principalPaid.append(principal_pmt)
            # This records any principal shortfall.
            self._principalShortfall.append(self._principalDue[self._period] - principal_pmt)
            # This calculates and records remaining balance.
            b0 = self._balance[self._period - 1] - self._principalPaid[self._period]
            if abs(b0) > 10 ** -6:
                self._balance.append(b0)
            # If the remaining balance is less than a certain threshold, it is simply set to 0.
            # This avoids AL becoming infinity due to rounding errors in balance.
            else:
                self._balance.append(0)
            # This calculates total periodic cash flow, which is simply the sum of interest paid
            # and principal paid.
            self._cashFlow.append(self._interestPaid[self._period] +
                                  self._principalPaid[self._period])

    # This returns the remaining notional balance.
    def notionalBalance(self):
        return self._balance[self._period]
