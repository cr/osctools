#!/usr/bin/env python

import serial
import array
import liblo
import sys
from threading import Timer
import time
from math import sqrt

IpAddress = "127.0.0.1"
UdpPort = 1234
UsbDevice = "/dev/tty.usbmodem001"

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

def bit_value( val, bit_nr ):
	return ( val >> bit_nr ) & 1

def convert_acceldata( raw ):	
	# Conversion values from data to mgrav taken
	# from CMA3000-D0x datasheet (rev 0.4, table 4)
	mgrav_per_bit = [ 18, 36, 71, 143, 286, 571, 1142 ]

	# fix signedness: uint8 to int8
	if raw > 128:
		sign = -1
		absraw = -raw
	else:
		sign = 1
		absraw = raw

	mgrav = 0
	for n in range( 7 ):
		mgrav += mgrav_per_bit[n] * bit_value( absraw, n )

	return sign * mgrav / 1000.0

def send_osc():
	# re-schedule myself
	Timer( 1.0/25, send_osc, () ).start()

	rawdata = portwrite( cmd_GetData() )
	# only regard response with data
	if rawdata[3] != 1: return

	now = time.time()

	global xold, yold, zold, told

	# convert raw sensor data and apply mild filter
	# z is shifted by ~g/2
	xval =  convert_acceldata( rawdata[4] ) * 0.2 + xold * 0.8
	yval =  convert_acceldata( rawdata[5] ) * 0.2 + yold * 0.8
	zval =  (convert_acceldata( rawdata[6] ) + 0.41) * 0.2 + zold * 0.8

	# differentiate da/dt
	dxdt = (xval - xold) / (now - told)
	dydt = (yval - yold) / (now - told)
	dzdt = (zval - zold) / (now - told)

	# length of difference vector
	difflen = sqrt ( dxdt*dxdt + dydt*dydt + dzdt*dzdt )

	# send out everything to Fluxus as float string
	liblo.send( target, "/sensor", str( xval ), str( yval ), str( zval ), str( dxdt ), str( dydt ), str( dzdt ), str( difflen ) )

	print >> sys.stderr, "x: " + str( xval ) + " y: " + str( yval ) + " z: " + str( zval ) + " dx/dt: " + str( dxdt ) + " dy/dt: " + str( dydt ) + " dz/dt: " + str( dzdt ) + " |d/dt|: " + str( difflen )

	# store previous values for next call
	xold = xval
	yold = yval
	zold = zval
	told = now

####################################################################################################

# open osc connection
try:
	target = liblo.Address( IpAddress, UdpPort )
except liblo.AddressError, err:
	print str( err )
	sys.exit()

# open serial connection to Chronos AP
port = serial.Serial( UsbDevice, 115200, timeout=1 )
portwrite ( cmd_StartAP() )

# prepare some globals
global xold, yold, zold, told
xold = 0
yold = 0
zold = 0
told = time.time()

# call self-rescheduling function
send_osc()

# and wait forever
while 1:
	time.sleep( 1 )

# wonthappen
port.close()

