#!/usr/bin/env python

from gi.repository import Gtk, Gdk, GtkSource, GObject, Vte, GLib, Pango
from gi.repository.GdkPixbuf import Pixbuf
import os
import stat
import time
import jedi


class Handler:

    def onShowCompletion(self, sview):
        buffer = sview.get_buffer()

        startiter, enditer = buffer.get_bounds()
        mark = buffer.get_insert()
        cpostiter = buffer.get_iter_at_mark(mark).copy()
        source = buffer.get_text(startiter, enditer,
                                 include_hidden_chars=False)

        script = jedi.Script(source, cpostiter.get_line() + 1,
                             cpostiter.get_line_offset(), 'example.py')
        completions = script.completions()

        if completions != []:
            Handler.openCompletions(completions, sview, cpostiter)

    def openCompletions(completions, sview, cpostiter):
        iter_loc = sview.get_iter_location(cpostiter)
        win_loc = sview.buffer_to_window_coords(
            Gtk.TextWindowType.WIDGET, iter_loc.x, iter_loc.y)

        win = sview.get_window(Gtk.TextWindowType.WIDGET)
        view_pos = win.get_toplevel().get_position()

        x = win_loc[0] + view_pos[0] + 180
        y = win_loc[1] + view_pos[1] + 130

        try:
            ccwin = Gtk.Window()
            ccwin.set_keep_above(True)
            ccwin.set_decorated(False)
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            swin = Gtk.ScrolledWindow()

            title = Gtk.Label("Title")
            descr = Gtk.Label("Descr")

            vbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            vbox2.pack_start(title, True, True, 0)
            vbox2.pack_start(descr, True, True, 0)

            for c in completions:
                b = Gtk.Button(c.name)
                b.connect("clicked", Handler.onComplete,
                          c, ccwin, sview.get_buffer())
                b.connect("focus-in-event", Handler.onFocusCompletion,
                          c, title, descr)
                b.connect("focus-out-event", Handler.onUnFocusCompletion)
                vbox.pack_start(b, True, True, 0)

            hbox.pack_start(swin, True, True, 0)
            swin.add(vbox)

            hbox.pack_start(vbox2, True, True, 0)

            ccwin.add(hbox)
            ccwin.set_size_request(800, 400)
            ccwin.move(x, y)
            ccwin.connect("focus-out-event", Handler.onCCWinDestroy, ccwin)
            ccwin.connect("key-release-event", Handler.onCCWinEsc)
            ccwin.show_all()

        except Exception as e:
            print(e)

    def onFocusCompletion(self, evt, completion, title, descr):
        title.set_text(completion.description)
        descr.set_text(completion.doc)

    def onUnFocusCompletion(self, evt, data=None):
        print("P")


    def onCCWinEsc(self, event, data=None):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()

    def onComplete(self, completion, win, buf):
        buf.insert_at_cursor(completion.complete)
        win.destroy()

    def onCCWinDestroy(self, evt, window):
        window.destroy()


########################################################

    def onCopy(self, *args):
        Handler.getCurrentBuffer().copy_clipboard(app.clipboard)

    def onCut(self, *args):
        Handler.getCurrentBuffer().cut_clipboard(app.clipboard, True)

    def onPaste(self, *args):
        Handler.getCurrentBuffer().paste_clipboard(app.clipboard, None, True)

    def onModified(self, label, buffer):
        if buffer.get_modified():
            label.set_markup("<span foreground='#ff8000'>%s</span>"
                             % label.get_text())

    def onDeleteWindow(self, *args):
        for i in app.openfiles:
            pos = app.builder.get_object("notebook1").page_num(i[2])
            app.builder.get_object("notebook1").set_current_page(pos)
            isclosed = Handler.onCloseTab(Handler(), i[0], i[1], i[2])
            print(isclosed)
            if not isclosed:
                return True
        Gtk.main_quit(*args)

    def onFullscreen(self, *args):
        app.builder.get_object("window1").fullscreen()

    def onWindow(self, *args):
        app.builder.get_object("window1").unfullscreen()

    def onOpen(self, *args):
        dialog = Gtk.FileChooserDialog("open file",
                                       app.builder.get_object("window1"),
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN,
                                        Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            Handler.openfile(dialog.get_filename())
        dialog.destroy()

    def onNew(self, *args):
        buffer = GtkSource.Buffer()
        lanm = GtkSource.LanguageManager()
        lan = lanm.get_language('python')
        buffer.set_language(lan)

        buffer.set_highlight_syntax(True)
        buffer.set_highlight_matching_brackets(True)
        buffer.set_text("#!/usr/bin/env python")
        buffer.set_modified(False)
        swindow = Handler.create_tab("unnamed", buffer)
        swindow.get_children()[0].connect("show-completion",
                                          Handler.onShowCompletion, buffer)
        app.openfiles.append([None, buffer, swindow])

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

        # make settings
        sview.set_show_line_numbers(True)
        sview.set_auto_indent(True)
        sview.set_tab_width(4)
        sview.set_indent_width(4)
        sview.set_insert_spaces_instead_of_tabs(True)
        sview.set_right_margin_position(80)
        sview.set_show_right_margin(True)
        sview.modify_font(Pango.FontDescription('Dejavu Sans Mono'))

#        try:
#            bg_color = Gdk.RGBA()
#            Gdk.RGBA.parse(bg_color, "#111111")
#            sview.override_background_color(Gtk.StateType.NORMAL, bg_color)
#            fg_color = Gdk.RGBA()
#            Gdk.RGBA.parse(fg_color, "#DDDDDD")
#            sview.override_color(Gtk.StateType.NORMAL, fg_color)
#        except Exception as e:
#            print(e)
#            pass

        swindow = Gtk.ScrolledWindow()
        swindow.add(sview)
        notebook = app.builder.get_object("notebook1")
        pos = notebook.append_page(swindow, hbox)
        notebook.show_all()
        btn.connect("clicked", Handler.onCloseTab, path, buffer, swindow)
        buffer.connect("modified-changed", Handler.onModified, label, buffer)
        notebook.set_current_page(pos)
        return swindow

    def openfile(path):
        for of in app.openfiles:
            if of[0] != None:
                if path in of[0]:
                    return
        with open(path, "r") as loadedfile:
            buffer = GtkSource.Buffer()
            buffer.set_text(loadedfile.read())
            buffer.set_modified(False)
            # syntax highlighting
            lman = GtkSource.LanguageManager()
            lan = lman.guess_language(path)
            swindow = Handler.create_tab(path, buffer)
            if lan:
                buffer.set_highlight_syntax(True)
                buffer.set_language(lan)
                if lan.get_name() == 'Python':
                    swindow.get_children()[0].connect("show-completion",
                                                      Handler.onShowCompletion,
                                                      swindow.get_children()[0])
            else:
                buffer.set_highlight_syntax(False)
            buffer.set_highlight_matching_brackets(True)

            app.openfiles.append([path, buffer, swindow])

    def askForSave(buffer):
        dialog = Gtk.Dialog("ask for save dialog", app.builder.get_object("window1"), 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_YES, Gtk.ResponseType.YES,
             Gtk.STOCK_NO, Gtk.ResponseType.NO))
        dialog.get_content_area().add(Gtk.Label("Datei nicht gespeichert. Wollen Sie die datei jetzt speichern?"))
        dialog.set_default_size(150, 100)
        dialog.show_all()
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            Handler.onSaveCurrent(Handler())
            dialog.destroy()
            if not buffer.get_modified():
                return True
            else:
                return False
        elif response == Gtk.ResponseType.NO:
            dialog.destroy()
            return True
        else:
            dialog.destroy()
            return False


    def onCloseTab(self, path, buffer, swindow):
        pos = app.builder.get_object("notebook1").page_num(swindow)
        window = app.builder.get_object("notebook1").get_nth_page(pos)
        buffer = window.get_child().get_buffer()
        if buffer.get_modified():
            response = Handler.askForSave(buffer)
            if response:
                app.builder.get_object("notebook1").remove_page(pos)
                for i in app.openfiles:
                    if i[1] == buffer:
                        path = i[0]
                        app.openfiles.remove([path, buffer, swindow])
                        return True
            else:
                return False
        else:
            app.builder.get_object("notebook1").remove_page(pos)
            for i in app.openfiles:
                if i[1] == buffer:
                    path = i[0]
                    app.openfiles.remove([path, buffer, swindow])
                    return True

    def savefile(buffer, path, label):
        with open(path, 'w') as f:
            f.write(buffer.get_text(*buffer.get_bounds(), include_hidden_chars=True))
            label.set_markup("<span foreground='#000000'>%s</span>" % label.get_text())
            buffer.set_modified(False)
            Handler.updateOpenFiles(path, buffer)

    def onSaveCurrent(self, *args):
        buffer, label = Handler.getCurrentBufferAndLabel()
        path = Handler.getPathFromOpenFiles(buffer)
        if path == None:
            path = Handler.saveAs()
            label.set_text(path)
        Handler.savefile(buffer, path, label)

    def updateOpenFiles(path, buffer):
        for i in app.openfiles:
            if i[1] == buffer:
                i[0] = path
                i[1] = buffer

    def onSaveAsCurrent(self, *args):
        buffer, label = Handler.getCurrentBufferAndLabel()
        path = Handler.saveAs()
        label.set_text(path)
        Handler.savefile(buffer, path, label)

    def saveAs():
        dialog = Gtk.FileChooserDialog("save file as", app.builder.get_object("window1"),
        Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        response = dialog.run()
        retval = None
        if response == Gtk.ResponseType.OK:
            retval = dialog.get_filename()
        dialog.destroy()
        return retval


    def getPathFromOpenFiles(buffer):
        for i in app.openfiles:
            if i[1] == buffer:
                return i[0]

    def getCurrentBufferAndLabel():
        currentpage = app.builder.get_object("notebook1").get_current_page()
        window = app.builder.get_object("notebook1").get_nth_page(currentpage)
        label = app.builder.get_object("notebook1").get_tab_label(window).get_children()[0]
        view = window.get_child()
        return view.get_buffer(), label

    def onRunApp(self, *args):

        f = "/tmp/%i.py" % int(time.time())
        with open (f, "w") as loadedfile:
            buffer, label = Handler.getCurrentBufferAndLabel()
            loadedfile.write(buffer.get_text(*buffer.get_bounds(), include_hidden_chars=True))
        label.set_markup("<span foreground='#009000'>%s</span>" % label.get_text())
        termwin = Gtk.Window()
        termwin.set_default_size(800, 600)

        def closeTerm(win, evt, label, buffer):
            win.destroy()
            os.remove(f)
            if buffer.get_modified():
                label.set_markup("<span foreground='#FF8000'>%s</span>" % label.get_text())
            else:
                label.set_markup("<span foreground='#000000'>%s</span>" % label.get_text())

        termwin.connect("delete-event", closeTerm, label, buffer)

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
        newPath = treeStore.get_value(treeIter, 2)
        # populate the subtree on curent position
        FsTree.populateFileSystemTreeStore(treeStore, newPath, treeIter)
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

        self.my_accelerators = Gtk.AccelGroup()

        fileSystemTreeStore = Gtk.TreeStore(str, Pixbuf, str)
        FsTree.populateFileSystemTreeStore(fileSystemTreeStore, os.path.expanduser("~"))
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

    def add_accelerator(self, widget, accelerator, signal="activate"):
        if accelerator is not None:
            key, mod = Gtk.accelerator_parse(accelerator)
            widget.add_accelerator(signal, self.my_accelerators, key, mod, Gtk.AccelFlags.VISIBLE)
            print("The accelerator is well added with the signal " + signal)

    def run(self):
        window = self.builder.get_object("window1")


        window.add_accel_group(self.my_accelerators)

        window.show_all()
        Handler.openfile("./pyide.py")
        Gtk.main()

if __name__ == "__main__":
    app = Pyide()
    app.run()
