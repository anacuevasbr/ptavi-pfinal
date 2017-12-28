#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socketserver
import sys
import time
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
    DicUsers = {} #Aquí se van a guardar los usuarios, es undicconario
                  #de listas donde la clave es el
                  #nombre de usuario,  y le primer elemento de la listae es
                  #el puerto en el que escucha y el segundo su fecha de expiración
    
    def ExpiresCheck(self):
        
        Delete = []
        for User in self.DicUsers:
            if str(self.DicUsers[User][1]) <= str(time.time()):
                Delete.append(User)
        for User in Delete:
            del self.DicUsers[User]
            print('eliminado ' + User)
    
    def RegisterManager(self, Data):
    
        NONCE = b'123456789'        
        username = Data[0].split(':')[1]
        serverport = Data[0].split(':')[2].split(' ')[0]
        expires = time.time() + float(Data[1].split(' ')[1].split('\r')[0])
        
        self.ExpiresCheck()
        print(self.DicUsers)
        
        if username in self.DicUsers:
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            self.DicUsers[username][1] = expires
        else:
            if Data[2].split(':')[0] =='Authorization':
                if Data[2].split('=')[1].split('\r')[0] == NONCE.decode('utf-8'):
                    self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
                    self.DicUsers[username]=[serverport,expires]
                    print(self.DicUsers)
            else:
                Message = b"SIP/2.0 401 Unauthorized" + b'\r\n' + b"WWW Authenticate: Digest nonce=" + NONCE
                self.wfile.write(Message)
                
    def handle(self):
        
        DATA = []
        
        for line in self.rfile:
            DATA.append(line.decode('utf-8'))
        print(DATA)

        if DATA[0].split(' ')[0] == 'REGISTER':
            self.RegisterManager(DATA)

                
if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 uaserver.py config')

    datos = parsercreator(sys.argv[1])

    IP = datos[0]['ip']
    PORT = int(datos[0]['puerto'])
    serv = socketserver.UDPServer((IP, PORT), EchoHandler)
    print("Lanzando servidor UDP de eco...")
    serv.serve_forever()
