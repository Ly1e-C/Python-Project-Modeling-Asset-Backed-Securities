'''
This module includes the StructuredSecurities class.
'''
from liability.tranche import Tranche
import logging


# This is the StructuredSecurities class, which will hold different tranches.
class StructuredSecurities(object):
    # The constructor creates the data members for keeping track of the structured deal.
    def __init__(self):
        self._trancheList = []
        self._percentNotionalDict = {}
        self._sequential = True
        self._period = 0
        self._cashReserve = 0

    # This adds the tranches to StructuredSecurities.
    def addTranche(self, *args):
        for tranche in args:
            # First, we check to make sure the inputs are tranche objects.
            if not isinstance(tranche, Tranche):
                logging.error('The input is of {0}, but an instance of Tranche class is '
                              'expected.'.format(type(tranche)))
                raise TypeError('Exception: The input is not a tranche.')
            # If it is indeed a tranche, it is added in.
            self._trancheList.append(tranche)
        # This sorts the tranches by subordination. This is helpful since the waterfall must be
        # done according to tranches' subordination levels.
        self._trancheList.sort(key=lambda x: x.subordination)
        # This calculates the total notional within the tranches.
        total_notional = sum(tranche.notional for tranche in self._trancheList)
        # This records the proportion of notional that belongs to each tranche.
        # It is useful for pro rata distribution of principal.
        for tranche in self._trancheList:
            self._percentNotionalDict[tranche.subordination] = tranche.notional / total_notional

    # This is the getter function for _sequential.
    @property
    def sequential(self):
        return self._sequential

    # This is the setter function for _sequential.
    @sequential.setter
    def sequential(self, i_sequential):
        self._sequential = i_sequential

    # This increases the time period for all tranches.
    def increaseTimePeriodForAll(self):
        self._period += 1
        for tranche in self._trancheList:
            tranche.increaseTimePeriod()

    # This contains the waterfall logic for payment distribution.
    def makePayments(self, interest_available, principal_available):
        # First, we calculate the total cash available for distribution.
        cash_amount = interest_available + principal_available + self._cashReserve

        # This loop is used for making interest payments.
        for tranche in self._trancheList:
            # This checks the amount of interest due for each tranche.
            tranche_interest_due = tranche.getInterestDue()
            # This pays the interest due if there is sufficient cash.
            if cash_amount > tranche_interest_due:
                tranche.makeInterestPayment(tranche_interest_due)
                cash_amount -= tranche_interest_due
            # If not, then it pays all the cash it has left.
            else:
                tranche.makeInterestPayment(cash_amount)
                cash_amount = 0

        # This loop is used for making principal payments.
        for tranche in self._trancheList:
            # This calculates principal due for when the mode of distribution is sequential.
            if self._sequential:
                tranche_principal_due = \
                    min(tranche.balance[self._period - 1], principal_available +
                        tranche.principalShortfall[self._period - 1])
                principal_available -= tranche_principal_due
            # This calculates principal due for when the mode of distribution is pro rata.
            else:
                tranche_principal_due = \
                    min(tranche.balance[self._period - 1], principal_available *
                        self._percentNotionalDict[tranche.subordination] +
                        tranche.principalShortfall[self._period - 1])
            # This tells each tranche its principal due.
            tranche.setPrincipalDue(tranche_principal_due)
            # This pays the principal due if there is sufficient cash.
            if cash_amount > tranche_principal_due:
                tranche.makePrincipalPayment(tranche_principal_due)
                cash_amount -= tranche_principal_due
            # If not, then it pays all the cash it has left.
            else:
                tranche.makePrincipalPayment(cash_amount)
                cash_amount = 0

        # This informs user that cash has run out for the period.
        if cash_amount == 0:
            logging.debug('Cash has run out in period {}.'.format(self._period))

        # The remaining cash after each period is the new cash reserve.
        self._cashReserve = cash_amount

    # This creates a list of lists that contains the waterfall results from each period.
    def getWaterfall(self):
        res = [[tranche.interestDue[self._period],
                tranche.interestPaid[self._period],
                tranche.interestShortfall[self._period],
                tranche.principalDue[self._period],
                tranche.principalPaid[self._period],
                tranche.principalShortfall[self._period],
                tranche.notionalBalance(),
                tranche.cashFlow[self._period]]
               for tranche in self._trancheList]
        return res, self._cashReserve

    # This converts the class into an iterable class.
    def __iter__(self):
        # This generator returns an item of the _trancheList.
        for tranche in self._trancheList:
            yield tranche

    # This resets the StructuredSecurities for a new simulation.
    def resetAll(self):
        self._period = 0
        self._cashReserve = 0
        # This tells each tranche to reset as well.
        for tranche in self._trancheList:
            tranche.reset()
        logging.debug('The tranches have been reset.')
