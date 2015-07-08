#!/usr/bin/env python

from gi.repository import Gtk, Gdk, GtkSource, GObject

class Handler:
    def onDeleteWindow(self, *args):
        Gtk.main_quit(*args)

    def onInfo(self, *args):
        dialog = app.builder.get_object("window2")
        dialog.set_title("info")
        dialog.show_all()

    def onInfoOk(sel, *args):
        print("hide")
        app.builder.get_object("window2").hide()

    def onFullscreen(self, *args):
        app.builder.get_object("window1").fullscreen()

    def onWindow(self, *args):
        app.builder.get_object("window1").unfullscreen()

    # file handling

    def onNew(self, *args):
        buffer = GtkSource.Buffer()
        buffer.set_modified(False)
        app.builder.get_object("gtksourceview1").set_buffer(buffer)

    def onOpen(self, *args):
        dialog = Gtk.FileChooserDialog("open file", app.builder.get_object("window1"),
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            with open (dialog.get_filename(), "r") as loadedfile:
                buffer = GtkSource.Buffer()
                buffer.set_text(loadedfile.read())
                buffer.set_modified(False)
                app.filename = dialog.get_filename()
                app.builder.get_object("gtksourceview1").set_buffer(buffer)
                app.builder.get_object("window1").set_title(dialog.get_filename())
        dialog.destroy()

    def onSaveAs(self, *args):
        dialog = Gtk.FileChooserDialog("save file as", app.builder.get_object("window1"),
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.save(dialog.get_filename())
        dialog.destroy()

    def onSave(self, *args):
        if app.filename == "":
            self.onSaveAs(*args)
            return
        self.save(app.filename)

    def save(self, filename):
        with open (filename, "w") as loadedfile:
            buffer = app.builder.get_object("gtksourceview1").get_buffer()
            loadedfile.write(buffer.get_text(*buffer.get_bounds(), include_hidden_chars=True))
            app.filename = filename
            buffer.set_modified(False)
            window = app.builder.get_object("window1").set_title(filename)

class Pyide:

    filename = ""

    def __init__(self, *args):
        self.builder = Gtk.Builder()
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        GObject.type_register(GtkSource.View)
        self.builder.add_from_file("pyide.glade")
        self.builder.get_object("gtksourceview1").set_buffer(GtkSource.Buffer())
        self.builder.connect_signals(Handler())

    def run(self):
        window = self.builder.get_object("window1")
        window.show_all()
        Gtk.main()

if __name__ == "__main__":
    app = Pyide()
    app.run()
