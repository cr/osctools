#!/usr/bin/env python

# In Traktor, go to
#  -> Preferences / Controller Manager
#  -> Device: Generic MIDI (Traktor Virtual I/O)
#     - Add out / Output / Beat Phase Monitor
#       - Assignment: Device Target

import array
import time
import sys
import socket
import pygame
import pygame.midi

IpAddress = "10.0.0.1"
UdpPort = 9005

INPUT=0
OUTPUT=1

def device_list( dir ):
	for dev in range( pygame.midi.get_count() ):
		interf,name,inp,outp,opened = pygame.midi.get_device_info( dev )
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
	midi_in = pygame.midi.Input( dev )
	cntr = 0
	prev = 0
	while 1:
		cntr += 1
		while not midi_in.poll(): pass
		midi_data = midi_in.read(1)
		#print "message is ", cntr, ": time ", midi_data[0][1],", ",
		#print  midi_data[0][0][0], " ", midi_data[0][0][1], " ", midi_data[0][0][2], midi_data[0][0][3]
		value = midi_data[0][0][2]
		if value < prev:
			time.sleep( 0.1 ) # poor girl's sync
			#liblo.send( target, "/baem", "clock" )
			packet = "/1/baem\x00,\x00\x00\x00"
			target.sendto( packet, ( IpAddress, UdpPort ) )
			sys.stdout.write( "baem! " )
			sys.stdout.flush()
		prev = value
	del midi_in
    
try:
	target = socket.socket( socket.AF_INET, socket.SOCK_DGRAM, 0 )
	pygame.midi.init()
except err:
	print str( err )
	sys.exit()

osc_beat()

