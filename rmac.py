#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: Radius MySQL Account Controller
Dev: K4YT3X
Date Created: July 2, 2018
Last Modified: July 5, 2018

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt
(C) 2018 K4YT3X
"""
import avalon_framework as avalon
import binascii
import hashlib
import MySQLdb
import re
from prettytable import PrettyTable
import traceback

VERSION = '1.3'


def missing_elements(L, start, end):
    if end - start <= 1:
        if L[end] - L[start] > 1:
            yield from range(L[start] + 1, L[end])
        return

    index = start + (end - start) // 2

    # is the lower half consecutive?
    consecutive_low = L[index] == L[start] + (index - start)
    if not consecutive_low:
        yield from missing_elements(L, start, index)

    # is the upper part consecutive?
    consecutive_high = L[index] == L[end] - (end - index)
    if not consecutive_high:
        yield from missing_elements(L, index, end)


class RadiusDB:

    def __init__(self):
        self.connection = MySQLdb.connect('localhost', 'radius', 'thisisthegensokyoradiuspassword', 'radius')
        self.cursor = self.connection.cursor()

    def __del__(self):
        try:
            self.connection.close()
        except Exception:
            pass

    def version(self):
        self.cursor.execute('SELECT VERSION()')
        data = self.cursor.fetchone()[0]
        print('DB Version: {}'.format(data))

    def ntlm_hash(self, plaintext):
        hash = hashlib.new('md4', plaintext.encode('utf-16le')).digest()
        return binascii.hexlify(hash).decode('utf-8')

    def add_user(self, username, password):
        prog = re.compile('^[a-f0-9]{32}$')
        if prog.match(password) is None:
            password = self.ntlm_hash(password)

        # Pick an id for user
        self.cursor.execute("SELECT * FROM radcheck")
        used_ids = []
        for user in self.cursor.fetchall():
            used_ids.append(user[0])
        used_ids_sorted = sorted(used_ids)
        user_id = list(missing_elements(used_ids_sorted, 0, len(used_ids_sorted) - 1))[0]

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

    def user_exists(self, username):
        self.cursor.execute("SELECT * FROM radcheck WHERE username = '{}'".format(username))
        user_id = self.cursor.fetchone()
        if user_id is not None:
            return True
        return False

    def list_users(self):
        total_users = self.cursor.execute("SELECT * FROM radcheck")
        table = PrettyTable(['ID', 'Username', 'Password'])
        for user in self.cursor.fetchall():
            table.add_row([user[0], user[1], user[4]])
        print(table)
        avalon.info('Query complete, {} users found in database'.format(total_users))

    def interactive(self):
        while True:
            exec(input('>>> '))

    def print_help(self):
        print('adduser [username] [password]')
        print('deluser [username]')
        print('list')

    def command_interpreter(self):
        try:
            while True:
                raw_input = input('>>> ')
                command = raw_input.lower().split(' ')
                try:
                    if command[0] == 'exit':
                        avalon.dbgInfo('Exiting')
                        exit(0)
                    elif command[0] == 'help':
                        self.print_help()
                    elif command[0] == 'adduser':
                        self.add_user(command[1], command[2])
                    elif command[0] == 'deluser':
                        if ' ' in command[1]:
                            avalon.error('There cannot be spaces in usernames')
                            continue
                        self.del_user(command[1])
                    elif command[0] == 'list':
                        self.list_users()
                    else:
                        self.print_help()
                except IndexError:
                    avalon.error('You are missing components in your command')
                    traceback.print_exc()
        except KeyboardInterrupt:
            avalon.warning('Ctrl^C caught, exiting')
            exit(0)


if __name__ == '__main__':
    rdb = RadiusDB()
    rdb.version()
    # rdb.interactive()
    rdb.command_interpreter()
    rdb.connection.close()
