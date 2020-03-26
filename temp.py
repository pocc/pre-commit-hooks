import scapy.all as scapy
from scapy.layers import http

#
def sniff(interface):
    scapy.sniff(iface=interface, store=False, prn=process_sniffed_packet)


def process_sniffed_packet(packet):
    # print(packet)
    # Check if our packet has HTTP layer. If our packet has the HTTP layer and it is HTTPRequest.
    # In this way I am excluding some garbage information in which I am not interested into.
    if packet.haslayer(http.HTTPRequest):
        print(packet.summary())
        return


sniff("en0")
