#!/usr/bin/env python

from gi.repository import Gtk, Gdk, GtkSource, GObject, Vte, GLib
from gi.repository.GdkPixbuf import Pixbuf
import os, stat, time


class Handler:

    def onModified(self, label, buffer):
        if buffer.get_modified():
            label.set_markup("<span foreground='#ff8000'>%s</span>" % label.get_text())

    def onDeleteWindow(self, *args):
        Gtk.main_quit(*args)

    def onInfo(self, *args):
        dialog = app.builder.get_object("window2")
        dialog.set_title("info")
        dialog.show_all()

    def onInfoOk(sel, *args):
        app.builder.get_object("window2").hide()

    def onFullscreen(self, *args):
        app.builder.get_object("window1").fullscreen()

    def onWindow(self, *args):
        app.builder.get_object("window1").unfullscreen()

    def onOpen(self, *args):
        dialog = Gtk.FileChooserDialog("open file", app.builder.get_object("window1"),
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            openfile(dialog.get_filename())
        dialog.destroy()

    def create_tab(path, buffer):
        hbox = Gtk.HBox(False, 0)
        label = Gtk.Label(path)
        hbox.pack_start(label, True, True, 0)
        close_image = Gtk.IconTheme.get_default().load_icon("exit", 16, 0)
        imgw = Gtk.Image()
        imgw.set_from_pixbuf(close_image)
        btn = Gtk.Button()
        btn.set_focus_on_click(False)
        btn.add(imgw)
        hbox.pack_start(btn, False, False, 0)
        hbox.show_all()

        sview = GtkSource.View()
        sview.set_buffer(buffer)
        swindow = Gtk.ScrolledWindow()
        swindow.add(sview)
        notebook = app.builder.get_object("notebook1")
        pos = notebook.append_page(swindow, hbox)
        notebook.show_all()
        btn.connect("clicked", Handler.onCloseTab, path, buffer, swindow)
        buffer.connect("modified-changed", Handler.onModified, label, buffer)

        return swindow

    def openfile(path):
        for of in app.openfiles:
            if path in of[0]:
                return
        with open (path, "r") as loadedfile:
            buffer = GtkSource.Buffer()
            buffer.set_text(loadedfile.read())
            buffer.set_modified(False)
            # syntax highlighting
            lman = GtkSource.LanguageManager()
            lan = lman.guess_language(path)
            if lan:
                buffer.set_highlight_syntax(True)
                buffer.set_language(lan)
            else:
                buffer.set_highlight_syntax(False)

            swindow = Handler.create_tab(path, buffer)
            app.openfiles.append([path, buffer, swindow])

    def onCloseTab(self, path, buffer, swindow):
        if buffer.get_modified():
            Handler.onSave(Handler(), path, buffer)

        pos = app.builder.get_object("notebook1").page_num(swindow)
        app.builder.get_object("notebook1").remove_page(pos)
        app.openfiles.remove([path, buffer, swindow])

    def onRunApp(self, *args):

        f = "/tmp/%i.py" % int(time.time())
        with open (f, "w") as loadedfile:
            buffer = app.builder.get_object("notebook1").get_current_page().get_child().get_child().get_buffer()
            loadedfile.write(buffer.get_text(*buffer.get_bounds(), include_hidden_chars=True))

        termwin = Gtk.Window()
        termwin.set_default_size(800, 600)

        def closeTerm(win, evt):
            win.destroy()
            os.remove(f)

        termwin.connect("delete-event", closeTerm)

        terminal = Vte.Terminal()
        terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            os.environ['HOME'],
            ["/bin/bash"],
            [],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None,
            )
        termwin.add(terminal)
        termwin.show_all()
        cmd = "python " + f + "\n"
        terminal.feed_child(cmd, len(cmd))



class FsTree:

    def populateFileSystemTreeStore(treeStore, path, parent=None):
        itemCounter = 0
        # iterate over the items in the path
        for item in os.listdir(path):
            # Get the absolute path of the item
            itemFullname = os.path.join(path, item)
            # Extract metadata from the item
            try:
                itemMetaData = os.stat(itemFullname)
            except:
                pass
            # Determine if the item is a folder
            itemIsFolder = stat.S_ISDIR(itemMetaData.st_mode)
            # Generate an icon from the default icon theme
            itemIcon = Gtk.IconTheme.get_default().load_icon("folder" if itemIsFolder else "empty", 22, 0)
            # Append the item to the TreeStore
            currentIter = treeStore.append(parent, [item, itemIcon, itemFullname])
            # add dummy if current item was a folder
            if itemIsFolder:
                try:
                    if not os.listdir(itemFullname) == [] :
                        treeStore.append(currentIter, [None, None, None])
                except:
                    pass
            #increment the item counter
            itemCounter += 1
        # add the dummy node back if nothing was inserted before
        if itemCounter < 1: treeStore.append(parent, [None, None, None])

    def onFSRowExpanded(treeView, treeIter, treePath):
        # get the associated model
        treeStore = treeView.get_model()
        # get the full path of the position
        print(treeIter)
        newPath = treeStore.get_value(treeIter, 2)
        # populate the subtree on curent position
        Handler.populateFileSystemTreeStore(treeStore, newPath, treeIter)
        # remove the first child (dummy node)
        treeStore.remove(treeStore.iter_children(treeIter))

    def onFSRowCollapsed(treeView, treeIter, treePath):
        # get the associated model
        treeStore = treeView.get_model()
        # get the iterator of the first child
        currentChildIter = treeStore.iter_children(treeIter)
        # loop as long as some childern exist
        while currentChildIter:
            # remove the first child
            treeStore.remove(currentChildIter)
            # refresh the iterator of the next child
            currentChildIter = treeStore.iter_children(treeIter)
        # append dummy node
        treeStore.append(treeIter, [None, None, None])

    def onFSRowActivated(treeView, path, column):
        model = treeView.get_model()
        curiter = model.get_iter(path)
        fspath = model.get_value(curiter, 2)
        if not os.path.isdir(str(fspath)):
            Handler.openfile(str(fspath))

class Pyide:

    openfiles = []
    # fs tree store from http://stackoverflow.com/questions/23433819/creating-a-simple-file-browser-using-python-and-gtktreeview
    def __init__(self, *args):
        self.builder = Gtk.Builder()
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        GObject.type_register(GtkSource.View)
        self.builder.add_from_file("pyide.glade")

        fileSystemTreeStore = Gtk.TreeStore(str, Pixbuf, str)
        FsTree.populateFileSystemTreeStore(fileSystemTreeStore, '/home/superdachs')
        fileSystemTreeView = self.builder.get_object("treeview1")
        fileSystemTreeView.set_model(fileSystemTreeStore)
        treeViewCol = Gtk.TreeViewColumn("File")
        colCellText = Gtk.CellRendererText()
        colCellImg = Gtk.CellRendererPixbuf()
        treeViewCol.pack_start(colCellImg, False)
        treeViewCol.pack_start(colCellText, True)
        treeViewCol.add_attribute(colCellText, "text", 0)
        treeViewCol.add_attribute(colCellImg, "pixbuf", 1)
        fileSystemTreeView.append_column(treeViewCol)
        fileSystemTreeView.connect("row-expanded", FsTree.onFSRowExpanded)
        fileSystemTreeView.connect("row-collapsed", FsTree.onFSRowCollapsed)
        fileSystemTreeView.connect("row-activated", FsTree.onFSRowActivated)

        self.builder.connect_signals(Handler())

    def run(self):
        window = self.builder.get_object("window1")
        window.show_all()
        Gtk.main()

if __name__ == "__main__":
    app = Pyide()
    app.run()
