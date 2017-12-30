#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import socketserver
import sys
import uaclient


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
            self.wfile.write(b"SIP/2.0 100 Trying\r\n\r\n")
            self.wfile.write(b"SIP/2.0 180 Ringing\r\n\r\n")
            self.wfile.write(b"SIP/2.0 200 OK\r\n" +
                             b'Content-Type: application/sdp\r\n\r\n' +
                             b'v=0\r\n' + b'o=' + bytes(USER, 'utf-8') +
                             b' 127.0.0.1\r\n' + b's=misesion\r\n' +
                             b't=0\r\n' + b'm=audio ' +
                             bytes(datos[2]['puerto'], 'utf-8') +
                             b' RTP\r\n')
        elif DATA[0].split(' ')[0] == 'ACK':
            print('Recibido ACK')
            audio = datos[5]['path']
            order = "./mp32rtp -i " + self.ClientIP + " -p " + self.ClientRTPPort + " < " + audio
        elif DATA[0].split(' ')[0] == 'BYE':
            print('Recibido bye')
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")

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
