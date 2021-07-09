# -*- coding: utf-8 -*-
#
# Rewrite the device path ('/dev/tty...') as you see fit.
# try `$ pytest tests -s`
# to print results to the standard output.
#
import time
from bbc1.lib.cdexcru920mj_drv import SimpleCdexCru920Mj


def test_cdexcru920mj():

    reader = SimpleCdexCru920Mj('/dev/tty.usbmodem15C1200031')

    for i in range(10):
        time.sleep(2)

        aTags = reader.read()

        print('Case {0}: {1} tag(s):'.format(i, len(aTags)))
        for sTag in aTags:
            print(sTag)

    reader.close()


# end of tests/test_cdexcru920mj_drv.py
