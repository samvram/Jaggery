import sqlite3
import os

"""
Commands:
    add -pub  file_path/dir_path
    add -pri  file_path/dir_path alias/ip
    rm -pub  file_path/dir_path
    rm -pri  file_path/dir_path
    search  file_path/dir_path
"""


class fileHandle:

    def __init__(self):
        self.path = 'fileData.db'
        try:
            self.createDB()
        except:
            print('File Database is ready')

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
        dbConnection.close()
        print('pri Table created')

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
        elif cmd == "getf":
            self.__handleGETF__(r)
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

    def __handleGETF__(self, opData):
        return 1

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
