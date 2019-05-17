import struct
from io import BytesIO

#constants
PF_CLOSED=-1
PF_READ=0
PF_CREATE=1

class BadPackFile(Exception):
	def __init__(self, reason):
		self.reason=reason

	def __str__(self):
		return self.reason

#a container for attributes given to every file in the pack
#only used when opened for reading
class file:
	def __init__(self, name, content_length, start_offset=0):
		self.name=name
		self.start_offset=start_offset
		self.content_length=content_length

class pack_file:

	header=b"SFPv"
	version=1

	def __init__(self):
		self.fileobj=None
		self.files=[]
		self.mode=PF_CLOSED

	def create(self, filename):
		"""
		Create a pack file and open it in write mode.
		If the file already exists, it will be overwritten.
		"""
		if self.active:
			self.close()
		self.fileobj=open(filename, "w+b")
		self.mode=PF_CREATE
		self.fileobj.write(self.header)
		#write dummy info for now, we'll touch it later
		self.fileobj.write(struct.pack("<3i", self.version, 0, 0))

	def add_file(self, file_on_disk, internal_name):
		"""
		Adds a file to the currently open pack file.
		The pack file must be opened in write mode with the create method for this operation to be successful.
		Internal_name is simply used to refer to the file inside the pack. This can contain any characters and can be laid out in any format.
		"""
		if type(internal_name)==str:
			internal_name=internal_name.encode()
		if self.mode!=PF_CREATE:
			return False
		f=open(file_on_disk, "rb")
		f.seek(0, 2)
		size=f.tell()
		f.seek(0)
		#put pointer to the end if we're not already there
		self.fileobj.seek(0, 2)
		self.fileobj.write(self.header)
		self.fileobj.write(struct.pack("<3i", len(internal_name), 0, size))
		self.fileobj.write(internal_name)
		#If size is bigger than 50MB, read in a buffer stream.
		if size>(1024*1024)*50:
			#read in 20MB increments
			r=read_buffered(f, (1024*1024)*20)
			for chunk in r:
				self.fileobj.write(chunk)
		else:
			self.fileobj.write(f.read())
		#update number of files in the header
		files=self._get_files_added()+1
		self._set_files_added(files)
		return True

	def open(self, filename):
		"""
		Open an existing pack file for reading.
		The pack file will be opened in read mode. Please note that a pack file cannot be added to once closed unless it is recreated from scratch.
		Returns True on success, False and raises an exception on failure.
		"""
		if self.active:
			self.close()
		self.fileobj=open(filename, "rb")
		self.mode=PF_READ
		header=self.fileobj.read(4)
		if header!=self.header:
			raise BadPackFile("Invalid header")
			return False
		version, num_files, something=struct.unpack("<3i", self.fileobj.read(12))
		for i in range(num_files):
			header=self.fileobj.read(4)
			if header!=self.header:
				raise BadPackFile("Abrupt ending to data")
				return False
			name_length, something, content_length=struct.unpack("<3i", self.fileobj.read(12))
			name=self.fileobj.read(name_length)
			self.files.append(file(name, content_length, start_offset=self.fileobj.tell()))
			self.fileobj.seek(self.fileobj.tell()+content_length)

	def list_files(self):
		"""
		List all files in the pack.
		Although internal names can take the form of directory formatting, the pack format cannot differentiate between directories and files. Therefore if you have an internal name of music/level1.ogg, that is what will appear in the relevant entry in the list.
		Files will be listed in the order they were added to the pack file.
		This method can only be used on a pack opened for reading.
		"""
		if self.mode!=PF_READ:
			return False
		files=[]
		for i in self.files:
			files.append(i.name)
		return files

	def get_file(self, internal_name):
		"""
		Passes data from a file inside a pack to a standard file like object. This allows a file to be read in chunks from inside the pack without the need to extract it to disk. The file object does not contain a copy of the data, it reads from the original pack but only the relevant section of the file, so that you need not worry about accessing other data in the pack by accident.
		This method can only be used on a pack opened for reading.
		"""
		if type(internal_name)==str:
			internal_name=internal_name.encode()
		if self.mode!=PF_READ:
			return False
		#Can we find the given internal_name in our pack?
		found=self._get_fileobj(internal_name)
		if not found:
			return False
		self.fileobj.seek(found.start_offset)
		#We're unfortunately unable to implement any sort of buffer stream here to handle large file sizes.
		#This is because io.BytesIO stores large files in memory, thus triggering a MemoryError
		#todo: Possibly subclass io.BytesIO and implement a custom read method that gets data from self.fileobj, making sure not to go out of bounds
		return BytesIO(self.fileobj.read(found.content_length))

	def _get_fileobj(self, filename):
		"""
		Returns the internal file instance for the given filename.
		Mostly used internally
		"""
		if type(filename)==str:
			filename=filename.encode()
		found=None
		for file in self.files:
			if file.name==filename:
				found=file
				break
		return found

	def file_exists(self, filename):
		"""
		checks whether a given file exists in the pack.
		Only works in instances opened for reading.
		"""
		if self.mode!=PF_READ:
			return False
		return self._get_fileobj(filename) is not None


	def extract_file(self, internal_name, file_on_disk):
		"""
		Extract a file from an open pack file back onto disk.
		Only works on a pack file opened for reading.
		"""
		if self.mode!=PF_READ:
			return False
		if type(internal_name)==str:
			internal_name=internal_name.encode()
		found=self._get_fileobj(internal_name)
		if not found:
			return False
		f=open(file_on_disk, "wb")
		self.fileobj.seek(found.start_offset)
		#If size is bigger than 50MB, read in a buffer stream.
		if found.content_length>(1024*1024)*50:
			#read in 20MB increments
			r=read_buffered(self.fileobj, (1024*1024)*20, self.fileobj.tell()+found.content_length)
			for i in r:
				f.write(i)
		else:
			f.write(self.fileobj.read())
		f.close()
		return True

	@property
	def active(self):
		"""Set to True when a pack file is associated with this instance, False otherwise."""
		return self.fileobj is not None

	@property
	def file_count(self):
		"""Returns the number of files stored in the currently open pack, or -1 on error."""
		if self.mode!=PF_READ:
			return -1
		return len(self.files)

	def _get_files_added(self):
		"""
		Return the number of files added to the pack so far.
		Only used when updating the header in packs opened for writing.
		"""
		orig_pos=self.fileobj.tell()
		self.fileobj.seek(8)
		data=struct.unpack("<i", self.fileobj.read(4))[0]
		self.fileobj.seek(orig_pos)
		return data

	def _set_files_added(self, num):
		"""
		Modify the number of files added to the pack so far.
		Only used when updating the header in packs opened for writing.
		"""
		orig_pos=self.fileobj.tell()
		self.fileobj.seek(8)
		num=struct.pack("<i", num)
		self.fileobj.write(num)
		self.fileobj.seek(orig_pos)

	def close(self):
		"""
		Close any pack file associated with an instance of this class.
		Content is written if opened for writing.
		"""
		if self.active:
			self.fileobj.close()
			self.__init__()

	def __del__(self):
		self.close()

def read_buffered(f, buffsize, until=0):
	"""
	Generator that reads a file in chunks.
	This is used in an attempt at memory efficiency, in addition to combatting the classic MemoryError when attempting to read an entire file at once.
	"""
	begin_offset=f.tell()
	bytes_read=0
	if until>0 and buffsize>until:
		buffsize=until
	while True:
		data=f.read(buffsize)
		bytes_read=f.tell()-begin_offset
		if not data: #we've reached the end of the file
			break
		if bytes_read==until:
			if data:
				yield data
			break
		elif until>0 and bytes_read+buffsize>until:
			buffsize=until-bytes_read
		yield data
