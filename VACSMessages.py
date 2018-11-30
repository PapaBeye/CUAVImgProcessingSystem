import xml.etree.ElementTree as ET
import struct


class Message:
    message_id = 0
    name = ""
    field_names = []
    field_types = []
    length = 0

    def __str__(self):
        return str(self.message_id) + ":" + self.name + "(fields=" + ':'.join(self.field_names) + ",types=" + ':'.join(self.field_types) + ')'


class Decoder:

    namespace = '{http://www.engineering.vcu.edu/uav/PlaneDefinition}'

    def __init__(self, message_definition_path):

        self.messages = {}
        self.message_ids = {}

        tree = ET.parse(message_definition_path)
        root = tree.getroot()

        xml_messages = root.findall(Decoder.namespace + 'message')

        for xml_message in xml_messages:

            message = Message()
            message.name = xml_message.find(Decoder.namespace + 'name').text
            message.message_id = int(xml_message.find(
                Decoder.namespace + 'code').text)
            message.field_names = []
            message.field_types = []
            message.length = 0
            format = xml_message.find(Decoder.namespace + 'format')
            for field in format.findall(Decoder.namespace + 'field'):
                field_name = field.find(Decoder.namespace + 'property').text
                field_type = field.find(Decoder.namespace + 'type').text
                message.field_names.append(field_name)
                message.field_types.append(field_type)
                message.length += self.field_size(field_type)
            self.messages[message.message_id] = message
            self.message_ids[message.name] = message.message_id

    def getMessageID(self, message_name):
        return self.message_ids[message_name]

    def field_size(self, field_type):
        if field_type == 'byte' or field_type == 'sbyte':
            return 1
        elif field_type == 'short' or field_type == 'ushort':
            return 2
        elif field_type == 'float' or field_type == 'long' or field_type == 'ulong':
            return 4
        else:
            print("Unknown type: ", field_type)

    def decode(self, packet):
        if packet.message_id not in self.messages:
            #print("Message received with unknown message_id: ", packet.message_id)
            return {}

        message_def = self.messages[packet.message_id]
        output = {}
        offset = 0

        if packet.message_id == 125:  # Message Report
            output['fcs/msg_code'] = packet.data[0]
            output['fcs/msg_text'] = packet.data[2:].decode("ascii")

        else:
            if message_def.length != len(packet.data):
                #print("Length error in message with type", packet.message_id,
                #      "(expected", message_def.length, "got", len(packet.data), ")")
                return {}

            for i in range(0, len(message_def.field_names)):
                if message_def.field_types[i] == 'byte':
                    output[message_def.field_names[i]] = packet.data[offset]
                    offset += 1
                elif message_def.field_types[i] == 'sbyte':
                    output[message_def.field_names[i]] = struct.unpack_from(
                        'b', packet.data, offset)[0]
                    offset += 1
                elif message_def.field_types[i] == 'float':
                    output[message_def.field_names[i]] = struct.unpack_from(
                        'f', packet.data, offset)[0]
                    offset += 4
                elif message_def.field_types[i] == 'short':
                    output[message_def.field_names[i]] = struct.unpack_from(
                        'h', packet.data, offset)[0]
                    offset += 2
                elif message_def.field_types[i] == 'ushort':
                    output[message_def.field_names[i]] = struct.unpack_from(
                        'H', packet.data, offset)[0]
                    offset += 2
                elif message_def.field_types[i] == 'long':
                    output[message_def.field_names[i]] = struct.unpack_from(
                        'i', packet.data, offset)[0]
                    offset += 4
                elif message_def.field_types[i] == 'ulong':
                    output[message_def.field_names[i]] = struct.unpack_from(
                        'I', packet.data, offset)[0]
                    offset += 4
                else:
                    print("Unknown type: ", message_def.field_types[i])

        return output

    def createMessagePayload(self, message_id, message_data):
        message_def = self.messages[message_id]
        payload = bytearray()

        if message_id == 125:  # Message Report
            payload.extend(struct.pack('B', message_data['fcs/msg_code']))
            payload.extend(struct.pack('B', len(message_data['fcs/msg_text'])))
            payload.extend(message_data['fcs/msg_text'].encode('ascii'))

        else:
            for i in range(0, len(message_def.field_names)):
                if message_def.field_types[i] == 'byte':
                    payload.extend(struct.pack(
                        'B', message_data[message_def.field_names[i]]))
                elif message_def.field_types[i] == 'sbyte':
                    payload.extend(struct.pack(
                        'b', message_data[message_def.field_names[i]]))
                elif message_def.field_types[i] == 'float':
                    payload.extend(struct.pack(
                        'f', message_data[message_def.field_names[i]]))
                elif message_def.field_types[i] == 'short':
                    payload.extend(struct.pack(
                        'h', message_data[message_def.field_names[i]]))
                elif message_def.field_types[i] == 'ushort':
                    payload.extend(struct.pack(
                        'H', message_data[message_def.field_names[i]]))
                elif message_def.field_types[i] == 'long':
                    payload.extend(struct.pack(
                        'i', message_data[message_def.field_names[i]]))
                elif message_def.field_types[i] == 'ulong':
                    payload.extend(struct.pack(
                        'I', message_data[message_def.field_names[i]]))
                else:
                    print("Unknown type: ", message_def.field_types[i])

        return payload
