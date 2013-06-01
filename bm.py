#!/usr/bin/env python

import sys

import numpy as np
from scipy import signal

import pyaudio

import pygame
from pygame.locals import *
from pygame import gfxdraw

class Bar( object ):

	def __init__( self, pos, size ):
		self.size = size
		self.pos = pos
		self.surface = pygame.surface.Surface( self.size )
		self.surface = self.surface.convert_alpha()
		self.fgcolor = pygame.Color( 255,255,255,220 )
		self.bgcolor = pygame.Color( 0,0,0,127 )
		self.set( 0 )
		self.update()

	def set( self, val ):
		self.v = float(val)

	def clear( self ):
		self.surface.fill( self.bgcolor )
		xsize,ysize = self.size
		yfill = int(ysize * self.v)
		rect = pygame.Rect( 0, ysize - yfill, xsize , yfill )
		pygame.gfxdraw.box( self.surface, rect, self.fgcolor )

	def update( self ):
		self.clear()
		
	def blit( self, surface ):
		surface.blit( self.surface, self.pos )


class MonoDiffStream( object ):

	def __init__( self, device=False, streamrate=12000, streamchunk=256, downsample=2 ):
		self.outputrate = streamrate
		self.outputchunk = streamchunk
		self.downsample = downsample
		self.inputrate = self.outputrate * self.downsample
		self.inputchunk = self.outputchunk * self.downsample
		self.p = pyaudio.PyAudio()

		if type(device)==bool:
			info = self.p.get_default_input_device_info()
			device = info['index']
		else:
			info = self.p.get_device_info_by_index( device )

		# assert that we have stereo input
		assert info['maxInputChannels'] >= 2

		self.s = self.p.open( input_device_index=device, # default if False
		                      format=pyaudio.paFloat32,
		                      channels=2,
		                      rate=self.inputrate,
		                      input=True,
		                      frames_per_buffer=self.inputchunk )

	def __del__( self ):
		self.s.close()
		self.p.terminate()

	def __iter__( self ):
		while True:
			# read chunk of frames as float32
			try:
				leftright = np.fromstring( self.s.read( self.inputchunk ), dtype=np.float32 )
			except IOError as err:
				if err[1] != pyaudio.paInputOverflowed:
					raise
				else:
					self.s.read( self.s.get_read_available() )	
					print "Dropping audio frames!"

			#detect clipping
			clip = np.sum( [leftright>0.99, leftright<-0.99] )
			if clip > 0: print "CLIPPING", clip, "samples"

			# split interleaved frames into channels
			left = leftright[0::2]
			right = leftright[1::2]

			mono = (left+right)*0.5
			diff = (left-right)*0.5

			unfiltered = mono[0::self.downsample] # keep unfiltered copy

			# low-pass filter to avoid mirror frequencies in fft
			# must filter before downsampling, because the filter is
			# blind to the interesting frequencies above f_samp/2.
			win = signal.firwin( len(mono)+1, cutoff=0.5, window='hanning' )
			mono = signal.lfilter( win, 1, mono )

			# downsample
			mono = mono[0::self.downsample]
			diff = diff[0::self.downsample]

			assert len(mono) == self.outputchunk
			assert len(diff) == self.outputchunk

			# fft calculation
			#h = np.hamming(len(mono))
			h = np.hanning(len(mono))
			fft = np.fft.rfft( mono * h, axis=0)[0:len(mono)/2]

			# fft of unfiltered signal
			ufft = np.fft.rfft( unfiltered * h, axis=0)[0:len(unfiltered)/2]

			yield mono, diff, ufft, fft

def binning( fft, start=0 ):
	# psychoacoustic binning per octave
	n = int(np.ceil(np.log2(len(fft)-start)))
	for bin in [fft[start+2**x-1:start+2**(x+1)-1] for x in xrange(n)]:
		yield bin

def avgbin( fft, offt, start=0 ):
	fftbins = binning( fft, start=start )
	offtbins = binning( offt, start=start )
	for bin in fftbins:
		obin = offtbins.next()
		avg = np.average(bin)
		yield avg

def fluxbin( fft, offt, start=0 ):
	fftbins = binning( fft, start=start )
	offtbins = binning( offt, start=start )
	for bin in fftbins:
		obin = offtbins.next()
		diffbin = bin - obin
		flux = np.average((np.abs(-diffbin)+diffbin)/2.0)
		yield flux

def main():

	pygame.init()

	#fullscreen mode
	use_fs = False

	# size for windowed mode
	screendim = 1200, 200

	if use_fs and pygame.display.list_modes():
		fs = True
		screendim = pygame.display.list_modes()[0]
		screen = pygame.display.set_mode( screendim, pygame.FULLSCREEN, 32 )
	else:
		fs = False
		screen = pygame.display.set_mode( screendim, 0, 32 )

	pygame.display.set_caption( "Beat Monitor" )
	clock = pygame.time.Clock()
	bgcolor = pygame.Color( 20, 40, 60, 255 )
	screen.fill( bgcolor )

	# some bars
	bars = [ Bar( (i*4+30,20),(3,170) ) for i in xrange(280) ]

	# the audio object
	a = MonoDiffStream()
	avg = 0.

	# main event loop syncs to incoming audio chunks
	for m,d,f,t in a: # reading audio is blocking
		try: of
		except: 
			of = f
			ot = t

		avgbins = [x for x in avgbin( f, of, start=0 )]
		fluxbins = [x for x in fluxbin( f, of, start=0 )]
		avgbins = 2.*np.log10(1.+10.*np.abs(avgbins))
		fluxbins = 0.5*np.log10(1.+10.*np.abs(fluxbins))
		try:
			avgbins = 0.7*oavgbins + 0.3*avgbins
			ofluxbins = 0.7*ofluxbins + 0.3*fluxbins
		except:
			pass
		oavgbins = avgbins
		ofluxbins = fluxbins

		logf = 0.4*np.log10(1.+10.*np.abs(f))
		logt = 0.4*np.log10(1.+10.*np.abs(t))
		try:
			logf = np.maximum( 0.9*ologf, logf )
			logt = np.maximum( 0.9*ologt, logt )
		except:
			pass
		ologf = logf
		ologt = logt

		monoenergy = np.average(np.square(m))
		diffenergy = np.average(np.square(d))
		energy = monoenergy + diffenergy

		avg = avg * 0.95 + energy * 0.05

		change =  1.-abs((avg-energy)/avg)

		logenergy = 10.*np.log10(1.+10.*energy)
		logavg = 20.*np.log10(1.+10.*avg)

		try:
			logenergy = max( 0.8*oldenergy,logenergy )
		except:
			pass
		oldenergy = logenergy



	
		#print "%.8f  %.8f   %.8f   %.8f   %.8f" % (energy, logenergy, avg, logavg, change)

		bars[0].fgcolor = pygame.Color( 255,255,150,220 )
		bars[0].set( logenergy )
		bars[0].update()
		bars[1].fgcolor = pygame.Color( 150,255,255,220 )
		bars[1].set( logavg )
		bars[1].update()
		bars[2].fgcolor = pygame.Color( 255,150,255,220 )
		bars[2].set( 0.5*change )
		bars[2].update()

		try:
			for i,v in enumerate(avgbins):
				bars[i+0].fgcolor = pygame.Color( 127,255,63,220 )
				bars[i+0].set(v)
				bars[i+0].update()
		except IndexError:
			break

		try:
			for i,v in enumerate(fluxbins):
				bars[i+10].fgcolor = pygame.Color( 63,255,127,220 )
				bars[i+10].set(v)
				bars[i+10].update()
		except IndexError:
			break

		# use some bars for unfiltered fft 
		#try:	
		#	for i,v in enumerate(ologf):
		#		bars[i+3].fgcolor = pygame.Color( 255,220,220,220 )
		#		bars[i+3].set(v)
		#		bars[i+3].update()
		#except IndexError:
		#	break

		# use some bars for filtered fft
		try:
			for i,v in enumerate(ologt):
				bars[i+20].fgcolor = pygame.Color( 255,127,63,220 )
				bars[i+20].set(v)
				bars[i+20].update()
		except IndexError:
			break


		for b in bars:
			b.blit( screen )
	
		# pygame event handling
		for event in pygame.event.get():
			if event.type == QUIT:
				sys.exit(0)
			elif event.type == KEYDOWN and event.key == K_ESCAPE:
				sys.exit(0)
			elif event.type == KEYDOWN and event.key == K_f:
				if fs:
					pygame.display.toggle_fullscreen()

		# refresh what's on screen
		# 
		pygame.display.update()

		# limit to max 120 Hz updates
		clock.tick( 120 )

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		sys.exit(1)
