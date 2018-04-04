import sqlite3
import os
from pathlib import Path
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
        self.a = 5
        path = 'fileData.db'
        self.dbConnection = sqlite3.connect(path)
        self.db = self.dbConnection.cursor()

    def createDB(self):
        q = """
                CREATE TABLE pub(
                Name VARCHAR(100) , 
                Path VARCHAR(100) PRIMARY KEY UNIQUE,
                TYPE INTEGER
                );"""
        self.db.execute(q)
        self.dbConnection.commit()
        print('pub Table created')

        q = """
                CREATE TABLE pri(
                Name VARCHAR(100) , 
                Path VARCHAR(100) PRIMARY KEY UNIQUE,
                TYPE INTEGER,
                mac INTEGER
                );"""
        self.db.execute(q)
        self.dbConnection.commit()
        print('pub Table created')

    def handleCMD(self, recData):
        recData = recData.lstrip()
        recData = recData.rstrip()
        index = self.getindex(recData, ' ')
        if index >0:
            cmd = recData[:index]
            opData = recData[index+1:]

            if cmd == "add":
                self.__handleADD__(opData)
            elif cmd == "get":
                self.__handleGET__(opData)
            elif cmd == "rm":
                self.__handleRM__(opData)
        else:
            return "illegalCMD"

    def __handleADD__(self, opData):
        opData = (opData.lstrip()).rstrip()
        index = self.getindex(opData, ' ')
        if index > 0:
            option = opData[:index]
            pS = opData[index + 1:]
            p = Path(pS)
            name = pS[pS.rfind('\\')+1:]
            if p.is_dir():
                type = 1
            elif p.is_file():
                type = 0
            else:
                return 'fdir_not_exist'
            if option == "-pub":
                q = """REPLACE INTO pub (name, path, type) VALUES (?, ?, ?)"""
                try:
                    self.db.execute(q, (name, pS, type))
                except:
                    print('Something Went Wrong')

            elif option == "-pri":
                q = """REPLACE INTO pri (name, path, type)"""
                try:
                    self.db.execute(q, (name, pS, type))
                except:
                    print('Something Went Wrong')
            else:
                return "illegalCMD"
        else:
            return "illegalCMD"

    def __handleGET__(self, opData):
        return 1

    def __handleRM__(self, opData):
        return 1

    def getindex(self, str, indexOf):
        try:
            return str.index(indexOf)
        except:
            return -1