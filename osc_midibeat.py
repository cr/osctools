#!/usr/bin/env python

# In Traktor, go to
#  -> Preferences / Controller Manager
#  -> Device: Generic MIDI (Traktor Virtual I/O)
#     - Add out / Output / Beat Phase Monitor
#       - Assignment: Device Target

import pypm
import array
import time
import liblo
import sys

IpAddress = "127.0.0.1"
UdpPort = 1234

INPUT=0
OUTPUT=1

def device_list( dir ):
	for dev in range( pypm.CountDevices() ):
		interf,name,inp,outp,opened = pypm.GetDeviceInfo( dev )
		if( (dir == INPUT) & (inp == 1) | (dir == OUTPUT) & (outp == 1)):
			print dev, name, " ",
			if( inp == 1 ): print "(input) ",
			else: print "(output) ",
			if( opened == 1 ): print "(opened)"
			else: print "(unopened)"
		print

def osc_beat():
	device_list( INPUT )
	dev = int( raw_input( "MIDI input number: " ) )
	midi_in = pypm.Input( dev )
#	midi_in.SetFilter( pypm.FILT_ACTIVE | pypm.FILT_CLOCK )
	cntr = 0
	prev = 0
	while 1:
		cntr += 1
		while not midi_in.Poll(): pass
		midi_data = midi_in.Read(1)
		#print "message is ", cntr, ": time ", midi_data[0][1],", ",
		#print  midi_data[0][0][0], " ", midi_data[0][0][1], " ", midi_data[0][0][2], midi_data[0][0][3]
		value = midi_data[0][0][2]
		if value < prev:
			time.sleep( 0.1 ) # poor girl's sync
			liblo.send( target, "/baem", "clock" )
			sys.stdout.write( "baem! " )
			sys.stdout.flush()
		prev = value
	del midi_in
    
try:
	target = liblo.Address( IpAddress, UdpPort )
except liblo.AddressError, err:
	print str( err )
	sys.exit()

osc_beat()
pypm.Terminate()

