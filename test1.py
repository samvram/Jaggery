from socket import *
from fileHandle import *
import json
import uuid

BufferSIZE = 1024

if __name__ == '__main__':
    print('Trying to connect to: 172.20.10.39 on port: 5000')

    soc = socket(AF_INET, SOCK_STREAM)

    # F = fileHandle()
    # F.createDB()
    # F.handleCMD("add -pub E:\\I2C_trial\\I2C_trial.prjx")
    # F.handleCMD("add -pub E:\\I2C_trial\\")
    # soc.connect(("172.20.10.39", 5000))
    soc.connect(("localhost", 5000))

    alias = uuid.getnode()
    soc.send(json.dumps(alias).encode())
    k = (soc.recv(BufferSIZE)).decode()
    print(k)


    alias = "alias avatar1"
    soc.send(alias.encode())
    k = (soc.recv(BufferSIZE)).decode()
    print(k)

    alias = "alias avatar2"
    soc.send(alias.encode())
    k = (soc.recv(BufferSIZE)).decode()
    print(k)

    alias = "alias avatar3"
    soc.send(alias.encode())
    k = (soc.recv(BufferSIZE)).decode()
    print(k)

    alias = "alias avatar4"
    soc.send(alias.encode())
    k = (soc.recv(BufferSIZE)).decode()
    print(k)

    alias = "alias avatar5"
    soc.send(alias.encode())
    k = (soc.recv(BufferSIZE)).decode()
    print(k)

    # alias = "alias -rm avatar5"
    # soc.send(alias.encode())
    # k = (soc.recv(BufferSIZE)).decode()
    # print(k)

    alias = "isonline -ip 127.0.0.1 127.1.0.1"

    soc.send(alias.encode())
    k = (soc.recv(BufferSIZE)).decode()
    data = json.loads(k)
    print(data)

    alias = "isonline -a sam avatar5"

    soc.send(alias.encode())
    k = (soc.recv(BufferSIZE)).decode()
    data = json.loads(k)
    print(data)

    soc.close()


