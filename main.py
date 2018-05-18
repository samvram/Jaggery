from clientGeneric import GenericClient

if __name__ == '__main__':
    d = dict()
    f = open("c.config", 'rb')
    rq = ['Transmission_Port', 'Listen_Conn_No', 'Server_IP', 'Buffer_size'
          'Server_Port']  # list of all the configuration parameters to be present in s.config
    lines = f.readlines()
    for l in lines:
        l = l.decode()
        if l[0] == "#":
            l = ((l[1:]).strip()).replace(':', '')
            words = l.split(' ')
            d[words[0].strip()] = words[1].strip()
    print('Server IP : '+d['Server_IP']+'\n')
    print('Server Port : '+d['Server_Port']+'\n')
    sam = GenericClient(alias='new_user', serverIP=d['Server_IP'], serverPort=int(d['Server_Port']), transmissionPort=int(d['Transmission_Port']),
                        buffer_size=int(d['Buffer_size']))
    sam.run_time()
