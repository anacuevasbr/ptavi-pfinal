#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import os
import socketserver
import sys
import uaclient


def AddtoLog(path, message, Action):

    f = open(path, "a")
    Entra = False
    if Action == 'Receive':
        Message = str(time.time())+ ' Receive ' + message.replace('\r\n', ' ') + '\r\n'
        Entra = True
    elif Action == 'Send':
        Message = str(time.time())+ ' Send ' + message.replace('\r\n', ' ') + '\r\n'
        Entra = True
    if Entra:
        f.write(Message) 
    
class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    ClientIP = ''
    ClientRTPPort = ''

    def SafeRTPData(self, DATA):

        ClientIP = DATA[4].split(' ')[1]
        ClientRTPPort = DATA[7].split(' ')[1]

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        DATA = []
        datos = uaclient.parsercreator(sys.argv[1])
        USER = datos[0]['username']

        for line in self.rfile:
            DATA.append(line.decode('utf-8'))
        print(DATA)

        if DATA[0].split(' ')[0] == 'INVITE':
            self.SafeRTPData(DATA)
            print('Respondiendo a invite')
            Message = ' '.join(DATA)
            AddtoLog(datos[4]['path'], Message, 'Receive')
            
            self.wfile.write(b"SIP/2.0 100 Trying\r\n\r\n")
            Message = 'SIP/2.0 100 Trying\r\n'
            AddtoLog(datos[4]['path'], Message, 'Send')
            
            self.wfile.write(b"SIP/2.0 180 Ringing\r\n\r\n")
            Message = 'SIP/2.0 180 Ringing\r\n'
            AddtoLog(datos[4]['path'], Message, 'Send')
            
            Message = 'SIP/2.0 200 OK\r\n' + 'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n' + 'o=' + USER + ' 127.0.0.1\r\n' + 's=misesion\r\n' + 't=0\r\n' + 'm=audio ' + datos[2]['puerto'] + ' RTP\r\n'
            self.wfile.write(bytes(Message, 'utf-8'))
            AddtoLog(datos[4]['path'], Message, 'Send')
            
        elif DATA[0].split(' ')[0] == 'ACK':
            print('Recibido ACK')
            Message = ' '.join(DATA)
            AddtoLog(datos[4]['path'], Message, 'Receive')
            audio = datos[5]['path']
            order = "./mp32rtp -i " + self.ClientIP + " -p " + self.ClientRTPPort + " < " + audio
        elif DATA[0].split(' ')[0] == 'BYE':
            print('Recibido bye')
            Message = ' '.join(DATA)
            AddtoLog(datos[4]['path'], Message, 'Receive')

            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            Message = 'Sent SIP/2.0 200 OK\r\n'
            AddtoLog(datos[4]['path'], Message, 'Send')
 
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
