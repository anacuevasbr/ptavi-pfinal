#!/usr/bin/python3
# -*- coding: utf-8 -*-

import calendar
import hashlib
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
        Line = DicUsers[User][0] + ': ' + str(DicUsers[User][1]) + ' '
        Line += str(DicUsers[User][2]) + ' ' + str(DicUsers[User][3]) + ' '
        Line += str(DicUsers[User][4]) + '\r\n'
        f.write(Line)


def ReadDataBase(path, DicUsers):

    f = open(path, "r")
    lineas = f.readlines()
    for linea in lineas:
        user = linea.split(':')[0]
        ip = linea.split(' ')[1]
        port = linea.split(' ')[2]
        expires = linea.split(' ')[3]
        registertime = linea.split(' ')[4].split('\n')[0]
        DicUsers[user] = [user, ip, port, expires, registertime]


def GetPassword(path, Username):
    f = open(path, "r")
    lineas = f.readlines()
    for linea in lineas:
        if linea.split(' ')[0] == Username:
            Password = linea.split(' ')[1][:-1]
            return Password


class EchoHandler(socketserver.DatagramRequestHandler):

    """
    Echo server class
    """
    datos = parsercreator(sys.argv[1])
    DicUsers = {}
    # Aquí se van a guardar los usuarios, es undicconario de listas
    # donde la clave es el nombre de usuario que tambien es el elemento 0 de
    # la lista, y el primer elemento de la lista es el puerto en el que
    # escucha, el segundo su fecha de expiración y el último la fecha
    # de registro

    try:
        ReadDataBase(datos[1]['path'], DicUsers)
    except FileNotFoundError:
        pass

    def ExpiresCheck(self):

        Delete = []
        for User in self.DicUsers:
            if str(self.DicUsers[User][3]) <= str(time.time()):
                Delete.append(User)
        for User in Delete:
            del self.DicUsers[User]
            print('eliminado ' + User)

    def RegisterManager(self, Data):

        NONCE = '123456789'
        if len(Data) < 3:
            self.wfile.write(b'SIP/2.0 400 Bad Request')
        else:

            username = Data[0].split(':')[1]
            serverport = Data[0].split(':')[2].split(' ')[0]
            expires = time.time() + float(Data[1].split(' ')[1].split('\r')[0])
            Client = self.client_address[0] + ':'
            Client += str(self.client_address[1]) + ' '
            self.ExpiresCheck()
            DataBaseFich(self.datos[1]['path'], self.DicUsers)
            print('recibe register')

            if username in self.DicUsers:
                self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
                uaserver.AddtoLog(self.datos[2]['path'],
                                  Client + "SIP/2.0 200 OK\r\n\r\n", 'Send')
                self.DicUsers[username][3] = expires
                DataBaseFich(self.datos[1]['path'], self.DicUsers)
            else:
                if Data[2].split(':')[0] == 'Authorization':
                    Password = GetPassword(self.datos[1]['passwdpath'],
                                           username)
                    h = hashlib.sha1(bytes(Password, 'utf-8'))
                    h.update(bytes(NONCE, 'utf-8'))
                    if Data[2].split('=')[1].split('\r')[0] == h.hexdigest():
                        self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
                        self.DicUsers[username] = [username,
                                                   self.client_address[0],
                                                   serverport,
                                                   expires, time.time()]
                        DataBaseFich(self.datos[1]['path'], self.DicUsers)
                        uaserver.AddtoLog(self.datos[2]['path'],
                                          Client + "SIP/2.0 200 OK\r\n\r\n",
                                          'Send')
                    else:
                        print('fallo en el nonce')

                else:
                    Message = "SIP/2.0 401 Unauthorized" + '\r\n'
                    Message += 'WWW-Authenticate: Digest nonce="'
                    Message += NONCE + '"\r\n\r\n'
                    self.wfile.write(bytes(Message, 'utf-8'))
                    uaserver.AddtoLog(self.datos[2]['path'], Message, 'Error')
                    uaserver.AddtoLog(self.datos[2]['path'], Client + Message,
                                      'Send')

    def ReceiveAnsInvite(self, my_socket, user):

        data = my_socket.recv(1024)
        datadec = data.decode('utf-8')
        Server = self.DicUsers[user][1] + self.DicUsers[user][2] + ' '
        uaserver.AddtoLog(self.datos[2]['path'], Server + datadec, 'Receive')
        if datadec.split(' ')[5] == '200':
            self.wfile.write(data)
            uaserver.AddtoLog(self.datos[2]['path'], Server + datadec, 'Send')
        else:
            print('Recibido 400')

    def ReceiveAnsBye(self, my_socket, user):

        data = my_socket.recv(1024)
        datadec = data.decode('utf-8')
        Server = self.DicUsers[user][1] + self.DicUsers[user][2] + ' '
        uaserver.AddtoLog(self.datos[2]['path'], Server + datadec, 'Receive')
        if datadec.split(' ')[1] == '200':
            self.wfile.write(data)
            uaserver.AddtoLog(self.datos[2]['path'], Server + datadec, 'Send')
        else:
            print('Recibido 400')

    def SendtoServer(self, DATA):
        userserv = DATA[0].split(':')[1].split(' ')[0]
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((self.DicUsers[userserv][1],
                              int(self.DicUsers[userserv][2])))

            Message = ''.join(DATA)
            Server = '127.0.0.1:' + self.DicUsers[userserv][1] + ' '
            uaserver.AddtoLog(self.datos[2]['path'], Server + Message, 'Send')

            my_socket.send(bytes(Message, 'utf-8'))
            if DATA[0].split(' ')[0] == 'INVITE':
                try:
                    self.ReceiveAnsInvite(my_socket, userserv)
                except ConnectionRefusedError:
                    print('No server listening at port ' + userserv)
                    self.wfile.write(b"SIP/2.0 404 User Not Found\r\n\r\n")
                    Client = self.client_address[0] + ':'
                    Client += str(self.client_address[1]) + ' '
                    Message = "SIP/2.0 404 User Not Found"
                    uaserver.AddtoLog(self.datos[2]['path'], Message, 'Error')
                    uaserver.AddtoLog(self.datos[2]['path'], Client + Message,
                                      'Send')

            elif DATA[0].split(' ')[0] == 'BYE':
                self.ReceiveAnsBye(my_socket, userserv)

    def InviteManager(self, DATA):
        print('recibe invite')
        self.ExpiresCheck()
        if DATA[4].split('=')[1].split(' ')[0] in self.DicUsers and DATA[0].split(':')[1].split(' ')[0] in self.DicUsers:
            print('Encontrado servidor')
            self.SendtoServer(DATA)
        else:
            self.wfile.write(b"SIP/2.0 404 User Not Found\r\n\r\n")
            Client = self.client_address[0] + ':'
            Client += str(self.client_address[1]) + ' '
            Message = "SIP/2.0 404 User Not Found"
            uaserver.AddtoLog(self.datos[2]['path'], Message, 'Error')
            uaserver.AddtoLog(self.datos[2]['path'], Client + Message, 'Send')

    def handle(self):

        DATA = []

        for line in self.rfile:
            DATA.append(line.decode('utf-8'))
        Message = ' '.join(DATA)
        Client = self.client_address[0] + ':'
        Client += str(self.client_address[1]) + ' '
        uaserver.AddtoLog(self.datos[2]['path'], Client + Message, 'Receive')

        if DATA[0].split(' ')[0] == 'REGISTER':
            self.RegisterManager(DATA)
        elif DATA[0].split(' ')[0] == 'INVITE':
            self.InviteManager(DATA)
        elif DATA[0].split(' ')[0] == 'ACK':
            if DATA[0].split(':')[1].split(' ')[0] in self.DicUsers:
                self.SendtoServer(DATA)
            else:
                self.wfile.write(b"SIP/2.0 404 User Not Found\r\n\r\n")
                Message = "SIP/2.0 404 User Not Found"
                uaserver.AddtoLog(self.datos[2]['path'], Message, 'Error')
                uaserver.AddtoLog(self.datos[2]['path'], Client + Message,
                                  'Send')

        elif DATA[0].split(' ')[0] == 'BYE':
            if DATA[0].split(':')[1].split(' ')[0] in self.DicUsers:
                self.SendtoServer(DATA)
            else:
                self.wfile.write(b"SIP/2.0 404 User Not Found\r\n\r\n")
                Message = "SIP/2.0 404 User Not Found"
                uaserver.AddtoLog(self.datos[2]['path'], Message, 'Error')
                uaserver.AddtoLog(self.datos[2]['path'], Client +
                                  Message, 'Send')
        else:
            self.wfile.write(b"SIP/2.0 405 Method Not Allowed\r\n\r\n")
            Message = "SIP/2.0 405 Method Not Allowed"
            uaserver.AddtoLog(self.datos[2]['path'], Message, 'Error')
            uaserver.AddtoLog(self.datos[2]['path'], Client + Message, 'Send')

if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 uaserver.py config')

    datos = parsercreator(sys.argv[1])
    uaserver.AddtoLog(datos[2]['path'], 'Starting...', 'Status')
    IP = datos[0]['ip']
    PORT = int(datos[0]['puerto'])
    serv = socketserver.UDPServer((IP, PORT), EchoHandler)
    print("Server " + datos[0]['name'] + ' listening at port ' + str(PORT))
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print('Cerrando servidor')
        uaserver.AddtoLog(datos[2]['path'], 'Finshing.', 'Status')
