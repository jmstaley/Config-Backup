# Copyright 2011 Jon Staley <jon@spandexbob.co.uk
# inspired by the script from http://crunchbanglinux.org/forums/post/114073
# http://crunchbanglinux.org/pastebin/905
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import os
import gio
import ConfigParser

class Config(object):
    def __init__(self):
        self.config_file = '%s/.config_backup' % os.getenv('HOME')
        self.files = []
        self.extra = ''
        self.target = '%s/bak' % os.getenv('HOME')
        if os.path.exists(self.config_file):
            self._get_config_from_file()

    def _get_config_from_file(self):
        config = ConfigParser.RawConfigParser()
        config.read(self.config_file)
        files = config.get('ui', 'files')
        if files:
            self.files = files.split(',')
        if config.get('ui', 'extra'):
            self.extra = config.get('ui', 'extra')
        if config.get('ui', 'target'):
            self.target = config.get('ui', 'target')

    def save(self, files='', extra='', target=''):
        config = ConfigParser.RawConfigParser()
        config.add_section('ui')

        config.set('ui', 'target', target)
        config.set('ui', 'files', files)
        config.set('ui', 'extra', extra)

        with open(self.config_file, 'wb') as configfile:
            config.write(configfile)

class Backup(object):
    def __init__(self, copy_finished_callback):
        self.copy_finished = copy_finished_callback

    def backup_files(self, files, target):
        if not os.path.exists(target):
            os.makedirs(target)
        
        for file_path in files:
            if not file_path.startswith('/'):
                file_path = '%s/%s' % (os.getenv('HOME'), file_path)

            if os.path.isdir(file_path):
                folder = file_path.split('/')[-1]
                target_folder = '%s/%s' % (target, folder)
                if not os.path.exists(target_folder):
                    os.mkdir(target_folder)
                dirs_to_copy = []
                files_to_copy = []
                for path, dirs, files in os.walk(file_path):
                    self.create_directories(dirs, path, file_path, target)
                    new_loc = path.split(file_path)[-1]
                    for f in files:
                        src = '%s/%s' % (path, f)
                        targ = '%s/%s/' % (target_folder, new_loc)
                        self.copy_file(src, targ)
            else:
                self.copy_file(file_path, target)

    def create_directories(self, dirs, path, file_path, target):
        for d in dirs:
            if not path.endswith('/'):
                path = '%s/' % path
            old_dir = '%s%s' % (path, d)
            new_dir = '%s/%s/%s' % (target,
                    file_path.split('/')[-1],
                    old_dir.split(file_path)[-1])
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)

    def copy_file(self, file_path, target):
        filename = file_path.split('/')[-1]
        target_path = '%s/%s' % (target, filename)

        if os.path.exists(target_path):
            os.unlink(target_path)

        src = gio.File(path=file_path)
        dest = gio.File(path=target_path)
        src.copy_async(dest, self.copy_finished, flags=gio.FILE_COPY_OVERWRITE|gio.FILE_COPY_ALL_METADATA)


class BackupUI(object):
    def __init__(self):
        self.config = Config()
        self.user_home = os.getenv('HOME')
        self.backup = Backup(self.copy_finished)
        self.number_files = 0
        self.files_done = 0

        self.builder = gtk.Builder()
        self.builder.add_from_file('gtk-ui.glade')
        self.builder.connect_signals({'gtk_main_quit': gtk.main_quit,
                                      'on_backup_btn_clicked': self.backup_clicked,
                                      'on_close_btn_clicked': self.close_clicked,
                                      'on_about_activate': self.about_clicked})

        table = self.builder.get_object('checkbox_table')
        self.checkboxes = table.get_children()
        self._set_active_checkboxes(self.config.files)

        self.other_files = self.builder.get_object('other_entry')
        self.other_files.set_text(self.config.extra)

        self.target_entry = self.builder.get_object('target_entry')
        self.target_entry.set_text(self.config.target)

        self.about = self.builder.get_object('aboutdialog')

        self.progress_dialog = self.builder.get_object('progress_dialog')
        self.pb = self.builder.get_object('progressbar')

        self.window = self.builder.get_object('main_window')
        self.window.show()

    def _set_active_checkboxes(self, active_labels):
        for check in self.checkboxes:
            if check.get_label() in active_labels:
                check.set_active(True)

    def _get_active_checkboxes(self):
        boxes = []
        for check in self.checkboxes:
            if check.get_active():
                boxes.append(check)
        return boxes

    def close_clicked(self, evt):
        active_checkboxes = self._get_active_checkboxes()
        files = ','.join([box.get_label() for box in active_checkboxes])
        self.config.save(files=files,
                extra=self.other_files.get_text(),
                target=self.target_entry.get_text())
        gtk.main_quit()

    def _get_files(self, files):
        """ spider through the file options given and return a 
            list of files to be copied """
        files_to_backup = []

        for file_path in files:
            if not file_path.startswith('/'):
                file_path = '%s/%s' % (os.getenv('HOME'), file_path)

            if os.path.isdir(file_path):
                dirs_to_copy = []
                files_to_copy = []
                for path, dirs, files in os.walk(file_path):
                    new_loc = path.split(file_path)[-1]
                    for f in files:
                        src = '%s/%s' % (path, f)
                        files_to_backup.append(src)
            else:
                files_to_backup.append(file_path)
        return files_to_backup 

    def backup_clicked(self, evt):
        file_options = []

        for check in self._get_active_checkboxes():
            file_path = '%s/%s' % (self.user_home, check.get_label())
            file_options.append(file_path)

        for file_path in self.other_files.get_text().split(','):
            if file_path:
                file_path = file_path.strip()
                file_options.append(file_path)

        files_to_backup = self._get_files(file_options)
        self.number_files = len(files_to_backup)

        self.backup.backup_files(file_options, self.target_entry.get_text())
        self.progress_dialog.show()

    def copy_finished(self, source, result):
        x = source.copy_finish(result)
        self.pb.set_text('Finished %s' % source.get_basename())
        self.files_done += 1
        frac = float(float(self.files_done)/float(self.number_files))
        self.pb.set_fraction(frac)
        if frac == 1.0:
            self.progress_dialog.destroy()

    def about_clicked(self, evt):
        self.about.connect('response', lambda d, r: d.destroy())
        self.about.run()


if __name__ == '__main__':
    app = BackupUI()
    gtk.main()
