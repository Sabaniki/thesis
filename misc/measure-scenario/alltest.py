from trex_stl_lib.api import *
from math import log, floor
import time
import argparse
import csv
import os
import subprocess
from distutils.util import strtobool

def human_format(number):
    units = ['', 'K', 'M', 'G', 'T', 'P']
    k = 1000.0
    if number < 1:
        return number
    magnitude = int(floor(log(number, k)))
    return '%.4f %s' % (number / k**magnitude, units[magnitude])
parser = argparse.ArgumentParser()
parser.add_argument("--param", "-p", required=True, nargs="*", type=int, help='a list of varied parameters during measurement')
parser.add_argument("--param_name", "-pn", required=True, type=str, help='a parameter name of varied parameters during measurement')
parser.add_argument("--file_name", "-f", type=str, help="output file name '[file_name].csv' will be generated")
parser.add_argument("--use_max", required=True, type=strtobool, help='to use or not to use max pps')

args = parser.parse_args()
if os.path.isfile(f"./result/{args.file_name}.csv"):
    print(f"'./result/{args.file_name}.csv' is already exist.")
    if input(f"Can I override the file?: yes / no: ") != "yes":
        exit()
c = STLClient(username = "sabaniki")
try:
    c.connect()
    with open(f"./result/{args.file_name}.csv", 'w') as file:
        writer = csv.writer(file)
        writer.writerow([args.param_name, "throughput"])
        for x in args.param:
            # ssh_res = subprocess.Popen(
            #     f"/home/sabaniki/measure-scenario/update-nft.sh {str(x)}",
            #     stdout=subprocess.PIPE,
            #     shell=True
            # ).communicate()[0].decode('utf-8')
            # print(f"command executed via ssh:\n{ssh_res}")
            c.reset()

            c.clear_stats()
            c.start_line(f" -f /home/sabaniki/measure-scenario/gen-srv6.py -d 60 -p 0 -t use_max={args.use_max},size={x}")
            # c.start_line(f" -f /home/sabaniki/measure-scenario/gen-srv6.py -d 60 -p 0 -t use_max=no,size={x}")
            print(f"exec as `start -f /home/sabaniki/measure-scenario/gen-srv6.py -d 60 -p 0 -t use_max={args.use_max},size={x}`")

            # c.start_line(f" -f /home/sabaniki/measure-scenario/gen-udp.py -d 60 -p 0 -t use_max={args.use_max},size=126")
            # print(f"exec as `start -f /home/sabaniki/measure-scenario/gen-sudp.py -d 60 -p 0 -t use_max={args.use_max},size=126`")
            # c.start_line(f" -f /home/sabaniki/measure-scenario/gen-udp.py -d 60 -p 0 -t use_max={args.use_max},size={x}")
            # print(f"exec as `start -f /home/sabaniki/measure-scenario/gen-sudp.py -d 60 -p 0 -t use_max={args.use_max},size={x}`")

            #c.wait_on_traffic(ports = [0])

            if c.get_warnings():
                print(c.get_warnings())
            time.sleep(20)
            print(f"Tx: {human_format(c.get_stats()[0]['tx_bps_L1'])}bps")
            print(f"Tx: {human_format(c.get_stats()[0]['tx_pps'])}pps")
            print(f"Rx: {human_format(c.get_stats()[0]['rx_bps_L1'])}bps")
            print(f"Rx: {human_format(c.get_stats()[0]['rx_pps'])}pps")
            c.stop()
            writer.writerow([x, c.get_stats()[0]['rx_bps_L1']])
            # writer.writerow([x, c.get_stats()[0]['rx_bps']])
            print(f"{'-'*8}the {x} part is done{'-'*8}\n")
            
            # if x != args.param[-1] and input("continue?: No-- input 'f' / Yes-- the other: ") == "f":
            #     break
finally:
    c.disconnect()
    print("disconnected from the T-Rex server")
    print("\a")


# 正しく統計値として出すということはみんなやるので，探せばあるのでは？
# 多分そうだよね？ で進んではならない