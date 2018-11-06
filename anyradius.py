#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: AnyRadius
Dev: K4YT3X
Date Created: July 2, 2018
Last Modified: November 3, 2018

Licensed under the GNU General Public License Version 3 (GNU GPL v3),
    available at: https://www.gnu.org/licenses/gpl-3.0.txt
(C) 2018 K4YT3X

Description: An account controller for radius
"""
from avalon_framework import Avalon
from prettytable import PrettyTable
import binascii
import hashlib
import json
import MySQLdb
import re
import readline
import sys
import traceback

VERSION = '1.5.2'
COMMANDS = [
    "TruncateUserTable",
    "AddUser",
    "DelUser",
    "ShowUsers",
    "Exit",
    "Quit",
]


def show_affection(function):
    """ Shows cursor execution affected rows
    """

    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
        Avalon.debug_info('{} row(s) affected'.format(args[0].cursor.rowcount))
    return wrapper


def catch_mysql_errors(function):
    """ Catch mysqldb warnings and errors
    """
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            Avalon.error(e)
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


class ShellCompleter(object):

    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if state == 0:
            if text:
                self.matches = [s for s in self.options if s and s.lower().startswith(text.lower())]
            else:
                self.matches = self.options[:]
        try:
            return self.matches[state]
        except IndexError:
            return None


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
            # password = ntlm_hash(password)
            password = sha2_512_hash(password)

        # Pick an id for user
        self.cursor.execute("SELECT * FROM {}".format(self.table))
        used_ids = []
        for user in self.cursor.fetchall():
            used_ids.append(user[0])
        used_ids_sorted = sorted(used_ids)
        try:
            user_id = list(missing_elements(used_ids_sorted, 0, len(used_ids_sorted) - 1))[0]
        except IndexError:
            try:
                user_id = used_ids_sorted[-1] + 1
            except IndexError:
                user_id = 1

        # self.cursor.execute("INSERT INTO {} (id, username, attribute, op, value) VALUES ({}, '{}', 'NT-Password',':=', '{}')".format(self.table, user_id, username, password))
        self.cursor.execute("INSERT INTO {} (id, username, attribute, op, value) VALUES ({}, '{}', 'SHA2-Password',':=', '{}')".format(self.table, user_id, username, password))
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
        table = PrettyTable(['ID', 'Username', 'Method', 'Password'])
        for user in self.cursor.fetchall():
            table.add_row([user[0], user[1], user[2], user[4]])
        print(table)
        Avalon.info('Query complete, {} users found in database'.format(total_users))


def ntlm_hash(plaintext):
    """ Returns the mschap hashed text
    """
    hash = hashlib.new('md4', plaintext.encode('utf-16le')).digest()
    return binascii.hexlify(hash).decode('utf-8')


def sha2_512_hash(plaintext):
    """ Returns Salted SHA2-512 hashed password
    """
    return hashlib.sha512('{}'.format(plaintext).encode('utf-8')).hexdigest()


def print_legal_info():
    print('AnyRadius {}'.format(VERSION))
    print('(C) 2018 K4YT3X')
    print('Licensed under GNU GPL v3')


def print_help():
    help_lines = [
        "\n{}Commands are not case-sensitive{}".format(Avalon.FM.BD, Avalon.FM.RST),
        "TruncateUserTable",
        "AddUser [username] [password]",
        "DelUser [username]",
        "ShowUsers",
        "Exit / Quit",
        "",
    ]
    for line in help_lines:
        print(line)


def command_interpreter(db_connection, commands):
    """ AnyRadius shell command interpreter
    """
    try:
        # Try to guess what the user is saying
        possibilities = [s for s in COMMANDS if s.lower().startswith(commands[1])]
        if len(possibilities) == 1:
            commands[1] = possibilities[0]

        if commands[1].replace(' ', '') == '':
            result = 0
        elif commands[1].lower() == 'help':
            print_help()
            result = 0
        elif commands[1].lower() == 'truncateusertable':
            Avalon.warning('By truncating you will LOSE ALL USER DATA')
            if Avalon.ask('Are you sure you want to truncate?'):
                result = db_connection.truncate_user_table()
            else:
                Avalon.warning('Operation canceled')
                result = 0
        elif commands[1].lower() == 'adduser':
            result = db_connection.add_user(commands[2], commands[3])
        elif commands[1].lower() == 'deluser':
            result = db_connection.del_user(commands[2])
        elif commands[1].lower() == 'showusers':
            result = db_connection.show_users()
        elif commands[1].lower() == 'exit' or commands[1].lower() == 'quit':
            Avalon.warning('Exiting')
            exit(0)
        elif len(possibilities) > 0:
            Avalon.warning('Ambiguous command \"{}\"'.format(commands[1]))
            print('Use \"Help\" command to list available commands')
            result = 1
        else:
            Avalon.error('Invalid command')
            print('Use \"Help\" command to list available commands')
            result = 1
        return result
    except IndexError:
        Avalon.error('Invalid arguments')
        print('Use \"Help\" command to list available commands')
        result = 0


def read_config(config_path):
    with open(config_path, 'r') as anyconfig:
        settings = json.loads(anyconfig.read())
        return settings['db_host'], settings['db_user'], settings['db_pass'], settings['db'], settings['table']


def main():
    """ AnyRadius Manager main function
    This function can only be executed when
    this file is not being imported.
    """
    # Create database controller connection

    try:
        if sys.argv[1].lower() == 'help':
            print_help()
            exit(0)
        elif sys.argv[1].lower() == 'config':
            config_path = sys.argv[2]
        else:
            config_path = '/etc/anyradius.json'
    except IndexError:
        Avalon.error('Error parsing configuration file path')
        exit(1)

    Avalon.debug_info('Reading config from: {}'.format(config_path))
    db_host, db_user, db_pass, db, table = read_config(config_path)

    Avalon.info('Connecting to RADIUS database')
    rdb = UserDatabase(db_host, db_user, db_pass, db, table)
    Avalon.info('Database connection established')

    # Begin command interpreting
    try:
        if sys.argv[1].lower() == 'interactive' or sys.argv[1].lower() == 'int':
            print_legal_info()
            # Set command completer
            completer = ShellCompleter(COMMANDS)
            readline.set_completer(completer.complete)
            readline.parse_and_bind('tab: complete')
            # Launch interactive trojan shell
            prompt = '{}[AnyRadius]> {}'.format(Avalon.FM.BD, Avalon.FM.RST)
            while True:
                command_interpreter(rdb, [''] + input(prompt).split(' '))
        else:
            # Return to shell with command return value
            exit(command_interpreter(rdb, sys.argv[0:]))
    except IndexError:
        Avalon.warning('No commands specified')
        exit(0)
    except (MySQLdb.Error, MySQLdb.Warning):
        Avalon.errors('Database error')
        traceback.print_exc()
        exit(1)
    except (KeyboardInterrupt, EOFError):
        Avalon.warning('Exiting')
        exit(0)
    except Exception:
        Avalon.error('Exception caught')
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()
