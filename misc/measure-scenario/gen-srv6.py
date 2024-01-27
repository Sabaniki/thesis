from trex_stl_lib.api import *
import argparse
from distutils.util import strtobool
# https://server-network-note.net/2022/03/ethernet-freme-format/
# packet size: 126byte(+FCS 4byte)
#   Ether:  14byte
#   vlan:   4byte
#   IPv6:   40byte
#   v6Ext:  16byte * 2(sid_len) + 8byte
#   IPv4:   20byte
#   UDP:    8byte
# sum of 126byte (without FCS)
# L1 size: 146byte
#   L2: 126byte + 4byte
#   MAC Preamble(+SFD): 8byte
#   IFG: 10G--0.96 nsec, min--12byte

# L2: base: 122byte + tagged_vlan: 4byte + FCS: 4byte


class SRv6(object):
    def __init__ (self):
        #self.fsize =152;
        # default IMIX properties
        # pps: 8550000 ← 1flow
        # -4 means FCS of Ether frame
        #self.imix_table = [ {'size': 256 - 4, 'pps': 4500000, 'isg':0 } for _ in range(1)]
        #self.imix_table = [ {'size': 256 - 4, 'pps': 4400000, 'isg':0 } for _ in range(1)]
        #self.imix_table = [ {'size':  1500, 'pps': 8561643, 'isg':0 } for _ in range(1)]
        self.args = None
        self.imix_table = [ {'size':  126, 'pps': 1, 'isg':0 } for _ in range(1)] # tag vlan 含めて 126byte (without L1 tax and FCS)
        
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
    def get_start_end_ipv6(self, start_ip, end_ip):
        try:
            ip1 = socket.inet_pton(socket.AF_INET6, start_ip)
            ip2 = socket.inet_pton(socket.AF_INET6, end_ip)
            hi1, lo1 = struct.unpack('!QQ', ip1)
            hi2, lo2 = struct.unpack('!QQ', ip2)
            if ((hi1 << 64) | lo1) > ((hi2 << 64) | lo2):
                print("IPv6: start_ip is greater than end_ip")
                sys.exit(2)
            max_p1 = abs(int(lo1) - int(lo2))
            base_p1 = lo1
        except AddressValueError as ex_error:
            print(ex_error)
            sys.exit(2)
        return base_p1, max_p1 + base_p1


    def create_stream(self, size, pps, isg, vm, pg_id):
        # create a base packet and pad it to size
        Eth_frame = Ether(dst="b4:96:91:bb:72:4c", src="b4:96:91:bb:73:74")
        IPv6_pkt = IPv6(src="2001:db8:100:100::1", dst="2001:db8:f3f3:10ca:ed7f::1111", nh=43)
        # SRH = IPv6ExtHdrSegmentRouting(nh=4, type=4, segleft=0, addresses=["2001:db8:9999::1","2001:db8:f3f3:10ca:ed7f::1111"])
        SRH = IPv6ExtHdrSegmentRouting(nh=4, type=4, segleft=1, addresses=["2001:db8:9999::1","2001:db8:f3f3:10ca:ed7f::1111"])
        IPv4_inner_pkt = IP(dst="10.0.0.10", src="10.100.100.100")
        UDP_dgm = UDP(dport=44444, sport=22222)
        inner_pkt = IPv4_inner_pkt/UDP_dgm
        base_pkt = Eth_frame/Dot1Q(vlan=10)/IPv6_pkt/SRH/inner_pkt
        pad_len = max(0, size - len(base_pkt))

        pkt = STLPktBuilder(
            #pkt = base_pkt/pad,
            pkt = base_pkt/Raw(RandString(size=pad_len)),
            vm = vm
        )

        return STLStream(
            packet = pkt,
            #mode = STLTXMultiBurst(pps=self.calc_max_pps(size) if self.use_max else pps, pkts_per_burst=2**32-1, count=2**32-1),
            mode = STLTXCont(pps=self.calc_max_pps(self.args.size) if self.args.use_max else 1),
            #mode = STLTXCont(percentage=100),
            #flow_stats = STLFlowLatencyStats(pg_id = pg_id)
            flow_stats = None
        )

    def get_streams(self, port_id, direction, tunables, **kwargs):
        parser = argparse.ArgumentParser(description='Argparser for {}'.format(os.path.basename(__file__)), 
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--use_max', type=strtobool)
        parser.add_argument('--size', type=int)


        self.args = parser.parse_args(tunables)
        # construct the base packet for the profile
        # 現実に即した計測をする．
        # これでは RSS が10にしかならない
        # key が 10 にしかならない
        # source をバラけさせるとコアが使える
        # ↑やっぱり flow-label をバラそう．するとコアによってバラける．理由は以下↓
        # SRv6 では  IPv6 header の flow-label を使っている？
        # なぜなら，通常 src アドレスは H.Encaps した lo になるので

        #src_ip_range = {'start': "2001:db8:100:100::3", 'end': "2001:db8:100:100:ffff:ffff:ffff:ffff"}
        src_ip_range = {'start': "2001:db8:100:100::1", 'end': "2001:db8:100:100::1"}
        src_min_value = src_ip_range['start']
        src_max_value = src_ip_range['end']

        src_min_value, src_max_value = self.get_start_end_ipv6(src_min_value, src_max_value)

        # dst_ip_range1 = {'start': "2001:db8:f3f3:10ca:ed7f::1111", 'end': "2001:db8:f3f3:10ca:ed7f::1111"}
        # dst_min_value1 = dst_ip_range1['start']
        # dst_max_value1 = dst_ip_range1['end']
        # dst_min_value1, dst_max_value1 = self.get_start_end_ipv6(dst_min_value1, dst_max_value1)

        vm = STLScVmRaw([
            # STLVmFlowVar(
            #     name="ip6_flow",
            #     min_value=0x0000,
            #     max_value=0xffff,
            #     size=2, op="inc"
            # ),
            # STLVmWrFlowVar(fv_name="ip6_flow", pkt_offset="IPv6.fl",offset_fixup=1),
            # STLVmFlowVar(
            #     name="ip6_src",
            #     min_value=src_min_value,
            #     max_value=src_max_value,
            #     size=8, op="inc"
            # ),
            # STLVmWrFlowVar(fv_name="ip6_src", pkt_offset="IPv6.src", offset_fixup=8),
            # STLVmFlowVar(
            #     name="ip6_dst",
            #     min_value=dst_min_value1,
            #     max_value=dst_max_value1,
            #     size=8, op="inc"
            # ),
            # STLVmWrFlowVar(fv_name="ip6_dst", pkt_offset="IPv6.dst", offset_fixup=40),
            STLVmFlowVar(
                name="ip_src",
                min_value="10.100.0.0",
                max_value="10.100.255.254",
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
                min_value="192.168.0.0",
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
        # vm.fix_chksum()
        return [self.create_stream(self.args.size, x['pps'],x['isg'],vm, i) for i, x in enumerate(self.imix_table)]
    #return [ self.create_stream() ]
    #return [ self.create_stream() for i in range(1000)]


# dynamic load - used for trex console or simulator
def register():
    return SRv6()
