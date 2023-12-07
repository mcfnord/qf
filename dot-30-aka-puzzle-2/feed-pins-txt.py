#!/usr/bin/python3

import gpiozero
import time
import os

pull_up = False

#inputPins = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27]
# ReactorPuzzle.SetAlgorithmInputs (  [13, 20, 12, 5], FailPin = 26, ActiveLow = False)
inputPins = [5,12,13,20,26]
#inputPins = range(0,27)  # :)

objInputPins = []

def handlerButton(button):
    print('>> ACTIVITY :-> PIN:[{}] VALUE:[{}]\r\n\r\n\r\n'.format(button.pin, button.value))
    if button.value == 1:
        # create pins.txt file with this value in it.
        os.system('echo {} > pins.txt'.format(button.pin))
        
#end def (handlerButton)


for individualPin in inputPins:
    
    print('Adding pin#[{}]..'.format(individualPin))
    
    tmpInput = gpiozero.Button(individualPin, pull_up=pull_up)
    
    tmpInput.when_released = handlerButton
    tmpInput.when_pressed  = handlerButton
    
#end for


try:
    
    while True:
        time.sleep(1)
    #end while

except Exception as e:
    print(e)
    raise
    
except KeyboardInterrupt:
    print('\r\n\Exiting..')

#end try
