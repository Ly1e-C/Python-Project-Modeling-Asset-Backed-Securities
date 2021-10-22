'''
This module contains the Timer class, which makes tracking runtime easier.
'''
import time
import logging


# Now that the class is used with context manager, it does not need to track if the instance is
# already running, i.e. no need to report error for mistakenly using start() or end() consecutively.
class Timer(object):
    # If runtime exceeds 60 seconds, a WARN statement is displayed instead of an INFO statement.
    _warnThreshold = 60

    # This initializes an instance of the class.
    def __init__(self, label):
        # This records the start time of the timer.
        self._startTime = None
        # This records the time elapsed when the timer is stopped.
        self._runTime = None
        # This gives a label for when runtime is reported.
        self._label = label
        # Time is reported in seconds by default.
        self._display = 'seconds'

    # This is entry point for 'with' statement.
    def __enter__(self):
        # This starts the timer.
        self._startTime = time.time()
        # This returns self so that the instance can be called upon.
        return self

    # This is the automatic exit for the timer.
    def __exit__(self, *args):
        # This calculates the runtime.
        self._runTime = time.time() - self._startTime
        # If runtime exceeds _warnThreshold, it is displayed by WARN statement.
        # Otherwise, it is displayed as INFO statement.
        if self._runTime > self._warnThreshold:
            if self._display == 'seconds':
                logging.warning('{0}: {1} seconds'.format(self._label, self._runTime))
            elif self._display == 'minutes':
                logging.warning('{0}: {1} minutes'.format(self._label, self._runTime / 60))
            elif self._display == 'hours':
                logging.warning('{0}: {1} hours'.format(self._label, self._runTime / 3600))
        else:
            if self._display == 'seconds':
                logging.info('{0}: {1} seconds'.format(self._label, self._runTime))
            elif self._display == 'minutes':
                logging.info('{0}: {1} minutes'.format(self._label, self._runTime / 60))
            elif self._display == 'hours':
                logging.info('{0}: {1} hours'.format(self._label, self._runTime / 3600))
        
    # This allows user to configure display unit.
    def configureTimerDisplay(self, displayUnit):
        # Error is raised if input is not one of the three allowed values.
        if displayUnit in ('seconds', 'minutes', 'hours'):
            self._display = displayUnit
        else:
            raise ValueError('Exception: This is not a valid unit for timer display.')

    # This method reports the last timer result.
    def lastTime(self, displayUnit=None):
        # If no display unit is explicitly given, then it is set to the timer's display unit.
        if displayUnit is None:
            displayUnit = self._display
        # This prints the previous runtime based on the time unit.
        if self._runTime is not None:
            if displayUnit == 'seconds':
                logging.info('Last timer result: {0} seconds'.format(self._runTime))
            elif displayUnit == 'minutes':
                logging.info('Last timer result: {0} minutes'.format(self._runTime/60))
            elif displayUnit == 'hours':
                logging.info('Last timer result: {0} hours'.format(self._runTime/3600))
        # If no runtime is ever recorded, an exception is raised.
        else:
            raise Exception('Exception: No timer result has been recorded.')
