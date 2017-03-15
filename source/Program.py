import time
import math
import threading
import sys
import os

import pygame

from Entity import *
from Player import *
from UIComponent import *
from UITextComponent import *
from Input import *
from Tile import *
from utilities import *
from Game import *

"""
	******************************************************************************

	Class: Program
	
	Description: A single instance (but not Singleton) class representing the program,
	with a window, draw loop, and game loop to handle logic.
	
	Author: Jason Milhaven
	
	History: No longer using "Daemon" thread as draw loop,
	draw loop should be terminated first, not last.
	
	******************************************************************************
"""

class Program():

	"""
		==============================================================================
		
		Method: __init__
		
		Description: Constructor for the Program class, creates the window given
		a title, w and h constants, sets window icon.
		
		The game logic and event handling is in event_loop, on the main thread.
		The drawing is handled exclusively in draw_loop, on a seperate thread.
		
		UI is created upon instantiation.
		
		Author: Jason Milhaven
		
		History:
		
		==============================================================================
	"""

	def __init__(self):
		
		# constants
		self.WIN_TITLE = "Pythonica"
		#self.WIN_WIDTH = 1024
		#self.WIN_HEIGHT = 576
		self.WIN_WIDTH = 1366
		self.WIN_HEIGHT = 768
		self.WIN_ICON_FILENAME = "Icon.png"
		self.FILL_COLOR = (0, 0, 0)
		
		# core variables
		self.isRunning = True
		self.isInGame = False
		self.uiComponents = []
		self.hoveredUI = None
		self.input = Input()
		self.lastEventTime = time.time()
		self.lastDrawTime = time.time()
		self.pyClock = pygame.time.Clock()
		
		# if activeGame is None, then use is in menu
		# if activeGame points to a Game, then in game
		self.activeGame = None
		
		# get rid of this line?
		self.activeGame = Game(self.WIN_WIDTH, self.WIN_HEIGHT)
		
		# pygame initialization
		pygame.init()
		self.pySurface = pygame.display.set_mode((self.WIN_WIDTH, self.WIN_HEIGHT))
		pygame.display.set_caption(self.WIN_TITLE)
		pygame.display.set_icon(load_img(self.WIN_ICON_FILENAME))
		
		# make the ui
		u = UITextComponent()
		u.set_pos(self.WIN_WIDTH * 0.5, self.WIN_HEIGHT * 0.89)
		u.set_size(self.WIN_WIDTH, TILE_SCALE * 4)
		u.set_visible(True)
		u.name = "UI 1"
		u.text = "test text here test text here test text here "
		u.borderSize = 1
		self.uiComponents.append(u)
		
		u2 = UIComponent(400, 400, 100, 100)
		u2.set_visible(False)
		u2.name = "UI 2"
		self.uiComponents.append(u2)
		
		b = UIComponent(400, 100, 300, 100)
		b.set_visible(False)
		b.name = "Banner"
		b.img = load_img("TestBanner.png")
		self.uiComponents.append(b)
		
		# testing collision
		
		print("Ctrl+F to here to fix the rooms")
		del self.activeGame.currentRoom.tiles[:] # delete each element in the list
		t = Tile(TILE_SCALE * 4, TILE_SCALE * 4)
		t.img = load_img("GrassMts.png")
		t.isBlocking = True
		self.activeGame.currentRoom.tiles.append(t)
		
		# begin the main program
		
		self.drawThread = threading.Thread(target=self.draw_loop)
		#self.drawThread.setDaemon(True)
		# threads should be killed manually
		self.drawThread.start()
		self.event_loop()

		
	def close(self):
		self.isRunning = False
		
		# kill any threads here
		self.drawThread.join()
		
		pygame.quit()
		sys.exit(0)


	def __is_in__(self, mX, mY, transform):
		
		ret = False
		
		xCondition = mX <= transform.get_pos_x() + transform.get_size_x() * 0.5 and mX > transform.get_pos_x() - transform.get_size_x() * 0.5
		yCondition = mY <= transform.get_pos_y() + transform.get_size_y() * 0.5 and mY > transform.get_pos_y() - transform.get_size_y() * 0.5
		
		ret = xCondition and yCondition
		return ret
		

	def __colliding_x__(self, t1, t2):
	
		ret = False
		
		len = abs(t1.get_size_x() * 0.5 + t2.get_size_x() * 0.5)
		
		if abs(t1.get_pos_x() - t2.get_pos_x()) < len:
			ret = True
		
		return ret

		
	def __colliding_y__(self, t1, t2):
		ret = False
		
		len = abs(t1.get_size_y() * 0.5 + t2.get_size_y() * 0.5)
		
		if abs(t1.get_pos_y() - t2.get_pos_y()) < len:
			ret = True
		
		return ret
		
		
	def __distance__(self, t1, t2):
		x1 = t1.get_pos_x()
		y1 = t1.get_pos_y()
		x2 = t2.get_pos_x()
		y2 = t2.get_pos_y()
		dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
		return dist
		
	
	def event_loop(self):
		while self.isRunning:
			mX, mY = pygame.mouse.get_pos()
			
			frameDelta = time.time() - self.lastEventTime
			self.lastEventTime = time.time()
			
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.close()
				elif event.type == pygame.MOUSEBUTTONDOWN:
					clickedUI = None
					
					# REVERSE the ui click detection, very important
					for ui in reversed(self.uiComponents):
						if ui.get_visible():
							if self.__is_in__(mX, mY, ui):
								clickedUI = ui
								ui.on_clicked()
								break
			
			for ui in self.uiComponents:
				if ui.get_visible():
					if self.hoveredUI:
						if not self.__is_in__(mX, mY, self.hoveredUI):
							self.hoveredUI.on_hover_end()
							self.hoveredUI = None
						break
					else:
						if self.__is_in__(mX, mY, ui):
							self.hoveredUI = ui
							ui.on_hover_begin()
							
				elif event.type == pygame.KEYDOWN:
				
					rawKey = event.key
					prettyKey = event.unicode
					
					if rawKey == pygame.K_w:
						self.input.set_pos_y(-1)
					elif rawKey == pygame.K_a:
						self.input.set_pos_x(-1)
					elif rawKey == pygame.K_s:
						self.input.set_pos_y(1)
					elif rawKey == pygame.K_d:
						self.input.set_pos_x(1)
					
					
				elif event.type == pygame.KEYUP:
				
					rawKey = event.key
						
					if rawKey == pygame.K_w:
						self.input.set_pos_y(-self.input.get_pos_y() + 1)
					elif rawKey == pygame.K_a:
						self.input.set_pos_x(-self.input.get_pos_x() + 1)
					elif rawKey == pygame.K_s:
						self.input.set_pos_y(-self.input.get_pos_y() - 1)
					elif rawKey == pygame.K_d:
						self.input.set_pos_x(-self.input.get_pos_x() - 1)
			
			if self.activeGame:
				self.activeGame.player.set_move(self.input.get_pos_x(), self.input.get_pos_y())
					
				
				# ensure entities cannot walk into tiles
				for entity in self.activeGame.currentRoom.entities:
					for tile in self.activeGame.currentRoom.tiles:
						if tile.isBlocking:
						
							a = tile.get_pos_x() - entity.get_pos_x()
							b = tile.get_pos_y() - entity.get_pos_y()
							
							xDir = clamp01(a)
							yDir = clamp01(b)
							
							#print(entity.get_pos())
						
							if self.__colliding_x__(entity, tile) and self.__colliding_y__(entity, tile):
								if entity.get_move_x() == xDir and (b > a or a > b):
									entity.set_move_x(0)
									#print("Xcolide")
								if entity.get_move_y() == yDir and (a > b or b > a):
									entity.set_move_y(0)
									#print("                      Ycolide")
							
							"""if self.__colliding_x__(entity, tile) or self.__colliding_y__(entity, tile):
								if self.__colliding_x__(entity, tile):
									if entity.get_move_x() == xDir:
										entity.set_move_x(0)
								elif self.__colliding_y__(entity, tile):
									if entity.get_move_y() == yDir:
										entity.set_move_y(0)"""
									
								

					entity.update(frameDelta)
					
	
	def __draw_ui__(self, ui):
		pygame.draw.rect(self.pySurface, ui.color, (
			ui.get_pos_x() - (ui.get_size_x() * 0.5),
			ui.get_pos_y() - (ui.get_size_y() * 0.5),
			ui.get_size_x(),
			ui.get_size_y()
		))
		pygame.draw.rect(self.pySurface, ui.borderColor, (
			ui.get_pos_x() - (ui.get_size_x() * 0.5),
			ui.get_pos_y() - (ui.get_size_y() * 0.5),
			ui.get_size_x(),
			ui.borderSize
		))
		pygame.draw.rect(self.pySurface, ui.borderColor, (
			ui.get_pos_x() - (ui.get_size_x() * 0.5),
			ui.get_pos_y() - (ui.get_size_y() * 0.5) + ui.get_size_y() - ui.borderSize,
			ui.get_size_x(),
			ui.borderSize
		))
		pygame.draw.rect(self.pySurface, ui.borderColor, (
			ui.get_pos_x() - (ui.get_size_x() * 0.5),
			ui.get_pos_y() - (ui.get_size_y() * 0.5),
			ui.borderSize,
			ui.get_size_y()
		))
		pygame.draw.rect(self.pySurface, ui.borderColor, (
			ui.get_pos_x() - (ui.get_size_x() * 0.5) + ui.get_size_x() - ui.borderSize,
			ui.get_pos_y() - (ui.get_size_y() * 0.5),
			ui.borderSize,
			ui.get_size_y()
		))
	
	def draw_loop(self):
		while self.isRunning:
			frameDelta = time.time() - self.lastDrawTime
			self.lastDrawTime = time.time()
			
			self.pySurface.fill(self.FILL_COLOR)
			
			if self.activeGame:
				for tile in self.activeGame.currentRoom.tiles:
					tile.draw(self.pySurface)
				for entity in self.activeGame.currentRoom.entities:
					entity.draw(self.pySurface)
					entity.animate()
				
			for ui in self.uiComponents:
				if ui.get_visible():
					self.__draw_ui__(ui)
					ui.draw(self.pySurface);

				
			self.pyClock.tick(60)
			pygame.display.update()
		
