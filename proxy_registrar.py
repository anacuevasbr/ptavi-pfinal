#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
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

        if username in self.DicUsers:
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            self.DicUsers[username][1] = expires
        else:
            if Data[2].split(':')[0] =='Authorization':
                if Data[2].split('=')[1].split('\r')[0] == NONCE.decode('utf-8'):
                    self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
                    self.DicUsers[username]=[serverport,expires]
            else:
                Message = b"SIP/2.0 401 Unauthorized" + b'\r\n' + b"WWW Authenticate: Digest nonce=" + NONCE
                self.wfile.write(Message)
                
    def ReceiveAnsInvite(self, my_socket):
        
        data = my_socket.recv(1024)
        datadec = data.decode('utf-8')
        print(datadec)
        if datadec.split(' ')[5] == '200':
            self.wfile.write(data)
            
    def ReceiveAnsBye(self, my_socket):
        
        data = my_socket.recv(1024)
        datadec = data.decode('utf-8')
        print(datadec)
        if datadec.split(' ')[1] == '200':
            self.wfile.write(data)
            
    def SendtoServer(self, DATA):
        userserv = DATA[0].split(':')[1].split(' ')[0]
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect(('127.0.0.1', int(self.DicUsers[userserv][0])))
            
            Message= ''.join(DATA)
            my_socket.send(bytes(Message, 'utf-8'))
            if DATA[0].split(' ')[0] == 'INVITE':
                self.ReceiveAnsInvite(my_socket)
            elif DATA[0].split(' ')[0] == 'BYE':
                self.ReceiveAnsBye(my_socket)
            
    def InviteManager(self, DATA):
        print('recibe invite')
        self.ExpiresCheck()
        if DATA[4].split('=')[1].split(' ')[0] in self.DicUsers:
            if DATA[0].split(':')[1].split(' ')[0] in self.DicUsers:
                print('Encontrado servidor')
                self.SendtoServer(DATA)
 
            else:
                self.wfile.write(b"SIP/2.0 404 User Not Found\r\n\r\n")
        else:
            self.wfile.write(b"SIP/2.0 404 User Not Found\r\n\r\n")


    def handle(self):
        
        DATA = []
        
        for line in self.rfile:
            DATA.append(line.decode('utf-8'))
        print(DATA)

        if DATA[0].split(' ')[0] == 'REGISTER':
            self.RegisterManager(DATA)
        elif DATA[0].split(' ')[0] == 'INVITE':
            self.InviteManager(DATA)
        elif DATA[0].split(' ')[0] == 'ACK':
            if DATA[0].split(':')[1].split(' ')[0] in self.DicUsers:
                self.SendtoServer(DATA)
            else:
                self.wfile.write(b"SIP/2.0 404 User Not Found\r\n\r\n")

        elif DATA[0].split(' ')[0] == 'BYE':
            if DATA[0].split(':')[1].split(' ')[0] in self.DicUsers:
                self.SendtoServer(DATA)
            else:
                self.wfile.write(b"SIP/2.0 404 User Not Found\r\n\r\n")

            
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
