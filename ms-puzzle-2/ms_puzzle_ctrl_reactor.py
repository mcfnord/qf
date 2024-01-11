#!/usr/bin/python3

# Reactor Puzzle
# Part of the RCPCS project (Room Control and Puzle Coordination System)
# Copyright (C) 2019  Joel D. Caturia
#
#
# This example code demonstrates how we bring together a puzzle controller
# class and the RCPCS communication controller class to provide bi-directional
# communications between the room controller and the physical puzzle.
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

# Here is how this puzzle works:
#
# - Probe Inputs are: [26, 13, 20, 12, 6, 5, 19,  21]
# - Probe FAIL Input is: 16
# - Probe LED Outputs are: [18, 27, 3, 23, 22, 17, 24, 2]
#   (these follow the stage we are on for the algorithmic solve)
#
# - The timer subassembly is controlled with four (4) output pins
#   "reset" -> 9,  "fail" -> 8,  "success" -> 11,  "countdown" -> 25
#
# THE TOWER SUBASSEMBLY IS CURRENTLY NOT FUNCTIONAL, SO IS NOT IMPLEMENTED IN THE PUZLE LOGIC
# - The tower subassembly is controlled by four(4) output pins
#   "lights" -> 10,  "up" -> 14,  "down" -> 15
#
# AUTO/RESET (in-active) STATE:
#  - Not solvable
#  - pulse "reset" pin LO
#  - turn OFF tower lights

#  - Unknown if any visual elements need to beconfigured
#
# ACTIVE STATE:
#  - pulse "countdown" pin to LO
#  - turn ON "tower lights"
#  - RAISE tower
#  - start a 120 second timer using a threading.Timer object
#
# SOLVED:
#  - cancel the 120 second probe timer
#  - turn ON the "probe light"
#  - turn OFF probe LED outputs
#  - set "success" pin to LO

# FAILED:
#  - cancel the 120 second probe timer
#  - turn OFF the "probe light"
#  - LOWER tower
#  - pulse "fail" pin to LO




import os
import time
import threading
import gpiozero

from class_puzzle_contact_algo import AlgoMatchPuzzleContacts as AlgoMatchPuzzleContacts
from controller_communications import ControllerCommunications

#FIXME - let's move this to a config file and/or command-line arguments someday
MQTTserver = 'ms-roomcontroller.local'
DebugFlag  = True
ProbeTimeout = 120
#ProbeTimeout = 10

probeTimer = None


# "reset" -> 9,  "fail" -> 8,  "success" -> 11,  "countdown" -> 25
timerAssemblyOutputs = {}
### REAL ONES
timerAssemblyOutputs.update( { 'reset'     : gpiozero.LED(9, active_high = False)  } )
timerAssemblyOutputs.update( { 'fail'      : gpiozero.LED(8, active_high = False)  } )
timerAssemblyOutputs.update( { 'success'   : gpiozero.LED(11, active_high = False) } )
timerAssemblyOutputs.update( { 'countdown' : gpiozero.LED(25, active_high = False) } )
#########################################################################################

### TEST ONES
#timerAssemblyOutputs.update( { 'reset'     : gpiozero.LED(13, active_high = False)  } )
#timerAssemblyOutputs.update( { 'countdown' : gpiozero.LED(19, active_high = False) } )
#timerAssemblyOutputs.update( { 'fail'      : gpiozero.LED(26, active_high = False)  } )
#timerAssemblyOutputs.update( { 'success'   : gpiozero.LED(20, active_high = False) } )
#########################################################################################


#towerAssemblyOutput  = {}


#########################################
## PUZZLE CONTROLLER -> REACTOR PUZZLE ##
#########################################
def handlerReactorPuzzleReset():
  global probeTimer
  
  ReactorRoomController.PublishStatus('RESET')

  # Cancel our internal probe timer
  try:
    probeTimer.cancel()
  except:
    pass
  #end try

  # Reset the timer subassemly - it will just show "ALERT"
  timerAssemblyOutputs['reset'].blink(on_time=.2, n=1)
  
#end def

def handlerReactorPuzzleActivated():
  global probeTimer
  
  ReactorRoomController.PublishStatus('ACTIVE')

  # Trigger our internal countdown timer
  probeTimer = threading.Timer(ProbeTimeout, handlerReactorPuzzleFailed)
  probeTimer.start()

  # Start the countdown from the timer subassemly
  timerAssemblyOutputs['countdown'].blink(on_time=.2, n=1)

#end def

def handlerReactorPuzzleSolved():
  ReactorRoomController.PublishStatus('SOLVED')

  # Stop our internal countdown timer
  try:
    probeTimer.cancel()
  except:
    pass
  #end try
  

  # Show "SUCCESS" on the timer subassemly
  timerAssemblyOutputs['reset'].blink(on_time=.2, n=1)
  timerAssemblyOutputs['success'].blink(on_time=.2, n=1)

#end def

def handlerReactorPuzzleFailed():
  
  print('FAILED!')
  
  ReactorRoomController.PublishStatus('FAILED')

  # Stop our internal countdown timer
  try:
    probeTimer.cancel()
  except:
    pass
  #end try


  # Show "FAIL" on the timer subassemly
  timerAssemblyOutputs['fail'].blink(on_time=.2, n=1)

#end def

ReactorPuzzle = AlgoMatchPuzzleContacts(Debug = DebugFlag, AlwaysActive = False)

# pin 19,21,16 that's the missing last ones
# 6 should also come after 12
ReactorPuzzle.SetAlgorithmInputs (  [13, 20, 12, 5], FailPin = 26, ActiveLow = False)
#ReactorPuzzle.SetAlgorithmInputs ( [13, 20,  19, 21], FailPin = 26, ActiveLow = False)

#Pin 24,2 missing last one
# 22 comes after 23 also
ReactorPuzzle.SetAlgorithmOutputs( [27, 3, 23, 17], ActiveLow = True )

# Workaround for a HW issue.
#ReactorPuzzle.setUnfailableInputIndex(3)

ReactorPuzzle.AddActiveOutput(7, ActiveLow = True)
ReactorPuzzle.AddActiveOutput(18, ActiveLow = True)

ReactorPuzzle.AddSolvedOutput(4, ActiveLow = True)   #this is the 8th LED (with a contact that does not currently work)

ReactorPuzzle.RegisterCallback('activated', handlerReactorPuzzleActivated)
ReactorPuzzle.RegisterCallback('solved',    handlerReactorPuzzleSolved)
ReactorPuzzle.RegisterCallback('failed',    handlerReactorPuzzleFailed)
ReactorPuzzle.RegisterCallback('reset',     handlerReactorPuzzleReset)
###############################################
## (END) PUZZLE CONTROLLER -> REACTOR PUZZLE ##
###############################################

##################################################
## ROOM CONTROL COMMUNICATION -> REACTOR PUZZLE ##
##################################################
def handlerReactorRoomControllerReboot():
  print('>> Processing a remote reboot command!')
  os.system('sudo reboot')
#end def

def handlerReactorRoomControllerReset():
  ReactorPuzzle.Reset()
#end def

def handlerReactorRoomControllerActivate():
  ReactorPuzzle.Activate()
#end def

def handlerReactorRoomControllerSolve():
  ReactorPuzzle.Solve()
#end def

def handlerReactorRoomControllerFail():
  ReactorPuzzle.Fail()
#end def

def handlerReactorRoomControllerPing():
  pass
#end def

def handlerReactorRoomControllerPong():
  pass
#end def

ReactorRoomController = ControllerCommunications('reactor', MQTTserver)

ReactorRoomController.RegisterCallback('command_reboot',   handlerReactorRoomControllerReboot)
ReactorRoomController.RegisterCallback('command_reset',    handlerReactorRoomControllerReset)
ReactorRoomController.RegisterCallback('command_activate', handlerReactorRoomControllerActivate)
ReactorRoomController.RegisterCallback('command_solve',    handlerReactorRoomControllerSolve)
ReactorRoomController.RegisterCallback('command_fail',     handlerReactorRoomControllerFail)
ReactorRoomController.RegisterCallback('ping',             handlerReactorRoomControllerPing)
ReactorRoomController.RegisterCallback('pong',             handlerReactorRoomControllerPong)

ReactorRoomController.connect()
########################################################
## (END) ROOM CONTROL COMMUNICATION -> REACTOR PUZZLE ##
########################################################





##################################################
####### MAIN PROGRAM EXECUTION BEGINS HERE #######
##################################################

try:

  ReactorPuzzle.Reset()

  while True:
    ReactorPuzzle.ProcessEvents()

    ReactorRoomController.ProcessEvents()

    time.sleep(1)
  #end while
  
except (KeyboardInterrupt, SystemExit):
  print("\r\nExiting..")
  quit()

except:
  raise

#end try

