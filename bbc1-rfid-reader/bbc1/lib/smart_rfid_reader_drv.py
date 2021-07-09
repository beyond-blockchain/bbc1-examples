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
import hashlib
import time

from bbc1.core import bbclib
from bbc1.lib.simple_rfid_reader_drv import SimpleRfidReader
from bbclib.libs import bbclib_binary


class Location:

    def __init__(self, latitude, longitude, altitude):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude


    @staticmethod
    def from_serialized(data):
        pass # FIXME


    def serialize(self):
        dat = bytearray(self.latitude.encode())
        dat.extend(self.longitude.encode())
        dat.extend(self.altitude.encode())

        return bytes(dat)


class RfidReadout:

    def __init__(self, iRandom, idTag, timestamp, location, dataTag):
        self.iRandom = iRandom
        self.idTag = idTag
        self.timestamp = timestamp
        self.location = location
        self.dataTag = dataTag


    @staticmethod
    def from_tuple(dataTuple):
        iRandom, idTag, timestamp, location, dataTag, sig, pubkey = dataTuple
        readout = RfidReadout(iRandom, idTag, timestamp, location, dataTag)
        readout.sig = sig
        readout.pubkey = pubkey

        return readout


    @staticmethod
    def from_serialized(data):
        pass # FIXME


    def get_signed_data(self):
        dat = bytearray(bbclib_binary.to_4byte(self.iRandom))
        dat.extend(self.idTag.encode())

        digest0 = hashlib.sha256(bytes(dat)).digest()

        dat = bytearray(bbclib_binary.to_8byte(self.timestamp))
        dat.extend(self.location.serialize())
        dat.extend(self.dataTag.encode())

        digest1 = hashlib.sha256(bytes(dat)).digest()

        dat = bytearray(digest0)
        dat.extend(digest1)

        return (hashlib.sha256(bytes(dat)).digest())


    def serialize(self):
        pass # FIXME


    def sign(self, keypair):
        self.sig = keypair.sign(self.get_signed_data())
        self.pubkey = keypair.public_key


    def to_tuple(self):
        return (
            self.iRandom,
            self.idTag,
            self.timestamp,
            self.location,
            self.dataTag,
            self.sig,
            self.pubkey
        )


    def verify(self, key_type=bbclib.DEFAULT_CURVETYPE):
        keypair = bbclib.KeyPair(curvetype=key_type, pubkey = self.pubkey)

        return keypair.verify(self.get_signed_data(), self.sig)


class SimpleRfidReaderSimulator(SimpleRfidReader):

    def __init__(self, path):
        self._f = open(path)


    def close(self):
        self._f.close()


    def read(self):
        s = self._f.readline().rstrip('\n')

        return s.split(',') if len(s) > 0 else []


class SmartRfidReader:

    def __init__(self, iRandom, reader, key_type=bbclib.DEFAULT_CURVETYPE):
        self._iRandom = iRandom
        self._reader = reader
        self._keypair = bbclib.KeyPair(curvetype=key_type)
        self._keypair.generate()


    def close(self):
        self._reader.close()


    @staticmethod
    def from_serialized(data, reader):
        pass # FIXME


    def get_public_key(self):
        return self._keypair.public_key


    def read(self):
        aS = self._reader.read()
        timestamp = int(time.time())
        aReadout = []

        for idTag in aS:
            readout = RfidReadout(self._iRandom, idTag, timestamp,
                    self._location, '')
            readout.sign(self._keypair)
            aReadout.append(readout.to_tuple())

        return aReadout


    def serialize(self):
        pass # FIXME


    def set_location(self, location):
        self._location = location


# end of smart_rfid_reader_drv.py
