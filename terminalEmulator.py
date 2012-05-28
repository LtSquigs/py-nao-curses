import curses
import curses.ascii
from curses.ascii import ESC

import itertools

class TerminalEmulator():
	"""
	Emulates a terminal in curses, parses telnet information, and uses
	vt_tiledata information to add some extra functionality.
	"""
	def __init__(self, window):
		"""
		Initializes windows, some state machine information, and the color information
		used by the terminal emulator.
		"""	
		self.borderWin = curses.newwin(27, 83, 0, 0)
		self.borderWin.border()
		self.borderWin.refresh()

		self.window = curses.newwin(25, 81, 1, 1)
		self.window.nodelay(1)
		self.window.keypad(1)

		self.windows = 	{ 
				  -1 : (self.window , False), 
				   3 : (self.window, False), 
				}

		self.nethackWindowsCleared = []
	
	 	curses.mousemask(curses.ALL_MOUSE_EVENTS)

		self.bottomWindowBorder = curses.newwin(4, 83, 27, 0)
		self.bottomWindowBorder.border()
		self.bottomWindowBorder.refresh()

		self.bottomWindow = curses.newwin(2, 81, 28, 1)
		self.bottomWindow.refresh()

		self.window.move(0,0)
	
		self.debugLevel = 0
		self.debugFile = None
		self.debugFileName = 'debug'
		
		self.escapeBuffer = ''
		self.isEscape = False
		self.isEscapeSequence = False
		self.isShiftSequence = False
		self.shiftOut = False
	
		self.carriageReturn = False
	
		self.fgColor = 'White'
		self.bgColor = 'Black'
		self.colors = { 'Black' : curses.COLOR_BLACK, 'Red' : curses.COLOR_RED, 'Green' : curses.COLOR_GREEN, 'Yellow' : curses.COLOR_YELLOW, 'Blue' : curses.COLOR_BLUE, 'Magenta' : curses.COLOR_MAGENTA, 'Cyan' : curses.COLOR_CYAN, 'White' : curses.COLOR_WHITE}
		self.fgColors = { 30 : 'Black', 31 : 'Red', 32 : 'Green', 33 : 'Yellow', 34 : 'Blue', 35 : 'Magenta', 36 : 'Cyan', 37 : 'White' }
		self.bgColors = { 40 : 'Black', 41 : 'Red', 42 : 'Green', 43 : 'Yellow', 44 : 'Blue', 45 : 'Magenta', 46 : 'Cyan', 47 : 'White' }
		self.colorPairs = {}
		
		self.initColors()

		self.tileArray = [[-1 for x in range(0, 80)] for x in range(0, 24)]

		self.tileData = {}
		self.loadTiles()

	def loadTiles(self):
		"""
		Loads tile data from file called 'tiles' in directory (if exists), used
		by emulator to provide information about clicked tiles in nethack.
		"""
		self.tileData = {}

		try:
			tileFile = open('tiles', 'r')
		except IOError: #If theres no tile data, then just dont load anything, other code will handle fine
			return

		for line in tileFile.readlines():
			if line.strip() == '':
				continue
			else:
				parts = line.split(': ')
				self.tileData[int(parts[0])] = parts[1]

	def writeToWindow(self, window, string, reset = False):
		"""
		Used to write strings to auxillary windows, writes the string and then 
		moves cursor back to the main window.
		"""
		origy, origx = self.window.getyx()
		maxy, maxx = window.getmaxyx()

		if reset:
			window.clear()
			window.move(0,0)	

		try:
			window.addstr(string)
		except curses.error:
			pass
		
		window.refresh()	
		self.window.move(origy, origx)

	def cleanup(self):
		"""
		Clean up some things before the TerminalEmulator object is destroyed
		"""
		if self.debugFile != None:
			self.debugFile.close()
			self.debugFile = None

		self.window.nodelay(0)
		self.window.keypad(0)

	def initColors(self):
		"""
		Initialize all color pairs allowed by the xterm escape codes.
		"""
		pairNum = 1
		for pair in itertools.product(self.colors.iterkeys(), repeat=2):
			curses.init_pair(pairNum, self.colors[pair[0]], self.colors[pair[1]])
			self.colorPairs[ (pair[0], pair[1]) ] = pairNum
			pairNum = pairNum + 1
		
	
	def set_debugLevel(self, level):
		"""
		Set debug level. If level > 0 then the file 'debug' is created in the working directory, and
		varying levels of debug information are outputted to it.
		"""
		self.debugLevel = level
		if level == 0 and self.debugFile != None:
			self.debugFile.close()
			self.debugFile = None
		elif level > 0 and self.debugFile == None:
			self.debugFile = open(self.debugFileName, 'w')
	
	def printDebug(self, string, level):
		"""
		Prints string to the debug file is the debug level is higher or equal to level
		"""
		if self.debugLevel >= level and self.debugLevel > 0:
			self.debugFile.write(string)
	
	def printCh(self, char):
		"""
		Prints character to the current window, handles shifting out of code page to emulate
		DECGraphics
		"""
		if self.shiftOut: # Change code pages if in a shift out section
			self.window.attron(curses.A_ALTCHARSET)
			
		try:
			self.window.addch(char)
		
			self.printDebug(char, 5)	
		except curses.error: # Apparent addchr raises an error to indicate the end of a line has been reached, ignore it
			pass
			
		if self.shiftOut:
			self.window.attroff(curses.A_ALTCHARSET) #undo code page shift
	
	def parseTelnetText(self, telnetBuffer):
		"""
		Parses a string of characters recieved over telnet. Escape codes are interpreted and handled, everything
		else is simply printed to the current window.
		"""
		self.printDebug('recv: ' + telnetBuffer + '\n', 2)
	
		for char in telnetBuffer:
			if self.carriageReturn and char != '\n': # Handles the special case of \r\n... if we see \r and not \n then back up and reprint \r
				self.printCh('\r')
				self.carriageReturn = False

			if char == '\x1b': # ESC, start of an escape sequence
				self.isEscape = True
				self.escapeBuffer += char
			elif char == '\x0f': #SHIFT IN, ASCII code to shift code pages back to normal
				self.shiftOut = False
			elif char == '\x0e': #SHIFT OUT, ASCII code to shift code pages to extended
				self.shiftOut = True
			elif char == '\r': #CURSES CAN NOT HANDLE \r\n.... so gotta work around that
				self.carriageReturn = True
	
			else:
				if not self.isEscape: #Not in an escape sequence, normal character
					self.printCh(char)	
				elif self.isEscape and not self.isEscapeSequence and not self.isShiftSequence: #We had an escape char, which means this might be an escape sequence
					if char == '[': #This is an escape code
						self.isEscapeSequence = True
						self.escapeBuffer += char
					elif char == '(': #This is an xterm code to switch to extended page, treat same as shift in and out
						self.isShiftSequence = True
						self.escapeBuffer += char
					else: #Might be an escape sequence, but its not one I know or care about
						self.isEscape = False
						self.window.addstr(self.escapeBuffer + char)
						self.escapeBuffer =''

				elif self.isEscape and self.isEscapeSequence: #We have an escape sequence
					if curses.ascii.isalpha(char): #ESC sequences are ended by an alpha char
						self.isEscape = False
						self.isEscapeSequence = False
						self.escapeBuffer += char
						self.parseEscape()
						self.escapeBuffer = ''
					else:
						self.escapeBuffer += char
				elif self.isEscape and self.isShiftSequence: #Have a shift out/in sequence
					if char == '0': #0 means to shift into extended
						self.shiftOut = True
					elif char == 'B': #B means to return to American
						self.shiftOut = False
					else: #Unkown
						self.printDebug('Unkonw shift sequence: ' + char + '\n', 3)
						
					self.isShiftSequence = False
					self.isEscape = False
					self.escapeBuffer = ''
		
		self.window.refresh()
		
	def parseEscape(self):
		"""
		Parses the escape code currently in self.escapeBuffer and executes the command
		on the terminal.
		"""
		ctrl = self.escapeBuffer[-1]
		params = self.escapeBuffer[2:-1]
		
		if ctrl == 'H' or ctrl == 'f': #Move cursor absolute
			if len(params) == 0: #default command is to move to origin
				self.window.move(0, 0)
			else: #else move to y, x (where y and x are off by one because escape codes start at 0,0)
				split = params.split(';')
				maxy, maxx = self.window.getmaxyx()

				self.window.move( min(int(split[0]), maxy) - 1, min(int(split[1]), maxx) - 1)
		elif ctrl == 'J': #Clear Screen
			if len(params) == 0 or int(params) == 0: #Clear to bottom of screen
				self.window.clrtobot()
			elif int(params) == 1: #Clear screen before this cursor
				y, x = self.window.getyx()
				
				for newy in range(y - 1, -1, -1): #Clear lines before this
					self.window.move(newy, x)
					self.window.deleteln()
					self.window.insertln()
		
				for newx in range(0, x + 1): #Then replace chars before it
					self.window.addch(y, newx, ' ', 0)
	
				self.window.move(y, x)
			elif int(params) == 2: #Erase whole screen
				self.window.erase()
				self.tileArray = [[-1 for x in range(0, 80)] for x in range(0, 24)] #Erase tile data

		elif ctrl == 'B': # Move Cursor Down
			y, x = self.window.getyx()
			maxy, maxx = self.window.getyx()
			
			if len(params) == 0:
				self.window.move(min(y + 1, maxy - 1), x)
			else:
				self.window.move(min(y + int(params), maxy - 1), x)
		elif ctrl == 'D': #Move Cursor Left
			y, x = self.window.getyx()
				
			if len(params) == 0:
				self.window.move(y, max(x - 1, 0))
			else:
				self.window.move(y, max(x - int(params), 0))
		elif ctrl == 'A': #Move Cursor Up
			y, x = self.window.getyx()
				
			if len(params) == 0:
				self.window.move(max(y - 1, 0), x)
			else:
				self.window.move(max(y - int(params), 0), x)
		elif ctrl == 'C': #Move Cursor Right
			y, x = self.window.getyx()
			maxy, maxx = self.window.getmaxyx()
			
			if len(params) == 0:
				self.window.move(y, min(x + 1, maxx - 1))
			else:
				self.window.move(y, min(x + int(params), maxx - 1))
		elif ctrl == 'd': #Move to row
			y, x = self.window.getyx()
			maxy, maxx = self.window.getmaxyx()
			
			if len(params) == 0:
				self.window.move(0, x)
			else:
				self.window.move(min(int(params) - 1, maxy -1 ), x)
		elif ctrl == 'G': #move to column
			y, x = self.window.getyx()
			maxy, maxx = self.window.getmaxyx()
			
			if len(params) == 0:
				self.window.move(y, 0)
			else:
				self.window.move(y, min(int(params) - 1, maxx - 1))
		elif ctrl == 'K': #Selective delete.... fix this shit up
			if len(params) == 0 or int(params) == 0: # DELETE ALL CHARS IN FRONT OF ME
				y, x = self.window.getyx()
			
				maxy, maxx = self.window.getmaxyx()

				for newx in range(x, maxx):
					self.window.addch(y, newx, ' ', 0) 

				self.window.move(y, x)

			elif int(params) == 1: #clear from beggining to cursor
				y, x = self.window.getyx()
				for newx in range(0, x+1):
					self.window.addch(y, newx, ' ', 0)
				self.window.move(y,x)

			elif int(params) == 2: #clear the line
				self.window.deleteln()
				self.window.insertln()
		elif ctrl == 'P': # Delete param # characters (1 default)
			if len(params) == 0: 
				y, x = self.window.getyx()
				self.window.addch(y, x, ' ', 0)
				self.window.move(y, x)
			else:
				numChars = int(params)
				y, x = self.window.getyx()
				maxy, maxx = self.window.getmaxyx()		
				stopx = x + numChars 

				for newx in range(x, min(maxx, stopx)):
					self.window.addch(y, x, ' ', 0)
				self.window.move(y, x)
				

		elif ctrl == 'h' or ctrl == 'l': #special terminal stuff, probably doesnt actually matter
			pass
		elif ctrl == 'r': # scrolling enabled...?, ignore for now
			pass
		elif ctrl == 'z': # vt_tiledata information 

			code = params[0]
			if code == '2': # Switch Screen...
				windowNum = params.split(';')[1]
				try:
					self.window = self.windows[int(windowNum)][0]
					if self.windows[int(windowNum)][1]:
						self.window.erase()

				except: # If we cant find it, lets use the default window
					self.window = self.windows[-1][0]
			if code == '0': # Glyph
				glyphNum = params.split(';')[1]
				y, x = self.window.getyx()
				self.tileArray[y][x] = int(glyphNum)
			if code == '1': # End Glyph
				pass
			if code == '3': # end of nethack output
				for window in self.windows:
					self.windows[window][0].refresh()
				self.window = self.windows[-1][0]
				self.nethackWindowsCleared = []

	
		elif ctrl == 'm': #Set terminal modes
			if len(params) == 0: # Reset modes to default settings
				self.window.attrset(0)
				self.fgColor = 'White'
				self.bgColor = 'Black'
				self.setColor()

			for num in params.split(';'):
				if num == '': 		
					pass
				elif num == '0': # Reset modes to default settings
					self.window.attrset(0)
					self.fgColor = 'White'
					self.bgColor = 'Black'
					self.setColor()
				elif num == '1': # Turn on bold
					self.window.attron(curses.A_BOLD)
				elif num == '2': # Turn on dim
					self.window.attron(curses.A_DIM)
				elif num == '4': # Turn on underline
					self.window.attron(curses.A_UNDERLINE)
				elif num == '5' or params == '6': # Turn on blinking (slow and fast are no different in curses)
					self.window.attron(curses.A_BLINK)
				elif num == '7': # turn on inverse
					self.window.attron(curses.A_REVERSE)
				elif num == '22': # turn off bold and/or dim
					self.window.attroff(curses.A_BOLD)
					self.window.attroff(curses.A_DIM)
				elif num == '24': # turn off underline
					self.window.attroff(curses.A_UNDERLINE)
				elif num == '25': # turn off blink
					self.window.attroff(curses.A_BLINK)
				elif num == '27': # turn off inverse
					self.window.attroff(curses.A_REVERSE)
				elif num == '30': # set fg color to black
					self.fgColor = 'Black'
				elif num == '31': # set fg color to red
					self.fgColor = 'Red'
				elif num == '32': # set fg color to green
					self.fgColor = 'Green'
				elif num == '33': # set fg color to yellow
					self.fgColor = 'Yellow'
				elif num == '34': # set fg color to blue
					self.fgColor = 'Blue'
				elif num == '35': # set fg color to magenta
					self.fgColor = 'Magenta'
				elif num == '36': # set fg color to cyan
					self.fgColor = 'Cyan'
				elif num == '37' or num == '39': # set fg color to white or default (which is white)
					self.fgColor = 'White'
				elif num == '40' or num == '49': # set bg color to black or default (which is black)
					self.bgColor = 'Black'
				elif num == '41': # set bg color to red
					self.bgColor = 'Red'
				elif num == '42': # set bg color to green
					self.bgColor = 'Green'
				elif num == '43': # set bg color to yellow
					self.bgColor = 'Yellow'
				elif num == '44': # set bg color to blue
					self.bgColor = 'Blue'
				elif num == '45': # set bg color to magenta
					self.bgColor = 'Magenta'
				elif num == '46': # set bg color to cyan
					self.bgColor = 'Cyan'
				elif num == '47': # set bg color to white
					self.bgColor = 'White'
				else:
					self.printDebug('unkown m code: ' + str(num) + '\n', 1)
					
				self.setColor()
		else:
			self.printDebug('Ctrl Not Implemented: ' + self.escapeBuffer[1] + ctrl + '\n', 1)
	
	def setColor(self):
		"""
		Sets the current writing color to the current self.fgColor and self.bgColor values
		"""
		self.window.attron(curses.color_pair(self.colorPairs[(self.fgColor, self.bgColor)]))
		
	def getCh(self):
		"""
		Gets a character from input immediately. If there is no character to get, returns -1.
		Also handles mouse events, and updates windows appropriately (returns -1 on mouse events)
		"""
		ch = self.window.getch()
	
		if ch == curses.KEY_MOUSE:
			mouseId, x, y, z, event = curses.getmouse()
			
			if event & curses.BUTTON1_CLICKED == curses.BUTTON1_CLICKED:
				x = x - 1 #Adjust due to being in window
				y = y - 1

				try:
					tile = self.tileArray[y][x]
					info = self.tileData[tile]
					self.writeToWindow(self.bottomWindow, 'Information on space from tile at (%d, %d) : %s' % (y, x, info), True)
				except IndexError:
					self.writeToWindow(self.bottomWindow, 'There is no tile information for this space.', True) 			
				except KeyError:
					self.writeToWindow(self.bottomWindow, 'Tile information for this space could not be found.', True)

			return -1

		if ch > 256 or ch < -1: #With keypad(1) enabled its possible to get non ascii values, ignore them
			return -1

		return ch
