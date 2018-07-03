#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: Radius MySQL Account Controller
Dev: K4YT3X
Date Created: July 2, 2018
Last Modified: July 2, 2018

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt
(C) 2018 K4YT3X
"""
import avalon_framework as avalon
import MySQLdb

VERSION = '1.0'


class RadiusDB:

    def __init__(self):
        self.connection = MySQLdb.connect('localhost', 'radius', 'thisisthegensokyoradiuspassword', 'radius')
        self.cursor = self.connection.cursor()

    def version(self):
        self.cursor.execute('SELECT VERSION()')
        data = self.cursor.fetchone()
        print('DB Version: {}'.format(data))

    def add_user(self, username, password):
        self.cursor.execute("SELECT * FROM radcheck ORDER BY id DESC LIMIT 1")
        user_id = self.cursor.fetchone()[0] + 1
        self.cursor.execute("INSERT INTO radcheck (id, username, attribute, op, value) VALUES ({}, '{}', 'NT-Password',':=', '{}')".format(user_id, username, password))
        if self.cursor.rowcount == 0:
            avalon.warning('No rows affected')
            return
        else:
            avalon.dbgInfo('{} row(s) affected'.format(self.cursor.rowcount))
        self.connection.commit()

    def del_user(self, username):
        self.cursor.execute("DELETE FROM radcheck WHERE username = '{}'".format(username))
        if self.cursor.rowcount == 0:
            avalon.warning('No rows affected')
            return
        else:
            avalon.dbgInfo('{} row(s) affected'.format(self.cursor.rowcount))
        self.connection.commit()

    def interactive(self):
        while True:
            exec(input('>>> '))

    def print_help(self):
        print('adduser [username] [password]')
        print('deluser [username]')

    def command_interpreter(self):
        try:
            while True:
                raw_input = input('>>> ')
                command = raw_input.lower().split(' ')
                try:
                    if command[0] == 'help':
                        self.print_help()
                    elif command[0] == 'adduser':
                        if ' ' in command[1]:
                            avalon.error('There cannot be spaces in usernames')
                            continue
                        self.add_user(command[1], command[2])
                    elif command[0] == 'deluser':
                        if ' ' in command[1]:
                            avalon.error('There cannot be spaces in usernames')
                            continue
                        self.del_user(command[1])
                    else:
                        self.print_help()
                except IndexError:
                    avalon.error('You are missing components in your command')
        except KeyboardInterrupt:
            avalon.warning('Exiting')
            exit(0)


rdb = RadiusDB()
rdb.version()
# rdb.interactive()
rdb.command_interpreter()
rdb.connection.close()
