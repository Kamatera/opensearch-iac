import time
from scapy.all import rdpcap, IP, UDP, Raw, send

pcap_file = ".data/sflow.pcap"
dst_ip = "127.0.0.1"
dst_port = 6343

packets = rdpcap(pcap_file)
while True:
    print(f'Sending {len(packets)} packets...')
    for pkt in packets:
        if UDP in pkt and pkt[UDP].dport == 6343:
            sflow_payload = b'\x00\x00' + pkt[UDP].payload.load
            new_pkt = IP(dst=dst_ip) / UDP(dport=dst_port) / sflow_payload
            send(new_pkt, verbose=0, realtime=False)
    time.sleep(1)
