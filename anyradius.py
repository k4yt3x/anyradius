#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: AnyRadius
Dev: K4YT3X
Date Created: July 2, 2018
Last Modified: July 12, 2018

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt
(C) 2018 K4YT3X

Description: An account controller for radius
"""
from prettytable import PrettyTable
import avalon_framework as avalon
import binascii
import hashlib
import MySQLdb
import re
import sys
import traceback

VERSION = '1.4.3'


def show_affection(function):
    """ Shows cursor execution affected rows
    """

    def wrapper(*args, **kwargs):
        function(*args, **kwargs)
        avalon.dbgInfo('{} row(s) affected'.format(args[0].cursor.rowcount))
    return wrapper


def catch_mysql_errors(function):
    """ Catch mysqldb warnings and errors
    """
    def wrapper(*args, **kwargs):
        try:
            function(*args, **kwargs)
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            avalon.error(e)
            return 1
    return wrapper


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


class UserDatabase:
    def __init__(self, db_host, db_user, db_pass, db, table):
        """ Initialize database connection
        """
        self.db_host = db_host
        self.db_user = db_user
        self.db_pass = db_pass
        self.db = db
        self.table = table
        self.connection = MySQLdb.connect(self.db_host, self.db_user, self.db_pass, self.db)
        self.cursor = self.connection.cursor()

    def __del__(self):
        """ Disconnect if connection still alive
        """
        try:
            self.connection.close()
        except Exception:
            pass

    @show_affection
    @catch_mysql_errors
    def truncate_user_table(self):
        """ truncate the user table
        """
        self.cursor.execute('TRUNCATE {};'.format(self.table))
        self.connection.commit()
        return 0

    @show_affection
    @catch_mysql_errors
    def add_user(self, username, password):
        """ Add a new user into the database

        This method adds new user into the database.
        Password will be added as is if it is already
        hashed. Otherwise the function will automatically
        has the password.

        IDs will be recycled upon deletion, and will be
        assigned to new users.
        """
        prog = re.compile('^[a-f0-9]{32}$')
        if prog.match(password) is None:
            password = ntlm_hash(password)

        # Pick an id for user
        self.cursor.execute("SELECT * FROM {}".format(self.table))
        used_ids = []
        for user in self.cursor.fetchall():
            used_ids.append(user[0])
        used_ids_sorted = sorted(used_ids)
        try:
            user_id = list(missing_elements(used_ids_sorted, 0, len(used_ids_sorted) - 1))[0]
        except IndexError:
            user_id = used_ids_sorted[-1] + 1

        self.cursor.execute("INSERT INTO {} (id, username, attribute, op, value) VALUES ({}, '{}', 'NT-Password',':=', '{}')".format(self.table, user_id, username, password))
        self.connection.commit()

    @show_affection
    @catch_mysql_errors
    def del_user(self, username):
        """ Delete a user from the database
        """
        self.cursor.execute("DELETE FROM {} WHERE username = '{}'".format(self.table, username))
        self.connection.commit()

    @catch_mysql_errors
    def user_exists(self, username):
        """ Determines if a user exists

        Returns true if user exists, false otherwise
        """
        self.cursor.execute("SELECT * FROM {} WHERE username = '{}'".format(self.table, username))
        user_id = self.cursor.fetchone()
        if user_id is not None:
            return True
        return False

    @show_affection
    @catch_mysql_errors
    def show_users(self):
        """ List all users from the database
        """
        total_users = self.cursor.execute("SELECT * FROM {}".format(self.table))
        table = PrettyTable(['ID', 'Username', 'Password'])
        for user in self.cursor.fetchall():
            table.add_row([user[0], user[1], user[4]])
        print(table)
        avalon.info('Query complete, {} users found in database'.format(total_users))


def ntlm_hash(plaintext):
    """ Returns the mschap hashed text
    """
    hash = hashlib.new('md4', plaintext.encode('utf-16le')).digest()
    return binascii.hexlify(hash).decode('utf-8')


def print_help():
    help_lines = [
        "\n{}Commands are not case-sensitive{}".format(avalon.FM.BD, avalon.FM.RST),
        "TruncateUserTable",
        "AddUser [username] [password]",
        "DelUser [username]",
        "ShowUsers",
        "",
    ]
    for line in help_lines:
        print(line)


def command_interpreter(db_connection, commands):
    """ AnyRadius shell command interpreter
    """
    try:
        if commands[1].lower() == 'help':
            print_help()
            result = 0
        elif commands[1].lower() == 'truncateusertable':
            avalon.warning('By truncating you will LOSE ALL USER DATA')
            if avalon.ask('Are you sure you want to truncate?'):
                result = db_connection.truncate_user_table()
            else:
                avalon.warning('Operation canceled')
                result = 0
        elif commands[1].lower() == 'adduser':
            result = db_connection.add_user(commands[2], commands[3])
        elif commands[1].lower() == 'deluser':
            result = db_connection.del_user(commands[2])
        elif commands[1].lower() == 'showusers':
            result = db_connection.show_users()
        else:
            avalon.error('Invalid command')
            print('Use \'Help\' command to list available commands')
            result = 1
        return result
    except IndexError:
        avalon.error('Invalid arguments')
        print('Use \'Help\' command to list available commands')
        result = 0


def main():
    """ AnyRadius Manager main function
    This function can only be executed when
    this file is not being imported.
    """
    # Create database controller connection
    rdb = UserDatabase('localhost', 'radius', 'thisisthegensokyoradiuspassword', 'radius', 'radcheck')

    # Begin command interpreting
    try:
        if sys.argv[1].lower() == 'interactive' or sys.argv[1].lower() == 'int':
            # Launch interactive AnyRadius shell
            prompt = '\n{}[AnyRadius]> {}'.format(avalon.FM.BD, avalon.FM.RST)
            while True:
                command_interpreter(rdb, [''] + input(prompt).split(' '))
        else:
            # Return to shell with command return value
            exit(command_interpreter(rdb, sys.argv[0:]))
    except IndexError:
        avalon.warning('No commands specified')
        exit(0)
    except KeyboardInterrupt:
        avalon.warning('Exiting')
        exit(0)
    except Exception:
        avalon.error('Exception caught')
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()
