#!/usr/bin/python3

# Puzzle Controller Class :: AND Match Contact Solve (with configurable delay allowance)
# Part of the RCPCS project (Room Control and Puzle Coordination System)
# Copyright (C) 2019  Joel D. Caturia
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
#  - gpiozero (It is very commonlyinstalled by default)
#  $> sudo pip3 install gpiozero


# TODO:
#  * Add a failed state: contacts, callback, and an output, with an optional timer for reset



import gpiozero
import time

class ANDMatchPuzzleContacts:

    def __init__(self, Debug = False, AlwaysActive = False, DelayAllowance = 1000):
    
        self.__debugFlag       = Debug
        self.__delayAllowance  = DelayAllowance      # How much time is allowed to elapse (in milliseconds) between the different contact closures
        self.__callbacks       = {}        

        self.__puzzleInputPinObjects     = {}   #FIXME: I need to let you define these as active LO/HI
        self.__puzzleActiveOutputObjects = []   #FIXME: I need to let you define these as active LO/HI
        self.__puzzleSolvedOutputObjects = []   #FIXME: I need to let you define these as active LO/HI
        self.__puzzleInputPinTimers      = {}
        
        self.__puzzleAlwaysActive        = AlwaysActive
        self.__puzzleActive              = AlwaysActive
        self.__puzzleSolved              = False
        self.__puzzleFailed              = False

    #end def
    

    def SetDelay(self, delay):
        self.__delayAllowance = delay
    #end def (SetDelay)

    
    def AddActiveOutput(self, activeOutputPinNumber, ActiveLow=False):
        if self.__debugFlag is True:
            print('>> Added Puzzle Active Output Pin #[{}]'.format(activeOutputPinNumber))
        #end if
        
        if ActiveLow is False:
            tmpOutputObject = gpiozero.PWMLED(activeOutputPinNumber, active_high = True)
        else:
            tmpOutputObject = gpiozero.PWMLED(activeOutputPinNumber, active_high = False)
        #end if

        tmpOutputObject.off()
        self.__puzzleActiveOutputObjects.append(tmpOutputObject)
    #end def (AddActiveOutput)


    def AddSolvedOutput(self, solvedOutputPinNumber, ActiveLow=False):
        if self.__debugFlag is True:
            print('>> Added Puzzle Solved Output Pin #[{}]'.format(solvedOutputPinNumber))
        #end if

        if ActiveLow is False:
            tmpOutputObject = gpiozero.PWMLED(solvedOutputPinNumber, active_high = True)	#FIXME - this is where we'll add stuff about active HI/LO
        else:
            tmpOutputObject = gpiozero.PWMLED(solvedOutputPinNumber, active_high = False)    #FIXME - this is where we'll add stuff about active HI/LO
        #end if

        tmpOutputObject.off()
        self.__puzzleSolvedOutputObjects.append(tmpOutputObject)
    #end def (AddActiveOutput)


    def AddContact(self, inputContactPinNumber, ActiveLow = False):
        if self.__debugFlag is True:
            print('>> Added Input Contact Pin #[{}]'.format(inputContactPinNumber))
        #end if

        if ActiveLow is False:
            tmpButtonObject = gpiozero.Button(inputContactPinNumber, pull_up=True)  #FIXME?, active_state=None)   #FIXME - this is where we fix active HI/LO
        else:
            tmpButtonObject = gpiozero.Button(inputContactPinNumber, pull_up=False)  #FIXME?, active_state=None)   #FIXME - this is where we fix active HI/LO
        #end if

        tmpButtonObject.when_pressed  = self.__handlerContactCallback 
        tmpButtonObject.when_released = self.__handlerContactCallback

        self.__puzzleInputPinObjects.update ({ tmpButtonObject.pin : tmpButtonObject } )
        
        self.__puzzleInputPinTimers.update( { tmpButtonObject.pin :  None } )
    #end def (AddContact)


    def __handlerContactCallback(self, btnObject):

        if self.__debugFlag is True:
            print('>> Input Contact Pin [{}] is ACTIVE: [{}]'.format(btnObject.pin, btnObject.is_active))
        #end if
        
        # We don't want to process any more events when we're in a solved state
        if ( self.__puzzleActive is True ) and ( self.__puzzleSolved is False ):

            if btnObject.is_active is True:
                currentMilliseconds = round( time.monotonic_ns() / 1000000 )
                #currentMilliseconds = round( time.monotonic() / 1000000 ) #FIME-HP
                self.__puzzleInputPinTimers[btnObject.pin] = currentMilliseconds

                self.__checkForSolve()

            else:
                self.__puzzleInputPinTimers[btnObject.pin] = None
                return False
            #end if
        #end if
    #end def (__handlerContactCallback)


    def __checkForSolve(self):

        currentMilliseconds = round( time.monotonic_ns() / 1000000 )

        for pinName, pinMilliseconds in self.__puzzleInputPinTimers.items():
            if self.__debugFlag is True:
                print('>> Pin: [{}], Milliseconds: [{}]'.format(pinName, pinMilliseconds))
            #end if

            if pinMilliseconds is None:
                return False
                
            elif ( currentMilliseconds - pinMilliseconds ) < self.__delayAllowance:
                pass

            elif ( currentMilliseconds - pinMilliseconds ) > self.__delayAllowance:
                self.Fail()
                return False

            else:
                return False
            #end if
        #end for

        # If we get down to here, then we have checked all of our input contacts and we're ready to solve!
        self.Solve()

        return True
    #end def (__checkForSolve)

    
    def RegisterCallback(self, callback, callbackFunction):
        self.__callbacks[callback] = callbackFunction
    #end def (RegisterCallbacks)


    def Activate(self):
        
        self.__puzzleActive = True
        self.__puzzleSolved = False

        if self.__debugFlag is True:
            print('>> PUZZLE IS ACTIVE: [{}]'.format(self.__puzzleActive))
        #end if

        for individualOutputObject in self.__puzzleActiveOutputObjects:
            individualOutputObject.on()            
        #end for

        try:
            self.__callbacks['activated']()
        except:
            pass
        #end try

    #end def (Activate)


    def Solve(self):

        self.__puzzleSolved = True
        
        if self.__debugFlag is True:
            print('>> PUZZLE SOLVED!')
        #end if

        for individualOutputObject in self.__puzzleActiveOutputObjects:
            individualOutputObject.off()            
        #end for

        for individualOutputObject in self.__puzzleSolvedOutputObjects:
            individualOutputObject.on()
        #end for

        try:
            self.__callbacks['solved']()
        except:
            pass
        #end try
    #end def (Solve)


    def Fail(self):
        
        self.__puzzleFailed = True
        self.__puzzleActive = False

        # Reset the timestamp on the contacts
        for pinName, pinMilliseconds in self.__puzzleInputPinTimers.items():
            self.__puzzleInputPinTimers[pinName] = None
        #end for

        for individualOutputObject in self.__puzzleActiveOutputObjects:
            individualOutputObject.off()            
        #end for

        for individualOutputObject in self.__puzzleSolvedOutputObjects:
            individualOutputObject.on()
        #end for

        try:
            self.__callbacks['failed']()
        except:
            pass
        #end try

    #end def (Fail)

    def Reset(self):
        
        if self.__debugFlag is True:
            print('>> PUZZLE RESET')
        #end if

        self.__puzzleSolved = False
        self.__puzzleFailed = False
        self.__puzzleActive = False
         

        # Reset the timestamp on the contacts
        for pinName, pinMilliseconds in self.__puzzleInputPinTimers.items():
            self.__puzzleInputPinTimers[pinName] = None
        #end for
       
        for individualOutputObjects in self.__puzzleActiveOutputObjects:
            individualOutputObjects.off()
        #end for

        for individualOutputObjects in self.__puzzleSolvedOutputObjects:
            individualOutputObjects.off()
        #end for

        try:
            self.__callbacks['reset']()
        except:
            pass
        #end try

        if self.__puzzleAlwaysActive is True:
            self.Activate()
        #end if

    #end def (Reset)


    def ProcessEvents(self):
        pass
    #end def (ProcessEvents)
    
        
    def Cleanup(self):
        pass
    #end def (Cleanup)


    def GetPuzzleSolved(self):
        return self.__puzzleSolved
    #end def (GetPuzzleSolved)

#end class
