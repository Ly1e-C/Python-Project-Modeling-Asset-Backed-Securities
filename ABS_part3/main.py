'''
Li Jin Chen
12-03-2020
Final Project: This script demonstrates the pricing of tranches using Monte Carlo simulations.
User may choose to run simulations either with multiprocessing or without multiprocessing. The
former uses the runSimulationParallel() function to carry out the inner loop using multiple
sub-processes and cuts down on total runtime. The latter uses simulateWaterfall() function
to carry out the inner loops one by one.
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
import logging
from timer.timer import Timer
import math
import multiprocessing
import copy


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


# This executes the ABS waterfall once and calculates the waterfall metrics.
def doMiniWaterfall(loaded_pool, structured_deal):
    # The period is initialized to 0.
    period = 0
    # This loop executes the waterfall.
    # The loop continues as long as there is still cash flow from the assets.
    while period == 0 or loaded_pool.totalMonthlyPaid(period) > 0:
        # First, we check if any loan within the pool should go into default.
        loaded_pool.checkDefaults(period)
        # On the asset side, getWaterfall() returns principal due, interest due, recovery
        # value, total monthly payment, and remaining balance.
        asset_waterfall = loaded_pool.getWaterfall(period)
        if period != 0:
            # This increases the period on the liability side by 1.
            structured_deal.increaseTimePeriodForAll()
            # Making payments to the liabilities requires information about the interest
            # payments and principal payments from the assets.
            structured_deal.makePayments(asset_waterfall[1], asset_waterfall[0])
        period += 1
    single_res = {}
    for tranche in structured_deal:
        # This calculates the IRR for each tranche.
        tranche_IRR = npf.irr(tranche.cashFlow) * 12
        # This calculates the DIRR for each tranche.
        tranche_DIRR = tranche.rate - tranche_IRR
        # This sets DIRR to 0 below a certain threshold, in order to avoid problems when using
        # DIRR to calculate yield.
        if tranche_DIRR < (tranche.rate * 10 ** (-6)):
            tranche_DIRR = 0.0
        # If the ending balance of the tranche is greater than 0, that means the tranche is not
        # completely paid off. So AL should return None.
        if tranche.notionalBalance() > 0:
            AL = None
        else:
            # This calculates AL using reduce().
            AL = functools.reduce(lambda total, pmt: total + pmt[0] * pmt[1],
                                  enumerate(tranche.principalPaid), 0.0) / tranche.notional
        # Each value to the dict is a tuple that contains DIRR and AL. The key is the tranche's
        # subordination level.
        single_res[tranche.subordination] = (tranche_DIRR, AL)
    # This resets the StructuredSecurities object.
    # For assets, only default period needs to be reset and that's done in every period 0.
    structured_deal.resetAll()
    return single_res


# This simulates out the inner loops when multiprocessing is not used. This carries out the
# waterfall NSIM times and records the average result.
def simulateWaterfall(loaded_pool, structured_deal, NSIM):
    # This list holds the combined results from all the simulations.
    combined_res_list = []
    # This loops through the desired number of simulations.
    for i in range(NSIM):
        # This runs the waterfall one time.
        single_res = doMiniWaterfall(loaded_pool, structured_deal)
        # If any of the tranche's AL is None, then the simulation is considered invalid and not
        # added to the combined list of results.
        invalid_AL = any(single_res[tranche.subordination][1] is None
                         for tranche in structured_deal)
        # If the simulation has valid AL, then it is added to the combined list of results.
        if not invalid_AL:
            combined_res_list.append(single_res)

    # This counts the number of trials with valid Average Life.
    num_valid_trials = len(combined_res_list)
    # If there is 0 trial with valid AL, then an error is raised.
    if num_valid_trials == 0:
        raise ValueError('The number of trials with valid Average Life is 0.')
    else:
        # This prints the number of trials with valid Average Life. This can be helpful information.
        print('\n{0} out of {1} trials with valid Average Life'.format(num_valid_trials, NSIM))

    # This dict will hold the average result.
    res = {}
    for tranche in structured_deal:
        # s is used just to make the code less cumbersome.
        s = tranche.subordination
        # Results from all the simulations will be averaged here.
        # First item of the tuple is DIRR. Second item is AL.
        res[s] = (sum(single_res[s][0] for single_res in combined_res_list) / num_valid_trials,
                  sum(single_res[s][1] for single_res in combined_res_list) / num_valid_trials)
    return res


# This is the function that each process executes.
def doWork(iQueue, oQueue):
    # This extracts the relevant objects from the input queue tuple.
    f, args, n = iQueue.get()
    # This executes the waterfall a number of times and records the results in a list.
    single_process_res_list = [f(*args) for i in range(n)]
    # The list of results is put into the output queue.
    oQueue.put(single_process_res_list)


# This executes the inner loops using parallel processes.
def runSimulationParallel(loaded_pool, structured_deal, NSIM, num_processes):
    # This is the number simulations allocated to each process.
    SIM_per_process = math.ceil(NSIM / num_processes)
    # This is the input queue that feeds parameters to each process.
    iQueue = multiprocessing.Queue()
    # This is the output queue that holds the results.
    oQueue = multiprocessing.Queue()

    # This makes copies of the loaded_pool and structured_deal, so each process can run
    # simulations on its own copy.
    pool_copies = [copy.deepcopy(loaded_pool) for i in range(num_processes)]
    deal_copies = [copy.deepcopy(structured_deal) for i in range(num_processes)]
    # This fills the input queue.
    for i in range(num_processes):
        iQueue.put((doMiniWaterfall, (pool_copies[i], deal_copies[i]), SIM_per_process))

    # This list holds the processes' handles, so they can be terminated later.
    process_handles = []
    # This creates the desired number of processes.
    for i in range(num_processes):
        # This creates one process and gives it the target function and arguments.
        p = multiprocessing.Process(target=doWork, args=(iQueue, oQueue))
        # This adds the process to the list of processes.
        process_handles.append(p)
        # This starts the process.
        p.start()

    # This list holds the combined results.
    combined_res_list = []
    while True:
        # This is blocked until a process provides a list of results.
        r = oQueue.get()
        # This lists of results are combined here.
        combined_res_list.extend(r)
        # Once the desired number of simulations is completed, the whole procedure ends.
        # ">=" is used here because when the total number of simulations is not divisible by
        # the number of processes, each process executing an equal number of simulations
        # means the final number of simulations would be slightly greater than the
        # user-specified NSIM.
        if len(combined_res_list) >= NSIM:
            # This for-loop terminates the spawned processes.
            for p in process_handles:
                p.terminate()
            break

    # This creates a new list by keeping only the results in combined_res_list with non-infinite
    # AL. This essentially drops the trials with infinite ALs.
    valid_res_list = [single_res for single_res in combined_res_list
                      if not any(single_res[tranche.subordination][1] is None
                                 for tranche in structured_deal)]
    # This counts the number of trials with valid Average Life.
    num_valid_trials = len(valid_res_list)
    # If there is 0 trial with valid AL, then an error is raised.
    if num_valid_trials == 0:
        raise ValueError('The number of trials with valid Average Life is 0.')
    else:
        # This prints the number of trials with valid Average Life. This can be helpful information.
        print('\n{0} out of {1} trials with valid Average Life'.format(num_valid_trials, NSIM))

    # This dict will hold the average result.
    res = {}
    for tranche in structured_deal:
        # s is used just to make the code less cumbersome.
        s = tranche.subordination
        # Results from all the simulations will be averaged here.
        # First item of the tuple is DIRR. Second item is AL.
        res[s] = \
            (sum(single_res[s][0] for single_res in valid_res_list) / num_valid_trials,
             sum(single_res[s][1] for single_res in valid_res_list) / num_valid_trials)
    return res


# This is the outer loop. It discovers the optimal rates for the tranches.
def runMonte(loaded_pool, structured_deal, tol, NSIM, num_processes, multi_choice):
    # This counts the number of outer loop.
    loop_counter = 0
    while True:
        # This calls the proper function to run the inner loops, either with multiprocessing or
        # without multiprocessing.
        if multi_choice == '2':
            res = simulateWaterfall(loaded_pool, structured_deal, NSIM)
        else:
            res = runSimulationParallel(loaded_pool, structured_deal, NSIM, num_processes)
        # These variables are used in calculations for optimizing tranche rates. They are dicts
        # because there are different values for different tranches.
        coeff_dict = {'A': 1.2, 'B': 0.8}
        yield_dict = {}
        old_rate_dict = {}
        new_rate_dict = {}
        notional_dict = {}
        diff_dict = {}
        for tranche in structured_deal:
            # s is used just to make the code less cumbersome.
            s = tranche.subordination
            # This calculates the yield.
            yield_dict[s] = calculateYield(res[s][0], res[s][1])
            # This contains the old tranche rates.
            old_rate_dict[s] = tranche.rate
            # This calculates the new tranche rates.
            new_rate_dict[s] = old_rate_dict[s] + coeff_dict[s] * (yield_dict[s] - old_rate_dict[s])
            # This contains the notional values of the tranches.
            notional_dict[s] = tranche.notional
            # This is one part of the formula for checking convergence.
            diff_dict[s] = notional_dict[s] * abs(old_rate_dict[s] - new_rate_dict[s]) / \
                           old_rate_dict[s]
        # This is the other part.
        diff = (diff_dict['A'] + diff_dict['B']) / (notional_dict['A'] + notional_dict['B'])
        loop_counter += 1
        # This prints the temporary results after each outer loop.
        print('{} outer loops complete.'.format(loop_counter))
        print('CLass A rate: {:.2f}%'.format(old_rate_dict['A'] * 100))
        print('Class B rate: {:.2f}%'.format(old_rate_dict['B'] * 100))
        print('diff: {:.5f}'.format(diff))
        # If diff is less than tol, then the simulation is completed.
        if diff < tol:
            logging.info('diff is lower than tolerance. Simulation completes.')
            break
        # Otherwise, we update the tranche rates and repeat the process.
        else:
            for tranche in structured_deal:
                s = tranche.subordination
                tranche.rate = new_rate_dict[s]
    # This prints the final results.
    for tranche in structured_deal:
        s = tranche.subordination
        print('\nClass {}:'.format(s))
        print('Rate: {:.2f}%'.format(old_rate_dict[s] * 100))
        print('Yield: {:.2f}%'.format(yield_dict[s] * 100))
        print('DIRR: {:.2f}bps'.format(res[s][0] * 10000))
        print('Rating: {}'.format(getRating(res[s][0])))
        print('WAL: {:.2f} months'.format(res[s][1]))


# This method helps to calculate yield using DIRR and AL.
def calculateYield(DIRR, AL):
    return (7 / (1 + 0.08 * math.exp(-0.19 * AL / 12)) +
            0.019 * math.sqrt(AL / 12 * DIRR * 100)) / 100


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
    # This sets the logging level so we get helpful messages throughout the process.
    logging.getLogger().setLevel(logging.INFO)
    # This loads the 1500 loans from Loans.csv and returns a LoanPool object containing the loans.
    loaded_pool = loadAssets()
    # This prompts user to choose to run simulations either with multiprocessing or without
    # multiprocessing.
    multi_choice = '0'
    while multi_choice not in ('1', '2'):
        multi_choice = input('How would you like to run the simulations?\n'
                             '1. With multiprocessing\n'
                             '2. Without multiprocessing\n')
        if multi_choice not in ('1', '2'):
            print('Please enter either 1 or 2 as your choice.\n')
    # non_equity is a modifier that is multiplied to the asset side's total principal to get the
    # proper total principal on the liability side. This modifier is set to a value slightly less
    # than 1, otherwise every trial result would be dropped due to infinite AL. This modifier also
    # has real-world significance since originators often have to keep a small and most
    # junior "equity tranche" in their own books. Increasing this modifier closer to 1 will
    # increase the number of trials getting thrown out due to infinite AL.
    non_equity = 0.95
    total_principal = loaded_pool.totalPrincipal() * non_equity
    # This creates two tranches of different sizes and different subordination levels.
    trancheA = StandardTranche(total_principal * 0.8, 0.05, 'A')
    trancheB = StandardTranche(total_principal * 0.2, 0.08, 'B')
    # This creates the an instance of StructuredSecurities.
    structured_deal = StructuredSecurities()
    # This adds the two tranches to the structured deal.
    structured_deal.addTranche(trancheA, trancheB)
    # This sets whether mode of principal distribution is sequential or pro rata.
    structured_deal.sequential = True

    # These are parameters used for the simulation.
    tol = 0.005
    NSIM = 20
    num_processes = 20
    # This carries out the simulation and keeps track of the runtime.
    with Timer('test1'):
        runMonte(loaded_pool, structured_deal, tol, NSIM, num_processes, multi_choice)

    # Running NSIM = 20 for the inner loop takes about 280 seconds without multiprocessing.
    # Therefore, I did not attempt NSIM = 2000. Running NSIM = 2000 with 20 processes took about
    # 1 hour and 45 minutes, which is  still quite a long time. But I estimate it is about 4
    # times faster than if no multiprocessing is used. In both cases, the program converges very
    # quickly on the outer loop, giving similar results:
    #
    # Sequential:
    # Class A:                  Class B:
    # Rate: 6.67%               Rate: 6.79%
    # Yield: 6.66%              Yield: 6.78%
    # DIRR: 0.00bps             DIRR: 0.00bps
    # Rating: Aaa               Rating: Aaa
    # WAL: 28.11 months         WAL: 56.19 months
    #
    # Pro rata:
    # Class A:                  Class B:
    # Rate: 6.70%               Rate: 6.70%
    # Yield: 6.69%              Yield: 6.69%
    # DIRR: 0.00bps             DIRR: 0.00bps
    # Rating: Aaa               Rating: Aaa
    # WAL: 33.72 months         WAL: 33.72 months


# This prevents main() from getting executed when imported.
if __name__ == '__main__':
    main()
