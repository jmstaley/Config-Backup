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
import shutil
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
    def backup_files(self, files, target):
        if not os.path.exists(target):
            os.makedirs(target)
        
        for file_path in files:
            if not file_path.startswith('/'):
                file_path = '%s/%s' % (os.getenv('HOME'), file_path)

            if os.path.isdir(file_path):
                folder = file_path.split('/')[-1]
                shutil.copytree(file_path, '%s/%s' % (target, folder))
            else:
                self.copy_file(file_path, target)

    def copy_file(self, file_path, target):
        filename = file_path.split('/')[-1]
        target_path = '%s/%s' % (target, filename)

        if os.path.exists(target_path):
            os.unlink(target_path)

        src = gio.File(path=file_path)
        dest = gio.File(path=target_path)
        src.copy_async(dest, self.copy_finished, flags=gio.FILE_COPY_OVERWRITE|gio.FILE_COPY_ALL_METADATA)

    def copy_finished(self, source, result):
        x = source.copy_finish(result)

class BackupUI(object):
    def __init__(self):
        self.config = Config()
        self.user_home = os.getenv('HOME')
        self.backup = Backup()

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

    def backup_clicked(self, evt):
        files_to_backup = []

        for check in self._get_active_checkboxes():
            file_path = '%s/%s' % (self.user_home, check.get_label())
            files_to_backup.append(file_path)

        for file_path in self.other_files.get_text().split(','):
            if file_path:
                file_path = file_path.strip()
                files_to_backup.append(file_path)

        self.backup.backup_files(files_to_backup, self.target_entry.get_text())

    def about_clicked(self, evt):
        self.about.connect('response', lambda d, r: d.destroy())
        self.about.run()


if __name__ == '__main__':
    app = BackupUI()
    gtk.main()
