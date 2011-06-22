#!/usr/bin/env python

import serial
import array
import liblo
import sys
from threading import Timer
import time

####################################################################################################

def cmd_StartAP():
    return array.array( 'B', [0xFF, 0x07, 0x03] )

def cmd_GetData():
    return array.array( 'B', [0xFF, 0x08, 0x07, 0x00, 0x00, 0x00, 0x00] )

def portwrite( cmd ):
	port.write ( cmd.tostring() )
	response = bytearray( port.read( 3 ) )
	if response[2] > 3:
		response += bytearray( port.read( response[2]-3 ) )
	return response

def send_osc():
	Timer( 1.0/25, send_osc, () ).start()

	data = portwrite( cmd_GetData() )

	xval =  data[4]
	yval =  data[5]
	zval =  data[6]
	if xval > 128:
		xval -= 256
	if yval > 128:
		yval -= 256
	if zval > 128:
		zval -= 256

	if data[3] == 1:
		liblo.send( target, "/sensor", xval, yval, zval )
#		print >> sys.stderr, "x: " + str( xval ) + " y: " + str( yval ) + " z: " + str( zval )

####################################################################################################

try:
	target = liblo.Address( "127.0.0.1", 1234 )
	#target = liblo.Address( "10.10.10.2", 1234 )
except liblo.AddressError, err:
	print str( err )
	sys.exit()

#port = serial.Serial( "/dev/tty.usbmodem001", 115200, timeout=1 )
#portwrite ( cmd_StartAP() )

send_osc()

while 1:
	time.sleep( 1 )
#	send_osc()

port.close()

