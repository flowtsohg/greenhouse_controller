__author__ = 'netanel'


from sensor_controller import SensorController, Measurement
from django.utils import timezone
import random


class DHT22HumidityController(SensorController):
    """
    DHT22 temperature & humidity sensor controller
    """
    def __init__(self, name, dht22_driver, simulate=True):
        super(DHT22HumidityController, self).__init__(name)
        self._dht22_driver = dht22_driver
        self._last_read = Measurement(sensor_name=self._name, time=timezone.now(), value=None)
        self._simulate = simulate

    def read(self):
        super(DHT22HumidityController, self).read()
        if self._simulate:
            h = self.simulate_data()
        else:
            h = self._dht22_driver.get_humidity()
            if h is None:
                self._logger.error('could not read data from sensor: {},'.format(self._name))
                return None
        self._last_read = Measurement(sensor_name=self._name, time=timezone.now(), value=h)
        self._logger.debug('read: {}'.format(self._last_read))
        return self._last_read

    def simulate_data(self):
        return random.randint(30, 90)
