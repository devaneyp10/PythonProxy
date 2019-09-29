'''
Thread function parses URL and port, then creates 
a connection to the server and sends the request and 
receives the response.
'''

def thread_create(conn, client_addr):
    request = conn.recv(DATA_RECV) #receive request
    parsed_request = request.split('n')[0]
    url = parsed_request.split(' ')[1]
    
    pos = url.find("://")
    if(pos<0):
        temp = url
    else:
        temp = url[(pos+3)]

    port_pos = temp.find(":")

    webserver_pos = temp.fin("/")
    if (webserver_pos<0):
        webserver_pos = len(temp)

    webserver = ""
    port = -1
    if(port_pos<0 or webserver_pos<port_pos):
        port = 8080
        webserver = temp[:webserver_pos]
    else:
        port = int((temp[(port_pos+1):]))[:webserver_pos - port_pos-1])
        webserver = temp[:port_pos]

    print "Connecting to : ", webserver, port

    try: 
        sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sckt.connect((webserver, port))
        sckt.send(request)         # send request to webserver

        while 1:
            data = sckt.receive(DATA_RECV)
            if(len(data)>0):
            conn.send(data)
            else:
            break
        sckt.close()
        conn.close()
    except socket.error, (value, message):
        if skct:
            s.close()
        print "Runtime error: ", message
        sys.exit(1)
    