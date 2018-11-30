import sys
import VACSParser

if len(sys.argv) != 2:
    print("Usage: python MessageIDTest.py message-definition-path")
    sys.exit(1)

message_definition_path = sys.argv[1]

parser = VACSParser.Parser(message_definition_path)

print(parser.get_message_id("Speed Report"))
