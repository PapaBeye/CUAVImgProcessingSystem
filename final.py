import cv2
import threading

import os
import serial
import imutils
import sys
import VACSParser
import time
from msvcrt import kbhit, getch



if len(sys.argv) != 5:
    print("final.exe PI COM3 COM1 \"FCSPlaneDefinition_Aries_FCS.xml\"")
    time.sleep(6)
    sys.exit(0)
else:
    stid = sys.argv[1]
    gscomport = sys.argv[2]
    fccomport = sys.argv[3]
    message_definition_path = sys.argv[4]


#q = multiprocessing.Queue()
vcap = cv2.VideoCapture(0)


gscomtopi = serial.Serial(str(gscomport), baudrate=57600,)

#gscomtopi = serial.Serial(str(gscomport), baudrate=57600, parity=serial.PARITY_NONE,
#                               stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
fccomport = serial.Serial(str(fccomport), baudrate=57600,)
message_definition_path = message_definition_path
parser = VACSParser.Parser(message_definition_path)
Altitude = 0.00
Latitude = 'wrong'
Longitude = 'wrong '
objectdist = 0
tentWidth = 20
focalLength = 415.15

def dis_to_camera(Width, focalLength, perWidth):
    # compute and return the distance from the maker to the camer
    return (Width * focalLength) / perWidth

def getFCdata():
    print('Running FC')
    global Latitude
    global Longitude
    global Altitude
    while 1:
        byte = fccomport.read(1)
        if byte:
            parser.parse(byte)
            newbyte = parser.get_packet()
            if newbyte:
                for i in newbyte.message:
                    #print(i, newbyte.message[i], newbyte.message_id)
                    if newbyte.message_id == 1:
                        Longitude = str(newbyte.message['position/longitude'])
                        print("Longitube: "+str(Longitude))
                        Latitude = str(newbyte.message[i])
                        print("Latitude: "+str(Latitude))
                        Altitude = float(newbyte.message['position/altitude'])
                        print("Altitude: "+str(Altitude)) #  getFCdata()
            if kbhit():
                break


def find_whiterec_fame():
    global vcap
    global Longitude
    global Latitude
    global Altitude
    global objectdist
    global focalLength
    while 1:
        _, img = vcap.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.threshold(gray, 235, 255, cv2.THRESH_BINARY)[1]
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]
        for c in cnts:
            M = cv2.moments(c)
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.14 * peri, True)
            area = cv2.contourArea(c)
            if len(approx) == 4:
                (x, y, w, h) = cv2.boundingRect(approx)
                r = w / float(h) # 1500 is arbitrary for this purpose its the area of the larget object on test image / 2
                if area > 1500 and r >= 0.65 and r <= 1.35:
                    cv2.drawContours(img, [c], -1, (0, 255, 0), 2)
                    marker = cv2.minAreaRect(c)
                    #if frun == True:
                    #    self.focalLength = (marker[1][0] * self.Altitude) / self.tentWidth
                    #    self.frun = False
                    objectdist = dis_to_camera(tentWidth, focalLength, marker[1][0])
                    comtogs(Altitude,Longitude,Latitude,objectdist)
                    handleimg(img, 1, Longitude)
            else:
                handleimg(img, 0, str(time.time()))
        cv2.imshow('img', img)
        #cv2.imshow('img2', gray)
        #cv2.imshow('img3', thresh)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
    vcap.release()


def handleimg(image, xint, name):
    if xint == 1:
        if not os.path.exists('positive'):
            os.makedirs('positive')
        cv2.imwrite("positive/img"+name+".jpg", image)
    elif xint == 0:
        if not os.path.exists('negative'):
            os.makedirs('negative')
        name = time.time() * 1000
        cv2.imwrite("negative/img"+str(name)+".jpg", image)
def comtogs(alt, lon, lat,dist):
    data = 'Altitude: '+str(alt)+'-'+'Latitude: '+lat+'-'+'Longitube: '+lon+'-'+'Distance: '+str(dist)+'\n'
    data = data.encode()
    gscomtopi.write(data)

try:
    print('Author Papa Beye\nVIP Image Proccessing 2018\nDr. Klenke  & Andy Fabian')
    t = threading.Thread(target=getFCdata)
    t2 = threading.Thread(target=find_whiterec_fame)
    t.start()
    t2.start()
    t.join()
    t2.join()
except KeyboardInterrupt:
    raise
'''
except KeyboardInterrupt:
    raise
    t._stop()
    t2._stop()
    print('exit by keyboard interrupt')
    exit(0)
except Exception as e:
    print(e)
'''