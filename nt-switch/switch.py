import cherrypy
import requests
import time
import threading
import RPi.GPIO as GPIO
import config
import os

#SETUP GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(26,GPIO.IN) #sensor moon
GPIO.setup(19,GPIO.IN) #sensor sun

GPIO.setup(13,GPIO.OUT) #relay safe
GPIO.setup(6,GPIO.OUT) #relay door

GPIO.setup(21,GPIO.OUT) #relay lights
GPIO.setup(20,GPIO.OUT) #relay 
GPIO.setup(16,GPIO.IN) #sensor power

GPIO.setup(12,GPIO.OUT) #relay blacklight
GPIO.setup(5,GPIO.OUT) #relay sunbeam

GPIO.setup(4,GPIO.IN) #sensor delta

#NETWORK PROPERTIES
IP = config.SWITCH_IP
PORT = config.SWITCH_PORT
SERVER_URL = config.SERVER_URL
CLOCK_URL = config.CLOCK_URL

s = requests.session()
s.keep_alive = False

#VARIABLES
moonstatus = False
sunstatus = False
powerstatus = False
deltastatus = False
jobs = []

#METHODS

def sun():
    return GPIO.input(26)

def moon():
    return GPIO.input(19)

def safe(action=False):
    if action:
        GPIO.output(13,GPIO.LOW)
    else:
        GPIO.output(13,GPIO.HIGH)

def door(action=False):
    if action:
        GPIO.output(6,GPIO.LOW)
    else:
        GPIO.output(6,GPIO.HIGH)
        time.sleep(1)
        GPIO.output(6,GPIO.LOW)

def sunCheck():
    global sunstatus
    while True:
        if sun() == 1 and sunstatus is False:
            sunstatus = True
        time.sleep(0.1)

def moonCheck():
    global moonstatus
    while True:
        if moon() == 1 and moonstatus is False:
            moonstatus = True
        time.sleep(0.1)

def power():
    return GPIO.input(16)

def lights(action=False):
    if action:
        os.system('/home/pi/.local/bin/kasa --host 192.168.1.144 --port 9999 --type plug on')
        os.system('/home/pi/.local/bin/kasa --host 192.168.1.249 --port 9999 --type plug on')
        GPIO.output(20,GPIO.LOW)
    else:
        GPIO.output(20,GPIO.HIGH)

def lights2(action=False):
    if action:
        os.system('/home/pi/.local/bin/kasa --host 192.168.1.144 --port 9999 --type plug on') # 4 circles
        os.system('/home/pi/.local/bin/kasa --host 192.168.1.249 --port 9999 --type plug on') # farwall
        GPIO.output(21,GPIO.LOW)
    else:
        GPIO.output(21,GPIO.HIGH)

def powerCheck():
    global powerstatus
    while True:
        if power() == 1 and powerstatus is False:
            powerstatus = True
            lights(True)
            time.sleep(0.2)
            lights(False)
            time.sleep(0.4)
            lights(True)
        time.sleep(0.1)

def blacklight(action=False):
    if action:
        os.system('/home/pi/.local/bin/kasa --host 192.168.1.144 --port 9999 --type plug off') # 4 circles
        GPIO.output(12,GPIO.LOW)
    else:
        GPIO.output(12,GPIO.HIGH)

def sunbeam(action=False):
    if action:
        print("turning on sun.")
        GPIO.output(5,GPIO.LOW)
        print("turning off overhead game light.")
        os.system('/home/pi/.local/bin/kasa --host 192.168.1.249 --port 9999 --type plug off') # farwall
    else:
        GPIO.output(5,GPIO.HIGH)

def delta():
    return GPIO.input(4)

def deltaCheck():
    global deltastatus
    while True:
        if delta() == 1 and deltastatus is False:
            deltastatus = True
            try:
                requests.get(SERVER_URL+'gamesuccess', timeout=100)
            except:
                print("Game Success Request")
            try:
                requests.get(CLOCK_URL+'actuatorOpen', timeout=100)
            except:
                print("Actuator Open Request")
        time.sleep(0.1)
        

#SERVER CLASS
class Server(object):

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def reset(self):
        global moonstatus
        global sunstatus
        global powerstatus
        global deltastatus
        sunstatus = False
        moonstatus = False
        powerstatus = False
        deltastatus = False
        safe(True)
        door(True)
        lights(False)
        blacklight(False)
        sunbeam(False)
        data={}
        data['status'] = 'OK'
        cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
        os.system('/home/pi/.local/bin/kasa --host 192.168.1.144 --port 9999 --type plug off')
        os.system('/home/pi/.local/bin/kasa --host 192.168.1.249 --port 9999 --type plug off') # farwall
        return data


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def openDoor(self):
        door(False)
        try:
            requests.get(SERVER_URL+'playDoorSound', timeout=3)
        except:
            print ("Failed to send request for Door Sound")
        data={}
        data['doorStatus'] = 'open'
        cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
        return data

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def black(self, action=True):
        if action:
            blacklight(True)
        else:
            blacklight(False)
        data={}
        data['blackLight'] = action
        cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
        return data

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def sun(self, action=True):
        if action == True:
            sunbeam(True)
        else:
            sunbeam(False)
        data={}
        data['sunBeam'] = action
        cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
        return data

    @cherrypy.expose
    def reboot(self):
        os.system('sudo reboot now')
        cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
        return "rebooting switch"
        

def server():
    global IP
    global PORT
    cherrypy.config.update({'server.socket_host':'::'})
    cherrypy.config.update({'server.socket_port':PORT})
    cherrypy.quickstart(Server())
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"

def loop():
    global sunstatus
    global moonstatus
    while True:
        if sunstatus and moonstatus:
            safe(False)
        time.sleep(1)

#PROGRAM
if __name__ == '__main__':
    safe(True)
    door(True)
    lights(False)
    blacklight(False)
    sunbeam(False)
    t1 = threading.Thread(target=server)
    t1.setDaemon(True)
    
    t2 = threading.Thread(target=loop)
    t2.setDaemon(True)

    t3 = threading.Thread(target=sunCheck)
    t3.setDaemon(True)

    t4 = threading.Thread(target=moonCheck)
    t4.setDaemon(True)

    t5 = threading.Thread(target=powerCheck)
    t5.setDaemon(True)

    t6 = threading.Thread(target=deltaCheck)
    t6.setDaemon(True)
    
    t1.start()
    t2.start()
    t3.start()
    t4.start()
    t5.start()
    t6.start()
    
    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
    


        
