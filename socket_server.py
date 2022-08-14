import base64
import hashlib
import socket
import threading


        

class SocketEx:
    GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    UPGRADE_RESP = "HTTP/1.1 101 Switching Protocols\r\n" + \
        "Upgrade: websocket\r\n" + \
        "Connection: Upgrade\r\n" + \
        "Sec-WebSocket-Accept: %s\r\n" + \
        "\r\n"
    UNAUTHORIZED_RESP = "HTTP/1.1 401 Unauthorized"+\
        "Content-Type: text/html"
    
    connectedUsers = []
    iterator = 1


    def handleConnection(self, conn, addr):
        print("")
        print('Connected to: ' + addr[0] + ':' + str(addr[1]))
        #The HTTP 101 response required to complete the handshake is returned
        self.endHandshake(conn)
       
        print("Handshake Finished: "+str(addr[1]))
        print("")
        print("")

        #sleep(1)
        self.sendData(conn,"Welcome")
        # socket listen forever.
        while True:
            # data is received
            data = self.recvData(conn)
            if data:
                print("received from: "+addr[0] +
                    " / received data: [%s]" % (data))
                # data is sent
                data = "Your Message:"+data
                self.sendData(conn,data)
        

    def sendData(self, conn, data):
        # veri WebSocket çerçevesine göre ayarlanır ve gönderilir.
        # 1st byte: fin bit set. text frame bits set.
        # 2nd byte: no mask. length set in 1 byte.
        resp = bytearray([0b10000001, len(data)])
        # append the data bytes
        for d in bytearray(data.encode('utf-8')):
            resp.append(d)

        conn.send(resp)

    def recvData(self, conn):
        data = bytearray(conn.recv(10240))
        if data:
            # Incoming data is parsed according to the websocket frame structure.
            assert(0x1 == (0xFF & data[0]) >> 7)
            # data must be a text frame
            # 0x8 (close connection) is handled with assertion failure
            assert(0x1 == (0xF & data[0]))

            # assert that data is masked
            assert(0x1 == (0xFF & data[1]) >> 7)
            datalen = (0x7F & data[1])
            stringData = ''
            if(datalen > 0):
                # The masked data is parsed.
                mask_key = data[2:6]
                masked_data = data[6:(6+datalen)]
                unmasked_data = [masked_data[i] ^ mask_key[i % 4]
                                 for i in range(len(masked_data))]
                stringData = bytearray(unmasked_data)
            return stringData.decode()
        return ""

    def endHandshake(self, conn):
        data = conn.recv(1024)
        data = data.decode('utf-8')
        #HTTP headers in the incoming request are parsed
        headers = self.splitHeaders(data)
    
        # Response with value "Sec-WebSocket-Accept"
        respData = self.calcSecWebSocketAccept(headers["Sec-WebSocket-Key"])
        # response sent over socket
        print(respData)
        conn.send(str.encode(respData))

 


    def calcSecWebSocketAccept(self, key):
        key = key + self.GUID
        # The value from the request is combined with the GUID to get the sha1 hash. Converted to hex and base64 encoded
        respKey = base64.standard_b64encode(
            hashlib.sha1(key.encode('utf-8')).digest())
        respData = self.UPGRADE_RESP % respKey.decode('utf-8')
        return respData

    def splitHeaders(self, data):
        # Headings are split line by line
        headers = data.split("\r\n")
        headerDict = {}
        for h in headers:
            # each line is parsed by ":"
            parseHeader = h.split(":")
            if len(parseHeader) > 1:
                headerDict[str(parseHeader[0]).strip()] = str(
                    parseHeader[1]).strip()
        return headerDict

 

    def startServer(self, host, port):
        # server is up
        serverSocket = socket.socket()
        serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            serverSocket.bind((host, port))
        except socket.error as e:
            print(str(e))
        print(f'Server is listing on the port {port}...')
        # up to 10 connections are received
        serverSocket.listen(10)
        while True:
            #request accepted
            conn, addr = serverSocket.accept()
            # accepted request is sent to handleConnection function in a thread
            threading.Thread(target=self.handleConnection,
                             args=(conn, addr)).start()





sc = SocketEx()
sc.startServer('127.0.0.1', 8585)
