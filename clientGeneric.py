import json
import ntpath
import threading
import os
import rlcompleter
import atexit
import numpy as np
import time
from socket import *
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from uuid import getnode as get_mac
import pip

try:
    from colorama import init, Fore, Style
except:
    pip.main(['install', 'colorama'])
    from colorama import init, Fore, Style

try:
    import readline
except:
    pip.main(['install', 'pyreadline'])
    import readline


class MyCompleter(object):  # custom autocompleter
    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = [s for s in self.options
                                if text in s]  # partial completion added
            else:  # no text entered -> don't return anything
                return None
                # self.matches = self.options[:]

        # return match indexed by state
        try:
            return self.matches[state]
        except IndexError:
            return None


class GenericClient:
    """
    Generic class code for the client end, which establishes communication with the server, and
    then co-ordinates activities among other clients in order to transfer and receive files.
    """

    def __init__(self, alias, serverIP='none', serverPort='none', transmissionPort='none', receptionPort='none', buffer_size = 4096):
        """
        The constructor of the generic class which at the moment takes only the alias name on
        creation and sets it efficiently as a class property
        :param alias: the alias name by which you are recognized online on the server
        """
        init(convert=True)
        try:
            s = socket(AF_INET, SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.client_ip = s.getsockname()[0]
            print('Your IP is :' + self.client_ip + '\n')
            s.close()
        except OSError:
            print("Can't get you IP address from DHCP using following address")
            self.client_ip = gethostbyname('localhost')
            print('Your IP is :' + self.client_ip + '\n')
        self.getf_lock = False
        self.alias = alias
        self.BUFFERSIZE = buffer_size
        self.server_ip = serverIP
        self.server_port = serverPort
        self.transmission_port = transmissionPort
        self.reception_port = receptionPort
        self.mac_id = get_mac()
        self.isrunning = True

    @property
    def server_ip(self):
        return self._server_ip

    @property
    def isrunning(self):
        return self._isRunning

    @property
    def reception_port(self):
        return self._reception_port

    @property
    def transmission_port(self):
        return self._transmission_port

    @isrunning.setter
    def isrunning(self, x):
        if type(x) is bool:
            self._isRunning = x
        else:
            self._isRunning = True

    @transmission_port.setter
    def transmission_port(self, x):
        if x is 'none':
            self._transmission_port = 9271
        else:
            self._transmission_port = x

    @reception_port.setter
    def reception_port(self, x):
        if x is 'none':
            self._reception_port = 5000
        else:
            self._reception_port = x

    @server_ip.setter
    def server_ip(self, x):
        if x is 'none':
            self._server_ip = 'localhost'
        else:
            self._server_ip = x

    @property
    def server_port(self):
        return self._server_port

    @server_port.setter
    def server_port(self, x):
        if x is 'none':
            self._server_port = '5000'
        else:
            self._server_port = x

    @property
    def alias(self):
        return self._alias

    @alias.setter
    def alias(self, x):
        if x not in ['', ' ']:
            self._alias = x
        else:
            self._alias = 'default'

    def server_query(self, sock, command):
        """
        The function which queries the server and gets the reply and prints it
        :param sock: The socket on which to query
        :param command: The command queried
        :return:
        """
        sock.send(command.encode())
        received_json = (sock.recv(self.BUFFERSIZE)).decode()
        return received_json

    def reception(self, main_server_socket, sock):
        """
        The function handling reception
        :param sock: The socket which communicates and looks for reception
        :return:
        """
        print('$$ Started Listening\n$$')
        sock.settimeout(1)
        while self.isrunning:
            try:
                sock.listen(10)
                connection, address = sock.accept()
            except timeout:
                continue
            else:
                s = 'isonline -ip ' + str(address[0])
                received_json = self.server_query(main_server_socket, s)
                received_dict = json.loads(received_json)

                k = ''
                for k, v in received_dict.items():
                    print(Fore.WHITE + 'A connection has been requested to established to your node from "' + k + '"\n')

                request = (connection.recv(self.BUFFERSIZE)).decode()
                request = request.split(':')
                if request[0] == 'fetch':
                    file_path = request[1]
                    self.getf_lock = True
                    root = Tk()
                    answer = messagebox.askyesno("Accept Connection", "Accept connection from '" + k + "' ?")
                    if not answer:
                        self.getf_lock = False
                        root.destroy()
                        connection.send('308'.encode())
                        connection.close()
                        print("$$ ", end="")
                        continue
                    root.destroy()

                    root = Tk()
                    root.filename = filedialog.askopenfilename(initialdir=os.path.expanduser('~/Documents'),
                                                               title='Request for %s' % file_path)
                    file_path = root.filename
                    root.destroy()

                    self.getf_lock = False
                    if file_path != ():
                        head, tail = ntpath.split(file_path)
                        if os.path.isfile(file_path):
                            connection.send(('yes:' + str(os.path.getsize(file_path)) + ':' + tail).encode())
                            file_size = os.path.getsize(file_path)
                            with open(file_path, 'rb') as f:
                                bytes_to_send = f.read()
                                bytes_sent = connection.send(bytes_to_send)
                                # print(bytes_sent)
                                total_bytes = bytes_sent
                                is_sent_success = False
                                while bytes_sent > 0:
                                    try:
                                        bytes_sent = connection.send(bytes_to_send[bytes_sent:])
                                        is_sent_success = True
                                        total_bytes += bytes_sent
                                    except error:
                                        if total_bytes != len(bytes_to_send):
                                            print("Connection Forceibly closed by remote host, Please try again")
                                            is_sent_success = False
                                        self.getf_lock = False
                                        break
                                try:
                                    connection.recv(self.BUFFERSIZE).decode()
                                except:
                                    print('Connection was forcfully closed from other end\n$$', end=' ')
                                if is_sent_success:
                                    print('File Successfully sent\n$$ ')
                            f.close()
                        else:
                            print('$$ File not Found on your machine\n$$ ')
                            connection.send('307'.encode())
                    else:
                        connection.send('308'.encode())
                else:
                    connection.send('309'.encode())
                self.getf_lock = False
            connection.close()
            print("Connection Stopped\n$$", end=' ')
        sock.close()
        print("Stopped Listening")

    def console(self, main_server_socket):
        """
        The function which runs the console on the client machine
        :return:
        """
        completer = MyCompleter(["isonline", "isonline -all", "isonline -a", "isonline -ip", "getf", "alias", "exit"])
        # tab completion
        readline.set_completer(completer.complete)
        readline.parse_and_bind('tab: complete')

        try:
            # history file
            histfile = os.path.join(os.environ['HOME'], '.pythonhistory')
            readline.read_history_file(histfile)
        except IOError:
            print("$$ Can't read command history file")

        while True:
            if self.getf_lock is True:
                continue
            inp = input('$$ ').strip()
            if inp == 'exit':
                self.handleEXIT(main_server_socket)
                break
            elif inp.split(' ')[0].lower() == 'help':
                self.help()
            elif inp.split(' ')[0] == 'isonline':
                self.handleISONLINE(inp, main_server_socket)
            elif inp.split(' ')[0] == 'getf':
                self.handleGETF(inp, main_server_socket)
            elif inp.split(' ')[0] == 'alias':
                self.handleALIAS(inp, main_server_socket)
            elif inp != '':
                print('$$ Invalid command! Try again\n')
        print("Console stopped")
        return

    def handleEXIT(self, main_server_socket):
        print('$$ Now initiating END\n')
        print('$$ 1 seconds to END\n')
        self.isrunning = False
        main_server_socket.close()

    def handleISONLINE(self, inp, main_server_socket):
        try:
            if inp.split(' ')[1] == '-all':
                print('$$ Fetching status of all clients \n')
                received_json = self.server_query(main_server_socket, inp)
                received_dict = json.loads(received_json)
                try:
                    for k, v in received_dict.items():
                        if (v)[1] == 1:
                            print(Fore.WHITE + k + "\t" + received_dict[k][0], end='')
                            print(Fore.GREEN + "\tONLINE", end='')
                            print(Fore.WHITE + '\n')
                        # else:
                        #     print(k + "\t" + received_dict[k][0] + "\tOFFLINE")
                except:
                    print("Can't get list from Server")
            elif inp.split(' ')[1] == '-ip' or inp.split(' ')[1] == '-a':
                print('$$ Checking clients: %s \n' % inp.split(' ')[2:])
                received_json = self.server_query(main_server_socket, inp)
                received_dict = json.loads(received_json)
                try:
                    for k, v in received_dict.items():
                        if v[0] == '0.0.0.0':
                            print(k + "\tDoes not exist")
                        elif v[1] == 1:
                            print(Fore.WHITE + k + "\t" + received_dict[k][0], end='')
                            print(Fore.GREEN + "\tONLINE", end='')
                            print(Fore.WHITE + '\n')
                        else:
                            print(Fore.WHITE + k + "\t" + received_dict[k][0], end='')
                            print(Fore.RED + Style.BRIGHT + "\tOFFLINE", end='')
                            print(Fore.WHITE + '\n')
                except:
                    print("Can't get list from Server")
            else:
                print('$$ Acceptable arguements with isonline are -ip -a -all\n')
        except:
            print('$$ Acceptable arguements with isonline are -ip -a -all\n')

    def handleALIAS(self, inp, main_server_socket):
        received_json = self.server_query(main_server_socket, inp)
        rec = json.loads(received_json)
        if rec == "success":
            print(Fore.GREEN + 'The alias name is successfully set to %s\n' % self.alias, end='')
            print(Fore.WHITE + '\n')
        else:
            print(Fore.RED + 'The alias name is unsuccessful ', end='')
            print(Fore.WHITE + '\n')

    def handleGETF(self, inp, main_server_socket):
        if len(inp.split(' ')) is 1:
            print('$$ Acceptable arguments with getf is <alias>/<IP> <File_name>(optional)\n')
        else:
            d = inp.split(' ')[1]
            if d.count('.') >= 3:
                s = 'isonline -ip ' + d
                # print(s)
            else:
                s = 'isonline -a ' + d
                # print(s)

            ip_alias = ''
            received_json = self.server_query(main_server_socket, s)
            received_dict = json.loads(received_json)
            for k, v in received_dict.items():
                if v[0] == '0.0.0.0':
                    print(k + "\tDoes not exist. Exiting command")
                    return
                if v[1] == 0:
                    print(k + " is \tOFFLINE")
                    return
                ip_alias = v[0]

            file_name = ''
            if len(inp.split(' ')) is 3:
                file_name = inp.split(' ')[2]
            elif len(inp.split(' ')) is 2:
                file_name = 'unkonwn.file'
            PORT = self.transmission_port
            self.getf(socket(AF_INET, SOCK_STREAM), ip_alias, file_name, PORT)

    def getf(self, sock, ip_alias, file_name, PORT = 5000):
        """
        The function which gets a file from the other clients
        :param ip_alias: The alias or ip on which to connect
        :param file_name: the file to fetch
        :param PORT: The port on which it should communicate
        :return:
        """
        print(
            '$$ Connecting to IP : %s with Alias: %s on Port : %s with Timeout of 5 sec\n' % (ip_alias, ip_alias, PORT))
        sock.settimeout(5)
        try:
            sock.connect((ip_alias, PORT))
        except timeout:
            print("Timeout. User might be offline")
            return 0
        except OSError:
            print("Unable to connet. User might be offline")
            return 0
        print('$$ Connected\n')
        sock.send(('fetch:%s' % file_name).encode())
        print('$$ Requesting file. Timeout 60 sec\n')
        sock.settimeout(60)
        try:
            reply = (sock.recv(self.BUFFERSIZE)).decode()
        except:
            print("Header got corrupted. Try Again")
            reply = 'HC:'
        reply = reply.split(':')
        if reply[0] == 'yes':
            file_size = int(reply[1])
            received_file_name = reply[2]
            print('Receiving FILE of Size ' + str(file_size) + '\n')
            Ft = received_file_name.split('.')
            lastFT = len(Ft) - 1
            root1 = Tk()
            root1.filename = filedialog.asksaveasfilename(initialdir=os.path.expanduser('~/Documents/'),
                                                          initialfile=received_file_name,
                                                          title='Save file as ', filetypes=(
                    (Ft[lastFT] + " files", "*." + Ft[lastFT]), ("all files", "*.*")))
            file_path = root1.filename
            root1.destroy()
            try:
                data = bytearray()
                written_size = 0
                with open(file_path, 'wb') as f:
                    data += (sock.recv(self.BUFFERSIZE))
                    total_received = len(data)

                    tic = time.time()
                    prev_rec_size = total_received
                    data_rates = []
                    inst_data_rate = 0
                    strD = ' null'
                    while total_received < file_size:
                        data += (sock.recv(self.BUFFERSIZE))
                        total_received = written_size + len(data)
                        if total_received % (1024*1024*512) == 0:
                            f.write(bytes(data))
                            written_size += len(data)
                            del data
                            data = bytearray()
                        toc = time.time()
                        if toc - tic > .1:
                            inst_data_rate = float(total_received - prev_rec_size)/(toc - tic)
                            data_rates.append(inst_data_rate)
                            tic = toc
                            prev_rec_size = total_received
                            strD = ' Bps'
                            if inst_data_rate > 1024:
                                inst_data_rate /= 1024
                                strD = ' KBps'
                            if inst_data_rate > 1024:
                                inst_data_rate /= 1024
                                strD = ' MBps'
                            if inst_data_rate > 1024:
                                inst_data_rate /= 1024
                                strD = ' GBps'
                        if strD == ' null':
                            print(
                                "{0:.2f}".format((total_received / float(file_size)) * 100) + " % downloaded", end='\r')
                        else:
                            print("{0:.2f}".format((total_received / float(file_size)) * 100) +
                                  " % downloaded at rate: ", "{0:.2f}".format(inst_data_rate), strD, end='\r')
                    avg_data_rate = float(sum(data_rates))/len(data_rates)
                    if avg_data_rate > 1024:
                        avg_data_rate /= 1024
                        strD = ' KBps'
                    if avg_data_rate > 1024:
                        avg_data_rate /= 1024
                        strD = ' MBps'
                    if avg_data_rate > 1024:
                        avg_data_rate /= 1024
                        strD = ' GBps'
                    print("Download Completed at average rate of: ", "{0:.2f}".format(avg_data_rate), strD)
                    sock.send('done'.encode())
                    f.write(bytes(data))
                f.close()
            except FileNotFoundError:
                print("No file name given, exiting")
                sock.close()
                return
            except ConnectionResetError:
                print("Connection has been closed in between")
                sock.close()
                return
        elif reply[0] == '308':
            print('$$ Permission Denied\n')
        elif reply[0] == '307':
            print('$$ File Not Found\n')
        else:
            print('$$ Unknown Response from Client\n')
        # Free the socket, i.e. disconnect it So it can be reused
        sock.close()

    def welcome(self):
        """
        Standard welcome function
        :return: void
        """
        print("******************************************************\n")
        print("         _                                            ")
        print("        | |                                           ")
        print("        | |  __ _   __ _   __ _   ___  _ __  _   _    ")
        print("    _   | | / _` | / _` | / _` | / _ \| '__|| | | |   ")
        print("   | |__| || (_| || (_| || (_| ||  __/| |   | |_| |   ")
        print("    \____/  \__,_| \__, | \__, | \___||_|    \__, |   ")
        print("                    __/ |  __/ |              __/ |   ")
        print("                   |___/  |___/              |___/  \n")
        print("______________________________________________________\n")
        print("        Developers - Ankit Verma, Samvram Sahu        \n")
        print("******************************************************\n")

    def aftermath(self):
        """
        THe ending
        :return:
        """
        print("************************************************************\n")
        print("                        Thank You                           \n")
        print("                           for                              \n")
        print("                      using Jaggery                         \n")
        print("____________________________________________________________\n")
        print("           Bugs - +919497300461 - Samvram Sahu              \n")
        print("           Bugs - +919497300089 - Ankit Verma               \n")
        print("************************************************************\n")
        # atexit.register(readline.write_history_file, histfile) # its time to delete
        # del os, histfile, readfile, rtlcompleter # separate hist for each run

    def run_time(self):
        """
        A function depicting the runtime of the Client as a whole
        :return: void
        """

        # Code for setting up a connection on server
        self.welcome()
        main_server_socket = socket(AF_INET, SOCK_STREAM)
        try:
            main_server_socket.connect((self.server_ip, self.server_port))
        except OSError:
            self.handleEXIT(main_server_socket)
            self.aftermath()
            print('Unable to connect to server')
            input("Press Enter to exit")
            return

        main_server_socket.send((json.dumps(self.mac_id)).encode())
        mac_id_reply = (main_server_socket.recv(self.BUFFERSIZE)).decode()
        if mac_id_reply == 'not_reg':
            while True:
                self.alias = input('Pleas type in your new Alias: ')
                main_server_socket.send(('alias %s' % self.alias).encode())
                alias_reply = json.loads(main_server_socket.recv(self.BUFFERSIZE).decode())
                if alias_reply == 'success':
                    print('The alias name is successfully set to %s\n' % self.alias)
                    break
        else:
            print('Welcome back %s\n' % mac_id_reply)

        # Setting up transmit and receive sockets
        receive_socket = socket(AF_INET, SOCK_STREAM)
        try:
            receive_socket.bind((self.client_ip, self.transmission_port))
            print('$$ IP bound successfully\n')
        except:
            input("Can't bind to the Port %d.\nPress Enter to exit" % self.transmission_port)
            return

        # Run a thread that looks for incoming connections and processes the commands that comes
        self.isrunning = True
        receive_thread = threading.Thread(target=self.reception, args=(main_server_socket, receive_socket,))
        receive_thread.start()

        # Running a Console on another thread
        console_thread = threading.Thread(target=self.console, args=(main_server_socket,))
        console_thread.start()

        receive_thread.join()
        console_thread.join()

        print("Threads joined")
        self.aftermath()
        input("Press Enter to exit")

    def print_h(self, cmd, work):
        print(cmd.rjust(30) + ' - ' + work + '\n')

    def help(self):
        """
        This is a general program help architecture to guide you through the help process.
        :return: Help
        """
        print('Welcome to JAGGERY - HELP\n'.center(80))
        print('Arguements in <> are required and those in [] are optional\n'.center(80))
        print('\n')
        print(
            'At the beginning you will be asked to register once, with a given alias! Please provide a legit alias.'.center(
                80))
        print(
            'Also when someone requests a file your console asks you if you want to provide a file, press \'Y\' or '.center(
                80))
        print(
            '\'y\' to go to file selection mode. When receiving the file, a save file dialog box opens where you will'.center(
                80))
        print(
            'need to select the save directory and mandatorily fill the file name with extension, the dialog box title'.center(
                80))
        print('contains name of the file the other node has sent\n'.center(80))
        print('\n')
        self.print_h('Command', 'Function')
        self.print_h('isonline -ip <ip_address>', 'Tells if node having <ip_address> is online')
        self.print_h('isonline -a <alias>', 'Tells if node having <alias> is online')
        self.print_h('isonline -all', 'Tells us the list of all connected users')
        self.print_h('getf <ip_address> [file_name]', 'Requests the node at <ip_address> for file:[file_name], '
                                                      'if no file_name is given it requests a file')
        self.print_h('getf <alias> [file_name', 'Requests the node with <alias> for file:[file_name], '
                                                'if no file_name is given it requests a file')
        self.print_h('alias <new_alias>', 'This asks the registry, to update your alias to <new_alias>')
        self.print_h('exit', 'This command ends the execution of script on your machine, prompts for exit')
