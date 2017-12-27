#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socketserver
import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class Proxyxmlhandler(ContentHandler):

    def __init__(self):
        """
        Constructor. Inicializamos las variables
        """
        self.etiquetas = []
        self.lista_etiq = ["server", "database", "log"]
        self.coleccion_attr = {'server': ['name','ip', 'puerto'],
                               'database': ['path', 'passwdpath'],
                               'log': ['path']}
    def startElement(self, element, attrs):

        if element in self.lista_etiq:
            Dict = {}
            Dict['element'] = element
            for atributo in self.coleccion_attr[element]:
                Dict[atributo] = attrs.get(atributo, "")
            self.etiquetas.append(Dict)

    def get_tags(self):
        return self.etiquetas

def parsercreator(xml):
    parser = make_parser()
    proxyhandler = Proxyxmlhandler()
    parser.setContentHandler(proxyhandler)
    parser.parse(open(xml))
    return (proxyhandler.get_tags())
    
class EchoHandler(socketserver.DatagramRequestHandler):

    """
    Echo server class
    """
    Users = []

    def handle(self):
        # Escribe dirección y puerto del cliente (de tupla client_address)
        DATA = []
        NONCE = b'123456789'
        for line in self.rfile:
            DATA.append(line.decode('utf-8'))
        print(DATA)

        if DATA[0].split(' ')[0] == 'REGISTER':
            print("Entra en register")
            username = DATA[0].split(':')[1]
            print(username)
            if username in self.Users:
                print("Enviamos 200 OK y csmbismos expiración")
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            else:
                if DATA[2].split(':')[0] =='Authorization':
                    print('check nonce')
                else:
                    print('Enviamos 401 unauthorized')
                    Message = b"SIP/2.0 401 Unauthorized" + b'\r\n' + b"WWW Authenticate: Digest nonce=" + NONCE
                    self.wfile.write(Message)
                
if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 uaserver.py config')

    datos = parsercreator(sys.argv[1])
    print(datos)
    
    IP = datos[0]['ip']
    PORT = int(datos[0]['puerto'])
    serv = socketserver.UDPServer((IP, PORT), EchoHandler)
    print("Lanzando servidor UDP de eco...")
    serv.serve_forever()
