__author__ = 'NYUAD'

import serial
import os
import subprocess as sp
ser = serial.Serial("/dev/ttyUSB0", 9600, timeout = 1)
ID_list = ["001", "002", "003"]
import time

class Command ():
    def __init__(self,ID,command,value):
        self.id = ID
        self.command = command
        self.value = value
    def makeCommand (self):
        if self.value == "":
            message = ":"+self.command+"0"+"\r\n" #Added space here
        else:
            message = ":"+self.command+" "+self.value+"\r\n"
        return message
    def writeCommand (self):
        ser.write(self.makeCommand())

class Response():
    def __init__(self,ID,command,value):
        self.rawMessage = ser.readlines()
        self.id = ID
        self.command = command
        self.value = value
    def excludeGarbage(self):
        notGarbage = []
        returnMessage = self.rawMessage
        for i in returnMessage:
            if "%" in i:
                message = ""
                read = False
                for c in range(len(i)):
                    if i[c] == "%":
                        read = True
                    if i[c] == "\r" or i[c] == "\n":
                        read = False
                    if read:
                        message += i[c]
                notGarbage.append(message)
        return notGarbage
#    def checkSum(self):
#        message = self.excludeGarbage()
#        for i in message:
#            if len(i)!=
    def readMessage(self):
        messageDictList = []
        messages = self.excludeGarbage()
        for i in messages:
            messageList = i.replace("%","").split(" ")
            messageDict = {}
            messageDict ["ID"] = messageList [0]
            messageDict ["command"] = messageList [1]
            messageDict ["value"] = messageList [2]
            messageDictList.append(messageDict)
        return messageDictList
    def checkEcho(self): #Check if the response matches the commmand
        messageDictList = self.readMessage()
        print(messageDictList)
        for i in messageDictList:
            messageDictList.remove(i)
            if self.command == i ["command"] and self.value in i["value"] and self.id == i ["ID"]:
                return messageDictList
        return "retry"
    def realResponse(self): #Dummy, Optimization (?)
        message = self.checkEcho()
        if message:
            return message
        else:
            return None

def downloadFiles(): #Transfers files from camera trap to drone.
# Rsync Arguments:
#   -a       is equivalent to -rlptgoD, preserves everything recursion enabled
#   -v       verbose
#   -P       combines --partial (keeps partially transferred files) and --pro-
#            gress (shows progress of transfer)
#   --chmod  sets permissions; "a"-for all:user/owner, group owner and all other users;
#            "rwx" is read, write, execute rights
#   --update This forces rsync to skip any files for which the destination file already
#            exists and has a date later than the source file.
# Camera IP: 192.168.10.22
    copy_files = sp.call("rsync -avP --chmod=a=rwX --update pi@192.168.42.15:/media/usbhdd/DCIM/ /media/usbhddDrone", shell=True)
    # make_backup = sp.call("ssh -v pi@192.168.10.22 'python -v /home/pi/Desktop/camerabu.py'",shell=True)


def POWR (value):
    message = Command(ID,"POWR",value)
    message.writeCommand()
    response = Response(ID,"POWR",value)
    responseMessage = response.realResponse()
    if responseMessage == "retry":
        ser.readlines()
        return POWR(value)
    return responseMessage

def IDEN (value="0"):
    message = Command(ID,"IDEN",value)
    message.writeCommand()
    response = Response(ID,"IDEN",value)
    responseMessage = response.realResponse()
    if responseMessage == "retry":
        return IDEN()
    return responseMessage

def RSET (value="0"):
    message = Command(ID,"RSET",value)
    message.writeCommand()
    response = Response(ID,"RSET",value)
    responseMessage = response.realResponse()
    if responseMessage == "retry":
        return RSET()
    return responseMessage

for ID in ID_list:
    os.system("sudo mount /dev/sda1") #mounts USB flash drive into which photos are saved
    ID = IDEN()[0]["ID"]
    #os.system("sudo python /home/pi/Desktop/GreenLED.py")
    POWR ("1")
    #os.system("sudo python /home/pi/Desktop/BlueLED.py")
    state = POWR ("?")
    while state[0]["value"] != "000001":
        state = POWR("?")
    #os.system("sudo python /home/pi/Desktop/RedLED.py")
    downloadFiles()
    POWR ("0")
    #os.system("sudo python /home/pi/Desktop/CyanLED.py")
    state = POWR ("?")
    print(state)
    while state[0] ["value"] != "000000":
        state = POWR ("?")
    RSET()
    os.system("sudo umount /dev/sda1") #unmounts USB
    #os.system("sudo python /home/pi/Desktop/RedLED.py")
