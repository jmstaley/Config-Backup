import gtk

class CbBackup(object):
    def __init__(self):
        self.files = []
        self.builder = gtk.Builder()
        self.builder.add_from_file('gtk-ui.glade')
        self.builder.connect_signals({'gtk_main_quit': gtk.main_quit})

        self.window = self.builder.get_object('main_window')
        self.window.show()

if __name__ == '__main__':
    app = CbBackup()
    gtk.main()
