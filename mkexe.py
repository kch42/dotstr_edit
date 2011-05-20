from distutils.core import setup
import py2exe

languages = ["de"]

setup(
	name="dotstr_edit",
	version="0.1",
	description="A tool for editing the .str files of EA's BFME2",
	author="\"Die Voelker Mittelerdes\" Modding Crew",
	windows=[
		{
			"script": "dotstr_edit.py",
			"icon_resources": [(1, "icon.ico")]
		}
	],
	data_files=[("", ["icon.ico", "icon.png", "wm-icon.ico", "LICENSE", "README.markdown"])] + [(p, [p + "/dotstr_edit.mo"]) for p in ["locale/%s/LC_MESSAGES" % l for l in languages]],
	options={
		"py2exe": {
			"optimize": 2,
			"excludes": ["pywin", "pywin.debugger", "pywin.debugger.dbgcon",
				"pywin.dialogs", "pywin.dialogs.list",
				"Tkconstants","Tkinter","tcl", "_ssl", "doctest", "pdb", "unittest", "difflib", "inspect", "wave", "xml", "email", "urllib", "urllib2"
			  ],
			"includes": ["zlib"], # So the resulting program is able tu unpack the library, even after recompressing.
			"dll_excludes": ["MSVCP90.dll"],
			"bundle_files": 2
		}
	}
)
