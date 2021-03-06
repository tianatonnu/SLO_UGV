'''Util methods for UGV'''
import json
import datetime
import subprocess
import sys
import shelve
from dronekit import connect, APIException


def setup_vehicle(configs, v_type):
    '''Sets up self as a rover vehicle'''
    if configs["vehicle_simulated"]:
        veh = scan_ports(configs, v_type)
    else:
        # connect to pixhawk via MicroUSB
        # if we switch back to using the telem2 port, use "/dev/serial0"
        con_str = "/dev/ttyACM0"
        veh = connect(con_str, baud=configs["baud_rate"], wait_ready=True, \
            vehicle_class=v_type, heartbeat_timeout=5, timeout=5)
    veh.configs = configs
    veh.setup()
    return veh


def scan_ports(configs, v_type):
    '''scans TCP ports to find open simulator'''
    itteration = 0
    shelf = shelve.open(configs['simulation']['shelveName'])
    try:
        port = shelf['port']
        print('shelf found')
    except KeyError:
        port = configs['simulation']['defaultPort']
        itteration += 1
        print('not found')
    while True:
        try:
            con_str = "tcp:127.0.0.1:{}".format(port)
            print("Attempting to connect to {}".format(con_str))
            veh = connect(con_str, wait_ready=True, vehicle_class=v_type, \
                heartbeat_timeout=5, timeout=5)
            shelf['port'] = port
            shelf.close()
            break
        except (OSError, APIException):
            port = configs['simulation']['defaultPort'] + itteration
            itteration += 1
            if itteration == 8:
                print('make sure your simulator is running')
                sys.exit(-1)
    return veh


def parse_configs(argv):
    """Parses the .json file given as the first command line argument.
    If no .json file is specified, defaults to "configs.json".
    If the specified .json file is found, returns a dict of the contents.
    """
    if len(argv) == 1:
        read_file = open("configs.json", "r")
    else:
        read_file = open(argv[1], "r")

    return json.load(read_file)


def new_output_file():
    '''Creates a new directory for the current date if not created already
    and creates an output file for all console output in the directory.'''
    curr_time = str(datetime.datetime.today()).split()
    date = curr_time[0]
    time = curr_time[1]

    # makes logs folder if not existing already
    try:
        if sys.platform == "darwin" or sys.platform == "linux" or sys.platform == "linux2":
            subprocess.check_output(["ls", "logs/"], shell=False, stderr=subprocess.STDOUT)
        elif sys.platform == "win32":
            subprocess.check_output(["cd", "logs/"], shell=True, stderr=subprocess.STDOUT)
        else:
            raise Exception("Operating system not recognized")
    except subprocess.CalledProcessError:
        if sys.platform == "darwin" or sys.platform == "linux" or sys.platform == "linux2":
            subprocess.call(["mkdir", "logs/"], shell=False)
        elif sys.platform == "win32":
            # No ls on Windows cmd
            subprocess.call(["mkdir", "logs/"], shell=True)
        else:
            raise Exception("Operating system not recognized")

    # makes folder for the current date in logs folder if not existing already
    try:
        if sys.platform == "darwin" or sys.platform == "linux" or sys.platform == "linux2":
            subprocess.check_output(["ls", "logs/" + date], shell=False, stderr=subprocess.STDOUT)
        elif sys.platform == "win32":
            # No ls on Windows cmd
            subprocess.check_output(["cd", "logs/" + date], shell=True, stderr=subprocess.STDOUT)
        else:
            raise Exception("Operating system not recognized")
    except subprocess.CalledProcessError:
        if sys.platform == "darwin" or sys.platform == "linux" or sys.platform == "linux2":
            subprocess.call(["mkdir", "logs/" + date], shell=False)
        elif sys.platform == "win32":
            # Windows cmd handles mkdir path in a strange way
            subprocess.call(["mkdir", "logs\\" + date], shell=True)
        else:
            raise Exception("Operating system not recognized")

    # open file for current time
    return open("logs/" + date + "/" + time.replace(":", ".") + ".txt", "w")


def get_distance_metres(loc_a, loc_b):
    """
    Returns the ground distance in metres between two LocationGlobal objects.
    This method is an approximation, and will not be accurate over large distances and close to the
    earth's poles. It comes from the ArduPilot test code:
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = loc_b.lat - loc_a.lat
    dlong = loc_b.lon - loc_a.lon
    dalt = loc_b.alt - loc_a.alt
    return sqrt((((dlat**2) + (dlong**2)) * 1.113195e5 ** 2) + (dalt ** 2))
