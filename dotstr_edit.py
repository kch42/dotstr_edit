#!/usr/bin/env python
# -*- coding: utf-8 -*-

import strfile
import wx
import sys, os
import locale, gettext

from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

class TransDictListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
	"""ListCtrl for a translation dictionary"""
	def __init__(self, parent):
		wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL)
		ListCtrlAutoWidthMixin.__init__(self)
		self.InsertColumn(0, _("Identification"), width=250)
		self.InsertColumn(1, _("Text"))
		self.dict = {}
		self.update()
	
	def update(self, onlyone=None):
		"""
		Update the list.
		
		If onlyone is set, only the translation with the key = onlyone will be updated
		If not, evrything will be updated
		"""
		if onlyone is None:
			self.DeleteAllItems()
			self.SetItemCount(len(self.dict))
			self.RefreshItems(0,len(self.dict))
		else:
			key, val = onlyone
			self.dict[key] = val
			self.RefreshItem(self.dict.keys().index(key))
	
	def set_dict(self, d):
		"""Set the translation dictionary"""
		self.dict = d
		self.update()
	
	def get_seclection(self):
		"""
		Get the key of the selected translation.
		
		If no translation is selected, an empty string will be returned
		"""
		index = self.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		return "" if index == -1 else self.dict.keys()[index]
	
	def OnGetItemText(self, item, col):
		"""Basic implementation of the LC_VIRTUAL mechanism"""
		if col == 0:
			return self.dict.keys()[item]
		else:
			return self.dict.values()[item]

class new_entry_dialog(wx.Dialog):
	"""
	Dialog that prompts the user for a new translation key
	"""
	def __init__(self, parent):
		# Layout stuff
		wx.Dialog.__init__(self, parent, title=_("New entry"), size=(500,-1))
		
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(wx.StaticText(self, label=_("Name of your new entry:")), 0, wx.EXPAND | wx.ALL, 5)
		
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		self.part1 = wx.TextCtrl(self)
		self.part2 = wx.TextCtrl(self)
		hbox.Add(self.part1, 2, wx.EXPAND, 0)
		hbox.Add(wx.StaticText(self, label=":"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT, 5)
		hbox.Add(self.part2, 3, wx.EXPAND, 0)
		hbox.SetMinSize((500,-1))
		vbox.Add(hbox, 0, wx.EXPAND | wx.ALL, 5)
		vbox.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.EXPAND | wx.ALL, 5)
		
		self.SetSizer(vbox)
		vbox.Fit(self)
		
		self.Bind(wx.EVT_BUTTON, self.on_ok,     id=wx.OK)
		self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.CANCEL)
		self.Bind(wx.EVT_CLOSE,  self.on_cancel)
	
	def get_identifier(self):
		"""
		This will return the key/identifier.
		"""
		allowed_chars = map(chr, range(ord("A"), ord("Z")+1) + range(ord("a"), ord("z")+1))+["_","-"]
		part1 = "".join(filter(lambda c: c in allowed_chars, self.part1.GetValue()))
		part2 = "".join(filter(lambda c: c in allowed_chars, self.part2.GetValue()))
		
		return part1 + ":" + part2
	
	def on_ok(self, event):
		self.EndModal(wx.ID_OK)
	
	def on_cancel(self, event):
		self.EndModal(wx.ID_CANCEL)

class editor_frame(wx.Frame):
	"""
	The Frame of the editor.
	"""
	def __init__(self):
		filter_label = _("&Filter")
		self.dict = {}
		self.changed = False
		self.filename = ""
		
		# GUI stuff
		the_arts = wx.ArtProvider()
		wx.Frame.__init__(self, None, title=_(".str Editor"), size=(500,600))
		
		# menubar
		menubar = wx.MenuBar()
		
		m_file = wx.Menu()
		m_file.AppendItem(wx.MenuItem(m_file, wx.ID_NEW, _("&New")))
		m_file.AppendItem(wx.MenuItem(m_file, wx.ID_OPEN, _("&Open")))
		m_file.AppendItem(wx.MenuItem(m_file, wx.ID_SEPARATOR))
		m_file.AppendItem(wx.MenuItem(m_file, wx.ID_SAVE, _("&Save")))
		m_file.AppendItem(wx.MenuItem(m_file, wx.ID_SAVEAS, _("Save &As")))
		m_file.AppendItem(wx.MenuItem(m_file, wx.ID_SEPARATOR))
		m_file.AppendItem(wx.MenuItem(m_file, wx.ID_EXIT, _("&Exit")))
		
		m_help = wx.Menu()
		m_help.AppendItem(wx.MenuItem(m_help, wx.ID_ABOUT, _("&About")))
		
		menubar.Append(m_file, _("&File"))
		menubar.Append(m_help, _("&Help"))
		
		self.SetMenuBar(menubar)
		
		# toolbar
		toolbar = self.CreateToolBar()
		toolbar.AddLabelTool(wx.ID_NEW, _("New"), the_arts.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR))
		toolbar.AddLabelTool(wx.ID_OPEN, _("Open"), the_arts.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR))
		toolbar.AddLabelTool(wx.ID_SAVE, _("Save"), the_arts.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR))
		toolbar.Realize()
		
		# shortcuts
		jump_to_filter_id = wx.NewId()
		filter_shortcut_char = ord(filter_label[filter_label.find("&")+1].lower())
		shortcuts = wx.AcceleratorTable([
			(wx.ACCEL_CTRL, ord('s'), wx.ID_SAVE),
			(wx.ACCEL_CTRL, ord('o'), wx.ID_OPEN),
			(wx.ACCEL_CTRL, ord('n'), wx.ID_NEW),
			(wx.ACCEL_CTRL, ord('q'), wx.ID_EXIT),
			(wx.ACCEL_CTRL, filter_shortcut_char, jump_to_filter_id)
		])
		self.SetAcceleratorTable(shortcuts)
		
		# the "real" GUI
		self.mainpanel = wx.Panel(self, -1)
		vbox = wx.BoxSizer(wx.VERTICAL)
		
		filter_hbox = wx.BoxSizer(wx.HORIZONTAL)
		self.input_filter = wx.TextCtrl(self.mainpanel)
		filter_hbox.Add(wx.StaticText(self.mainpanel, label=filter_label), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
		filter_hbox.Add(self.input_filter, 1, wx.EXPAND, 0)
		vbox.Add(filter_hbox, 0, wx.EXPAND | wx.ALL, 5)
		
		trl_hbox = wx.BoxSizer(wx.HORIZONTAL)
		self.transl_list = TransDictListCtrl(self.mainpanel)
		
		trl_vbox = wx.BoxSizer(wx.VERTICAL)
		trl_add_btn = wx.BitmapButton(self.mainpanel, bitmap=the_arts.GetBitmap(wx.ART_ADD_BOOKMARK, wx.ART_BUTTON))
		trl_del_btn = wx.BitmapButton(self.mainpanel, bitmap=the_arts.GetBitmap(wx.ART_DEL_BOOKMARK, wx.ART_BUTTON))
		trl_vbox.Add(trl_add_btn, 0, wx.EXPAND | wx.BOTTOM, 5)
		trl_vbox.Add(trl_del_btn, 0, wx.EXPAND, 0)
		
		trl_hbox.Add(self.transl_list, 1, wx.EXPAND, wx.RIGHT, 5)
		trl_hbox.Add(trl_vbox, 0, wx.EXPAND, 0)
		vbox.Add(trl_hbox, 3, wx.EXPAND | wx.ALL, 5)
		
		vbox.Add(wx.StaticLine(self.mainpanel, style=wx.LI_HORIZONTAL),.0, wx.EXPAND | wx.ALL, 5)
		
		vbox.Add(wx.StaticText(self.mainpanel, label=_("Text:")), 0, wx.EXPAND | wx.ALL, 5)
		self.trans_text_ctrl = wx.TextCtrl(self.mainpanel, style=wx.TE_MULTILINE)
		vbox.Add(self.trans_text_ctrl, 2, wx.EXPAND | wx.ALL, 5)
		
		self.mainpanel.SetSizer(vbox)
		
		cool_icon = wx.Icon(os.path.join(scriptdir, "wm-icon.ico"), wx.BITMAP_TYPE_ICO)
		self.SetIcon(cool_icon)
		
		# Binding events
		self.Bind(wx.EVT_MENU,   self.on_new,        id=wx.ID_NEW)
		self.Bind(wx.EVT_MENU,   self.on_open,       id=wx.ID_OPEN)
		self.Bind(wx.EVT_MENU,   self.on_save,       id=wx.ID_SAVE)
		self.Bind(wx.EVT_MENU,   self.on_saveas,     id=wx.ID_SAVEAS)
		self.Bind(wx.EVT_MENU,   self.on_close,      id=wx.ID_EXIT)
		self.Bind(wx.EVT_MENU,   self.on_about,      id=wx.ID_ABOUT)
		self.Bind(wx.EVT_TEXT,   self.on_filter,     id=self.input_filter.GetId())
		self.Bind(wx.EVT_TEXT,   self.on_textedit,   id=self.trans_text_ctrl.GetId())
		self.Bind(wx.EVT_BUTTON, self.on_add,        id=trl_add_btn.GetId())
		self.Bind(wx.EVT_BUTTON, self.on_del,        id=trl_del_btn.GetId())
		self.Bind(wx.EVT_MENU,   self.on_jmp_filter, id=jump_to_filter_id)
		self.Bind(wx.EVT_CLOSE,  self.on_close)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED,   self.on_listsel,   id=self.transl_list.GetId())
		self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_listunsel, id=self.transl_list.GetId())
		
	def really_discard(self):
		"""
		If the content was modified, the user will be asked if he really wants to discard the changes
		
		This will return True if the calling function can continue normal work.
		"""
		if self.changed:
			dialog = wx.MessageDialog(None,
			                          message=_("You did not save your changes. Continue?"),
			                          caption=_("Unsaved changes"),
			                          style=wx.ICON_QUESTION | wx.YES_NO)
			user_ret = dialog.ShowModal()
			dialog.Destroy()
			return user_ret == wx.ID_YES
		return True
	
	def populate_list(self, autoselect=None):
		"""
		Populating the translation list with the filtered self.dict
		
		If autoselect is not None, the given translation will be selected and focussed.
		"""
		filter_str = self.input_filter.GetValue().lower()
		f_dict = {}
		for key in self.dict.iterkeys():
			if filter_str != '':
				if (filter_str not in key.lower()) and (filter_str not in self.dict[key].lower()):
					continue
			f_dict[key] = self.dict[key]
		self.transl_list.set_dict(f_dict)
		self.trans_text_ctrl.SetValue("")
		if autoselect is not None:
			self.transl_list.Select(f_dict.keys().index(autoselect))
			self.transl_list.Focus(f_dict.keys().index(autoselect))
	
	def form_init(self):
		"""
		Initializes / clears all formulars
		"""
		self.populate_list()
		self.input_filter.SetValue("")
	
	def on_close(self, event):
		if self.really_discard():
			self.Destroy()
	
	def on_new(self, event):
		if self.really_discard():
			self.dict = {}
			self.changed = False
			self.filename = ""
			self.form_init()
	
	def load_file(self, new_fn):
		if new_fn != "":
			try:
				fp = open(new_fn, "rb")
				temp_dict = strfile.dict_parse(fp.read())
				self.dict = temp_dict
				fp.close()
				self.filename = new_fn
				self.changed = False
				self.form_init()
			except:
				del dialog
				dialog = wx.MessageDialog(None,
					                  message=_("Could not open file.\nUsually that means that the file is invalid or you do not have enough privileges."),
					                  caption=_("Could not open file"),
					                  style=wx.ICON_ERROR | wx.OK)
				dialog.ShowModal()
				dialog.Destroy()
	
	def on_open(self, event):
		if self.really_discard():
			new_fn = ""
			dialog = wx.FileDialog(None, _("Choose a file"), wildcard=fd_wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
			if dialog.ShowModal() == wx.ID_OK:
				new_fn = dialog.GetPath()
			dialog.Destroy()
			
			self.load_file(new_fn)
	
	def save_file(self, force_path=False):
		saveto = ""
		if force_path or self.filename=='':
			if self.filename == "":
				dialog = wx.FileDialog(None,
				                       message=_("Save to"),
				                       wildcard=fd_wildcard,
				                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
			else:
				def_dir, def_file = os.path.split(self.filename)
				dialog = wx.FileDialog(None,
				                       message=_("Save to"),
				                       wildcard=fd_wildcard,
				                       defaultDir=def_dir,
				                       defaultFile=def_file,
				                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
			if dialog.ShowModal() == wx.ID_OK:
				saveto = dialog.GetPath()
			else:
				saveto = ""
			dialog.Destroy()
		else:
			saveto = self.filename
		if saveto != "":
			try:
				fp = open(saveto, "w")
				strfile.dict_gen(self.dict, fp)
				fp.close()
			except:
				err_dialog = wx.MessageDialog(
					None,
					message=_("Can not write to file \"%s\".\nUsually that means that you do not have enough privileges or you ran out of disc memory.") % saveto,
					caption=_("Can not save file."),
					style=wx.ICON_ERROR | wx.OK)
				err_dialog.ShowModal()
				err_dialog.Close()
			self.changed = False
	
	def on_save(self, event):
		self.save_file()
	
	def on_saveas(self, event):
		self.save_file(True)
	
	def on_about(self, event):
		description = _(".str Editor is a tool for editing the .str files of EA's BFME2")
		licence = u"""Copyright (c) 2010-2011 \"Die Völker Mittelerdes\" Modding Crew

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""
		info = wx.AboutDialogInfo()
		info.SetName(_('.str Editor'))
		info.SetVersion('0.1')
		info.SetDescription(description)
		info.SetCopyright(u'(C) 2010-2011 \"Die Völker Mittelerdes\" Modding Crew')
		info.SetLicence(licence)
		info.AddDeveloper('Kevin Chabowski')
		info.SetIcon(wx.Icon(os.path.join(scriptdir, 'icon.png'), wx.BITMAP_TYPE_PNG))
		
		wx.AboutBox(info)
	
	def on_listsel(self, event):
		self.trans_text_ctrl.SetValue(strfile.unescape(self.dict[self.transl_list.get_seclection()]))
	
	def on_listunsel(self, event):
		self.trans_text_ctrl.SetValue("")
	
	def on_filter(self, event):
		if event.GetString() != "":
			self.populate_list()
		if len(self.transl_list.dict) == 0 and event.GetString() != "":
			self.input_filter.SetBackgroundColour(wx.Colour(255,100,100))
		else:
			self.input_filter.SetBackgroundColour(wx.NullColour)
		self.input_filter.Refresh()
	
	def on_textedit(self, event):
		key = self.transl_list.get_seclection()
		if key != "":
			newval = strfile.escape(self.trans_text_ctrl.GetValue())
			self.dict[key] = newval
			self.transl_list.update((key, newval))
			self.changed = True
	
	def on_add(self, event):
		addthis = ":"
		while addthis == ":":
			dialog = new_entry_dialog(None)
			if dialog.ShowModal() != wx.ID_OK:
				dialog.Destroy()
				return
			addthis = dialog.get_identifier()
			dialog.Destroy()
			if addthis in self.dict.keys():
				addthis = ':'
				del dialog
				dialog = wx.MessageDialog(
					None,
					message=_("This name is already in use. Choose another one."),
					caption=_("Invalid name"),
					style=wx.ICON_WARNING | wx.OK
				)
				dialog.ShowModal()
				dialog.Destroy()
			del dialog
		self.changed = True
		self.dict[addthis] = ""
		self.input_filter.SetValue("")
		self.populate_list(addthis)
		
	
	def on_del(self, event):
		delthis =  self.transl_list.get_seclection()
		if delthis != "":
			del self.dict[delthis]
			self.changed = True
			self.populate_list()
	
	def on_jmp_filter(self, event):
		self.input_filter.SetFocus()

class dotstr_edit_app(wx.App):
	def OnInit(self):
		app_frame = editor_frame()
		app_frame.Show()
		if len(sys.argv) > 1:
			app_frame.load_file(sys.argv[1])
		self.SetTopWindow(app_frame)
		return True

if __name__ == '__main__':
	# get directory of script / executable
	scriptdir = os.path.dirname(unicode(
		sys.executable if hasattr(sys,"frozen") and sys.frozen in ("windows_exe", "console_exe") else __file__,
		sys.getfilesystemencoding()))
	
	# init localisation
	if os.name == 'nt': 
		# windows hack for locale setting 
		lang = os.getenv('LANG') 
		if lang is None: 
			default_lang, default_enc = locale.getdefaultlocale() 
			if default_lang: 
				lang = default_lang 
		if lang: 
			os.environ['LANG'] = lang
	locale.setlocale(locale.LC_ALL, '')
	translator = gettext.translation('dotstr_edit', os.path.join(scriptdir, 'locale'), fallback=True)
	translator.install(True)
	
	fd_wildcard = _("str File")+"|*.str|*.*|*.*"
	
	# Start application
	app = dotstr_edit_app()
	app.MainLoop()

