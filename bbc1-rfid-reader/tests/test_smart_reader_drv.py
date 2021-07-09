# -*- coding: utf-8 -*-
#
# Rewrite the device path ('/dev/tty...') as you see fit.
# Rewrite the simulated data path ('sim-data.txt') as you see fit.
# try `$ pytest tests -s`
# to print results to the standard output.
#
import datetime
import time
from bbc1.lib.cdexcru920mj_drv import SimpleCdexCru920Mj
from bbc1.lib.smart_rfid_reader_drv import SimpleRfidReaderSimulator
from bbc1.lib.smart_rfid_reader_drv import RfidReadout, SmartRfidReader
from bbc1.lib.smart_rfid_reader_drv import Location


def test_smart_rfid_reader():

    readers = [
        ('CDEX CRU-920MJ', SimpleCdexCru920Mj('/dev/tty.usbmodem15C1200031')),
        ('Simulator', SimpleRfidReaderSimulator('sim-data.txt'))
    ]

    for (name, reader) in readers:
        print('Base reader: {0}'.format(name))
        smartReader = SmartRfidReader(12345678, reader)
        smartReader.set_location(
                Location('3568.0959N', '13976.7307E', '-29.19'))

        for i in range(10):
            time.sleep(2)

            aReadout = smartReader.read()

            print('Case {0}: {1} tag(s):'.format(i, len(aReadout)))

            for t in aReadout:
                readout = RfidReadout.from_tuple(t)
                assert readout.verify() == True
                print('{0} at {1}'.format(readout.idTag,
                        datetime.datetime.fromtimestamp(readout.timestamp)))

        smartReader.close()


# end of tests/test_smart_reader_drv.py
