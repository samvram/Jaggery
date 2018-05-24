from clientGeneric import GenericClient

if __name__ == '__main__':
    d = dict()
    f = open("c.config", 'rb')
    # list of all the configuration parameters to be present in s.config
    rq = ['Transmission_Port', 'Listen_Conn_No', 'Server_IP', 'Buffer_size', 'Rec_thread_start',
          'Server_Port',
          'UDP_PORT', 'UDP_RESPONSE_TIME', 'UDP_RESPONSE_ATTEMPTS','UDP_RESPONSE_DELTA']

    lines = f.readlines()
    for l in lines:
        l = l.decode()
        if l[0] == "#":
            l = ((l[1:]).strip()).replace(':', '')
            words = l.split(' ')
            d[words[0].strip()] = words[1].strip()
    print('Server IP : ' + d['Server_IP'] + '\n')
    print('Server Port : ' + d['Server_Port'] + '\n')
    sam = GenericClient(alias='new_user', serverIP=d['Server_IP'], serverPort=int(d['Server_Port']),
                        transmissionPort=int(d['Transmission_Port']),
                        buffer_size=int(d['Buffer_size']), rec_thread=int(d['Rec_thread_start']))
    sam.run_time(UDP_PORT=int(d['UDP_PORT']), UDP_RESPONSE_ATTEMPTS=int(d['UDP_RESPONSE_ATTEMPTS'])
                 , UDP_RESPONSE_DELTA=int(d['UDP_RESPONSE_DELTA']), UDP_RESPONSE_TIME = int(d['UDP_RESPONSE_TIME']))
