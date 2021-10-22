'''
This module includes the LoanPool class, which composes of a list of loans.
'''
# This imports the 'reduce' method from functools.
from functools import reduce
import numpy as np
import logging


# This is the LoanPool class, which contains a list of loans.
class LoanPool(object):
    # The class requires a list of loans to initialize.
    def __init__(self, loan_list):
        self._loanList = loan_list

    # This returns the total loan principal of all loans in the list.
    def totalPrincipal(self):
        # This uses generator expression to get principal of each loan and then get the sum.
        return sum(loan.face for loan in self._loanList)

    # This returns the total loan balance of all loans for a given period.
    def totalBalance(self, period):
        # This uses generator expression to get balance of each loan and then get the sum.
        return sum(loan.balance(period) for loan in self._loanList)

    # This returns the total monthly payment of all loans for a given period.
    def totalMonthlyPmt(self, period=1):
        # This uses generator expression to get the monthly payment of each loan.
        return sum(loan.monthlyPayment(period) for loan in self._loanList)

    # This returns the total principal due of all loans for a given period.
    def totalPrincipalDue(self, period):
        # This uses generator expression to get principal due of each loan and then get the sum.
        return sum(loan.principalDue(period) for loan in self._loanList)

    # This returns the total interest due of all loans for a given period.
    def totalInterestDue(self, period):
        # This uses generator expression to get interest due of each loan and then get the sum.
        return sum(loan.interestDue(period) for loan in self._loanList)

    # This returns the total recovery values of all loans for a given period.
    def totalRecoveries(self, period):
        # This uses generator expression to get interest due of each loan and then get the sum.
        return sum(loan.recoveryValue(period) for loan in self._loanList)

    # This returns a list of all active loans.
    def activeLoans(self, period):
        # Active loans are the ones with balance greater than 0 for a given period.
        return [loan for loan in self._loanList if loan.balance(period) > 0]

    # This returns the weighted average rate of active loans.
    # Loans that are completely paid down should no longer matter.
    def getWAR(self, period=0):
        # This creates a list of mortgage tuples as input for the following reduce() calls.
        loanTups = [(loan.balance(period), loan.rate(period)) for loan in self.activeLoans(period)]
        # This calls for reduce() twice to calculate the weighted average: once for the numerator
        # and once for the denominator.
        return reduce(lambda total, mort_tup: total + (mort_tup[0] * mort_tup[1]), loanTups,
                      0.0) / sum(mort_tup[0] for mort_tup in loanTups)

    # This returns the weighted average maturity of active loans.
    # Loans that are completely paid down should no longer matter.
    def getWAM(self, period=0):
        # This creates a list of mortgage tuples as input for the following reduce() calls.
        loanTups = [(loan.balance(period), loan.term - period) for loan in self.activeLoans(period)]
        # This calls for reduce() twice to calculate the weighted average: once for the numerator
        # and once for the denominator.
        return reduce(lambda total, mort_tup: total + (mort_tup[0] * mort_tup[1]), loanTups,
                      0.0) / sum(mort_tup[0] for mort_tup in loanTups)

    # This converts the class into an iterable class.
    def __iter__(self):
        # This generator returns an item of the _loanList.
        for loan in self._loanList:
            yield loan

    # This returns the information to be stored on the asset-side output file.
    def getWaterfall(self, period):
        return [self.totalPrincipalDue(period), self.totalInterestDue(period),
                self.totalRecoveries(period), self.totalMonthlyPmt(period),
                self.totalBalance(period)]
