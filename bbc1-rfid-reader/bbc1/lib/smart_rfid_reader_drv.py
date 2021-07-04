# -*- coding: utf-8 -*-
"""
Copyright (c) 2021 beyond-blockchain.org.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from bbc1.lib.simple_rfid_reader_drv import SimpleRfidReader
from bbc1.lib.cdexcru920mj_drv import SimpleCdexCru920Mj


RFID_SIMULATOR      = 0
RFID_CDEX_CRU_920MJ = 1


class SimpleRfidReaderSimulator(SimpleRfidReader):

    def __init__(self, path):
        self._f = open(path)


    def close(self):
        self._f.close()


    def read(self):
        s = self._f.readline().rstrip('\n')

        return s.split(',') if len(s) > 0 else []


# end of smart_rfid_reader_drv.py
