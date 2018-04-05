import json
import ntpath
import os
import threading
from socket import *
from tkinter import *
from tkinter import filedialog
from uuid import getnode as get_mac

# import pip
# import importlib
# try:
#     importlib.import_module('FORE', 'colorama')
# except ImportError:
#     print("Package colorama not found, installing\n")
#     pip.main(['install', 'colorama'])
from colorama import init, Fore, Style

init(convert=True)


class GenericClient:
    """
    Generic class code for the client end, which establishes communication with the server, and
    then co-ordinates activities among other clients in order to transfer and receive files.
    """

    def __init__(self, alias, serverIP='none', serverPort='none', transmissionPort='none', receptionPort='none'):
        """
        The constructor of the generic class which at the moment takes only the alias name on
        creation and sets it efficiently as a class property
        :param alias: the alias name by which you are recognized online on the server
        """
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.client_ip = s.getsockname()[0]
        print('Your IP is :' + self.client_ip + '\n')
        s.close()
        self.getf_lock = False
        self.alias = alias
        self.BUFFERSIZE = 4096
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
        # query = dict( )
        # query['command'] = command
        # query['arguemets'] = arguements
        # json_q = json.dumps(query)
        sock.send(command.encode())
        received_json = (sock.recv(self.BUFFERSIZE)).decode()
        return received_json


    def reception(self, sock):
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
            except:
                # print("$$ Timed out. Trying again")
                continue
            else:
                print(Fore.WHITE + '$$ A connection has been successfully established to yur node from ' + str(
                    address) + '\n')
                request = (connection.recv(self.BUFFERSIZE)).decode()
                if request.split(':')[0] == 'fetch':
                    file_path = request.split(':')[1]
                    self.getf_lock = True
                    permission = input('$$ %s has requested %s from you. Y/N : ' % (address, file_path))
                    if permission in ['Y', 'y']:
                        root = Tk()
                        try:
                            root.filename = filedialog.askopenfilename(initialdir=os.path.expanduser('~/Documents'),
                                                                   title='Select file')
                        except:
                            print('You didn not select any file, exiting command')
                        file_path = root.filename
                        root.destroy()
                        head, tail = ntpath.split(file_path)
                        self.getf_lock = False
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
                                    except:
                                        if total_bytes != len(bytes_to_send):
                                            print("Connection Forceibly closed by remote host, Please try again")
                                            is_sent_success = False
                                        self.getf_lock = False
                                        break
                                # connection.settimeout(100)
                                connection.recv(self.BUFFERSIZE).decode()
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
            print("Connection Stopped\n$$")
        sock.close()
        print("Stopped Listening")

    def getf(self, sock, ip_alias, file_name, PORT=5000):
        """
        The function which gets a file from the other clients
        :param ip_alias: The alias or ip on which to connect
        :param file_name: the file to fetch
        :param PORT: The port on which it should communicate
        :return:
        """
        print('$$ Now connecting to IP : %s on Port : %s with Timeout of 5 sec\n' % (ip_alias, PORT))
        sock.settimeout(5)
        try:
            sock.connect((ip_alias, PORT))
        except:
            print("Timeout. User might be offline")
            return 0
        print('$$ Connected\n')
        sock.send(('fetch:%s' % file_name).encode())
        print('$$ Requesting file\n')
        sock.settimeout(100)
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
            root1 = Tk()
            try:
                root1.filename = filedialog.asksaveasfilename(initialdir=os.path.expanduser('~/Documents/'),
                                                          title='Save file as ' + received_file_name)
            except:
                print("No file name given, exiting")
                sock.close()
            file_path = root1.filename
            root1.destroy()
            with open(file_path, 'wb') as f:
                data = sock.recv(self.BUFFERSIZE)
                total_received = len(data)
                f.write(data)
                while total_received < file_size:
                    data = sock.recv(self.BUFFERSIZE)
                    total_received += len(data)
                    f.write(data)
                    print("{0:.2f}".format((total_received / float(file_size)) * 100) + " % downloaded", end='\r')
                print("Download Complete\n")
                sock.send('done'.encode())
            f.close()
        elif reply[0] == '308':
            print('$$ Permission Denied\n')
        elif reply[0] == '307':
            print('$$ File Not Found\n')
        else:
            print('$$ Unknown Response from Client\n')
        # Free the socket, i.e. disconnect it So it can be reused
        sock.close()

    def console(self, main_server_socket):
        """
        The function which runs the console on the client machine
        :return:
        """
        while True:
            if self.getf_lock is True:
                continue
            inp = input('$$ ').strip()
            if inp == 'exit':
                print('$$ Now initiating END\n')
                print('$$ 1 seconds to END\n')
                self.isrunning = False
                main_server_socket.close()
                break
            elif inp.split(' ')[0].lower() == 'help':
                self.help( )
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
            print('The alias name is successfully changed.\n')
        else:
            print("Alias name change was unsuccessful")

    def handleGETF(self, inp, main_server_socket):
        if len(inp.split(' ')) is 1:
            print('$$ Acceptable arguements with getf is <alias>/<IP> <File_name>(optional)\n')
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
                    print(k + "is \tOFFLINE")
                    return
                ip_alias = v[0]

            if len(inp.split(' ')) is 3:
                # ip_alias = inp.split(' ')[1]
                file_name = inp.split(' ')[2]
                PORT = self.transmission_port
                self.getf(socket(AF_INET, SOCK_STREAM), ip_alias, file_name, PORT)
            elif len(inp.split(' ')) is 2:
                # ip_alias = inp.split(' ')[1]
                file_name = 'unkonwn.file'
                PORT = self.transmission_port
                self.getf(socket(AF_INET, SOCK_STREAM), ip_alias, file_name, PORT)

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

    def run_time(self):
        """
        A function depicting the runtime of the Client as a whole
        :return: void
        """
        # Code for setting up a connection on server
        self.welcome()
        main_server_socket = socket(AF_INET, SOCK_STREAM)
        main_server_socket.connect((self.server_ip, self.server_port))
        main_server_socket.send((json.dumps(self.mac_id)).encode())
        mac_id_reply = (main_server_socket.recv(self.BUFFERSIZE)).decode()
        if mac_id_reply == 'not_reg':
            while True:
                self.alias = input('Pleas type in your new Alias: ')
                main_server_socket.send(('alias %s' % (self.alias)).encode())
                alias_reply = json.loads(main_server_socket.recv(self.BUFFERSIZE).decode())
                if alias_reply == 'success':
                    print('The alias name is successfully set to %s\n' % self.alias)
                    break
        else:
            print('Welcome back %s\n' % mac_id_reply)

        # Setting up transmit and receive sockets
        receive_socket = socket(AF_INET, SOCK_STREAM)
        receive_socket.bind((self.client_ip, self.transmission_port))
        print('$$ IP bound successfully\n')

        # Run a thread that looks for incoming connections and processes the commands that comes
        self.isrunning = True
        receive_thread = threading.Thread(target=self.reception, args=(receive_socket,))
        receive_thread.start()

        # Running a Console on another thread
        console_thread = threading.Thread(target=self.console, args=(main_server_socket,))
        console_thread.start()

        receive_thread.join()
        console_thread.join()

        print("Threads joined")
        self.aftermath()
        input("Press any key to exit")

    def print_h(self, cmd, work):
        print(cmd.rjust(30)+' - '+ work +'\n')

    def help(self):
        """
        This is a general program help architecture to guide you through the help process.
        :return: Help
        """
        print('Welcome to JAGGERY - HELP\n'.center(80))
        print('Arguements in <> are required and those in [] are optional\n'.center(80))
        print('\n')
        print('At the beginning you will be asked to register once, with a given alias! Please provide a legit alias.'.center(80))
        print('Also when someone requests a file your console asks you if you want to provide a file, press \'Y\' or '.center(80))
        print('\'y\' to go to file selection mode. When receiving the file, a save file dialog box opens where you will'.center(80))
        print('need to select the save directory and mandatorily fill the file name with extension, the dialog box title'.center(80))
        print('contains name of the file the other node has sent\n'.center(80))
        print('\n')
        self.print_h('Command','Function')
        self.print_h('isonline -ip <ip_address>','Tells if node having <ip_address> is online')
        self.print_h('isonline -a <alias>','Tells if node having <alias> is online')
        self.print_h('isonline -all','Tells us the list of all connected users')
        self.print_h('getf <ip_address> [file_name]', 'Requests the node at <ip_address> for file:[file_name], '
                                                      'if no file_name is given it requests a file')
        self.print_h('getf <alias> [file_name','Requests the node with <alias> for file:[file_name], '
                                                      'if no file_name is given it requests a file')
        self.print_h('alias <new_alias>','This asks the registry, to update your alias to <new_alias>')
        self.print_h('exit','This command ends the execution of script on your machine, prompts for exit')
