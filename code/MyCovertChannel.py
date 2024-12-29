from CovertChannelBase import CovertChannelBase

# from threading import Event
from scapy.all import IP, UDP, sniff
import math
import random
import time
import warnings

warnings.simplefilter("ignore", SyntaxWarning)


class MyCovertChannel(CovertChannelBase):
    def __init__(self):
        super().__init__()
        self.received_message = ""
        self.received_bits = ""
        self.stop_event = False

    def send(
        self,
        log_file_name,
        min_ttl_val,
        max_ttl_value,
        num_ttl_ranges,
    ):
        """
        Encodes and sends the covert message using TTL field manipulation.

        - min_ttl_val: Minimum TTL value (e.g., 32)
        - max_ttl_val: Maximum TTL value (e.g., 224)
        - num_ttl_ranges: Number of TTL ranges (e.g., 4 for 2-bit encoding)
        """
        binary_message = self.generate_random_binary_message_with_logging(log_file_name)
        range_size = (max_ttl_value - min_ttl_val + 1) // num_ttl_ranges
        bits_per_packet = int(math.log2(num_ttl_ranges))

        start_time = time.time()
        for i in range(0, len(binary_message), bits_per_packet):
            chunk = binary_message[i : i + bits_per_packet].ljust(bits_per_packet, "0")
            value = int(chunk, 2)
            ttl = min_ttl_val + (value * range_size) + random.randint(0, range_size - 1)
            packet = IP(dst="receiver", ttl=ttl) / UDP(dport=12345, sport=12345)
            super().send(packet)

        end_time = time.time()
        duration = end_time - start_time
        capacity = len(binary_message) / duration
        #print(f"Covert Channel Capacity: {capacity:.2f} bps")

    def receive(
        self, log_file_name, min_ttl_val, max_ttl_value, num_ttl_ranges, sender_ip
    ):
        """
        Receives and decodes the covert message from TTL field manipulation.

        - min_ttl_val: Minimum TTL value (e.g., 32)
        - max_ttl_value: Maximum TTL value (e.g., 224)
        - num_ttl_ranges: Number of TTL ranges (e.g., 4 for 2-bit encoding)
        - sender_ip: IP address of the sender
        """
        range_size = (max_ttl_value - min_ttl_val + 1) // num_ttl_ranges
        bits_per_packet = int(math.log2(num_ttl_ranges))

        def process_packet(packet):
            if IP in packet and UDP in packet and packet[IP].src == sender_ip:
                ttl_value = packet[IP].ttl
                if min_ttl_val <= ttl_value <= max_ttl_value:
                    value = (ttl_value - min_ttl_val) // range_size
                    bits = format(value, f"0{bits_per_packet}b")
                    self.received_bits += bits

                    while len(self.received_bits) >= 8:
                        char = self.convert_eight_bits_to_character(
                            self.received_bits[:8]
                        )
                        self.received_message += char
                        self.received_bits = self.received_bits[8:]

                        if char == ".":
                            self.log_message(self.received_message, log_file_name)
                            self.stop_event = True

        sniff(
            filter="udp and port 12345",
            prn=lambda pkt: process_packet(pkt),
            stop_filter=self.stop_filter,
        )

    def stop_filter(self, packet):
        return self.stop_event
