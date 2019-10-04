from pandas import DataFrame, Series
from numpy import dtype


class J1979:
    def __init__(self, pid: int,  original_data: DataFrame, pid_dict: DataFrame):
        self.pid:   int = pid
        self.title: str = pid_dict.at[pid, 'title']
        self.data:  Series = self.process_response_data(original_data, pid_dict)
        print("Found " + str(self.data.shape[0]) + " responses for J1979 PID " + str(hex(self.pid)) + ":", self.title)

    def process_response_data(self, original_data, pid_dict) -> Series:
        A = original_data['b3']
        B = original_data['b4']
        C = original_data['b5']
        D = original_data['b6']
        try:
            return Series(data=pid_dict.at[self.pid, 'formula'](A,B,C,D),
                          index=original_data.index,
                          name=self.title,
                          dtype=dtype(pid_dict.at[self.pid, 'formula'](A,B,C,D)))
        except:
            raise ValueError("Encountered J1979 PID " + str(hex(self.pid)) +
                             " in Pre-Processing that hasn't been programmed. Expand the OBD2_pids.csv file to handle all "
                             "J1979 requests made during data collection.")
