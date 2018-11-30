from enum import Enum
import VACSMessages
import struct


class Parser:

    class Packet:
        src_addr = 0
        dst_addr = 0
        message_id = 0
        data = bytearray()
        message = {}

        def __str__(self):
            return "VACS.Parser.Packet(src=" + str(self.src_addr) + ",dst=" + str(self.dst_addr) + ",m_id=" + str(self.message_id) + ",data_len=" + str(len(self.data)) + ")"

    class States(Enum):
        sync0 = 0
        sync1 = 1
        dst_addr = 2
        src_addr = 3
        msg_id_lsb = 4
        msg_id_msb = 5
        length_lsb = 6
        length_msb = 7
        data = 8
        chka = 9
        chkb = 10
        none = 11

    def __init__(self, message_definition_path):
        self.state = Parser.States.none
        self.packet_working = Parser.Packet()
        self.chk_a = 0
        self.chk_b = 0
        self.length = 0
        self.data_length = 0
        self.sync_error_count = 0
        self.constraints_error_count = 0
        self.checksum_error_count = 0
        self.correct_message_count = 0
        self.current_byte = 0
        self.packet_ready = False
        self.packet_finished = None
        self.decoder = VACSMessages.Decoder(message_definition_path)

        self.switcher = {
            Parser.States.sync0: Parser.parse_sync0,
            Parser.States.sync1: Parser.parse_sync1,
            Parser.States.dst_addr: Parser.parse_dst_addr,
            Parser.States.src_addr: Parser.parse_src_addr,
            Parser.States.msg_id_lsb: Parser.parse_msg_id_lsb,
            Parser.States.msg_id_msb: Parser.parse_msg_id_msb,
            Parser.States.length_lsb: Parser.parse_length_lsb,
            Parser.States.length_msb: Parser.parse_length_msb,
            Parser.States.data: Parser.parse_data,
            Parser.States.chka: Parser.parse_chka,
            Parser.States.chkb: Parser.parse_chkb,
            Parser.States.none: Parser.parse_none,
        }

        self.expected_sync_0 = 0x76
        self.expected_sync_1 = 0x63
        self.payload_size_max = 1024

    def get_message_id(self, message_name):
        return self.decoder.getMessageID(message_name)

    def create_message_packet(self, message_id, message_data, src_addr, dst_addr):
        output = bytearray()
        output.extend(struct.pack('B', self.expected_sync_0))
        output.extend(struct.pack('B', self.expected_sync_1))
        output.extend(struct.pack('B', dst_addr))
        output.extend(struct.pack('B', src_addr))
        output.extend(struct.pack('h', message_id))
        payload = self.decoder.createMessagePayload(message_id, message_data)
        output.extend(struct.pack('h', len(payload)))
        output.extend(payload)
        checksum = self.compute_checksum(output[2:])
        output.extend(checksum)
        return output

    def compute_checksum(self, data):
        chk_a = 0
        chk_b = 0
        for i in data:
            chk_a = (chk_a + i) % 256
            chk_b = (chk_b + chk_a) % 256
        output = bytearray([chk_a, chk_b])
        return output

    def get_packet(self):
        if self.packet_ready:
            self.packet_ready = False
            return self.packet_finished
        else:
            return False

    def parse(self, incoming_byte):
        self.current_byte = incoming_byte[0]
        func = self.switcher.get(
            self.state, lambda: "Invalid state in VACS.Parser.parse")
        func(self)

    def parse_sync0(self):
        if self.current_byte == self.expected_sync_0:
            self.chk_a = 0
            self.chk_b = 0
            self.state = Parser.States.sync1
        else:
            self.sync_error_count += 1
            self.state = Parser.States.none

    def parse_sync1(self):
        if self.current_byte == self.expected_sync_1:
            self.state = Parser.States.dst_addr
        else:
            self.sync_error_count += 1
            self.state = Parser.States.none

    def parse_dst_addr(self):
        self.chk_a = (self.chk_a + self.current_byte) % 256
        self.chk_b = (self.chk_b + self.chk_a) % 256
        self.packet_working.dst_addr = self.current_byte
        self.state = Parser.States.src_addr

    def parse_src_addr(self):
        self.chk_a = (self.chk_a + self.current_byte) % 256
        self.chk_b = (self.chk_b + self.chk_a) % 256
        self.packet_working.src_addr = self.current_byte
        self.state = Parser.States.msg_id_lsb

    def parse_msg_id_lsb(self):
        self.chk_a = (self.chk_a + self.current_byte) % 256
        self.chk_b = (self.chk_b + self.chk_a) % 256
        self.packet_working.message_id = self.current_byte
        self.state = Parser.States.msg_id_msb

    def parse_msg_id_msb(self):
        self.chk_a = (self.chk_a + self.current_byte) % 256
        self.chk_b = (self.chk_b + self.chk_a) % 256
        self.packet_working.message_id += (self.current_byte * 256)
        self.state = Parser.States.length_lsb

    def parse_length_lsb(self):
        self.chk_a = (self.chk_a + self.current_byte) % 256
        self.chk_b = (self.chk_b + self.chk_a) % 256
        self.length = self.current_byte
        self.state = Parser.States.length_msb

    def parse_length_msb(self):
        self.chk_a = (self.chk_a + self.current_byte) % 256
        self.chk_b = (self.chk_b + self.chk_a) % 256
        self.length += (self.current_byte * 256)
        if self.length > self.payload_size_max:
            self.constraints_error_count += 1
            self.state = Parser.States.none
        else:
            self.packet_working.data = bytearray()
            self.data_length = 0
            if self.length > 0:
                self.state = Parser.States.data
            else:
                self.state = Parser.States.chka

    def parse_data(self):
        self.chk_a = (self.chk_a + self.current_byte) % 256
        self.chk_b = (self.chk_b + self.chk_a) % 256
        self.packet_working.data.append(self.current_byte)
        self.data_length += 1
        if self.data_length == self.length:
            self.state = Parser.States.chka

    def parse_chka(self):
        if self.chk_a == self.current_byte:
            self.state = Parser.States.chkb
        else:
            self.checksum_error_count += 1
            self.state = Parser.States.none

    def parse_chkb(self):
        if self.chk_b == self.current_byte:
            self.packet_finished = self.packet_working
            self.packet_finished.message = self.decoder.decode(
                self.packet_finished)
            self.packet_ready = True
            self.correct_message_count += 1
            self.state = Parser.States.sync0
        else:
            self.checksum_error_count += 1
            self.state = Parser.States.none

    def parse_none(self):
        if self.current_byte == self.expected_sync_0:
            self.chk_a = 0
            self.chk_b = 0
            self.state = Parser.States.sync1
