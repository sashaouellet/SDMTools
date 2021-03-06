"""Represents different collections/specifications for file(s) i.e. shots, sequences, image, scripts, etc.

__author__ = Sasha Ouellet (www.sashaouellet.com)
__version__ = 1.0.0
__date__ = 11/27/17
"""

import os, re

class Sequence():
	_frames = []
	_dir = ''
	_range = ()
	_index = 0

	FRAME_NAME_PATTERN = r'^(?P<prefix>{})[\.\-_](?P<framePadding>\d+)\.(?P<ext>{})$'
	STANDARD_FRAME_FORMAT = '#'
	HOUDINI_FRAME_FORMAT = '$F'

	def __init__(self, dir, range=(), prefix=r'[\w\-\.]+', ext=r'[a-zA-Z]+'):
		self._dir = dir
		self._frames = self._getFrameListFromDir(dir, prefix, ext, range)

		if self._frames:
			self._range = (self._frames[0].getNumber(), self._frames[-1].getNumber())

	def _getFrameListFromDir(self, dir, prefix, ext, range):
		"""Given a directory to look in, retrieves the first found sequence that fits
		the given specifications for prefix and extension. If the range specified
		is not an empty tuple, the frame list returned is limited to that range

		Args:
			dir (str): The directory path to look for a sequence in
			prefix (str): A pattern to match the prefix of the file name against
			ext (str): A pattern to match the extension of the file against
			range (tuple): A tuple representing the allowed start and end range of
				the returned frame lisr. If empty, the full range found is returned

		Returns:
			list: The frame list for the sequence found, empty if no sequence was found
		"""
		frameList = []
		foundArbitrary = False
		padding = 0

		for f in os.listdir(dir):
			parts = self._decompose(f, prefix=prefix, ext=ext)

			if parts:
				frame = Frame(*parts)

				if not foundArbitrary:
					prefix = parts[0].replace('.', '\.').replace('-', '\-')
					ext = parts[2]
					padding = frame.getPadding()

					foundArbitrary = True
				else:
					if len(parts[1]) != padding: # Must continue to match padding length
						continue

				# Is the found frame within the range, if we have specified a range to look for?
				if range:
					if frame.getNumber() < range[0] or frame.getNumber() > range[1]: # Nope, out of range
						continue

				frameList.append(frame)

		frameList.sort(key=lambda f: f.getNumber())

		return frameList

	def _decompose(self, file, prefix, ext):
		"""Decomposes the given file name into its 3 parts: prefix, frame
		padding, and extension

		Returns None if any of the 3 parts are missing

		This makes some assumptions on the standard convention of how frames are
		labeled, in that the frame number occurs as the last string of digits before
		the extension, and is separated from the rest of the file name by one of: '. _ -'

		Args:
			file (str): The file name to check, assumed to be only the file
				name, not a full path
			prefix (str, optional): The prefix pattern that must be matched, by default
				is a generic alphanumeric regex
			ext (str, optional): The extension pattern to match, by default is any extension

		Returns:
			tuple: A tuple containing the value of the 3 parts: file name prefix, frame padding,
				and extension. Returns None if any of these 3 parts was not matched in the file
				given
		"""

		pattern = self.FRAME_NAME_PATTERN.format(prefix, ext)
		regx = re.compile(pattern)
		match = regx.match(file)

		if match:
			return match.groups()

		return None

	def getFrames(self):
		return self._frames

	def getFramesAsNumberList(self):
		return [f.getNumber() for f in self._frames]

	def getDir(self):
		return self._dir

	def getRange(self):
		return self._range

	def getLength(self):
		return self._range[1] - self._range[0] + 1

	def getPadding(self):
		return self._frames[0].getPadding()

	def getPrefix(self):
		return self._frames[0].getPrefix()

	def getExt(self):
		return self._frames[0].getExt()

	def getMissingFrames(self, format=False):
		"""Gets the list of frame numbers that are missing from this sequence

		Returns:
			list: The list of missing frame numbers

		Args:
			format (bool, optional): Convenience for immediately returning a formatted
				list of the missing frames. By default still returns the list, when True
				returns a string with the pretty-printed list
		"""
		current = self.getFramesAsNumberList()
		missing = []

		for i in range(*self._range):
			if i not in current:
				missing.append(i)

		if format:
			return Sequence.prettyPrintFrameList(missing)

		return missing

	def getFormatted(self, format='#', includeDir=False):
		"""Constructs the string format of the file name that represents the
		entire sequence, using the given format as the wildcard replacement
		for the frame number in the file name

		Ex (default behavior):

		fooBar.####.exr where '####' is the frame number replacement for 4-digit padding

		Houdini format ('$F') is handled like so:

		fooBar.$F4.exr (again for 4-digit padding)

		Args:
			format (str, optional): The format of the wildcard for the frame number
				replacement. By default uses the standard wildcard '#'
			includeDir (bool, optional): Whether the returned representative string
				should be the full path to the file, or just the file name. By default,
				only the file name is returned

		Returns:
			str: The formatted string representing the whole sequence
		"""
		padding = self.getPadding()
		framePadding = format * padding

		if format == HOUDINI_FRAME_FORMAT:
			framePadding = HOUDINI_FRAME_FORMAT + padding if padding > 1 else HOUDINI_FRAME_FORMAT

		fileName = '{}.{}.{}'.format(self.getPrefix(), framePadding, self.getExt())

		if includeDir:
			return os.path.join(self.getDir(), fileName)

		return fileName

	def __iter__(self):
		return self

	def next(self):
		if self._index == len(self._frames):
			raise StopIteration

		frame = self._frames[self._index]
		self._index += 1

		return frame

	def __next__(self):
		if self._index == len(self._frames):
			raise StopIteration

		frame = self._frames[self._index]
		self._index += 1

		return frame

	@staticmethod
	def prettyPrintFrameList(frames):
		"""Given a list of frames (represented as their
		integers), builds a string representing the combination
		of discrete frames and frame ranges.

		i.e. a list [1, 2, 3, 4, 5, 9, 10, 13, 15] would be formatted
		as: '1-5, 9-10, 13, 15'

		Args:
		    frames (list): The frame list to format

		Returns:
		    str: The formmated frame list
		"""
		parts = []
		currRangeStart = None
		last = None

		for f in frames:
			if not currRangeStart: # First frame of streak
				currRangeStart = f
				last = f

				continue

			if f != last + 1: # End streak
				# Finalize streak
				if currRangeStart == last: # no streak
					parts.append(str(last))
				elif last - currRangeStart == 1: # don't use range format for 1 length streaks
					parts.append(str(currRangeStart))
					parts.append(str(last))
				else:
					parts.append('{}-{}'.format(currRangeStart, last))

				currRangeStart = f # Reset streak and last
				last = f
			else:
				last = f

		if currRangeStart == last:
			parts.append(str(last))
		elif last - currRangeStart == 1:
			parts.append(str(currRangeStart))
			parts.append(str(last))
		else:
			parts.append('{}-{}'.format(currRangeStart, last))

		return ', '.join(parts)

	@staticmethod
	def parseFrameString(frameString):
		"""Given a string representing a sequence of discrete frames and
		ranges of frames, compiles the complete list of the frames.

		i.e. the string '1-3, 5, 9, 10-20:2' will produce [1, 2, 3, 5, 9,
		10, 12, 14, 16, 18, 20]

		Args:
		    frameString (str): The string representing the sequence of discrete
		    	and ranges of frames

		Returns:
		    list: The complete expanded list of the frames compiled from the frame string

		Raises:
		    ValueError: When one of the sequences contains a match, but does not properly match for
		    	the start of the range. Should never occur.
		"""
		blocks = frameString.split(',')
		blockRegex = re.compile(r'(?P<start>\-?\d+)(\-(?P<end>\-?\d+))?(:(?P<inc>\d+))?')
		frameList = []

		for block in blocks:
			block = block.strip()
			match = blockRegex.match(block)

			if match:
				start = match.group('start')
				end = match.group('end')
				end = end if end else start
				inc = match.group('inc')
				inc = inc if inc else 1

				if not start: # not even a single frame number present
					raise ValueError('Error in frame string. Invalid block: {} (expected at least 1 frame number)'.format(block))
					return None

				if end:
					assert int(end) >= int(start), 'End frame in range cannot be smaller than start frame (Block: {})'.format(block)

				for i in range(int(start), int(end) + 1, int(inc)):
					frameList.append(i)

		frameList = list(set(frameList))

		frameList.sort()

		return frameList

class Frame():
	_prefix = ''
	_padding = 0
	_number = 0
	_ext = ''

	def __init__(self, prefix, framePadding, ext):
		self._prefix = prefix
		self._padding, self._number = self._interpretFramePadding(framePadding)
		self._ext = ext

	def _interpretFramePadding(self, framePadding):
		"""Given a string that represents the frame padding portion
		of a file, interprets what the actual frame number is and how
		many digits of padding it is composed of

		Ex:

		'0000' --> (4, 0)
		'010'  --> (3, 10)
		'200'  --> (3, 200)

		Args:
			framePadding (str): The frame padding portion of the file name

		Returns:
			tuple: A tuple with the number of digits of padding (0020 is 4 digit padding),
				and the integer value of the frame that the string represents

		Raises:
			ValueError: In the case where we cannot determine the integer value of the
				given frame padding, which means that the string passed is not of the
				expected format of pure digits
		"""

		try:
			frameNum = int(framePadding)

			return (len(framePadding), frameNum)
		except ValueError:
			raise ValueError('Malformed frame padding string: {}'.format(framePadding))

	def getPrefix(self):
		return self._prefix

	def getExt(self):
		return self._ext

	def getPadding(self):
		return self._padding

	def getNumber(self):
		return self._number

	def __str__(self):
		return 'Frame {} from: {} ({})'.format(self._number, self._prefix, self._ext)
