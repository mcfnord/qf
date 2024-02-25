#!/usr/bin/python3


try:
	from pad4pi import rpi_gpio
except:
	print ('FATAL ERROR: Cannot import the pad4pi module!')
	print ('  -> This can probably be fixed by running "sudo pip3 install pad4pi"\r\n\r\n')
	raise

try:
	import speech_recognition as sr
except:
	print ('FATAL ERROR: Cannot import the speech recognition module!')
	print ('  -> This can probably be fixed by running "sudo pip3 install SpeechRecognition"')
	print ('  -> You also need FLAC, you can get that by running "sudo apt-get install flac\r\n\r\n"')
	raise
	

try:
	import pyaudio
except:
	print ('FATAL ERROR: Cannot import the pyAudio module!')
	print ('  -> This can probably be fixed by running "sudo apt-get install python3-pyaudio\r\n\r\n"')
	raise


try:
	import cherrypy
except:
	print ('FATAL ERROR: Cannot import the pyAudio module!')
	print ('  -> This can probably be fixed by running "sudo pip3 install cherrypy\r\n\r\n"')
	raise


import wave
import RPi.GPIO as GPIO
import time
import threading
import os
import config
from difflib import SequenceMatcher


#VOICE RECORDING VALUES
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 10


#NETWORK PROPERTIES
IP = config.PHONE_IP
PORT = config.PHONE_PORT


# FILE PATHS
SOUND_PATH = os.path.dirname(os.path.abspath(__file__)) + '/audio'
WAVE_OUTPUT_FILENAME = '/dev/shm/rec.wav'


#VARIABLES
dialerBuffer = ''
number = '1837260459'
password = '149254'

## USE FOR TESTING ##
#number = '1234'
#password = '1234'
#####################

buttonSounds = {
	'0': 'b10.wav',
	'1': 'b1.wav',
	'2': 'b2.wav',
	'3': 'b3.wav',
	'4': 'b4.wav',
	'5': 'b5.wav',
	'6': 'b6.wav',
	'7': 'b7.wav',
	'8': 'b8.wav',
	'9': 'b9.wav'
	}

# GPIO Connections for keypad matrix
# COLS : 4, 27, 22
# ROWS : 5, 6, 13, 19
#
# RESET: 23

ROW_PINS = [5, 6, 13, 19] 
COL_PINS = [4, 27, 22]
RESET_PIN = 23

KEYPAD = [ ['1','2','3'], ['4','5','6'], ['7','8','9'], ['*', '0', '#'] ]

#SETUP GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RESET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

keypad_factory = rpi_gpio.KeypadFactory()
keypad = keypad_factory.create_keypad(	keypad=KEYPAD,
										row_pins=ROW_PINS,
										col_pins=COL_PINS
									)


def handlerKeypad(key):
	global dialerBuffer
		
	print('KEY PRESSED: [{}]'.format(key))
	
	if key in ['#', '*']:
		dialerBuffer = ''
		print('Special Key Detected. Resetting dial string buffer..')
	
	else:
		playFX( buttonSounds[key] )
		dialerBuffer = dialerBuffer + key
	#end if
	
	print('DIAL BUFFER: [{}]'.format(dialerBuffer))

	checkNumber(dialerBuffer)
#end def

	

keypad.registerKeyPressHandler(handlerKeypad)	



def phoneIsOffHook():

	if not GPIO.input(RESET_PIN):
		return False	# Phone is ON-hook

	else:
		return True		# Phone is OFF-hook

	#end if
	
#end def



def checkNumber(numberToCheck):

	if len(number) == len(numberToCheck):
		if SequenceMatcher(None,number,numberToCheck).ratio() >=0.75:
			print('Correct Number! Ringing..')


			playFX('answer.wav')
			time.sleep(20)

			print ('Recording ...')
			record()


			print ('Recognizing ...')
			speechToText = recognize()
			
			if speechToText is not None:
				speechToText = speechToText.replace(' ','')
				print ('  Result: [{}]'.format(speechToText))


				m = SequenceMatcher(None,password,speechToText)
				if m.ratio() >= 0.7:
					print ('Password Match!')
					playFX('process.wav')
					time.sleep(12.75)
					
					while phoneIsOffHook():
						playFX('melody.wav')
						time.sleep(22)
					#end while
						
				else:
					playFX('incorrect.wav')
					time.sleep(7)
					
					while phoneIsOffHook():
						playFX('busy.wav')
						time.sleep(2)
					#end while
						
				#end if

			else:
			
				playFX('incorrect.wav')
				time.sleep(7)
					
				while phoneIsOffHook():
					playFX('busy.wav')
					time.sleep(2)
				#end while
			#end if				


		else:
			print('Incorrect Number! Playing Busy Tones..')

			playFX('incorrect.wav')
			time.sleep(7)
					
			while phoneIsOffHook():
				playFX('busy.wav')
				time.sleep(2)

			#end while
		#end if
	#end if
#end def



def playFX(media):
	try:
		p = os.popen('aplay -D default:CARD=S3 -f cd -t wav ' + SOUND_PATH + '/' + media)
	except Exception as e:
		print(e)
	#end try
#end def
	


#VOICE
def record(seconds=RECORD_SECONDS):

	p = pyaudio.PyAudio()
	
	stream = p.open(format=FORMAT,
				channels=CHANNELS,
				rate=RATE,
				input=True,
				frames_per_buffer=CHUNK)
	print ('* recording')
	frames = []
	for i in range(0, int(RATE / CHUNK * seconds)):
		data = stream.read(CHUNK, exception_on_overflow = False)
		frames.append(data)
	print ('* done record')
	stream.stop_stream()
	stream.close()
	p.terminate()
	wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
	wf.setnchannels(CHANNELS)
	wf.setsampwidth(p.get_sample_size(FORMAT))
	wf.setframerate(RATE)
	wf.writeframes(b''.join(frames))
	wf.close()
#end def


def recognize():

	r = sr.Recognizer()
	with sr.AudioFile(WAVE_OUTPUT_FILENAME) as source:
		audio = r.record(source)
	
	try:
		speechtotext = r.recognize_google(audio)
		return speechtotext
		
	except sr.UnknownValueError:
		print ('Unable to understand audio')
		return None
		
	except sr.RequestError as e:
		print ('Unable to get results from google')
		return None
	#end try
	
#end def


def loop():
	global dialerBuffer

	while True:

		if not phoneIsOffHook():
			print('Handset is ON-HOOK. Sleeping..')
			dialerBuffer = ''
		#end if
		
		time.sleep(1)
	#end while
#end def





class Server(object):

	@cherrypy.expose
	def index(self):
		cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
		return "Server is running!!!"

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def reset(self):
		data={}
		data['status'] = 'OK'
		cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
		return data

	@cherrypy.expose
	def reboot(self):
		os.system('sudo reboot now')
		cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
		return "rebooting phone"  
		
	
def server():
	cherrypy.config.update({'server.socket_host': IP})
	cherrypy.config.update({'server.socket_port': PORT})
	cherrypy.quickstart(Server())
	cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
			

#PROGRAM
if __name__ == '__main__':
	t1 = threading.Thread(target=loop)
	t1.setDaemon(True)
	t2 = threading.Thread(target=server)
	t2.setDaemon(True)

	t1.start()
	t2.start()

	t1.join()
	t2.join()
#end if
