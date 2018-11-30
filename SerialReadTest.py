import serial
import sys
import VACSParser

if len(sys.argv) != 3:
    print("Usage: python SerialReadTest.py serial-port-path message-definition-path")
    sys.exit(1)

serial_port_path = sys.argv[1]
message_definition_path = sys.argv[2]

serial_port = open(str(serial_port_path),'rb')#serial.Serial(serial_port_path, 57600)

parser = VACSParser.Parser(message_definition_path)

while True:

    serial_byte = serial_port.read(1)

    if serial_byte:

        parser.parse(serial_byte)

        new_packet = parser.get_packet()

        if new_packet:
            print(new_packet)
            for i in new_packet.message:
                print("  ", i, new_packet.message[i])
