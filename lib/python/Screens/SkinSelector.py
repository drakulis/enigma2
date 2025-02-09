# -*- coding: utf-8 -*-
from __future__ import print_function
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.MessageBox import MessageBox
from Components.ActionMap import NumberActionMap
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_GUISKIN
from enigma import eEnv, ePicLoad
import os


class SkinSelectorBase:
	def __init__(self, session, args=None):
		self.setTitle(_("Skin Selector"))
		self.skinlist = []
		self.previewPath = ""
		if self.SKINXML and os.path.exists(os.path.join(self.root, self.SKINXML)):
			self.skinlist.append(self.DEFAULTSKIN)
		if self.PICONSKINXML and os.path.exists(os.path.join(self.root, self.PICONSKINXML)):
			self.skinlist.append(self.PICONDEFAULTSKIN)
		if self.ALTERNATESKINXML and os.path.exists(os.path.join(self.root, self.ALTERNATESKINXML)):
			self.skinlist.append(self.ALTERNATESKIN)
		if self.USERSKINXML and os.path.exists(os.path.join(self.root, self.USERSKINXML)):
			self.skinlist.append(self.USERSKIN)
		for root, dirs, files in os.walk(self.root, followlinks=True):
			for subdir in dirs:
				if subdir == "skin_default":
					continue
				dir = os.path.join(root, subdir)
				if os.path.exists(os.path.join(dir, self.SKINXML)):
					self.skinlist.append(subdir)
			dirs = []

		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["introduction"] = StaticText(_("Press OK to activate the selected skin."))
		self["SkinList"] = MenuList(self.skinlist)
		self["Preview"] = Pixmap()
		self.skinlist.sort()

		self["actions"] = NumberActionMap(["SetupActions", "DirectionActions", "TimerEditActions", "ColorActions"],
		{
			"ok": self.ok,
			"cancel": self.close,
			"red": self.close,
			"green": self.ok,
			"up": self.up,
			"down": self.down,
			"left": self.left,
			"right": self.right,
			"log": self.info,
		}, -1)

		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.showPic)

		self.onLayoutFinish.append(self.layoutFinished)

	def showPic(self, picInfo=""):
		ptr = self.picload.getData()
		if ptr is not None:
			self["Preview"].instance.setPixmap(ptr.__deref__())
			self["Preview"].show()

	def layoutFinished(self):
		self.picload.setPara((self["Preview"].instance.size().width(), self["Preview"].instance.size().height(), 1, 1, False, 1, "#00000000"))
		tmp = self.config.value.find("/" + self.SKINXML)
		if tmp != -1:
			tmp = self.config.value[:tmp]
			idx = 0
			for skin in self.skinlist:
				if skin == tmp:
					break
				idx += 1
			if idx < len(self.skinlist):
				self["SkinList"].moveToIndex(idx)
		self.loadPreview()

	def ok(self):
		if self["SkinList"].getCurrent() == self.DEFAULTSKIN:
			self.skinfile = ""
			self.skinfile = os.path.join(self.skinfile, self.SKINXML)
		elif self["SkinList"].getCurrent() == self.PICONDEFAULTSKIN:
			self.skinfile = ""
			self.skinfile = os.path.join(self.skinfile, self.PICONSKINXML)
		elif self["SkinList"].getCurrent() == self.ALTERNATESKIN:
			self.skinfile = ""
			self.skinfile = os.path.join(self.skinfile, self.ALTERNATESKINXML)
		elif self["SkinList"].getCurrent() == self.USERSKIN:
			self.skinfile = ""
			self.skinfile = os.path.join(self.skinfile, self.USERSKINXML)
		else:
			self.skinfile = self["SkinList"].getCurrent()
			self.skinfile = os.path.join(self.skinfile, self.SKINXML)

		print("Skinselector: Selected Skin: " + self.root + self.skinfile)
		restartbox = self.session.openWithCallback(self.restartGUI, MessageBox, _("GUI needs a restart to apply a new skin\nDo you want to restart the GUI now?"), MessageBox.TYPE_YESNO)
		restartbox.setTitle(_("Restart GUI now?"))

	def up(self):
		self["SkinList"].up()
		self.loadPreview()

	def down(self):
		self["SkinList"].down()
		self.loadPreview()

	def left(self):
		self["SkinList"].pageUp()
		self.loadPreview()

	def right(self):
		self["SkinList"].pageDown()
		self.loadPreview()

	def info(self):
		aboutbox = self.session.open(MessageBox, _("Enigma2 skin selector"), MessageBox.TYPE_INFO)
		aboutbox.setTitle(_("About..."))

	def loadPreview(self):
		if self["SkinList"].getCurrent() == self.DEFAULTSKIN:
			pngpath = "."
			pngpath = os.path.join(os.path.join(self.root, pngpath), "prev.png")
		elif self["SkinList"].getCurrent() == self.PICONDEFAULTSKIN:
			pngpath = "."
			pngpath = os.path.join(os.path.join(self.root, pngpath), "piconprev.png")
		elif self["SkinList"].getCurrent() == self.ALTERNATESKIN:
			pngpath = "."
			pngpath = os.path.join(os.path.join(self.root, pngpath), "alternate.png")
		elif self["SkinList"].getCurrent() == self.USERSKIN:
			pngpath = "."
			pngpath = os.path.join(os.path.join(self.root, pngpath), "userskin.png")
		else:
			pngpath = self["SkinList"].getCurrent()
			try:
				pngpath = os.path.join(os.path.join(self.root, pngpath), "prev.png")
			except:
				pass

		if not os.path.exists(pngpath):
			pngpath = resolveFilename(SCOPE_GUISKIN, "noprev.png")

		if self.previewPath != pngpath:
			self.previewPath = pngpath

		self.picload.startDecode(self.previewPath)

	def restartGUI(self, answer):
		if answer is True:
			if isinstance(self, LcdSkinSelector):
				config.skin.display_skin.value = self.skinfile
				config.skin.display_skin.save()
			else:
				try:
					if config.skin.primary_skin.value == "MetrixHD/skin.MySkin.xml":
						from Plugins.Extensions.MyMetrixLite.ActivateSkinSettings import ActivateSkinSettings
						ActivateSkinSettings().RefreshIcons(True) #restore default icons
				except:
					pass
				config.skin.primary_skin.value = self.skinfile
				config.skin.primary_skin.save()
			self.session.open(TryQuitMainloop, 3)


class SkinSelector(Screen, SkinSelectorBase):
	SKINXML = "skin.xml"
	DEFAULTSKIN = _("< Default >")
	PICONSKINXML = None
	PICONDEFAULTSKIN = None
	ALTERNATESKINXML = None
	ALTERNATESKIN = None
	USERSKINXML = None
	USERSKIN = None

	skinlist = []
	root = os.path.join(eEnv.resolve("${datadir}"), "enigma2")

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		SkinSelectorBase.__init__(self, args)
		Screen.setTitle(self, _("Skin setup"))
		self.skinName = "SkinSelector"
		self.config = config.skin.primary_skin


class LcdSkinSelector(Screen, SkinSelectorBase):
	SKINXML = "skin_display.xml"
	DEFAULTSKIN = _("< Default >")
	PICONSKINXML = "skin_display_picon.xml"
	PICONDEFAULTSKIN = _("< Default with Picon >")
	ALTERNATESKINXML = "skin_display_alternate.xml"
	ALTERNATESKIN = _("< Alternate Skin >")
	USERSKINXML = "skin_display_usr.xml"
	USERSKIN = _("< User Skin >")

	skinlist = []
	root = os.path.join(eEnv.resolve("${datadir}"), "enigma2/display/")

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		SkinSelectorBase.__init__(self, args)
		Screen.setTitle(self, _("LCD Skin Setup"))
		self.skinName = "SkinSelector"
		self.config = config.skin.display_skin
