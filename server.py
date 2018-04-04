from socket import *
import threading
import sqlite3
import json

class Server:

    def __init__(self):
        d = self.readConfig()
        self.BUFFERSIZE = int(d['Buffer_Size'])
        self.serverSoc = socket(AF_INET, SOCK_STREAM)
        self.port = int(d['Server_Port'])
        self.serverSoc.bind((d['Server_IP'], self.port))
        self.listenConn = d['Listen_Conn_No']

        self.thread = []

        # self.createTable()

    def readConfig(self):
        d = dict()
        f = open("s.config", 'rb')
        rq = ['Buffer_Size', 'Server_Port', 'Server_IP', 'Listen_Conn_No'] # list of all the configuration parameters to be present in s.config
        lines = f.readlines()
        for l in lines:
            l = l.decode()
            if l[0] == "#":
                l = ((l[1:]).strip()).replace(':', '')
                words = l.split(' ')
                d[words[0].strip()] = words[1].strip()
        isExit = False
        for r in rq:
            if r not in d:
                print("Invalid 's.config' file: '%s' parameter is missing" % r)
                isExit = True

        if isExit:
            exit(0)
        return d

    def createTable(self):
        dbConnection = sqlite3.connect('netProj.db')
        db = dbConnection.cursor()

        q = """
        CREATE TABLE onlines (
        alias VARCHAR(100) PRIMARY KEY UNIQUE, 
        ip VARCHAR(100), 
        status INTEGER,
        mac INTEGER UNIQUE);"""
        db.execute(q)

        dbConnection.commit()
        dbConnection.close()
        print('Table created')

    def start(self):
        print("Starting server at port " + str(self.port))
        listenThread = threading.Thread(target=self.listen(), args=())
        listenThread.start()
        self.thread.append(listenThread)

    def listen(self):
        while True:
            self.serverSoc.listen(10)
            print("listening")
            connection, address = self.serverSoc.accept()
            print("Connected to ", address)
            client_thread = threading.Thread(target=self.clientHandle, args=(connection, address,))

            self.thread.append(client_thread)
            client_thread.start()

    def clientHandle(self, conn, addr):
        recData = conn.recv(self.BUFFERSIZE).decode()
        mac = json.loads(recData)

        dbConnection = sqlite3.connect('netProj.db')
        db = dbConnection.cursor()

        q = """SELECT * FROM onlines WHERE mac=?"""
        db.execute(q, (mac,))

        r = db.fetchall()

        dbConnection.commit()
        dbConnection.close()

        if len(r) == 0:
            conn.send("not_reg".encode())
        else:
            d = r[0]
            d1 = json.dumps(d[0])
            conn.send(d1.encode())
            print("Alias sent")

            dbConnection = sqlite3.connect('netProj.db')
            db = dbConnection.cursor()

            q = """UPDATE onlines SET status=? WHERE mac=?"""
            db.execute(q, (1, mac,))

            dbConnection.commit()
            dbConnection.close()

            dbConnection = sqlite3.connect('netProj.db')
            db = dbConnection.cursor()

            q = """UPDATE onlines SET ip=? WHERE mac=?"""
            db.execute(q, (addr[0], mac,))

            dbConnection.commit()
            dbConnection.close()

            print("Setting status to 1")


        while True:
            print("Listening for client")
            try:
                recData = conn.recv(self.BUFFERSIZE)
            except timeout:
                print("Timeout of client")
                continue
            except:
                print("Client disconnected")
                break
            print("Got data from client %s")
            recData = recData.strip()
            if len(recData) == 0:
                break
            recData = recData.decode()

            cmd = recData[:recData.index(' ')]
            opData = recData[recData.index(' ') + 1:]
            conn.send(self.handleCommand(cmd, opData, mac, addr))

        print('Closing Connection')
        dbConnection = sqlite3.connect('netProj.db')
        db = dbConnection.cursor()

        q = """SELECT * FROM onlines WHERE mac=?"""
        db.execute(q, (mac,))
        r = db.fetchall()

        dbConnection.commit()
        dbConnection.close()
        if len(r) == 0:
            print('Unknown client')
        else:

            dbConnection = sqlite3.connect('netProj.db')
            db = dbConnection.cursor()

            q = """UPDATE onlines SET status=? WHERE mac=?"""
            db.execute(q, (0, mac,))

            dbConnection.commit()
            dbConnection.close()
            print("Setting status to 0")


        conn.close()
        print('Database and TCP Connection Closed')

    def handleCommand(self, cmd, opData, mac, addr):
        opData = opData.strip()
        if cmd == 'alias':
            return self.handleALIAS(opData, addr, mac)
        elif cmd == 'isonline':
            return self.handleISONLINE(opData)
        elif cmd == 'search':
            print('search')
        else:
            return  json.dumps('301').encode()

    def handleALIAS(self, opData, addr, mac):
        ip = addr[0]
        words = opData.split(' ')
        if len(words) == 1:

            dbConnection = sqlite3.connect('netProj.db')
            db = dbConnection.cursor()

            q = """REPLACE INTO onlines (alias, ip, status, mac) VALUES (?, ?, ?, ?)"""
            db.execute(q, (opData, ip, 1, mac))

            dbConnection.commit()
            dbConnection.close()
            # conn.send('success'.encode())
            print('success')
            return json.dumps('success').encode()
        elif len(words) == 2:
            option = words[0]
            if option == '-rm':
                a = words[1]
                dbConnection = sqlite3.connect('netProj.db')
                db = dbConnection.cursor()

                q = """DELETE FROM onlines WHERE alias = ?"""
                db.execute(q, (a,))

                dbConnection.commit()
                dbConnection.close()

                return json.dumps('deleted').encode()
            else:
                return json.dumps('undefined_cmd').encode()
        else:
            if len(words) == 0:
                return json.dumps('303').encode()
            else:
                return json.dumps('304').encode()



    def handleISONLINE(self, opData):
        d = dict()
        words = opData.split(' ')

        if len(words) == 1:
            if words[0] == '-all':
                dbConnection = sqlite3.connect('netProj.db')
                db = dbConnection.cursor()

                q = """SELECT * FROM onlines"""
                db.execute(q)
                r = db.fetchall()

                dbConnection.commit()
                dbConnection.close()
                if len(r) != 0:
                    for row in r:
                        d[row[0]] = (row[1], row[2])
                else:
                    d['no_no_no'] = ('0.0.0.0', '0')
            else:
                return json.dumps('302').encode()
        elif len(words) >= 2:
            params = words[1:]
            if words[0] == '-a':
                q = """SELECT * FROM onlines WHERE alias=?"""
            elif words[0] == '-ip':
                q = """SELECT * FROM onlines WHERE ip=?"""
            else:
                return json.dumps('302').encode()
            for data in params:
                dbConnection = sqlite3.connect('netProj.db')
                db = dbConnection.cursor()

                db.execute(q, (data,))
                r = db.fetchall()

                dbConnection.commit()
                dbConnection.close()
                if len(r) != 0:
                    row = r[0]
                    d[row[0]] = (row[1], row[2])
                else:
                    d[data] = ('0.0.0.0', '0')

        tosend = json.dumps(d)
        print('Data Sent')
        return tosend.encode()


if __name__ == '__main__':
    s = Server()
    s.start()
    for t in s.thread:
        t.join()
