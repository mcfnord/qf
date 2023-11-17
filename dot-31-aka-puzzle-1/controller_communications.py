#!/usr/bin/python3

# Room Controller Communications Class
# Part of the RCPCS project (Room Control and Puzle Coordination System)
# Copyright (C) 2019  Joel D. Caturia
#
#
# This class is intended to handle all of the heavy lifting necessary
# to participate in a RCPCS ecosystem, things like performing connection maintenance
# and making heartbeat calls.
#
# The idea is that you should *not* ever need to make unique edits to this file across
# puzzle installations. If you find that you need a specific feature, then it should be
# added in a way that is believed to add the most flexibility and can be used in other
# puzzles. Finally, changes SHALL never break backwards compatibility with previous
# versions of this class.
# 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


# Python3 Dependencies:
#  - paho-mqtt-client
#  $> sudo pip3 install paho-mqtt


import paho.mqtt.client as mqtt
import json
import time
import socket
import uuid
import re
import math
import sys

__version__  = '0.9'

print('\r\n----------------------------------------------------------')
print('Room Controller Communications Class v{}'.format(__version__))
print('Room Control and Puzzle Coordination System (RCPCS)')
print('(c)2019 Joel Caturia <jcaturia@katratech.com>')
print('----------------------------------------------------------\r\n')


class ControllerCommunications:

  def __init__(self, puzzleID, mqttBroker, mqttPort = 1883):
    self.mqttBroker = mqttBroker
    self.mqttPort = mqttPort
    self.puzzleID = puzzleID
  
    self.mqttKeepalive = 15

    self.__pingDelay = 3
    self.__timestampLastPing = time.time()
    self.__puzzleState = None
    self.__callbacks = {}
    self.__MQTTConnected = False

    
    
    def handlerMQTTonConnect(client, userdata, flags, rc):
      print('>> Puzzle ID [{}] successfully connected to MQTT Broker [{}:{}]..'.format(self.puzzleID, self.mqttBroker, self.mqttPort) )
      
      self.__MQTTConnected = True
      
      self.mqttClient.subscribe('COPI/' + self.puzzleID + '/#')	# Subscribe to Controller-Out-Puzzle-In		
      self.mqttClient.subscribe('POPI/' + self.puzzleID + '/#')	# Subscribe to Puzzle-Out-Puzzle-In topic
      
      self.PublishState(self.__puzzleState)
      
      self.SendPing()
    #end def (handlerMQTTonConnect)


    def handlerMQTTonDisconnect(client, userdata, rc):
        
      self.__MQTTConnected = False

      if self.__puzzleState == 'REBOOTING':
        self.mqttClient.loop_stop()
        self.__callbacks['command_reboot']()
              
      else:
        self.mqttClient.reconnect()
      #end if
    
    #end def (handlerMQTTonDisconnect)

  
    def handlerMQTTonMessage(client, userdata, message):

      if ('COMMANDS' in message.topic):
            
        incomingCommand = message.payload.decode()
                    
        if incomingCommand in ['RESET', 'ACTIVATE', 'SOLVE', 'PONG', 'REBOOT', 'FAIL']:
          print(' -> Received MQTT command: [{}]'.format(incomingCommand))
                            
          if incomingCommand == 'RESET':
            self.__callbacks['command_reset']()
            
          elif incomingCommand == 'ACTIVATE':
            self.__callbacks['command_activate']()
                            
          elif incomingCommand == 'SOLVE':
            self.__callbacks['command_solve']()

          elif incomingCommand == 'FAIL':
            self.__callbacks['command_fail']()

          elif incomingCommand == 'REBOOT':
            self.PublishStatus('REBOOTING')
            self.mqttClient.disconnect()
            # We fire the command_reboot callback in the on_disconnect event for the MQTT client            
          #end if

      elif ('PONG' in message.topic):
            self.__callbacks['pong']()
                  
      else:
        self.mqttClient.publish('CIPO/' + self.puzzleID + '/ERROR', 'Unknown COMMAND received: [{}]'.format(incomingCommand))
        self.mqttClient.publish('CIPO/' + self.puzzleID + '/STATE', self.__puzzleState)
      #end if
                                                                                                                                                                                                                                                                                        
    #end def (handlerMQTTonMessage)
## end nested defines (under __init__)

    
    self.mqttClient = mqtt.Client()

    self.mqttClient.on_connect    = handlerMQTTonConnect
    self.mqttClient.on_disconnect = handlerMQTTonDisconnect
    self.mqttClient.on_message    = handlerMQTTonMessage

    self.mqttClient.will_set('CIPO/' + self.puzzleID + '/STATE', payload='UNKNOWN', qos=1)

    backOffTimer = 2

    while (self.__MQTTConnected == False):
      try:
        print(">> Attempting MQTT broker connection..")
        self.mqttClient.connect(self.mqttBroker, self.mqttPort, self.mqttKeepalive)
        self.mqttClient.loop_start()  
        time.sleep(1)

      except:
        print('>> Unable to connect to MQTT broker! Sleeping for {} seconds..'.format(backOffTimer) )
        time.sleep(backOffTimer)
        
        # Incremement the backoff timer util we get over 30, then we just leave it there.
        # This logic will actually ensure we spend one cycle over 30 (at 64, in fact). I am OK with this.
        if backOffTimer == 30:
          pass
        elif backOffTimer > 30:
          backOffTimer = 30
        else:
          backOffTimer = backOffTimer * 2
        #end if
        
      #end try
    #end while
        
  #end def


  def disconnect(self):
    self.mqttClient.disconnect()
  #end def (disconnect)  


  def SendPing(self):

    platform = 'RCPCS v{}/Python v{}.{}.{}/{}'.format(__version__, sys.version_info[0], sys.version_info[1], sys.version_info[2], self.__getRaspberryPiVersion() )
 
    #TODO - add wireless signal strength as well
    data = {}
    data['timestamp']    = time.time()
    data['puzzleID']     = self.puzzleID
    data['ipAddress']    = self.__getIPAddress()
    data['uptime']       = self.__getUptime()
    data['MACaddress']   = self.__getMACaddress()
    data['temperature']  = self.__getTemperature()
    data['role']         = 'puzzle'
    data['platform']     = platform
    data['currentStatus'] = self.__puzzleState
    json_data = json.dumps(data)
    
    self.mqttClient.publish('CIPO/PING/' + self.puzzleID, json_data )
    
    self.__callbacks['ping']()
  
  #end def
  

  def ProcessEvents(self):
  
    if time.time() - self.__timestampLastPing > self.__pingDelay:        # send a controller ping periodically
      self.__timestampLastPing = time.time()
      self.SendPing()
    #end if
        
  #end def (ProcessLoop)


  def PublishStatus(self, newStatus):
    if newStatus in ['RESET', 'ACTIVE', 'SOLVED', 'FAILED', 'REBOOTING']:
      self.__puzzleState = newStatus
      self.mqttClient.publish('CIPO/' + self.puzzleID + '/STATE', self.__puzzleState, qos=1)
    #end if
  #end def
  
      
  # These are the callbacks we will support at the moment:
  # - command_reset 
  # - command_activate
  # - command_solve
  # - command_reboot
  # - pong
  def RegisterCallback(self, eventName, callbackFunction):
  
    if eventName in ['command_reset', 'command_activate', 'command_solve', 'command_reboot', 'command_fail', 'pong', 'ping']:
      self.__callbacks[eventName] = callbackFunction
    #end if
        
  #end def (RegisterCallback)


  def __getTemperature(self):
    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
      celsius = int(f.readline().strip()) / 1000;

      fahrenheit = math.floor((celsius * 1.8) + 32);

    return fahrenheit
  #end def (__getTemperature)
  
  
  def __getUptime(self):
    with open('/proc/uptime', 'r') as f:
      uptime_seconds = float(f.readline().split()[0])
              
    return uptime_seconds
  #end def (__getUptime)
  
  
  def __getIPAddress(self):
    try: 
      s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      s.connect((self.mqttBroker, 80))  # The server doesn't need to actually be listening on this port for this to work BTW

      host_ip = s.getsockname()[0]

      s.close()
    
      return host_ip
    
    except:
      return None
    #end try
    
  #end def (__getIPAddress)

  def __getMACaddress(self):
    return ':'.join(re.findall('..', '%012x' % uuid.getnode() ))
  #end def (__getMACaddress)
    
  
  def __getRaspberryPiVersion(self):
  
    # Only Raspberry Pi's will have this, so we catch the error to mean we're running on some other platform (Simu-Puzzle perhaps?)
#    try:
    with open('/proc/device-tree/model', 'r') as f:
      model = f.readline()
      return model
        
#    except:
#      return 'Unknown'
      #end try
  #end def (__getRaspberryPiVersion)