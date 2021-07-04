# -*- coding: utf-8 -*-
#
# Rewrite the simulated data path ('sim-data.txt') as you see fit.
# try `$ pytest tests -s`
# to print results to the standard output.
#
from bbc1.lib.smart_rfid_reader_drv import SimpleRfidReaderSimulator


def test_simulator():

    reader = SimpleRfidReaderSimulator('sim-data.txt')

    for i in range(10):
        aTags = reader.read()

        print('Case {0}: {1} tag(s):'.format(i, len(aTags)))
        for sTag in aTags:
            print(sTag)

    reader.close()


# end of tests/test_simulator_drv.py
