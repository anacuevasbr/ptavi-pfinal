#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import socketserver
import sys
import time
import uaserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class Proxyxmlhandler(ContentHandler):

    def __init__(self):
        """
        Constructor. Inicializamos las variables
        """
        self.etiquetas = []
        self.lista_etiq = ["server", "database", "log"]
        self.coleccion_attr = {'server': ['name', 'ip', 'puerto'],
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

def DataBaseFich(path, DicUsers):
    
    f = open(path, "w")
    
    for User in DicUsers:
        Line = DicUsers[User][0] + ': ' + str(DicUsers[User][1]) + ' ' + str(DicUsers[User][2]) + '\r\n'
        f.write(Line)

class EchoHandler(socketserver.DatagramRequestHandler):

    """
    Echo server class
    """
    DicUsers = {}  # Aquí se van a guardar los usuarios, es undicconario
                   # de listas donde la clave es el
                   # nombre de usuario que tmbien es el lmento 0 e la lista,
                   # y le primer elemento de la lista
                   # es el puerto en el que escucha y el segundo su
                   # fecha de expiración

    def ExpiresCheck(self):

        Delete = []
        for User in self.DicUsers:
            if str(self.DicUsers[User][2]) <= str(time.time()):
                Delete.append(User)
        for User in Delete:
            del self.DicUsers[User]
            print('eliminado ' + User)

    def RegisterManager(self, Data):
        
        datos = parsercreator(sys.argv[1])
        NONCE = '123456789'
        username = Data[0].split(':')[1]
        serverport = Data[0].split(':')[2].split(' ')[0]
        expires = time.time() + float(Data[1].split(' ')[1].split('\r')[0])

        self.ExpiresCheck()
        DataBaseFich(datos[1]['path'], self.DicUsers)

        if username in self.DicUsers:
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            uaserver.AddtoLog(datos[2]['path'], "SIP/2.0 200 OK\r\n\r\n", 'Send')
            self.DicUsers[username][2] = expires
        else:
            if Data[2].split(':')[0] == 'Authorization':
                if Data[2].split('=')[1].split('\r')[0] == NONCE:
                    self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
                    self.DicUsers[username] = [username, serverport, expires]
                    DataBaseFich(datos[1]['path'], self.DicUsers)
                    uaserver.AddtoLog(datos[2]['path'], "SIP/2.0 200 OK\r\n\r\n", 'Send')

            else:
                Message = "SIP/2.0 401 Unauthorized" + '\r\n' + "WWW Authenticate: Digest nonce=" + NONCE
                self.wfile.write(bytes(Message, 'utf-8'))
                uaserver.AddtoLog(datos[2]['path'], Message, 'Send')

    def ReceiveAnsInvite(self, my_socket):

        data = my_socket.recv(1024)
        datadec = data.decode('utf-8')
        uaserver.AddtoLog(datos[2]['path'], datadec, 'Receive')
        print(datadec)
        if datadec.split(' ')[5] == '200':
            self.wfile.write(data)
            uaserver.AddtoLog(datos[2]['path'], datadec, 'Send')

    def ReceiveAnsBye(self, my_socket):

        data = my_socket.recv(1024)
        datadec = data.decode('utf-8')
        uaserver.AddtoLog(datos[2]['path'], datadec, 'Receive')
        print(datadec)
        if datadec.split(' ')[1] == '200':
            self.wfile.write(data)
            uaserver.AddtoLog(datos[2]['path'], datadec, 'Send')

    def SendtoServer(self, DATA):
        userserv = DATA[0].split(':')[1].split(' ')[0]
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect(('127.0.0.1', int(self.DicUsers[userserv][0])))

            Message = ''.join(DATA)
            uaserver.AddtoLog(datos[2]['path'], Message, 'Send')

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
        Message = ' '.join(DATA)
        uaserver.AddtoLog(datos[2]['path'], Message, 'Receive')

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
