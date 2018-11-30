from serial.tools import list_ports
import time

def princer():
    p = list_ports.comports()
    for i in p:
        print(i)

while 1:
    princer()
    time.sleep(5)
