#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import os
import socketserver
import sys
import uaclient


def AddtoLog(path, message, Action):

    f = open(path, "a")
    if Action == 'Receive':
        Message = time.strftime('%Y%m%d%H%M%S',time.gmtime(time.time()))+ ' Received from ' + message.replace('\r\n', ' ') + '\r\n'
    elif Action == 'Send':
        Message = time.strftime('%Y%m%d%H%M%S',time.gmtime(time.time())) + ' Sent to ' + message.replace('\r\n', ' ') + '\r\n'
    elif Action == 'Error':
        Message = time.strftime('%Y%m%d%H%M%S',time.gmtime(time.time())) + ' Error ' + message.replace('\r\n', ' ') + '\r\n'
    f.write(Message) 
    f.close()

def Valid(message):
    
    VAL = False
    print(message.split(' ')[0])
    if message.split(' ')[0] == 'INVITE':
        Length = (len(message.split('\r\n')))>=9
        Arroba = message.split('\r\n')[4].find('@') != -1
        if Length and Arroba:
            VAL = True
    elif message.split(' ')[0] == 'ACK':
        print(len(message.split('\r\n')))
        VAL = True
    elif message.split(' ')[0] == 'BYE':
        print(len(message.split('\r\n')))
        VAL = True

    return VAL
    
class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    RTPDATA = {}

    def SafeRTPData(self, DATA):
        
        IP = DATA[4].split(' ')[1]
        self.RTPDATA['1'] = [IP[0:-1],DATA[7].split(' ')[1]]

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        DATA = []
        datos = uaclient.parsercreator(sys.argv[1])
        USER = datos[0]['username']

        for line in self.rfile:
            DATA.append(line.decode('utf-8'))

        if not Valid(''.join(DATA)):
            print('400 bad request')
        if DATA[0].split(' ')[0] == 'INVITE':
            self.SafeRTPData(DATA)
            print('Respondiendo a invite')
            Message = ' '.join(DATA)
            Client = self.client_address[0] + ':' + str(self.client_address[1]) + ' '
            Client = self.client_address[0] + ':' + str(self.client_address[1]) + ' '
            AddtoLog(datos[4]['path'], Client + Message, 'Send')
            
            self.wfile.write(b"SIP/2.0 100 Trying\r\n\r\n")
            Message = 'SIP/2.0 100 Trying\r\n'
            Client = self.client_address[0] + ':' + str(self.client_address[1]) + ' '
            AddtoLog(datos[4]['path'], Client + Message, 'Send')
            
            self.wfile.write(b"SIP/2.0 180 Ringing\r\n\r\n")
            Message = 'SIP/2.0 180 Ringing\r\n'
            Client = self.client_address[0] + ':' + str(self.client_address[1]) + ' '
            AddtoLog(datos[4]['path'], Client + Message, 'Send')
            
            Message = 'SIP/2.0 200 OK\r\n' + 'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' + 'o=' + USER + ' 127.0.0.1\r\n' + 's=hungry\r\n' + 't=0\r\n' + 'm=audio ' + datos[2]['puerto'] + ' RTP\r\n'
            self.wfile.write(bytes(Message, 'utf-8'))
            Client = self.client_address[0] + ':' + str(self.client_address[1]) + ' '
            AddtoLog(datos[4]['path'], Client + Message, 'Send')
            
        elif DATA[0].split(' ')[0] == 'ACK':
            print('Recibido ACK')
            Message = ' '.join(DATA)
            Client = self.client_address[0] + ':' + str(self.client_address[1]) + ' '
            AddtoLog(datos[4]['path'], Client + Message, 'Receive')
            audio = datos[5]['path']
            order = "./mp32rtp -i " + self.RTPDATA['1'][0] + " -p " + self.RTPDATA['1'][1] + " < " + audio
            os.system(order)
        elif DATA[0].split(' ')[0] == 'BYE':
            print('Recibido bye')
            Message = ' '.join(DATA)
            Client = self.client_address[0] + ':' + str(self.client_address[1]) + ' '
            AddtoLog(datos[4]['path'], Client + Message, 'Receive')

            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            Message = 'Sent SIP/2.0 200 OK\r\n'
            Client = self.client_address[0] + ':' + str(self.client_address[1]) + ' '
            AddtoLog(datos[4]['path'], Client + Message, 'Send')
        else:
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
            Message = "SIP/2.0 405 Method Not Allowed"
            AddtoLog(datos[4]['path'], Message, 'Error')
 
if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 uaserver.py config')

    datos = uaclient.parsercreator(sys.argv[1])
    IP = datos[1]['ip']
    if IP == '':
        IP = '127.0.0.1'
    PORT = int(datos[1]['puerto'])
    serv = socketserver.UDPServer((IP, PORT), EchoHandler)
    print("Lanzando servidor UDP de eco...")
    serv.serve_forever()
