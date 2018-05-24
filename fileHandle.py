from socket import *
import time
import threading
import sqlite3
import os
import json

"""
Commands:
    addf -pub  file_path/dir_path
    addf -pri  file_path/dir_path alias/ip
    rmf -pub  file_path/dir_path
    rmf -pri  file_path/dir_path
    search  file_path/dir_path
"""


class fileHandle:

    def __init__(self, port, buffer_size, client_ip, alias, mac, UDP_RESPONSE_TIME,
                 UDP_RESPONSE_ATTEMPTS, UDP_RESPONSE_DELTA):


        self.alias = alias
        self.mac = mac
        self.client_ip = client_ip
        self.BUFFER_SIZE = buffer_size
        self.UDP_PORT = port
        self.path = 'fileData.db'
        self.isrunning = True
        try:
            self.createDB()
        except:
            print('File Database is ready')
        self.UDP_th = threading.Thread(target=self.__handleUDPServer__)
        self.UDP_th.start()

        self.UDP_RESPONSE_TIME = UDP_RESPONSE_TIME
        self.UDP_RESPONSE_ATTEMPTS = UDP_RESPONSE_ATTEMPTS
        self.UDP_RESPONSE_DELTA = UDP_RESPONSE_DELTA

        self.udp_client_sock = socket(AF_INET, SOCK_DGRAM)
        self.udp_client_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.udp_client_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.lock = threading.Lock()
        self.requiredResponse = False
        self.gotResponse = 0

    def createDB(self):
        dbConnection = sqlite3.connect(self.path)
        db = dbConnection.cursor()
        q = """
                CREATE TABLE pub(
                Name VARCHAR(100) , 
                Path VARCHAR(1000) PRIMARY KEY UNIQUE,
                Folder VARCHAR(100) DEFAULT '/'
                );"""
        db.execute(q)
        dbConnection.commit()
        print('pub Table created')

        q = """
                CREATE TABLE pri(
                Name VARCHAR(100) , 
                Path VARCHAR(100) PRIMARY KEY UNIQUE,
                Folder VARCHAR(100) DEFAULT '/',
                mac INTEGER DEFAULT 0
                );"""
        db.execute(q)
        dbConnection.commit()
        print('pri Table created')

        q = """
                CREATE TABLE know(
                sr INTEGER PRIMARY KEY,
                mac INTEGER,
                ip VARCHAR(100),
                alias VARCHAR (100),
                filename VARCHAR (1000)
                );"""
        db.execute(q)
        dbConnection.commit()
        print('know Table created')

        dbConnection.close()

    def handleCMD(self, inp, main_server_sock):
        inp = inp.lstrip()
        inp = inp.rstrip()
        try:
            r = inp.split(' ')
        except:
            return "illegalCMD"
        cmd = r[0]
        opData = inp[inp.index(' ') + 1:].strip()
        try:
            r = opData.split(' ')
        except:
            print('Illegal Command')
            return "illegalCMD"
        if cmd == "addf":
            self.__handleADDF__(r)
        elif cmd == "searchf":
            self.__handleSEARCHF__(r)
        elif cmd == "rmf":
            self.__handleRMF__(r)
        elif cmd == "showf":
            self.__handleSHOWF__(r)
        else:
            return "illegalCMD"

    def __handleADDF__(self, r):
        option = r[0]
        if option == "-pub":
            q = """INSERT INTO pub (name, path, folder) VALUES (?, ?, ?)"""
            strDisp = 'public '
        elif option == "-pri":
            q = """INSERT INTO pri (name, path, folder) VALUES (?, ?, ?)"""
            strDisp = 'private '
        else:
            return "illegalCMD"
        i = 1
        while i < len(r):
            pS = r[i]
            i += 1
            name = os.path.basename(pS)
            if os.path.isdir(pS):
                fileList = os.listdir(pS)
                for k in fileList:
                    r.append(os.path.abspath(pS) + "\\" + k)
                continue
            elif not os.path.isfile(pS):
                print(pS, ' is not a file or directory')
                continue
            (_, folder) = os.path.split(os.path.dirname(pS))
            if not folder:
                folder = "\\"
                pS = os.path.abspath(pS)
            dbConnection = sqlite3.connect(self.path)
            db = dbConnection.cursor()
            try:
                db.execute(q, (name, pS, folder))
                print('Added to ', strDisp, name)
            except sqlite3.IntegrityError:
                print('File ', name, 'already added to the database', strDisp)
            except Exception as e:
                print('Something went wrong while retrieving data from ', strDisp, "database\n", e)
            else:
                dbConnection.commit()
                dbConnection.close()

    def __handleSEARCHF__(self, r):
        dbConnection = sqlite3.connect(self.path)
        db = dbConnection.cursor()
        files = []
        for fn in r:
            q = """SELECT * FROM  know WHERE filename = ?"""

            db.execute(q, (fn,))
            data = db.fetchall()

            if len(data) == 0:
                files.append(fn)

            else:
                for rows in data:
                    print('Contacting: ', rows[2], ' for file: ', fn)
        dbConnection.close()
        if len(files) == 0:
            return

        print('Searching, in the network, for files: ', files)
        self.udp_client_sock.sendto(
            self.__makePacket__(type="request", sub_type="file_request", info=[], files=files,
                                dest=(0, '127.255.255.255', 'all')),
            ("127.255.255.255", self.UDP_PORT))
        print('Request broadcast')
        with self.lock:
            print('Lock Acquired')
            self.requiredResponse = True
            self.gotResponse = 0
        print('Lock Released')
        count = 0
        wait_time = self.UDP_RESPONSE_TIME
        while count < self.UDP_RESPONSE_ATTEMPTS:
            tic = time.time()
            toc = tic
            print("Waiting for ", wait_time, " seconds")
            while toc - tic < wait_time:
                toc = time.time()
            with self.lock:
                if self.gotResponse > 0:
                    print('Got some response. Exiting waiting loop')
                    break
            wait_time += self.UDP_RESPONSE_DELTA
            count += 1
            print("Timeout, No response received")

        with self.lock:
            if self.gotResponse == 0:
                print("Files: ", files, "\nare not found in the network")
                return
        self.gotResponse = 0
        self.requiredResponse = False
        print("Got some response")

        return

    def __handleRMF__(self, r):
        option = r[0]
        i = 1
        if len(r) == 1:
            if option == "-pub":
                q = """DELETE FROM pub"""
                strDisp = 'public '
            elif option == "-pri":
                q = """DELETE FROM pri"""
                strDisp = 'private '
            else:
                print("Illegal Command")
                return "illegalCMD"
            dbConnection = sqlite3.connect(self.path)
            db = dbConnection.cursor()
            try:
                db.execute(q)
            except Exception as e:
                print('Something went wrong while Deleting data from ', strDisp, "database\n", e)
            else:
                dbConnection.commit()
                dbConnection.close()
        else:
            if option == "-pub":
                q1 = """DELETE FROM pub WHERE path=?"""
                q2 = """DELETE FROM pub WHERE name=?"""
                q3 = """DELETE FROM pub WHERE folder=?"""
                strDisp = 'public '
            elif option == "-pri":
                q1 = """DELETE FROM pri WHERE path=?"""
                q2 = """DELETE FROM pri WHERE name=?"""
                q3 = """DELETE FROM pri WHERE folder=?"""
                strDisp = 'private '
            else:
                return "illegalCMD"
            while i < len(r):
                pS = r[i]
                i += 1
                if os.path.isdir(pS):
                    fileList = os.listdir(pS)
                    for k in fileList:
                        r.append(os.path.abspath(pS) + "\\" + k)
                    continue
                dbConnection = sqlite3.connect(self.path)
                db = dbConnection.cursor()
                try:
                    db.execute(q1, (pS,))
                    (_, pS2) = os.path.split(pS)
                    db.execute(q2, (pS2,))
                    db.execute(q3, (pS,))
                except Exception as e:
                    print('Something went wrong while retrieving data from ', strDisp, "database\n", e)
                else:
                    dbConnection.commit()
                    dbConnection.close()

    def __handleSHOWF__(self, r):
        option = r[0]
        i = 1
        if len(r) == 1:
            if option == "-pub":
                q = """SELECT * FROM pub"""
                strDisp = 'public '
            elif option == "-pri":
                q = """SELECT * FROM pri"""
                strDisp = 'private '
            else:
                print("Illegal Command")
                return "illegalCMD"
            dbConnection = sqlite3.connect(self.path)
            db = dbConnection.cursor()
            try:
                db.execute(q)
                res = db.fetchall()
                if len(res) != 0:
                    for row in res:
                        print(row[0], ": ", row[1], " Parent Folder: ", row[2])
            except Exception as e:
                print('Something went wrong while retrieving data from ', strDisp, "database\n", e)
            else:
                dbConnection.commit()
                dbConnection.close()
        else:
            if option == "-pub":
                q1 = """SELECT * FROM pub WHERE path=?"""
                q2 = """SELECT * FROM pub WHERE name=?"""
                q3 = """SELECT * FROM pub WHERE folder=?"""
                strDisp = 'public '
            elif option == "-pri":
                q1 = """SELECT * FROM pri WHERE path=?"""
                q2 = """SELECT * FROM pri WHERE name=?"""
                q3 = """SELECT * FROM pri WHERE folder=?"""
                strDisp = 'private '
            else:
                return "illegalCMD"
            while i < len(r):
                pS = r[i]
                i += 1
                if os.path.isdir(pS):
                    fileList = os.listdir(pS)
                    for k in fileList:
                        r.append(os.path.abspath(pS) + "\\" + k)
                    continue
                dbConnection = sqlite3.connect(self.path)
                db = dbConnection.cursor()
                try:
                    db.execute(q1, (pS,))
                    res1 = db.fetchall()
                    (_, pS2) = os.path.split(pS)
                    db.execute(q2, (pS2,))
                    res2 = db.fetchall()
                    db.execute(q3, (pS,))
                    res3 = db.fetchall()

                    if len(res1) != 0:
                        for row in res1:
                            print(row[0], ": ", row[1], " Parent Folder: ", row[2])
                    elif len(res2) != 0:
                        for row in res2:
                            print(row[0], ": ", row[1], " Parent Folder: ", row[2])
                    elif len(res3) != 0:
                        for row in res3:
                            print(row[0], ": ", row[1], " Parent Folder: ", row[2])
                            r.append(os.path.split(row[1])[0])
                    else:
                        print(pS, ": NOT in ", strDisp, "Database")
                except Exception as e:
                    print('Something went wrong while retrieving data from ', strDisp, "database\n", e)
                else:
                    dbConnection.commit()
                    dbConnection.close()

    def closeAll(self):
        self.isrunning = False
        self.UDP_th.join()
        self.udp_client_sock.close()

    def __handleUDPServer__(self):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        sock.settimeout(1)
        try:
            sock.bind((self.client_ip, self.UDP_PORT))
            print('UDP bind to port:', self.UDP_PORT)
        except Exception as e:
            print('Cant bind to UDP port\n', e)
            return
        print('UDP server: Running')
        while self.isrunning:
            try:
                data, addr = sock.recvfrom(self.BUFFER_SIZE)
            except timeout:
                continue
            else:
                data = json.loads(data.decode())
                print("Received\n", data, '\n', addr)
                if data['type'] == 'request':
                    self.__packethandleREQUEST__(data)
                elif data['type'] == 'info':
                    self.__packethandleINFO__(data)
                elif data['type'] == 'response':
                    with self.lock:
                        if not (data['dest'][0] == self.mac and self.requiredResponse == True):
                            continue
                        else:
                            self.gotResponse += 1

                    print('YEAH!!!')
                    self.__packethandleRESPONSE__(data)
                else:
                    continue
        print("UDP server: Stopping ")
        sock.close()

    def __packethandleREQUEST__(self, data):
        dbConnection = sqlite3.connect(self.path)
        db = dbConnection.cursor()
        info = []
        if data['sub_type'] == 'file_request':
            print('FILE REQUEST')
            for fn in data['files']:
                q = "SELECT * FROM pub WHERE name = ?"

                db.execute(q, (fn,))
                r = db.fetchall()

                if len(r) != 0:
                    for rows in r:
                        info.append(rows)
        if len(info) != 0:
            self.udp_client_sock.sendto(
                self.__makePacket__(type='response', sub_type='file_response', info=info,
                                    files=[], dest=data['source']), (data['source'][1], self.UDP_PORT)
            )

    def __packethandleRESPONSE__(self, data):
        with self.lock:
            if not (data['dest'][0] == self.mac and self.requiredResponse):
                return


        print("Response handle")

    def __packethandleINFO__(self, data):
        print("Info handle")

    def handleUDPClient(self,UDP_RESPONSE_TIME, UDP_RESPONSE_ATTEMPTS, UDP_RESPONSE_DELTA):
        self.udp_client_sock.sendto('Test1'.encode(), ("255.255.255.255", self.UDP_PORT))

    def __makePacket__(self, type, sub_type, info, files, dest):
        d = {'source': (self.mac, self.client_ip, self.alias), 'type': type, 'sub_type': sub_type,
             'info': info, 'files': files, 'dest': dest}
        return json.dumps(d).encode()
