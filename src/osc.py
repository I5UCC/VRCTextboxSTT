# Code taken and modified katosc.py from https://github.com/killfrenzy96/KatOscApp
# Copyright (C) 2022 KillFrenzy / Evan Tran
# This code is provided under the GPL-3.0 license

from threading import Timer
from pythonosc import udp_client, osc_server, dispatcher
import math, asyncio, threading


class OscHandler:
	def __init__(self, osc_ip: str, osc_port: int, osc_server_ip: str, osc_server_port: int):
		self.isactive = False

		self.osc_enable_server = True # Used to improve sync with in-game avatar and autodetect sync parameter count used for the avatar.
		self.osc_server_ip = osc_server_ip # OSC server IP to listen too
		self.osc_server_port = osc_server_port # OSC network port for recieving messages
		self.osc_ip = osc_ip # OSC server IP to send too
		self.osc_port = osc_port # OSC network port for sending messages

		self.osc_delay: float = 0.25 # Delay between network updates in seconds. Setting this too low will cause issues.
		self.osc_chatbox_delay: float = 1.25 # Delay between chatbox updates in seconds. Setting this too low will cause issues.
		self.sync_params: int = 16 # Default sync parameters. This is automatically updated if the OSC server is enabled.

		self.line_length: int = 32 # Characters per line of text
		self.line_count: int = 4 # Maximum lines of text

		self.kat_charlimit: int = 128 # Maximum length of text for KAT
		self.textbox_charlimit: int = 144 # Maximum length of text for textbox
		self.sync_params_max: int = 16 # Maximum sync parameters
		self.sync_params_last: int = self.sync_params # Last detected sync parameters

		self.pointer_count: int = int(self.kat_charlimit / self.sync_params)
		self.pointer_clear: int = 255
		self.pointer_index_resync: int = 0

		self.sync_params_test_char_value: int = 97 # Character value to use when testing sync parameters

		self.param_visible: str = "KAT_Visible"
		self.param_pointer: str = "KAT_Pointer"
		self.param_sync: str = "KAT_CharSync"

		self.osc_parameter_prefix: str = "/avatar/parameters/"
		self.osc_avatar_change_path: str = "/avatar/change"
		self.osc_chatbox_path: str = "/chatbox/input"
		self.osc_chatbox_typing_path = "/chatbox/typing"
		self.osc_parameter_listening = "/avatar/parameters/stt_listening"
		self.last_chatbox_text: str = ""
		self.osc_chatbox_text: str = ""
		self.osc_text: str = ""
		self.kat_target_text: str = ""
		self.textbox_target_text: str = ""

		self.invalid_char: str = "?" # character used to replace invalid characters

		self.keys = {
			" ": 0,
			"!": 1,
			"\"": 2,
			"#": 3,
			"$": 4,
			"%": 5,
			"&": 6,
			"'": 7,
			"(": 8,
			")": 9,
			"*": 10,
			"+": 11,
			",": 12,
			"-": 13,
			".": 14,
			"/": 15,
			"0": 16,
			"1": 17,
			"2": 18,
			"3": 19,
			"4": 20,
			"5": 21,
			"6": 22,
			"7": 23,
			"8": 24,
			"9": 25,
			":": 26,
			";": 27,
			"<": 28,
			"=": 29,
			">": 30,
			"?": 31,
			"@": 32,
			"A": 33,
			"B": 34,
			"C": 35,
			"D": 36,
			"E": 37,
			"F": 38,
			"G": 39,
			"H": 40,
			"I": 41,
			"J": 42,
			"K": 43,
			"L": 44,
			"M": 45,
			"N": 46,
			"O": 47,
			"P": 48,
			"Q": 49,
			"R": 50,
			"S": 51,
			"T": 52,
			"U": 53,
			"V": 54,
			"W": 55,
			"X": 56,
			"Y": 57,
			"Z": 58,
			"[": 59,
			"\\": 60,
			"]": 61,
			"^": 62,
			"_": 63,
			"`": 64,
			"a": 65,
			"b": 66,
			"c": 67,
			"d": 68,
			"e": 69,
			"f": 70,
			"g": 71,
			"h": 72,
			"i": 73,
			"j": 74,
			"k": 75,
			"l": 76,
			"m": 77,
			"n": 78,
			"o": 79,
			"p": 80,
			"q": 81,
			"r": 82,
			"s": 83,
			"t": 84,
			"u": 85,
			"v": 86,
			"w": 87,
			"x": 88,
			"y": 89,
			"z": 90,
			"{": 91,
			"|": 92,
			"}": 93,
			"~": 94,
			"???": 95,
			"??": 96,
			"??": 97,
			"??": 98,
			"??": 99,
			"??": 100,
			"??": 101,
			"??": 102,
			"??": 103,
			"??": 104,
			"??": 105,
			"??": 106,
			"??": 107,
			"??": 108,
			"??": 109,
			"??": 110,
			"??": 111,
			"??": 112,
			"??": 113,
			"??": 114,
			"??": 115,
			"??": 116,
			"??": 117,
			"??": 118,
			"??": 119,
			"??": 120,
			"??": 121,
			"??": 122,
			"??": 123,
			"??": 124,
			"??": 125,
			"??": 126,
			"???": 127,
			"???": 129,
			"???": 130,
			"???": 131,
			"???": 132,
			"???": 133,
			"???": 134,
			"???": 135,
			"???": 136,
			"???": 137,
			"???": 138,
			"???": 139,
			"???": 140,
			"???": 141,
			"???": 142,
			"???": 143,
			"???": 144,
			"???": 145,
			"???": 146,
			"???": 147,
			"???": 148,
			"???": 149,
			"???": 150,
			"???": 151,
			"???": 152,
			"???": 153,
			"???": 154,
			"???": 155,
			"???": 156,
			"???": 157,
			"???": 158,
			"???": 159,
			"???": 160,
			"???": 161,
			"???": 162,
			"???": 163,
			"???": 164,
			"???": 165,
			"???": 166,
			"???": 167,
			"???": 168,
			"???": 169,
			"???": 170,
			"???": 171,
			"???": 172,
			"???": 173,
			"???": 174,
			"???": 175,
			"???": 176,
			"???": 177,
			"???": 178,
			"???": 179,
			"???": 180,
			"???": 181,
			"???": 182,
			"???": 183,
			"???": 184,
			"???": 185,
			"???": 186,
			"???": 187,
			"???": 188,
			"???": 189,
			"???": 190,
			"???": 191,
			"???": 192,
			"???": 193,
			"???": 194,
			"???": 195,
			"???": 196,
			"???": 197,
			"???": 198,
			"???": 199,
			"???": 200,
			"???": 201,
			"???": 202,
			"???": 203,
			"???": 204,
			"???": 205,
			"???": 206,
			"???": 207,
			"???": 208,
			"???": 209,
			"???": 210,
			"???": 211,
			"???": 212,
			"???": 213,
			"???": 214,
			"???": 215,
			"???": 216,
			"???": 217,
			"???": 218,
			"???": 219,
			"???": 220,
			"???": 221,
			"???": 222,
			"???": 223,
			"???": 224,
			"???": 225,
			"???": 226,
			"???": 227,
			"???": 228,
			"???": 229,
			"???": 230,
			"???": 231,
			"???": 232,
			"???": 233,
			"???": 234,
			"???": 235,
			"???": 236,
			"???": 237,
			"???": 238,
			"???": 239,
			"???": 240,
			"???": 241,
			"???": 242,
			"???": 243,
			"???": 244,
			"???": 245,
			"???": 246,
			"???": 247,
			"???": 248,
			"???": 249,
			"???": 250,
			"???": 251,
			"???": 252,
			"???": 253,
			"???": 254,
			"??": 255
		}

		self.emote_keys = dict()
		i = 0
		tmp = ""
		for key, value in self.keys.items():
			if value >= 96:
				if value % 2 == 0:
					tmp = str(key)
				else:
					tmp = tmp + str(key)
					self.emote_keys[i] = tmp
					tmp = ""
					i = i + 1
				
		# Character to use in place of unknown characters
		self.invalid_char_value: int = self.keys.get(self.invalid_char, 0)

		# --------------
		# OSC Setup
		# --------------

		# Setup OSC Chatbox
		self.osc_chatbox_timer = RepeatedTimer(self.osc_chatbox_delay, self.osc_chatbox_loop)

		# Setup OSC Client
		self.osc_client = udp_client.SimpleUDPClient(self.osc_ip, self.osc_port)
		self.osc_timer = RepeatedTimer(self.osc_delay, self.osc_timer_loop)

		self.osc_client.send_message(self.osc_parameter_prefix + self.param_pointer, 255) # Clear KAT text
		for value in range(self.sync_params):
			self.osc_client.send_message(self.osc_parameter_prefix + self.param_sync + str(value), 0.0) # Reset KAT characters sync

		# Setup OSC Server
		self.osc_server: osc_server.ThreadingOSCUDPServer = None
		self.osc_server_test_step: int = 0
		self.osc_dispatcher: dispatcher.Dispatcher = None

		if self.osc_enable_server:
			self.osc_start_server()

		# Start timer loop
		self.osc_chatbox_timer.start()
		self.osc_timer.start()

	# Starts the OSC Server
	def osc_start_server(self):
		if self.osc_server == None:
			try:
				self.osc_server_test_step = 1

				self.osc_dispatcher = dispatcher.Dispatcher()
				self.osc_dispatcher.map(self.osc_parameter_prefix + self.param_sync + "*", self.osc_server_handler_char)
				self.osc_dispatcher.map(self.osc_avatar_change_path + "*", self.osc_server_handler_avatar)

				self.osc_server = osc_server.ThreadingOSCUDPServer((self.osc_server_ip, self.osc_server_port), self.osc_dispatcher, asyncio.get_event_loop())
				threading.Thread(target = self.osc_server_serve, daemon = True).start()
			except:
				self.osc_enable_server = False
				self.osc_server_test_step = 0

	# Stops the OSC Server
	def osc_stop_server(self):
		if self.osc_server:
			self.osc_server.shutdown()
			self.osc_server = False
			self.osc_enable_server = False


	# Set the text to any value
	def set_textbox_text(self, text: str, cutoff: bool = False, instant: bool = False):
		if cutoff:
			self.textbox_target_text = text[-self.textbox_charlimit:]
		else:
			self.textbox_target_text = text[:self.textbox_charlimit]

		if instant:
			self.osc_chatbox_loop()


	# Set the text to any value
	def set_kat_text(self, text: str, cutoff: bool = False):
		if cutoff:
			self.kat_target_text = text[-self.kat_charlimit:]
		else:
			self.kat_target_text = text[:self.kat_charlimit]


	# Sets the sync parameter count
	def set_sync_params(self, sync_params: int):
		if sync_params == 0:
			# Automatic sync parameters
			self.osc_start_server()
		else:
			# Manual sync parameter setting
			self.sync_params = sync_params
			self.sync_params_last = self.sync_params
			self.pointer_count = int(self.kat_charlimit / self.sync_params)

			self.osc_server_test_step = -1 # Reset parameters and clear text
			self.osc_stop_server()


	# Chatbox loop
	def osc_chatbox_loop(self):
		gui_text = self.textbox_target_text.replace("\n", " ")

		if gui_text == self.last_chatbox_text:
			return

		self.last_chatbox_text = gui_text

		self.osc_client.send_message(self.osc_chatbox_path, [gui_text, True, True if self.textbox_target_text == "" else False])
		self.osc_chatbox_text = gui_text

	def set_kat_typing_indicator(self, state: bool):
		self.osc_client.send_message(self.osc_parameter_listening, state)

	def set_textbox_typing_indicator(self, state: bool):
		self.osc_client.send_message(self.osc_chatbox_typing_path, state)

	# Syncronisation loop
	def osc_timer_loop(self):
		gui_text = self.kat_target_text

		# Test parameter count if an update is requried
		if type(self.osc_server) == osc_server.ThreadingOSCUDPServer:
			if self.osc_server_test_step > 0:
				# Keep text cleared during test
				self.osc_client.send_message(self.osc_parameter_prefix + self.param_pointer, self.pointer_clear)

				if self.osc_server_test_step == 1:
					# Reset sync parameters count
					self.sync_params = 0

					# Reset character text values
					for char_index in range(self.sync_params_max):
						self.osc_client.send_message(self.osc_parameter_prefix + self.param_sync + str(char_index), 0.0)
					self.osc_server_test_step = 2
					return

				elif self.osc_server_test_step == 2:
					# Set characters to test value
					for char_index in range(self.sync_params_max):
						self.osc_client.send_message(self.osc_parameter_prefix + self.param_sync + str(char_index), self.sync_params_test_char_value / 127.0)
					self.osc_server_test_step = 3
					return

				elif self.osc_server_test_step == 3:
					# Set characters back to 0
					for char_index in range(self.sync_params_max):
						self.osc_client.send_message(self.osc_parameter_prefix + self.param_sync + str(char_index), 0.0)
					self.osc_server_test_step = 4
					return

				elif self.osc_server_test_step == 4:
					# Finish the parameter sync test
					if self.sync_params == 0:
						self.sync_params = self.sync_params_last # Test failed, reuse last detected param count
						self.isactive = False
					else:
						self.sync_params_last = self.sync_params
						self.isactive = True
					self.osc_server_test_step = 0
					self.pointer_count = int(self.kat_charlimit / self.sync_params)
					self.osc_text = " ".ljust(self.kat_charlimit) # Resync letters

		# Do not process anything if sync parameters are not setup
		if self.sync_params == 0:
			return

		# Sends clear text message if all text is empty
		if gui_text.strip("\n").strip(" ") == "" or self.osc_server_test_step == -1:

			# Reset parameters
			if self.osc_server_test_step == -1:
				for char_index in range(self.sync_params_max):
					self.osc_client.send_message(self.osc_parameter_prefix + self.param_sync + str(char_index), 0.0)
					self.osc_server_test_step = 0

			# Clear text
			self.osc_client.send_message(self.osc_parameter_prefix + self.param_pointer, self.pointer_clear)
			self.osc_text = " ".ljust(self.kat_charlimit)
			return

		# Make sure KAT is visible even after avatar change
		self.osc_client.send_message(self.osc_parameter_prefix + self.param_visible, True)

		# Pad line feeds with spaces for OSC
		text_lines = gui_text.split("\n")
		for index, text in enumerate(text_lines):
			text_lines[index] = self._pad_line(text)
		gui_text = self._list_to_string(text_lines)

		# Pad text with spaces up to the text limit
		gui_text = gui_text.ljust(self.kat_charlimit)
		osc_text = self.osc_text.ljust(self.kat_charlimit)

		# Text syncing
		osc_chars = list(osc_text)
		if gui_text != self.osc_text: # GUI text is different, needs sync

			for pointer_index in range(self.pointer_count):
				# Check if characters within this pointer are different
				equal = True
				for char_index in range(self.sync_params):
					index = (pointer_index * self.sync_params) + char_index

					if gui_text[index] != osc_text[index]:
						equal = False
						break

				if equal == False: # Characters not equal, need to sync this pointer position
					self.osc_update_pointer(pointer_index, gui_text, osc_chars)
					return

		# No updates required, use time to resync text
		self.pointer_index_resync = self.pointer_index_resync + 1
		if self.pointer_index_resync >= self.pointer_count:
			self.pointer_index_resync = 0

		pointer_index = self.pointer_index_resync
		self.osc_update_pointer(pointer_index, gui_text, osc_chars)

	# Starts the OSC server serve
	def osc_server_serve(self):
		self.osc_server.serve_forever(2)


	# Handle OSC server to detect the correct sync parameters to use
	def osc_server_handler_char(self, address: tuple[str, int], value: str, *args: list[dispatcher.Any]):
		if self.osc_server_test_step > 0:
			length = len(self.osc_parameter_prefix + self.param_sync)
			self.sync_params = max(self.sync_params, int(address[length:]) + 1)


	# Handle OSC server to retest sync on avatar change
	def osc_server_handler_avatar(self, address: tuple[str, int], value: str, *args: list[dispatcher.Any]):
		self.osc_server_test_step = 1
		self.isactive = False


	# Updates the characters within a pointer
	def osc_update_pointer(self, pointer_index: int, gui_text: str, osc_chars: list[int]):
		self.osc_client.send_message(self.osc_parameter_prefix + self.param_pointer, pointer_index + 1) # Set pointer position

		# Loop through characters within this pointer and set them
		for char_index in range(self.sync_params):
			index = (pointer_index * self.sync_params) + char_index
			gui_char = gui_text[index]

			# Convert character to the key value, replace invalid characters
			key = self.keys.get(gui_char, self.invalid_char_value)

			# Calculate character float value for OSC
			value = float(key)
			if value > 127.5:
				value = value - 256.0
			value = value / 127.0

			self.osc_client.send_message(self.osc_parameter_prefix + self.param_sync + str(char_index), value)
			osc_chars[index] = gui_char # Apply changes to the networked value

		self.osc_text = self._list_to_string(osc_chars)


	# Combines an array of strings into a single string
	def _list_to_string(self, string: str):
		return "".join(string)


	# Pads the text line to its effective length
	def _pad_line(self, text: str):
		return text.ljust(self._get_padded_length(text))


	# Gets the effective padded length of a line
	def _get_padded_length(self, text: str):
		lines = max(math.ceil(len(text) / self.line_length), 1)
		return self.line_length * lines


	# Stop the timer and hide the text overlay
	def stop(self):
		try:
			self.osc_timer.stop()
		except Exception as e:
			print(e)
		try:
			self.osc_chatbox_timer.stop()
		except Exception as e:
			print(e)
		try:
			self.osc_stop_server()
		except Exception as e:
			print(e)
		self.hide()
		self.clear_kat()
		self.clear_chatbox()
		


	# Restart the timer for syncing texts and show the overlay
	def start(self):
		try:
			self.osc_timer.start()
		except Exception as e:
			print(e)
		try:
			self.osc_chatbox_timer.start()
		except Exception as e:
			print(e)
		try:
			self.osc_start_server()
		except Exception as e:
			print(e)
		self.osc_timer.start()
		self.osc_chatbox_timer.start()
		self.hide()
		self.clear_kat()
		self.clear_chatbox()


	# show overlay
	def show(self):
		self.osc_client.send_message(self.osc_parameter_prefix + self.param_visible, True) # Hide KAT


	# hide overlay
	def hide(self):
		self.osc_client.send_message(self.osc_parameter_prefix + self.param_visible, False) # Hide KAT


	# clear text
	def clear_kat(self):
		self.osc_text = ""
		self.kat_target_text = ""
		self.osc_client.send_message(self.osc_parameter_prefix + self.param_pointer, 255) # Clear KAT text
		self.hide()

	def clear_chatbox(self, instant: bool = False):
		self.textbox_target_text = ""

		if instant:
			self.osc_chatbox_loop()


class RepeatedTimer(object):
	def __init__(self, interval: float, function, *args, **kwargs):
		self._timer: Timer = None
		self.interval = interval
		self.function = function
		self.args = args
		self.kwargs = kwargs
		self.is_running: bool = False
		self.start()

	def _run(self):
		self.is_running = False
		self.start()
		self.function(*self.args, **self.kwargs)

	def start(self):
		if not self.is_running:
			self._timer = Timer(self.interval, self._run)
			self._timer.start()
			self.is_running = True

	def stop(self):
		self._timer.cancel()
		self.is_running = False


class ReturnThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        threading.Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, timeout=None):
        threading.Thread.join(self, timeout)
        return self._return
