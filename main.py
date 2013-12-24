import curses
import terminalEmulator
import telnetClient
		
def main(stdscr):
	
	term = terminalEmulator.TerminalEmulator(stdscr)
	term.set_debugLevel(0)
	
	ß
	client = telnetClient.TelnetClient()
	client.connect()

	try:	
		while True:
			telnetText = client.read()
			if telnetText != '':
				term.parseTelnetText(telnetText)
		
			# get input from term
			inputCh = term.getCh()
			if inputCh != -1:
				client.write( chr(inputCh) )
	except EOFError:  #CONNECTION TERMINATED
		return
	finally:
		term.cleanup()

curses.wrapper(main)
