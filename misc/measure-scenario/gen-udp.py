from trex_stl_lib.api import *
from trex_stl_lib.api import *
import argparse
from distutils.util import strtobool
# https://server-network-note.net/2022/03/ethernet-freme-format/


class SRv6(object):
    def __init__ (self):
        #self.fsize =152;
        # default IMIX properties
        # pps: 8550000 ← 1flow
        # -4 means FCS of Ether frame
        #self.imix_table = [ {'size': 256 - 4, 'pps': 4500000, 'isg':0 } for _ in range(1)]
        #self.imix_table = [ {'size': 256 - 4, 'pps': 4400000, 'isg':0 } for _ in range(1)]
        self.imix_table = [ {'size':  126, 'pps': 1, 'isg':0 } for _ in range(1)]
        
        # IP packet として short packet でやって欲しい
    def calc_max_pps(self, size):        
        tax = [
            4,  # FCS
            8,  # MAC Preamble(+SFD)
            12  # IFG (min)
        ]
        real_size = size + sum(tax)
        bps = 100 * 10**9 # 100 Gbps
        pps = bps / (real_size * 8)
        return int(pps)

    def create_stream(self, size, pps, isg, vm, pg_id):
        # create a base packet and pad it to size
        Eth_frame = Ether(dst="b4:96:91:bb:72:4c", src="cc:aa:ee:9e:d9:08")
        IPv4_pkt = IP(dst="10.0.0.10", src="10.100.100.100")
        UDP_dgm = UDP(dport=44444, sport=22222)
        base_pkt = Eth_frame/Dot1Q(vlan=10)/IPv4_pkt/UDP_dgm
        pad_len = max(0, size - len(base_pkt))

        pkt = STLPktBuilder(
            pkt = base_pkt/Raw(RandString(size=pad_len)),
            #pkt = base_pkt,
            vm = vm
        )

        return STLStream(
            packet = pkt,
            mode = STLTXCont(pps=self.calc_max_pps(self.args.size) if self.args.use_max else 1),
            flow_stats = None
        )

    def get_streams(self, port_id, direction, tunables, **kwargs):
        parser = argparse.ArgumentParser(description='Argparser for {}'.format(os.path.basename(__file__)), 
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--use_max', type=strtobool)
        parser.add_argument('--size', type=int)
        # construct the base packet for the profile
        # 現実に即した計測をする．
        # これでは RSS が10にしかならない
        # key が 10 にしかならない
        # source をバラけさせるとコアが使える
        # ↑やっぱり flow-label をバラそう．するとコアによってバラける．理由は以下↓
        # SRv6 では  IPv6 header の flow-label を使っている？
        # なぜなら，通常 src アドレスは H.Encaps した lo になるので

        # dst_ip_range1 = {'start': "2001:db8:f3f3:10ca:ed7f::1111", 'end': "2001:db8:f3f3:10ca:ed7f::1111"}
        # dst_min_value1 = dst_ip_range1['start']
        # dst_max_value1 = dst_ip_range1['end']
        # dst_min_value1, dst_max_value1 = self.get_start_end_ipv6(dst_min_value1, dst_max_value1)
        self.args = parser.parse_args(tunables)
        vm = STLScVmRaw([
            STLVmFlowVar(
                name="ip_src",
                min_value="10.100.100.1",
                max_value="10.100.100.254",
                size=4,
                step=1,
                op="inc"
            ),
            STLVmWrFlowVar(
                fv_name="ip_src",
                pkt_offset="IP.src",
            ), # write ip to packet IP.src
            STLVmFlowVar(
                name="ip_dst",
                min_value="192.168.0.1",
                max_value="192.168.255.254",
                size=4,
                step=1,
                op="inc"
            ),
            STLVmWrFlowVar(
                fv_name="ip_dst",
                pkt_offset="IP.dst",
            ), # write ip to packet IP.src
            STLVmFixIpv4(offset="IP"),
        ])
        return [self.create_stream(self.args.size, x['pps'],x['isg'],vm, i) for i, x in enumerate(self.imix_table)]
    #return [ self.create_stream() ]
    #return [ self.create_stream() for i in range(1000)]


# dynamic load - used for trex console or simulator
def register():
    return SRv6()
