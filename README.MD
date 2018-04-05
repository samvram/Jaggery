# Project Jaggery

This project is aimed at making the process of file sharing hassle free, saving data bandwidth by using a layer inside 
the local network rather than the superficial network in a group of huge computers. By accomplishing the above objectives, we 
also get data security, i.e. data is not exposed to other people on the Internet as the pathing is apt and importantly
less time consuming. Also you wont need pen-drives, hard disks for sharing files!

## Requirements
* OS : Windows or Linux
* Python Version : 3.0+

## Dependencies:

*Jaggery* presently depends on the following libraries:
* Tkinter - python 2.7 or tkinter - python 3

### Installing Tkinter

 To see if you have Tkinter, type python on the Linux command line. 
 Then at the Python *prompt*, type

 `import Tkinter`

Or in *Python 3*

` import tkinter`

If you have Tkinter, Python will not print an error message and you can go on to the next section.

Otherwise you will see something like this:

`ImportError: No module named Tkinter`

In that case, you have to install Tkinter. On Ubuntu, you can run

`sudo apt-get install python-tk`

Or for Python 3

`sudo apt-get install python python3-tk`

Windows should have default version of Tkinter

## Running the program

### Linux machines

On your linux machine, navigate to the directory in which the scripts are present and open
a terminal in the location, and type

```bash
chmod +x run_linux.sh

./run_linux.sh
```

### Windows machines

On Windows machine, just double click **run_windows.bat**

## Starting with Jaggery

On starting *Jaggery* you will come across a CLI(Command Line Interface),
which is pretty simplified, the first thing you will be asked is:

* An alias name if you are signing in for the first time
* Your patience and co-operation :p


## Using Jaggery

Now that you have set-up Jaggery successfully you are ready to receive files on Jaggery.

Lets begin with a very basic concept, **When do you get a file?**. The answer is when 
you **request** it and someone **accept** your request. We will follow a similar structure of 
file transfer. 

`$$ isonline [-all |  -ip | -a] [<alias_name> | <ip_name>]`

This command can be used to check how many people are online.

`$$ getf <ip_address> <file_name>`

Using this command you request a file from a given IP address.

`$$ Enter the port you wish to communicate with on the remote machine: `

Enter the port they entered on their machine while setting  up, like a secure key among you 2

Next, the person you request, if running the script, will get a file dialog which asks to select the file,
on your end you will get a file save dialog where you will save the file.

`$$ exit`

Use this command and wait for 30s to end the program

## Help

A help page can be accessed anytime using: `help`  in the console

The help page is:
```
 Welcome to JAGGERY - HELP
                           
          Arguements in <> are required and those in [] are optional
           


At the beginning you will be asked to register once, with a given alias! Please provide a legit alias.
Also when someone requests a file your console asks you if you want to provide a file, press 'Y' or 
'y' to go to file selection mode. When receiving the file, a save file dialog box opens where you will
need to select the save directory and mandatorily fill the file name with extension, the dialog box title
               contains name of the file the other node has sent
               


                       Command - Function

     isonline -ip <ip_address> - Tells if node having <ip_address> is online

           isonline -a <alias> - Tells if node having <alias> is online

                 isonline -all - Tells us the list of all connected users

 getf <ip_address> [file_name] - Requests the node at <ip_address> for file:[file_name], if no file_name is given it requests a file

       getf <alias> [file_name - Requests the node with <alias> for file:[file_name], if no file_name is given it requests a file

             alias <new_alias> - This asks the registry, to update your alias to <new_alias>

                          exit - This command ends the execution of script on your machine, prompts for exit

```  

## Bugs

You can raise issues in this GIT or mail me at samvram.iist@gmail.com
