from pandas import DataFrame, Series
from numpy import int8, float16, uint8, uint16


class J1979:
    def __init__(self, pid: int,  original_data: DataFrame):
        self.pid:   int = pid
        self.title: str = ""
        self.data:  Series = self.process_response_data(original_data)
        print("Found " + str(self.data.shape[0]) + " responses for J1979 PID " + str(hex(self.pid)) + ":", self.title)

    def process_response_data(self, original_data) -> Series:
        # ISO-TP formatted Universal Diagnostic Service (UDS) requests that were sent by the CAN collection device
        # during sampling. Request made using Arb ID 0x7DF with DLC of 8. Response should use Arb ID 7E8 (0x7DF + 0x8).

        #                    DataFrame Columns: b0 b1 b2 b3 ... b7
        #                                       -- -- -- --     --
        # PID 0x0C (12 dec) (Engine RPM):       02 01 0c 00 ... 00
        # PID 0x0D (13 dec) (Vehicle Speed):    02 01 0d 00 ... 00
        # PID 0x11 (17 dec) (Trottle Pos.):     02 01 11 00 ... 00
        # PID 0x61 (97 dec) (Demand % Torque):  02 01 61 00 ... 00
        # PID 0x62 (98 dec) (Engine % Torque):  02 01 62 00 ... 00
        # PID 0x63 (99 dec) (Ref. Torque):      02 01 63 00 ... 00
        # PID 0x8e (142 dec) (Friction Torque): 02 01 8e 00 ... 00

        # Responses being managed here should follow the ISO-TP + UDS per-byte format AA BB CC DD .. DD
        # BYTE:         AA                    BB             CC          DD ... DD
        # USE:  response size (bytes)   UDS mode + 0x40    UDS PID     response data
        # DF COLUMN:    b0                    b1             b2          b3 ... b7

        # Remember that this response data is already converted to decimal. Thus, byte BB = 65 = 0x41 = 0x01 + 0x40.
        # If BB isn't 0x41, check what the error code is. Some error code are listed in the UDS chapter of the car
        # hacker's handbook available at http://opengarages.org/handbook/ebook/.
        if self.pid == 12:
            self.title = 'Engine RPM'
            # PID is 0x0C: Engine RPM. 2 byte of data AA BB converted using 1/4 RPM per bit: (256*AA+BB)/4
            # Min value: 0      Max value: 16,383.75    units: rpm
            return Series(data=(256*original_data['b3']+original_data['b4'])/4,
                          index=original_data.index,
                          name=self.title,
                          dtype=float16)
        elif self.pid == 13:
            self.title = 'Speed km/h'
            # PID is 0x0D: Vehicle Speed. 1 byte of data AA using 1km/h per bit: no conversion necessary
            # Min value: 0      Max value: 255 (158.44965mph)   units: km/h
            return Series(data=original_data['b3'],
                          index=original_data.index,
                          name=self.title,
                          dtype=uint8)
        elif self.pid == 17:
            self.title = 'Throttle %'
            # PID is 0x11: Throttle Position. 1 byte of data AA using 100/255 % per bit: AA * 100/255% throttle.
            # Min value: 0      Max value: 100          units: %
            return Series(data=100 * original_data['b3'] / 255,
                          index=original_data.index,
                          name=self.title,
                          dtype=uint8)
        elif self.pid == 97:
            self.title = 'Demand Torque %'
            # PID is 0x61: Driver's demand engine - percent torque. 1 byte of data AA using 1%/bit with -125 offset
            # AA - 125
            # Min value: -125   Max value: 130          units: %
            return Series(data=original_data['b3'] - 125,
                          index=original_data.index,
                          name=self.title,
                          dtype=int8)
        elif self.pid == 98:
            self.title = 'Actual Torque %'
            # PID is 0x62: Actual engine - percent torque. 1 byte of data AA using 1%/bit with -125 offset
            # AA - 125
            # Min value: -125   Max value: 130          units: %
            return Series(data=original_data['b3'] - 125,
                          index=original_data.index,
                          name=self.title,
                          dtype=int8)
        elif self.pid == 99:
            self.title = 'Reference Torque Nm'
            # PID is 0x63: Engine reference torque. 2 byte of data AA BB using 1 Nm/bit: 256*AA + BB Nm torque
            # Min value: 0   Max value: 65,535          units: Nm
            return Series(data=256*original_data['b3'] + original_data['b4'],
                          index=original_data.index,
                          name=self.title,
                          dtype=uint16)
        elif self.pid == 142:
            self.title = 'Engine Friction Torque %'
            # PID is 0x8E: Engine Friction - Percent Torque. 1 byte of data AA using 1%/bit with -125 offset. AA - 125
            # Min value: -125   Max value: 130          units: %
            return Series(data=original_data['b3'] - 125,
                          index=original_data.index,
                          name=self.title,
                          dtype=int8)
        else:
            # Looks like you were requesting J1979 data with your sniffer that hasn't been implemented in this code.
            # Time to do the leg work to expand this class accordingly then re-run the pipeline.
            raise ValueError("Encountered J1979 PID " + str(hex(self.pid)) +
                             " in Pre-Processing that hasn't been programmed. Expand the J1979 class to handle all "
                             "J1979 requests made during data collection.")
