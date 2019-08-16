from os import chdir, path, getcwd, walk
import re
from Sample import Sample


can_data_filename:          str = ''


class FileBoi:
    def __init__(self):
        self.sample_dict = self.go_fetch()
        # path.exists(output_folder):
        #         mkdir(output_folder)
        #     chdir(output_folder)

    @staticmethod
    def go_fetch(kfold_n: int = 5):
        # NOTE: File structure relative to this script is expected to be as follows.
        # .
        # +-- Captures
        # |   +-- Make x_0
        # |   |   +-- Model y_0
        # |   |   |   +-- ModelYear z_0
        # |   |   |   |   +-- Samples
        # |   |   |   |   |   +-- sample = re.match('loggerProgram[\d]+.log', a_file_in_this_folder)
        # |   +-- Make x_1.... etc.
        # +-- Some folder
        # |   +-- The directory with these scripts
        # |   |   +-- this_script.py

        script_dir: str = getcwd()
        chdir("../../")
        if not path.exists("Captures"):
            # Make sure your local directory structure matches the example above. If not... adjust accordingly
            print("Error finding Captures folder. Please check the relative path between this script and Captures.")
            print("See the source of go_fetch() in FileBoi.py for an example of the expected relative paths.")
            chdir(script_dir)
            quit()

        chdir("Captures")
        root_dir = getcwd()
        make: str = ""
        model: str = ""
        year: str = ""
        current_vehicle = []
        sample_dict = {}
        for dirName, subdirList, fileList in walk(root_dir, topdown=True):
            this_dir = path.basename(dirName)
            if len(subdirList) == 0:
                if len(current_vehicle) == 3:
                    make = current_vehicle[0]
                    model = current_vehicle[1]
                    year = current_vehicle[2]
                elif len(current_vehicle) == 2:
                    model = current_vehicle[0]
                    year = current_vehicle[1]
                elif len(current_vehicle) == 1 and current_vehicle != "":
                    year = current_vehicle[0]
                for file in fileList:
                    # Check if this file name matches the expected name for a CAN data sample. If so, create new Sample
                    m = re.match('loggerProgram[\d]+.log', file)
                    if m:
                        if not (make, model, year) in sample_dict:
                            sample_dict[(make, model, year)] = []
                        this_sample_index = str(len(sample_dict[(make, model, year)]))
                        this_sample = Sample(make=make, model=model, year=year, sample_index=this_sample_index,
                                             sample_path=dirName + "/" + m.group(0), kfold_n=kfold_n)
                        sample_dict[(make, model, year)].append(this_sample)
                current_vehicle = []
            else:
                if this_dir == "Captures":
                    continue
                current_vehicle.append(this_dir)

        chdir(script_dir)
        return sample_dict
