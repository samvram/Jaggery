from clientGeneric import GenericClient

if __name__ == '__main__':
    server_IP  = '127.0.0.1'
    server_port = 5000
    d = dict()
    f = open("c.config", 'rb')
    rq = ['Transmission_Port', 'Listen_Conn_No', 'Server_IP',
          'Server_Port']  # list of all the configuration parameters to be present in s.config
    lines = f.readlines()
    for l in lines:
        l = l.decode()
        if l[0] == "#":
            l = ((l[1:]).strip()).replace(':', '')
            words = l.split(' ')
            d[words[0].strip()] = words[1].strip()
    # server_IP = input('Enter the Server IP : \n')
    print('Server IP : '+d['Server_IP']+'\n')
    print('Server Port : '+d['Server_Port']+'\n')
    sam = GenericClient(alias='new_user', serverIP=d['Server_IP'], serverPort=int(d['Server_Port']), transmissionPort=int(d['Transmission_Port']))
    sam.run_time()
