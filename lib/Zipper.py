import os
import sys
from shutil import make_archive
from shutil import copyfile
from shutil import rmtree
from pathlib import Path
import math
from lib.Logger import Logger
from lib.Helpers import Helpers

# BYTES TO SIZE OF UNIT IN GB
BYTE = 1
KB = 1024 * BYTE
MB = 1048576 * BYTE
GB = 1073741824 * BYTE

class Zipper:
    def __init__(self):
        self.parent_directory = ""
        self.destination = ""
        self.archive_size = 1073741824
        self.logger = None

    def reset(self):
        self.parent_directory = ""
        self.destination = ""
        self.archive_size = 1073741824
        self.logger = None

    def get_name(self, path):
        i = 0
        while os.path.exists(path + 'archive_' + str(i) + '.zip') or os.path.exists(path + 'archive_' + str(i) + '/'):
            i += 1
        
        return 'archive_' + str(i)
    
    def get_bytes(self, amt, unit):
        if unit == "GB":
            return amt * GB
        elif unit == "MB":
            return amt * MB
        else:
            return amt * KB

    def archive_prompt(self):
        valid_unit = False
        unit = ""
        while not valid_unit:
            unit = input("\nPlease select unit: \n[1] GB\n[2] MB\n[3] KB\n--> ")
            if unit.lower() in ["1", "gb"]:
                print("GB Selected.\n")
                unit = "GB"
                valid_unit = True
            elif unit.lower() in ["2", "mb"]:
                print("MB Selected.\n")
                unit = "MB"
                valid_unit = True
            elif unit.lower() in ["3", "kb"]:
                print("KB Selected.\n")
                unit = "KB"
                valid_unit = True
            else:
                print("\nInvalid input...\n")
        
        valid_amt = False
        amt = ""
        while not valid_amt:
            amt = input("Please enter size in {}:\n--> ".format(unit))
            try:
                amt = int(amt)
                print("\nConfiguration completed. Archives will cap at {} {}".format(amt, unit))
                valid_amt = True
            except ValueError:
                try:
                    amt = float(amt)
                    print("\nDetected decimal value...")
                    print("\nConfiguration completed. Archives will cap at {} {}".format(amt, unit))
                    valid_amt = True
                except ValueError:
                    print("\n{} is invalid input...".format(amt))
        
        self.archive_size = self.get_bytes(amt, unit)
        print("Amount to cap in Bytes: {}".format(self.archive_size))
                


    def zip(self, path, groups):
        # shutil.copyFile()
        for group in groups:
            archive_name = self.get_name(self.destination)
            os.mkdir(self.destination + archive_name + '/')
            for f in group:
                f_name = ''
                if '/' in f:
                    f_name = f.split('/').pop()
                else:
                    f_name = f.split('\\').pop()
                # print(f_name)
                print("Copying {} to {}".format(f, self.destination + archive_name + '/' + f_name))
                copyfile(f, self.destination + archive_name + '/' + f_name)
        
        dirs = [f for f in os.listdir(self.destination) if os.path.isdir(self.destination + f + '/')]
        print("Zipping folders...")
        for dir in sorted(dirs):
            print('Current archive: {}'.format(self.destination + dir))
            make_archive(base_name=self.destination + dir, format='zip', root_dir=self.destination + dir + '/')
            print('Completed. Removing temporary directory.\n')
            rmtree(self.destination + dir + '/', ignore_errors=True)
        
        print("Finished...")

    def group_files(self, path):
        global GB

        # get dictionary of (paths, file size) and sort in decreasing order
        files = dict((str(f), f.stat().st_size) for f in path.glob('**/*') if f.is_file() and 'LOW-RES' in str(f))

        # print(files)

        files = {k: v for k, v in sorted(files.items(), key=lambda item: item[1], reverse=True)}
        # file_list = list(files.keys())

        # calculate total size of all dir
        total_size = sum(f.stat().st_size for f in path.glob('**/*') if f.is_file() and 'LOW-RES' in str(f))

        # calculate total num of files in all levels at and below dir
        num_files = sum(f.stat().st_size * 0 + 1 for f in path.glob('**/*') if f.is_file() and 'LOW-RES' in str(f))

        # calculate approx num of groups of 1GB
        num_groups = int(math.ceil(total_size / self.archive_size))

        # calculate approx avg file size
        try:
            avg_size_file = total_size / num_files
        except:
            print("Error thrown: Attempting to divide by zero. Program will now terminate safely.")
            print("Please check filesystem and ensure folders generated by the downscaler program exist.")
            sys.exit(1)

        # calculate approx file count per group
        file_per_group = math.floor(num_files / num_groups)

        # print(file_list)
        print('\nApproximate total size: {} BYTES'.format(total_size))
        print('Approximate num of files: {}'.format(num_files))
        print('Approximate size per files: {} BYTES'.format(avg_size_file))
        print('Approximate number of groups: {}'.format(num_groups))
        print('Approximate number of files per group: {}\n'.format(file_per_group))

        if total_size / num_files > self.archive_size:
            print("Cannot parse files into archive size specified...")
            print("Hint: total size of files divided by number of files is greater " \
                "than the archive size, and therefore cannot be achieved. Select a larger archive size or " \
                "make large files smaller.")
            return

        # loop through files
        # if file fits cap, add it, else add current group to groups and move on
        groups = []
        current_group = []
        remaining_space = self.archive_size
        for _file in files:
            # print(_file)
            if files[_file] < remaining_space:
                current_group.append(_file)
                remaining_space -= files[_file]
            elif files[_file] == remaining_space:
                current_group.append(_file)
                remaining_space = self.archive_size
                groups.append(current_group)
                current_group = []
            else:
                groups.append(current_group)
                current_group = []
                current_group.append(_file)
                remaining_space = self.archive_size - files[_file]
        
        if len(current_group) > 0:
            groups.append(current_group)
        
        print("Actual number of groups created: {}\nStarting to copy files to destination folders...\n".format(len(groups)))
        
        self.zip(path, groups)

    def run(self):
        print('### ZIPPER PROGRAM ###\n')
        help_prompt = str(
            "\nThis program was designed to work in conjunction with the downscaling program " \
            "(which is also bundled in this Digitization.py program). It will require a search " \
            "path (i.e. the path to the starting folder where the program will " \
            "find all images that are products of the downscaling program), " \
            "a destination folder (where the archives will be stored) and a " \
            "maximum size for the archives. It is important to note, the destination " \
            "path MUST be outside of the search path provided, otherwise the program " \
            "will generate an endless loop as it creates new files."
        )
        Helpers.ask_usage(help_prompt)

        path_prompt = "\nPlease input the path to the directory that contains the files: \n --> "
        destination_prompt = "\nPlease input the path to the directory you would like the archive(s) to go: \n --> "

        self.parent_directory = Helpers.get_existing_path(Helpers.path_prompt(path_prompt), True)
        self.destination = Helpers.get_existing_path(Helpers.path_prompt(destination_prompt), True)

        # ask if want something other than a GB
        valid = False

        while not valid:
            non_std = input("\nWould you like the default archive size (1GB cap) or something else? \n[1] or [2]\n--> ")
            if non_std == "" or non_std == "1":
                print("Using default configuration...")
                valid = True
            elif non_std == "2":
                valid = True
                self.archive_prompt()
            else:
                print("\nInvalid input...\n")
                valid = False

        # run
        self.group_files(Path(self.parent_directory))
        
        print('Program complete.\n')
        self.reset()


    """
    Find the target group size. This is the sum of all sizes divided by n.
    Create a list of sizes.
    Sort the files decreasing in size. 
    for each group
        while the remaining space in your group is bigger than the first element of the list
            take the first element of the list and move it to the group
        for each element
            find the elemnet for which the difference between group size and target group size is minimal
        move this elemnt to the group
    """



# C:\Users\aaron\Documents\museum\Aaron_dups_for_testing
# C:\Users\aaron\Documents\museum\New folder