'''
Li Jin Chen
12-03-2020
Final Project: This script tests the ABS waterfall and calculates the waterfall metrics.
'''
# This imports the relevant classes for testing.
from loan.auto_loan import AutoLoan
from loan.mortgage_mixin import FixedMortgage, VariableMortgage
from loan.loan_pool import LoanPool
from asset.cars import Car
from asset.houses import PrimaryHome, VacationHome
from liability.tranche import StandardTranche
from liability.securities import StructuredSecurities
import os
import numpy_financial as npf
import functools


# This function loads the 1500 loans from Loans.csv and returns a LoanPool object containing the
# loans.
def loadAssets():
    # This dict provides the conversion between the "Loan Type" as entered in the Loans.csv and
    # the loan constructor function to be called. Though there are only auto loans in the csv,
    # this allows the program to be more generic.
    loan_type_dict = {'Auto Loan': AutoLoan,
                      'Fixed Rate Mortgage': FixedMortgage,
                      'Variable Rate Mortgage': VariableMortgage}
    # This dict provides the conversion between the "Asset" as entered in the Loans.csv and
    # the asset constructor function to be called. Though there are only cars in the csv,
    # this allows the program to be more generic.
    asset_type_dict = {'Car': Car,
                       'Primary Home': PrimaryHome,
                       'Vacation Home': VacationHome}
    # This creates a list that will hold the created loans. This list is then used as input for
    # the initializing the LoanPool object.
    loan_list = []
    # This context manager reads the .csv file within the current working directory.
    with open(os.path.join(os.getcwd(), "Loans.csv"), "r") as fp:
        # This skips the first line, which is just the header.
        next(fp)
        for line in fp:
            split_line = line.split(',')
            # This creates a single loan.
            # loan_type_dict[split_line[1]]() returns the loan constructor function.
            single_loan = loan_type_dict[split_line[1]](
                # asset_type_dict[split_line[5]]() returns the asset constructor function.
                # float(split_line[6]) returns the asset value.
                asset_type_dict[split_line[5]](float(split_line[6])),
                # This returns the balance.
                float(split_line[2]),
                # This returns the rate.
                float(split_line[3]),
                # This returns the term.
                float(split_line[4]))
            # This adds one loan to the list.
            loan_list.append(single_loan)
    # This returns the LoanPool object containing all the loans.
    return LoanPool(loan_list)


# This executes the ABS waterfall and calculates the waterfall metrics.
def doWaterfall(loaded_pool, structured_deal):
    # This sets the output files to locate at current working directory.
    assets_file_path = os.path.join(os.getcwd(), "Assets.csv")
    liabilities_file_path = os.path.join(os.getcwd(), "Liabilities.csv")
    # This context manager creates the two output files and writes to them.
    with open(assets_file_path, 'w') as afp, open(liabilities_file_path, 'w') as lfp:
        # This writes the header for the asset-side output file.
        afp.write('Period,Principal,Interest,Recoveries,Total,Balance,\n')
        # This writes the first cell of the header for the liability-side output file.
        lfp.write('Period,')
        # This writes the rest of the header for the liability-side output file. Note that
        # "tranche.subordination" is repeated many times because each piece of information needs
        # to be labelled with the tranche to which the information pertains. Subordination takes
        # on either "A" or "B".
        for tranche in structured_deal:
            lfp.write('{0} Interest Due,{1} Interest Paid,{2} Interest Shortfall,{3} Principal Due,'
                      '{4} Principal Paid,{5} Principal Shortfall,{6} Balance,{7} Cash Flow,'
                      .format(tranche.subordination, tranche.subordination, tranche.subordination,
                              tranche.subordination, tranche.subordination, tranche.subordination,
                              tranche.subordination, tranche.subordination))
        # This writes the last cell of the header.
        lfp.write('Cash Reserve\n')

        # The period is initialized to 0.
        period = 0
        # This loop executes the waterfall and records the results to the output files. The loop
        # continues as long as there is still cash flow from the assets.
        while period == 0 or loaded_pool.totalMonthlyPmt(period) > 0:
            # On the asset side, getWaterfall() returns principal due, interest due, recovery
            # value, total monthly payment, and remaining balance.
            asset_waterfall = loaded_pool.getWaterfall(period)
            if period != 0:
                # This increases the period on the liability side by 1.
                structured_deal.increaseTimePeriodForAll()
                # Making payments to the liabilities requires information about the interest
                # payments and principal payments from the assets.
                structured_deal.makePayments(asset_waterfall[1], asset_waterfall[0])
            # On the liability side, getWaterfall() returns interest due, interest paid,
            # interest shortfall, principal due, principal paid, principal shortfall, remaining
            # balance, cash flow, and cash reserve.
            liability_waterfall, cash_reserve = structured_deal.getWaterfall()
            # Information contained in asset_waterfall is written to asset-side output file.
            afp.write('{0},{1},\n'.format(period, ','.join(map(str, asset_waterfall))))
            lfp.write('{},'.format(period))
            # Information contained in liability_waterfall is written to liability-side file.
            for tranche in liability_waterfall:
                lfp.write('{},'.format(','.join(map(str, tranche))))
            lfp.write('{},\n'.format(cash_reserve))
            # One period is completed, and period is incremented.
            period += 1

    # Now that the waterfall is completed, we can calculated pricing metrics.
    for tranche in structured_deal:
        print('\nClass {}'.format(tranche.subordination))
        # This calculates the IRR for each tranche.
        tranche_IRR = npf.irr(tranche.cashFlow) * 12
        print('IRR: {:.2f}%'.format(tranche_IRR * 100))
        # This calculates the DIRR for each tranche.
        tranche_DIRR = tranche.rate - tranche_IRR
        print('DIRR: {:.2f}bps'.format(abs(tranche_DIRR * 10000)))
        # This uses getRating() function to get teh proper letter rating.
        print('Rating: {}'.format(getRating(tranche_DIRR)))
        # If the tranche is never paid off, then its AL is displayed as None.
        if tranche.notionalBalance() > 0:
            print('AL: None')
        else:
            # This calculates AL using reduce().
            AL = functools.reduce(lambda total, pmt: total + pmt[0] * pmt[1],
                                  enumerate(tranche.principalPaid), 0.0) / tranche.notional
            print('AL: {:.2f} months'.format(AL))


# This function converts DIRR into proper letter rating.
def getRating(DIRR):
    # This dict provides conversion between DIRR and letter rating.
    rating_dict = {0.06: 'Aaa', 0.67: 'Aa1', 1.3: 'Aa2', 2.7: 'Aa3', 5.2: 'A1', 8.9: 'A2',
                   13: 'A3', 19: 'Baa1', 27: 'Baa2', 46: 'Baa3', 72: 'Ba1', 106: 'Ba2',
                   143: 'Ba3', 183: 'B1', 231: 'B2', 311: 'B3', 2500: 'Caa', 10000: 'Ca'}
    if DIRR < 1.0:
        # This returns the best letter rating for which our tranche's DIRR qualifies.
        return rating_dict[min(level for level in rating_dict if level > DIRR * 10000)]
    else:
        # If DIRR is greater than 10000 bps, then the tranche is rated D.
        return 'D'


def main():
    # This loads the 1500 loans from Loans.csv and returns a LoanPool object containing the loans.
    loaded_pool = loadAssets()
    # This calculates the total principal within the assets.
    total_principal = loaded_pool.totalPrincipal()
    # This creates two tranches of different sizes and different subordination levels.
    trancheA = StandardTranche(total_principal * 0.8, 0.13, 'A')
    trancheB = StandardTranche(total_principal * 0.2, 0.23, 'B')
    # This creates the an instance of StructuredSecurities.
    structured_deal = StructuredSecurities()
    # This adds the two tranches to the structured deal.
    structured_deal.addTranche(trancheA, trancheB)
    # This sets whether mode of principal distribution is sequential or pro rata.
    structured_deal.sequential = True
    # This executes the waterfall using the pool of assets and the structured deal.
    doWaterfall(loaded_pool, structured_deal)


# This prevents main() from getting executed when imported.
if __name__ == '__main__':
    main()
