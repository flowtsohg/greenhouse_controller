__author__ = 'netanel'

import logging


class RelayController(object):
    def __init__(self, name, pin, state=0, simulate=True):
        self._name = name
        self._pin = pin
        self._state = state
        self._simulate = simulate
        self._logger = logging.getLogger(name)

    def change_state(self, new_state):
        if self._check_state(new_state):
            if self._simulate:
                self._state = new_state
        else:
            self._logger.info('state: {} is not legal'.format(new_state))

    def get_state(self):
        return self._state

    def get_name(self):
        return self._name

    def _check_state(self, state):
        if state in [1, 0]:
            return True
        else:
            return False

    def __unicode__(self):
        return 'name: {}, pin: {}, state: {}'.format(self._name, self._pin, self._state)

