#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socketserver
import sys
import uaclient

class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        DATA = []
        
        for line in self.rfile:
            DATA.append(line.decode('utf-8'))
        print(DATA)
        
        if DATA[0].split(' ')[0] == 'INVITE':
            print('Respondiendo a invite')
            self.wfile.write(b"SIP/2.0 100 Trying\r\n\r\n")
            self.wfile.write(b"SIP/2.0 180 Ringing\r\n\r\n")
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
        elif DATA[0].split(' ')[0] == 'ACK':
            print('Recibido ACK')

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
