import gtk

class CbBackup(object):
    def __init__(self):
        self.files = []
        self.builder = gtk.Builder()
        self.builder.add_from_file('gtk-ui.glade')
        self.builder.connect_signals({'gtk_main_quit': gtk.main_quit,
                                      'on_backup_btn_clicked': self.backup_clicked})

        self.window = self.builder.get_object('main_window')
        self.window.show()

    def backup_clicked(self, evt):
        print "backup"

if __name__ == '__main__':
    app = CbBackup()
    gtk.main()
