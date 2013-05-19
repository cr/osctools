#!/usr/bin/env python

# In Traktor, go to
#  -> Preferences / Controller Manager
#  -> Device: Generic MIDI (Traktor Virtual I/O)
#     - Add out / Output / Beat Phase Monitor
#     - Add out / Deck Coomon / Beat Phase (Traktor 2+)
#       - Assignment: Device Target
#       - Choose any Midi channel

import time
import sys
import socket
import pygame
import pygame.midi

IpAddress = "10.0.0.1"
UdpPort = 9005

INPUT=0
OUTPUT=1

def device_list( direction ):
	for dev in range( pygame.midi.get_count() ):
		interf,name,inp,outp,opened = pygame.midi.get_device_info( dev )
		if   ((direction == INPUT ) and (inp  == 1)) or ((direction == OUTPUT) and (outp == 1)):
			print dev, name, " ",
			if( inp == 1 ): print "(input) ",
			else: print "(output) ",
			if( opened == 1 ): print "(opened)",
			else: print "(unopened)",
		print

def osc_beat():
	device_list( INPUT )
	dev = int( raw_input( "MIDI input number: " ) )
	midi_in = pygame.midi.Input( dev )

	cntr = 0
	prev = 0
	while 1:
		cntr += 1

		# wait for any MIDI message to arrive
		while not midi_in.poll():
			time.sleep( 1./256 )
			pass
		midi_data = midi_in.read(1)

		# extract Traktor Beat Phase argument
		#print "message is ", cntr, ": time ", midi_data[0][1],", ",
		#print  midi_data[0][0][0], " ", midi_data[0][0][1], " ", midi_data[0][0][2], midi_data[0][0][3]
		value = midi_data[0][0][2]

		# trigger beat as soon as sawtooth has falling edge
		if value < prev:

			time.sleep( 0.1 ) # poor girl's sync

			# generate OSC message
			packet = "/1/baem\x00,\x00\x00\x00" # poor girl's osc message
			try:
				target.sendto( packet, ( IpAddress, UdpPort ) )
			except err:
				print str( err )

			sys.stdout.write( "baem! " )
			sys.stdout.flush()
		prev = value

	del midi_in
    
try:
	target = socket.socket( socket.AF_INET, socket.SOCK_DGRAM, 0 )
	pygame.midi.init()
except err:
	print str( err )
	sys.exit(5)

try:
	osc_beat()
except:
	pygame.midi.quit()
	target.close()
