from os import listdir
from os.path import basename, dirname, isdir, join as pathjoin, normpath, realpath, exists
from re import compile

from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent, eServiceReference, eServiceReferenceFS, eServiceCenter, gFont

from skin import fonts, parameters
from Components.Harddisk import harddiskmanager
from Components.MenuList import MenuList
from Tools.Directories import SCOPE_GUISKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap

EXTENSIONS = {
		"m4a": "music",
		"mp2": "music",
		"mp3": "music",
		"wav": "music",
		"ogg": "music",
		"wma": "music",
		"flac": "music",
		"jpg": "picture",
		"jpeg": "picture",
		"png": "picture",
		"bmp": "picture",
		"ts": "movie",
		"avi": "movie",
		"divx": "movie",
		"m4v": "movie",
		"mpg": "movie",
		"mpeg": "movie",
		"mkv": "movie",
		"mp4": "movie",
		"mov": "movie",
		"m2ts": "movie",
		"3gp": "movie",
		"3g2": "movie",
		"asf": "movie",
		"wmv": "movie",
		"webm": "movie",
	}


def FileEntryComponent(name, absolute=None, isDir=False):
	res = [(absolute, isDir)]
	x, y, w, h = parameters.get("FileListName", (35, 1, 470, 20))
	res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT, name))
	if isDir:
		png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_GUISKIN, "extensions/directory.png"))
	else:
		extension = name.split(".")
		extension = extension[-1].lower()
		if extension in EXTENSIONS:
			png = LoadPixmap(resolveFilename(SCOPE_GUISKIN, "extensions/%s.png" % EXTENSIONS[extension]))
		else:
			png = None
	if png is not None:
		x, y, w, h = parameters.get("FileListIcon", (10, 2, 20, 20))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, x, y, w, h, png))

	return res


class FileList(MenuList):
	def __init__(self, directory, showDirectories=True, showFiles=True, showMountpoints=True, matchingPattern=None, useServiceRef=False, inhibitDirs=False, inhibitMounts=False, isTop=False, enableWrapAround=False, additionalExtensions=None):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.additional_extensions = additionalExtensions
		self.mountpoints = []
		self.current_directory = None
		self.current_mountpoint = None
		self.useServiceRef = useServiceRef
		self.showDirectories = showDirectories
		self.showMountpoints = showMountpoints
		self.showFiles = showFiles
		self.isTop = isTop
		# example: matching .nfi and .ts files: "^.*\.(nfi|ts)"
		if matchingPattern:
			self.matchingPattern = compile(matchingPattern)
		else:
			self.matchingPattern = None
		self.inhibitDirs = inhibitDirs or []
		self.inhibitMounts = inhibitMounts or []

		self.refreshMountpoints()
		self.changeDir(directory)
		font = fonts.get("FileList", ("Regular", 18, 23))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.l.setItemHeight(font[2])
		self.serviceHandler = eServiceCenter.getInstance()

	def refreshMountpoints(self):
		self.mountpoints = [pathjoin(p.mountpoint, "") for p in harddiskmanager.getMountedPartitions()]
		self.mountpoints.sort(reverse=True)

	def getMountpoint(self, file):
		file = pathjoin(realpath(file), "")
		for m in self.mountpoints:
			if file.startswith(m):
				return m
		return False

	def getMountpointLink(self, file):
		if realpath(file) == file:
			return self.getMountpoint(file)
		else:
			if file[-1] == "/":
				file = file[:-1]
			mp = self.getMountpoint(file)
			last = file
			file = dirname(file)
			while last != "/" and mp == self.getMountpoint(file):
				last = file
				file = dirname(file)
			return pathjoin(last, "")

	def getSelection(self):
		if self.l.getCurrentSelection() is None:
			return None
		return self.l.getCurrentSelection()[0]

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		if not l or l[0][1] == True:
			return None
		else:
			return self.serviceHandler.info(l[0][0]).getEvent(l[0][0])

	def getFileList(self):
		return self.list

	def inParentDirs(self, dir, parents):
		dir = realpath(dir)
		for p in parents:
			if dir.startswith(p):
				return True
		return False

	def changeDir(self, directory, select=None):
		self.list = []

		# if we are just entering from the list of mount points:
		if self.current_directory is None:
			if directory and self.showMountpoints:
				self.current_mountpoint = self.getMountpointLink(directory)
			else:
				self.current_mountpoint = None
		self.current_directory = directory
		directories = []
		files = []

		if directory is None and self.showMountpoints: # present available mountpoints
			for p in harddiskmanager.getMountedPartitions():
				path = pathjoin(p.mountpoint, "")
				if path not in self.inhibitMounts and not self.inParentDirs(path, self.inhibitDirs):
					self.list.append(FileEntryComponent(name=p.description, absolute=path, isDir=True))
			files = []
			directories = []
		elif directory is None:
			files = []
			directories = []
		elif self.useServiceRef:
			# we should not use the 'eServiceReference(string)' constructor, because it doesn't allow ':' in the directoryname
			root = eServiceReference(eServiceReference.idFile, eServiceReference.noFlags, eServiceReferenceFS.directory)
			root.setPath(directory)
			if self.additional_extensions:
				root.setName(self.additional_extensions)
			serviceHandler = eServiceCenter.getInstance()
			_list = serviceHandler.list(root)

			while True:
				s = _list.getNext()
				if not s.valid():
					del _list
					break
				if s.flags & s.mustDescent:
					directories.append(s.getPath())
				else:
					files.append(s)
			directories.sort()
			files.sort()
		else:
			if isdir(directory):
				try:
					files = listdir(directory)
				except:
					files = []
				files.sort()
				tmpfiles = files[:]
				for x in tmpfiles:
					if isdir(directory + x):
						directories.append(directory + x + "/")
						files.remove(x)

		if self.showDirectories:
			if directory is not None and not self.isTop:
				if directory == self.current_mountpoint and self.showMountpoints:
					self.list.append(FileEntryComponent(name="<" + _("List of storage devices") + ">", absolute=None, isDir=True))
				elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
					self.list.append(FileEntryComponent(name="<" + _("Parent directory") + ">", absolute='/'.join(directory.split('/')[:-2]) + '/', isDir=True))

			for x in directories:
				if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
					name = x.split('/')[-2]
					self.list.append(FileEntryComponent(name=name, absolute=x, isDir=True))

		if self.showFiles:
			for x in files:
				if self.useServiceRef:
					path = x.getPath()
					name = path.split('/')[-1]
				else:
					path = directory + x
					name = x

				if (self.matchingPattern is None) or self.matchingPattern.search(path):
					self.list.append(FileEntryComponent(name=name, absolute=x, isDir=False))

		if self.showMountpoints and len(self.list) == 0:
			self.list.append(FileEntryComponent(name=_("nothing connected"), absolute=None, isDir=False))

		self.l.setList(self.list)

		if select is not None:
			i = 0
			self.moveToIndex(0)
			for x in self.list:
				p = x[0][0]

				if isinstance(p, eServiceReference):
					p = p.getPath()

				if p == select:
					self.moveToIndex(i)
				i += 1

	def getCurrentDirectory(self):
		return self.current_directory

	def canDescent(self):
		if self.getSelection() is None:
			return False
		return self.getSelection()[1]

	def descent(self):
		if self.getSelection() is None:
			return
		self.changeDir(self.getSelection()[0], select=self.current_directory)

	def getFilename(self):
		if self.getSelection() is None:
			return None
		x = self.getSelection()[0]
		if isinstance(x, eServiceReference):
			x = x.getPath()
		return x

	def getServiceRef(self):
		if self.getSelection() is None:
			return None
		x = self.getSelection()[0]
		if isinstance(x, eServiceReference):
			return x
		return None

	def execBegin(self):
		harddiskmanager.on_partition_list_change.append(self.partitionListChanged)

	def execEnd(self):
		harddiskmanager.on_partition_list_change.remove(self.partitionListChanged)

	def refresh(self):
		self.changeDir(self.current_directory, self.getFilename())

	def partitionListChanged(self, action, device):
		self.refreshMountpoints()
		if self.current_directory is None:
			self.refresh()


def MultiFileSelectEntryComponent(name, absolute=None, isDir=False, selected=False):
	res = [(absolute, isDir, selected, name)]
	x, y, w, h = parameters.get("FileListMultiName", (55, 0, 470, 25))
	res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT, name))
	if isDir:
		png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_GUISKIN, "extensions/directory.png"))
	else:
		extension = name.split('.')
		extension = extension[-1].lower()
		if extension in EXTENSIONS:
			png = LoadPixmap(resolveFilename(SCOPE_GUISKIN, "extensions/%s.png" % EXTENSIONS[extension]))
		else:
			png = None
	if png is not None:
		x, y, w, h = parameters.get("FileListMultiIcon", (30, 2, 20, 20))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, x, y, w, h, png))
	if not name.startswith('<'):
		if selected:
			icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_GUISKIN, "icons/lock_on.png"))
		else:
			icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_GUISKIN, "icons/lock_off.png"))
		x, y, w, h = parameters.get("FileListMultiLock", (2, 0, 25, 25))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, x, y, w, h, icon))
	return res


class MultiFileSelectList(FileList):
	def __init__(self, preselectedFiles, directory, showMountpoints=False, matchingPattern=None, showDirectories=True, showFiles=True, useServiceRef=False, inhibitDirs=False, inhibitMounts=False, isTop=False, enableWrapAround=False, additionalExtensions=None):
		if preselectedFiles is None:
			self.selectedFiles = []
		else:
			self.selectedFiles = preselectedFiles
		FileList.__init__(self, directory, showMountpoints=showMountpoints, matchingPattern=matchingPattern, showDirectories=showDirectories, showFiles=showFiles, useServiceRef=useServiceRef, inhibitDirs=inhibitDirs, inhibitMounts=inhibitMounts, isTop=isTop, enableWrapAround=enableWrapAround, additionalExtensions=additionalExtensions)
		self.changeDir(directory)
		font = fonts.get("FileListMulti", ("Regular", 20, 25))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.l.setItemHeight(font[2])
		self.onSelectionChanged = []

	def selectionChanged(self):
		for f in self.onSelectionChanged:
			f()

	def changeSelectionState(self):
		if len(self.list):
			idx = self.l.getCurrentSelectionIndex()
			newList = self.list[:]
			x = self.list[idx]
			if not x[0][3].startswith('<'):
				if x[0][1] is True:
					realPathname = x[0][0]
				else:
					realPathname = self.current_directory + x[0][0]
				if x[0][2]:
					SelectState = False
					try:
						self.selectedFiles.remove(realPathname)
					except:
						try:
							self.selectedFiles.remove(normpath(realPathname))
						except (IOError, OSError) as err:
							print("[FileList] Error %d: Can't remove '%s'!  (%s)" % (err.errno, realPathname, err.strerror))
				else:
					SelectState = True
					if (realPathname not in self.selectedFiles) and (normpath(realPathname) not in self.selectedFiles):
						self.selectedFiles.append(realPathname)
				newList[idx] = MultiFileSelectEntryComponent(name=x[0][3], absolute=x[0][0], isDir=x[0][1], selected=SelectState)
			self.list = newList
			self.l.setList(self.list)

	def getSelectedList(self):
		selectedFilesExist = []
		for x in self.selectedFiles:
			if exists(x):
				selectedFilesExist.append(x)
		return selectedFilesExist

	def changeDir(self, directory, select=None):
		self.list = []

		# if we are just entering from the list of mount points:
		if self.current_directory is None:
			if directory and self.showMountpoints:
				self.current_mountpoint = self.getMountpointLink(directory)
			else:
				self.current_mountpoint = None
		self.current_directory = directory
		directories = []
		files = []

		if directory is None and self.showMountpoints: # present available mountpoints
			for p in harddiskmanager.getMountedPartitions():
				path = pathjoin(p.mountpoint, "")
				if path not in self.inhibitMounts and not self.inParentDirs(path, self.inhibitDirs):
					self.list.append(MultiFileSelectEntryComponent(name=p.description, absolute=path, isDir=True))
			files = []
			directories = []
		elif directory is None:
			files = []
			directories = []
		elif self.useServiceRef:
			root = eServiceReference(eServiceReference.idFile, eServiceReference.noFlags, eServiceReferenceFS.directory)
			root.setPath(directory)
			if self.additional_extensions:
				root.setName(self.additional_extensions)
			serviceHandler = eServiceCenter.getInstance()
			_list = serviceHandler.list(root)

			while True:
				s = _list.getNext()
				if not s.valid():
					del _list
					break
				if s.flags & s.mustDescent:
					directories.append(s.getPath())
				else:
					files.append(s)
			directories.sort()
			files.sort()
		else:
			if isdir(directory):
				try:
					files = listdir(directory)
				except:
					files = []
				files.sort()
				tmpfiles = files[:]
				for x in tmpfiles:
					if isdir(directory + x):
						directories.append(directory + x + "/")
						files.remove(x)

		if self.showDirectories:
			if directory is not None and not self.isTop:
				if directory == self.current_mountpoint and self.showMountpoints:
					self.list.append(MultiFileSelectEntryComponent(name="<" + _("List of storage devices") + ">", absolute=None, isDir=True))
				elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
					self.list.append(MultiFileSelectEntryComponent(name="<" + _("Parent directory") + ">", absolute='/'.join(directory.split('/')[:-2]) + '/', isDir=True))

			for x in directories:
				if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
					name = x.split('/')[-2]
					alreadySelected = (x in self.selectedFiles) or (normpath(x) in self.selectedFiles)
					self.list.append(MultiFileSelectEntryComponent(name=name, absolute=x, isDir=True, selected=alreadySelected))

		if self.showFiles:
			for x in files:
				if self.useServiceRef:
					path = x.getPath()
					name = path.split('/')[-1]
				else:
					path = directory + x
					name = x
				if (self.matchingPattern is None) or self.matchingPattern.search(path):
					alreadySelected = False
					for entry in self.selectedFiles:
						#if os.path.basename(entry) == x:
						if entry == path:
							alreadySelected = True
					self.list.append(MultiFileSelectEntryComponent(name=name, absolute=x, isDir=False, selected=alreadySelected))

		self.l.setList(self.list)

		if select is not None:
			i = 0
			self.moveToIndex(0)
			for x in self.list:
				p = x[0][0]

				if isinstance(p, eServiceReference):
					p = p.getPath()

				if p == select:
					self.moveToIndex(i)
				i += 1
