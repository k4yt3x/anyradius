[![GitHub issues](https://img.shields.io/github/issues/K4YT3X/AnyRadius.svg)](https://github.com/K4YT3X/AnyRadius/issues)
[![GitHub license](https://img.shields.io/github/license/K4YT3X/AnyRadius.svg)](https://github.com/K4YT3X/AnyRadius/blob/master/LICENSE)

# AnyRadius

## 1.5.1 (November 2, 2018)

- Updated for avalon framework 1.6.x

## Description

AnyRadius is a python software that can **manage freeradius users in MySQL**. It features an easy-to-use shell (somewhat Cisco like), which can make adding and removing users from the database easier, faster and more intuitive.

![Screenshot](https://user-images.githubusercontent.com/21986859/43348094-593a5156-91c6-11e8-9501-490e67021d28.png)

## Installation

### Clone the repository to download software

```bash
$ git clone https://github.com/K4YT3X/AnyRadius.git
```

You can run AnyRadius directly, or you can choose to create a symbolic link to `/usr/bin/anyradius` or `/usr/local/bin/anyradius`. Creating a symbolic link enables you to launch AnyRadius directly in the command line without having to type python3 or specify the directory.

### Run AnyRadius directly through python command

```bash
$ python3 anyradius.py
```

### Create symbolic link and run AnyRadius

```bash
$ ln -s anyradius.py /usr/bin/anyradius  # Create symbolic link
$ anyradius  # Launch anyradius directly
```

## Usages

You can use any of the commands either by passing it directly into the software through command line arguments, or type it in the interactive shell.

### Interactive Shell

You can use either of the two commands to launch the interactive shell. It enables you to keep executing AnyRadius commands, **and it also supports tab completion**.

```bash
$ anyradius interactive
$ anyradius int
```

### All Commands

All the commands available can be listed by using the `help` command.  
**Commands are not case-sensitive.**

```
TruncateUserTable                # Truncate the user table
AddUser [username] [password]    # Add a user
DelUser [username]               # Delete a user
ShowUsers                        # Show all users in a table
Exit / Quit                      # Exit the program
```
