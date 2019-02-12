from socket import *
import threading
import sqlite3
import json
import logging

class Server:

    def __init__(self):
        self.initLogger()
        logger = logging.getLogger('Server')
        logger.info("-----------------------------------")
        logger.info("STARTING SERVER")
        d = self.readConfig()
        self.BUFFERSIZE = int(d['Buffer_Size'])
        self.serverSoc = socket(AF_INET, SOCK_STREAM)
        self.port = int(d['Server_Port'])
        self.serverSoc.bind((d['Server_IP'], self.port))
        self.listenConn = d['Listen_Conn_No']
        self.thread = []
        logger.info("Initialization Over")

        # self.createTable()
    def initLogger(self):
        logger = logging.getLogger('Server')
        hdlr = logging.FileHandler('server_logs.log')
        formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(name)s - %(levelname)s -> %(message)s',"%Y-%m-%d %H:%M:%S")
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging.DEBUG)


    def readConfig(self):
        logger = logging.getLogger('Server.readConfig')
        logger.info('Reading Config file')
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
                logger.error("Invalid 's.config' file: '%s' parameter is missing" % r)
                isExit = True

        if isExit:
            logger.info("Exiting Server")
            exit(0)
        logger.info("Config file has been successfully read")
        return d

    def createTable(self):
        logger = logging.getLogger('Server.createTable')

        dbConnection = sqlite3.connect('netProj.db')
        db = dbConnection.cursor()
        logger.info('Connected to Database')
        q = """
        CREATE TABLE onlines (
        alias VARCHAR(100) PRIMARY KEY UNIQUE, 
        ip VARCHAR(100), 
        status INTEGER,
        mac INTEGER UNIQUE);"""
        db.execute(q)

        dbConnection.commit()
        dbConnection.close()
        logger.info('Table created and disconnected from Database')
        print('Table created')

    def start(self):
        logger = logging.getLogger('Server.start')
        print("Starting server at port " + str(self.port))
        logger.info("Starting server at port " + str(self.port))
        listenThread = threading.Thread(target=self.listen(), args=())
        listenThread.setName('Listening_Thread')
        listenThread.start()
        self.thread.append(listenThread)
        logger.info("%s added to threads array " % listenThread.getName())

    def listen(self):
        logger = logging.getLogger('Server.listen')
        while True:
            self.serverSoc.listen(10)
            print("listening")
            logger.info("Listening for clients")
            connection, address = self.serverSoc.accept()
            print("Connected to ", address)
            logger.info("Connected to " + str(address))
            client_thread = threading.Thread(target=self.clientHandle, args=(connection, address,))
            client_thread.setName(str(address[0])+"_Thread")
            self.thread.append(client_thread)
            client_thread.start()

    def clientHandle(self, conn, addr):
        logger = logging.getLogger('Server.clientHandle')
        recData = conn.recv(self.BUFFERSIZE).decode()
        mac = json.loads(recData)

        dbConnection = sqlite3.connect('netProj.db')
        db = dbConnection.cursor()

        logger.info('Fetching information of  '+str(addr)+' having MAC: ' + str(mac))
        q = """SELECT * FROM onlines WHERE mac=?"""
        db.execute(q, (mac,))

        r = db.fetchall()

        dbConnection.commit()
        dbConnection.close()

        if len(r) == 0:
            conn.send("not_reg".encode())
            logger.info('User '+str(addr)+' having MAC: '+str(mac)+' NOT registered')
        else:
            d = r[0]
            d1 = json.dumps(d[0])
            conn.send(d1.encode())
            print("Alias sent")
            logger.info('Alias %s has been sent' % d[0])

            dbConnection = sqlite3.connect('netProj.db')
            db = dbConnection.cursor()

            logger.info('Connected to Database to set status 1')
            q = """UPDATE onlines SET status=? WHERE mac=?"""
            db.execute(q, (1, mac,))

            dbConnection.commit()
            dbConnection.close()

            dbConnection = sqlite3.connect('netProj.db')
            db = dbConnection.cursor()
            logger.info('Status set to 1 and database disconnected')

            logger.info('Connected to Database to update IP address')
            q = """UPDATE onlines SET ip=? WHERE mac=?"""
            db.execute(q, (addr[0], mac,))

            dbConnection.commit()
            dbConnection.close()
            logger.info('IP address updated and database disconnected')
            print("Setting status to 1")


        while True:
            print("Waiting for client")
            logger.info('Waiting for message from client')
            try:
                recData = conn.recv(self.BUFFERSIZE)
            except timeout:
                print("Timeout of client")
                logger.exception('Timeout')
                continue
            except:
                print("Client disconnected")
                logger.exception('Client Disconnected')
                break
            print("Got data from client %s" % str(recData))
            logger.info('Client sent: %s' % str(recData))
            recData = recData.strip()
            if len(recData) == 0:
                break
            recData = recData.decode()

            cmd = recData[:recData.index(' ')]
            opData = recData[recData.index(' ') + 1:]
            conn.send(self.handleCommand(cmd, opData, mac, addr))
        print('Closing Connection')
        logger.info('Closing Connection')
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
            logger.info('Status set to 0')
            print("Setting status to 0")
        conn.close()
        print('Database and TCP Connection Closed')
        logger.info('Database closed')

    def handleCommand(self, cmd, opData, mac, addr):
        logger = logging.getLogger('Server.handleCommand')
        opData = opData.strip()
        if cmd == 'alias':
            logger.info('Asked for Alias')
            return self.handleALIAS(opData, addr, mac)
        elif cmd == 'isonline':
            logger.info('Asked for isonline')
            return self.handleISONLINE(opData)
        elif cmd == 'search':
            logger.info('Asked for search')
            print('search')
        else:
            logger.info('Unkonwn command 301')
            return  json.dumps('301').encode()

    def handleALIAS(self, opData, addr, mac):
        logger = logging.getLogger('Server.handleALIAS')
        ip = addr[0]
        words = opData.split(' ')
        if len(words) == 1:

            dbConnection = sqlite3.connect('netProj.db')
            db = dbConnection.cursor()

            q = """SELECT * FROM onlines WHERE alias=?"""
            db.execute(q, (opData,))
            r = db.fetchall()

            dbConnection.commit()
            dbConnection.close()

            if not len(r) == 0:
                res = r[0]
                if not res[3] == mac:
                    logger.info("New alias already exist")
                    return json.dumps('not success').encode()


            dbConnection = sqlite3.connect('netProj.db')
            db = dbConnection.cursor()

            q = """REPLACE INTO onlines (alias, ip, status, mac) VALUES (?, ?, ?, ?)"""
            db.execute(q, (opData, ip, 1, mac,))

            dbConnection.commit()
            dbConnection.close()
            # conn.send('success'.encode())
            logger.info("Alias changed")
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
        logger = logging.getLogger('Server.handleISONLINE')
        d = dict()
        words = opData.split(' ')

        if len(words) == 1:
            if words[0] == '-all':
                logger.info('-all requested')
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
                logger.info('-a requested: %s' % params)
                q = """SELECT * FROM onlines WHERE alias=?"""
            elif words[0] == '-ip':
                logger.info('-ip requested: %s' % params)
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
        logger.info('Data sent')
        print('Data Sent')
        return tosend.encode()


if __name__ == '__main__':
    s = Server()
    s.start()
    for t in s.thread:
        t.join()
