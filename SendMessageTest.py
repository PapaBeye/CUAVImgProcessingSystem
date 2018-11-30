import serial
import sys
import VACSParser

if len(sys.argv) != 3:
    print("Usage: python SendMessageTest.py serial-port-path message-definition-path")
    sys.exit(1)

serial_port_path = sys.argv[1]
message_definition_path = sys.argv[2]

serial_port = serial.Serial(serial_port_path, 57600)

parser = VACSParser.Parser(message_definition_path)

# Test 1: Text Message

my_tail_number = 99

message_id = parser.get_message_id("message report")

message_data = {
    'fcs/msg_code': 1,
    'fcs/msg_text': "This is a test message"
}

message_buffer = parser.create_message_packet(message_id, message_data, my_tail_number, 0)

serial_port.write(message_buffer)
serial_port.flush()

# Test 2: FCS Settings Message

message_id = parser.get_message_id("Fixed FCS Settings")

message_data = {
    'config/fcs_mode': 0,
    'config/nav_mode': 1,
    'config/remote_mode': 1,
    'config/target_altitude': 150,
    'config/target_airspeed': 35,
    'config/arrival_range': 50,
    'config/loiter_radius': 100,
    'config/loiter_rtlr_airspeed': 32,
    'config/rtl_min_altitude': 200,
    'config/loiter_course_gain': 0.5,
    'config/crosstrack_kp': 0.28
}

message_buffer = parser.create_message_packet(message_id, message_data, my_tail_number, 21)

serial_port.write(message_buffer)
serial_port.flush()
