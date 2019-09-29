import os
import thread
import sys 
import socket

MAX_DATA_RECV = 10000 #max bytes received at by proxy at one time
CONNECTION_QUEUE = 30  #pending connections

def main():
    cache = {} #initiate dictionary for caching http http responses
    cache_count = 0 #number of items in cache

    url_blacklist = raw_input("Enter URLs that you would like to blacklist separated by a space: ").split(' ')
    print "BLACKLISTED: ", url_blacklist

    if (sys.argv[1]): #no argument given for port number
        port = int(sys.argv[1]) #use argument as port number  
    else:
        print "Port not specified!" 
        sys.exit(1) #exit if no port specified
    
    host = 'localhost' #localhost
    print ":: A proxy server has been set up :: \n",host,":",port ,"\n\n"
    try:
        sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create a socket
        sckt.bind((host, port)) #bind the socket to the specified host & port
        sckt.listen(CONNECTION_QUEUE) #begin listening, accept 30 connecions
    
        while 1:
            connection, client_address = sckt.accept() #accept connection from client
            thread.start_new_thread(request_handler, (connection, client_address, cache, cache_count, url_blacklist)) #for each request create a new thread to handle that request
        sckt.close() #close the socket
    except socket.error, (value, message):
        if sckt:
            sckt.close()
        print "There was an error opening the socket: ", message
        sys.exit(1)

#request_handler() function handles requests sent from client to proxy 
def request_handler(connection, client_address, cache, cache_count, url_blacklist):
    print "\nRequest sent from client to proxy\n"
    request = connection.recv(MAX_DATA_RECV) #receive request from client

    parse_line = request.split('\n')[0] #parse first line
    #get url of client request
    if(len(parse_line)>1):    
        url = parse_line.split(' ')[1]
    else:
        url = parse_line.split(' ')[0] 

    if (not check_url(url, url_blacklist)):#check if client's request is in list of blocked urls
        connection.close()#end handling of request if url is blocked
        sys.exit(1)
    
    check_https = parse_line.split(' ')[0] #if start of request is CONNECT it is a https request
    https = False
    if(check_https == "CONNECT"):
        https = True

    #make copy of url
    http_pos = url.find("://") #start of url          
    if (http_pos==-1):
        temp = url 
    else:
        temp = url[(http_pos+3):]  

    #get webserver
    port_pos = temp.find(":") #position of port         
    webserver_pos = temp.find("/")
    if webserver_pos == -1:
        webserver_pos = len(temp)
    webserver = ""
    port = -1
    if (port_pos==-1 or webserver_pos < port_pos): # use 80 as default
        port = 80
        webserver = temp[:webserver_pos]
    else:       
        port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = temp[:port_pos]
    
    #distinguish type of request
    if https:
        https_connection(connection, webserver, port,url) #handle https request

    else: #handle http request
        try:
            sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #create new socket 
            sckt.connect((webserver, port)) #connect to webserver
            sckt.send(request) #send client's request to webserver
            dashboard(https, url, 1,0)
            
            #check is request is already in cache
            if request in cache :
                #print "CACHE HIT"
                data = cache[request] #get data from cache
                if (len(data) > 0): 
                    connection.send(data) #send data back to client
                    dashboard(https, url, 0,1)

            else:
                sckt.send(request) #send client's request to webserver
                while 1:
                    data = sckt.recv(MAX_DATA_RECV) #receive data from webserver
                    if (len(data) > 0):
                        connection.send(data) #send data back to client 
                        cache[request]=data #store data in cache for later use
                        cache_count= cache_count+1 
                        if(cache_count<20): #check if cache has reached capacity
                            empty_cache(cache) #empty if full
                        dashboard(https, url, 0,0)
                    else:
                        break
            sckt.close() #close socket
            connection.close() #close connection)
            sys.exit(1)
        except socket.error, (value, message):
            if sckt:
                sckt.close()
            if connection:
                connection.close()
            
        sys.exit(1)
        
def https_connection(connection, webserver, port, url):
    https = True; #for printing to console
    sckt = socket.socket()
    try:
        #resond to https request
        https_response  = "HTTP/1.0 200 Connection Established\r\n"
        https_response += "Connection: close\r\n"
        https_response += "Proxy-agent: Pyx\r\n"
        https_response += "\r\n"
        https_response += "\r\n" 
        #set up connection    
        connection.send(https_response.encode())
        sckt.connect((webserver, port))

    except socket.error as error:
        print(error)

    client_comms_open = 1 #communication between client and proxy
    server_comms_open = 1 #communication between proxy and server

    #turn off blocking mode on both ends
    connection.setblocking(0)
    sckt.setblocking(0)

    #keep communications open between proxy and webserver for https 
    while client_comms_open and server_comms_open:
        try:
            client_data = connection.recv(MAX_DATA_RECV) #get request from client 

            if(len(client_data)>0):
                client_comms_open = 1
                sckt.send(client_data) #send request to webserver
                dashboard(https,url, 1,0) #print to console
                
            else:
                client_comms_open = 0
        except socket.error:
            pass
        try:
            server_data = sckt.recv(MAX_DATA_RECV) #retrieve response from webserver

            if(len(server_data)> 0):
                server_comms_open = 1
                connection.send(server_data) #sent response back to client 
                dashboard(https,url, 0,0) #print to console

            else:
                server_comms_open = 0
        except socket.error:
            pass

    connection.close() #close connection between proxy and client 
    sckt.close() # close connection between proxy and web server

def check_url(url, url_blacklist):
    for i in range(0,len(url_blacklist)):
        if url_blacklist[i] in url:
            print ":: This URL is Blacklisted, request not sent ::\nURL: ",url_blacklist[i], "\n\n"
            return False
        else: return True

#empty_cache() function deletes everything from the cache once it reaches a capacity of 50 entries
def empty_cache(cache):
    cache={}
    cache_count=0

def dashboard(https, url, dir, cache):
    type = "HTTP"
    if https:
        type = "HTTPS"
        if dir == 1:
            print "::HTTPS request sent::\nType: ", type, "\nURL: ", url, "\n\n"
        else:
            print "::HTTPS response received::\nType: ", type, "\nURL: ", url, "\n\n"
    else:
        if cache:
            if dir == 1:
                print "::HTTP request sent::\nType: ", type, "\nURL: ", url, "\n\n"
            else:
                print "::   CACHE HIT   ::\nType: ", type, "\nURL: ", url, "\n\n"
        else:
            if dir == 1:
                print "::HTTP request sent::\nType: ", type, "\nURL: ", url, "\n\n"
            else:
                print "::HTTP response received::\nType: ", type, "\nURL: ", url, "\n\n"

if __name__ == '__main__':
    main()