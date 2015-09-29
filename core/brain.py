__author__ = 'netanel'

import cfg
import logging
from datetime import datetime, timedelta
from sensors.dht22_temp_controller import DHT22TempController
from sensors.dht22_humidity_controller import DHT22HumidityController
import csv
import time
import threading
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenhouse_django_project.settings')
import django
django.setup()
from greenhouse_app.models import Sensor, Measure


class Brain(threading.Thread):
    """
    main control object
     - reads data from sensors
     - controls all output relays
     - makes decisions according to time, sensors, cfg file
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self._logger = logging.getLogger(__name__)
        self._sensors = []
        self._create_sensor_controllers()
        self._last_read_time = datetime.now()
        self._reading_issue_time = datetime.now()
        self._data_lock = threading.RLock()
        self._data = []
        #self._csv_writer = self.initialise_csv()
        self._killed = False

    def run(self):
        while not self._killed:
            if datetime.now() - self._last_read_time > timedelta(seconds=cfg.READING_RESOLUTION):
                self._reading_issue_time = self._last_read_time = datetime.now()
                self.issue_sensor_reading()

                time.sleep(cfg.READING_TIME)
                self.issue_data_gathering()
                #self._write_data_to_csv()
                self._write_data_to_db()
                # do many things

            time.sleep(1)
        self._logger.info('brain killed')

    def get_current_data(self):
        with self._data_lock:
            return self._data

    def _create_sensor_controllers(self):
        """
        build controllers for all sensors
        - DHT22_SENSORS
        - add more later
        """
        #for s in cfg.DHT22_SENSORS:
        for s in Sensor.objects.order_by():
            self._logger.debug('found sensor: ({}), creating controller'.format(s))

            if s.kind.kind == 'dht22temp':
                self._logger.debug('sensor: ({}) is dht22temp, creating controller'.format(s))
                self._sensors.append(DHT22TempController(name=s.name, pin_number=s.pin, simulate=s.simulate))

            elif s.kind.kind == 'dht22humidity':
                self._logger.debug('sensor: ({}) is dht22humidity, creating controller'.format(s))
                self._sensors.append(DHT22HumidityController(name=s.name, pin_number=s.pin, simulate=s.simulate))

    def issue_sensor_reading(self):
        self._logger.debug('issuing a read for all sensors')
        for s in self._sensors:
            s.read()

    def issue_data_gathering(self):
        self._logger.debug('issuing a data gather for all sensors')
        with self._data_lock:
            self._data = []
            for s in self._sensors:
                self._data.append(s.get_read())

    def _write_data_to_csv(self):
        self._logger.debug('in _write_data_to_csv')
        csv_outpud_dictionary = dict()
        csv_outpud_dictionary['time'] = datetime.now()
        with self._data_lock:
            for d in self._data:
                csv_outpud_dictionary.update(d)

        self._logger.debug('writing line: {}'.format(csv_outpud_dictionary))
        self._csv_writer.writerow(csv_outpud_dictionary)

    def _write_data_to_db(self):
        self._logger.debug('in _write_data_to_db')
        with self._data_lock:
            for d in self._data:
                self._logger.debug('looking for sensor: {} in Sensors Table'.format(d.sensor_name))
                sensor = Sensor.objects.get(name=d.sensor_name)
                Measure.objects.create(sensor=sensor, time=d.time, val=d.value)


    def initialise_csv(self):
        self._logger.info('opening .csv file')
        f = open(name='logs/data_{}.csv'.format(datetime.now()), mode='wb', buffering=1)
        sensor_names = [s.get_read().keys() for s in self._sensors]
        fieldnames = ['time']
        [fieldnames.extend(n) for n in sensor_names]
        self._logger.info('writing to .csv file headers: {}'.format(fieldnames))
        csv_writer = csv.DictWriter(f=f, fieldnames=fieldnames)
        csv_writer.writeheader()
        return csv_writer

    def kill_brain(self):
        self._logger.info('killing brain thread')
        self._killed = True


def init_logging():
    logger = logging.getLogger()
    s_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(filename='logs/greenHouseCntrl_{}.log'.format(datetime.now().strftime('%d-%m-%y_%H:%M:%S.%f')))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    s_handler.setFormatter(formatter)
    f_handler.setFormatter(formatter)
    logger.addHandler(s_handler)
    logger.addHandler(f_handler)
    logger.setLevel(cfg.LOG_LEVEL)


if __name__ == '__main__':
    init_logging()
    b = Brain()
    b.setDaemon(True)
    b.start()

    name = raw_input("Do you want to exit? (Y)")
    print 'user entered {}'.format(name)
    if name == 'Y':
        b.kill_brain()
        time.sleep(2)

