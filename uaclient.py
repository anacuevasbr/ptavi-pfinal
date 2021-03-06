#!/usr/bin/python3
# -*- coding: utf-8 -*-

import hashlib
import os
import socket
import sys
import uaserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class UAxmlhandler(ContentHandler):

    def __init__(self):
        """
        Constructor. Inicializamos las variables
        """
        self.etiquetas = []
        self.lista_etiq = ["account", "uaserver", "rtpaudio", "regproxy",
                           "log", "audio"]
        self.coleccion_attr = {'account': ['username', 'passwd'],
                               'uaserver': ['ip', 'puerto'],
                               'rtpaudio': ['puerto'],
                               'regproxy': ['ip', 'puerto'],
                               'log': ['path'],
                               'audio': ['path']}

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
    uahandler = UAxmlhandler()
    parser.setContentHandler(uahandler)
    parser.parse(open(xml))
    return (uahandler.get_tags())


def RecieveRegister():

    data = my_socket.recv(1024).decode('utf-8')
    if data != '':
        Server = Server = datos[3]['ip'] + ':' + datos[3]['puerto'] + ' '
        if data.split(' ')[1] == '401':
            uaserver.AddtoLog(datos[4]['path'], Server + data, 'Receive')
            print('Recibido 401')
            NONCE = data.split('=')[1]
            NONCE = NONCE.split('"')[1]
            Password = datos[0]['passwd']
            h = hashlib.sha1(bytes(Password, 'utf-8'))
            h.update(bytes(NONCE, 'utf-8'))
            Message = METHOD + ' sip:' + USER + ':' + str(SERVERPORT)
            Message += ' SIP/2.0\r\n' + 'Expires: ' + sys.argv[3] + '\r\n'
            Message += 'Authorization: Digest response=' + h.hexdigest()
            Message += '\r\n\r\n'
            my_socket.send(bytes(Message, 'utf-8'))
            uaserver.AddtoLog(datos[4]['path'], Server + Message, 'Send')
            RecieveRegister()

        elif data.split(' ')[1] == '200':
            print('Recibido 200 ok')
            uaserver.AddtoLog(datos[4]['path'], Server + data, 'Receive')

        elif data.split(' ')[1] == '400':
            print('Recubido 400')
            uaserver.AddtoLog(datos[4]['path'], Server + data, 'Receive')


def ManageRegister(datos):

    USER = datos[0]['username']
    SERVERPORT = int(datos[1]['puerto'])

    Message = METHOD + ' sip:' + USER + ':' + str(SERVERPORT)
    Message += ' SIP/2.0\r\n' + 'Expires: ' + sys.argv[3] + '\r\n\r\n'

    my_socket.send(bytes(Message, 'utf-8'))
    Server = datos[3]['ip'] + ':' + datos[3]['puerto'] + ' '
    uaserver.AddtoLog(datos[4]['path'], Server + Message, 'Send')
    RecieveRegister()


def SendRTP(datos, DATA):

    ServerIP = DATA.split('\r\n')[8].split(' ')[1]
    ServerRTPPort = DATA.split('\r\n')[11].split(' ')[1]
    audio = datos[5]['path']
    order = "./mp32rtp -i " + ServerIP + " -p " + ServerRTPPort + " < " + audio
    os.system(order)
    order = "cvlc rtp://@127.0.0.1:" + datos[2]['puerto']
    os.system(order)
    Server = ServerIP + ':'
    Server += ServerRTPPort + ' '
    uaserver.AddtoLog(datos[4]['path'], Server + 'Enviando RTP', 'Send')


def ManageInvite(datos):

    USER = datos[0]['username']
    SERVERPORT = int(datos[1]['puerto'])

    Message = 'INVITE sip:' + sys.argv[3] + ' SIP/2.0\r\n'
    Message += 'Content-Type: application/sdp\r\n\r\n' + 'v=0\r\n'
    Message += 'o=' + USER + ' 127.0.0.1\r\n' + 's=hungry\r\n'
    Message += 't=0\r\n' + 'm=audio ' + datos[2]['puerto'] + ' RTP\r\n'

    my_socket.send(bytes(Message, 'utf-8'))
    Server = datos[3]['ip'] + ':' + datos[3]['puerto'] + ' '
    uaserver.AddtoLog(datos[4]['path'], Server + Message, 'Send')

    data = my_socket.recv(1024).decode('utf-8')
    uaserver.AddtoLog(datos[4]['path'], Server + data, 'Receive')
    if len(data.split(' ')) > 6:

        if data.split(' ')[5] == '200':
            Message = 'ACK sip:' + sys.argv[3] + ' SIP/2.0\r\n\r\n'
            my_socket.send(bytes(Message, 'utf-8'))
            uaserver.AddtoLog(datos[4]['path'], Server + Message, 'Send')
            SendRTP(datos, data)
    else:
        print('Recibido ' + data)
        uaserver.AddtoLog(datos[4]['path'], Server + data, 'Error')


def ManageBye(datos):

    Message = 'BYE sip:' + sys.argv[3] + ' SIP/2.0\r\n\r\n'
    my_socket.send(bytes(Message, 'utf-8'))
    Server = datos[3]['ip'] + ':' + datos[3]['puerto'] + ' '
    uaserver.AddtoLog(datos[4]['path'], Server + Message, 'Send')
    data = my_socket.recv(1024).decode('utf-8')
    uaserver.AddtoLog(datos[4]['path'], Server + data, 'Receive')

if __name__ == "__main__":
    """
    Programa principal
    """
    if len(sys.argv) != 4:
        sys.exit('Usage: python3 uaclient.py config metodo opcion')

    datos = parsercreator(sys.argv[1])

    USER = datos[0]['username']
    PASSWORD = datos[0]['passwd']
    METHOD = sys.argv[2]
    SERVERIP = datos[1]['ip']
    if SERVERIP == '':
        SERVERIP = '127.0.0.1'
    SERVERPORT = int(datos[1]['puerto'])
    PROXYIP = datos[3]['ip']
    if PROXYIP == '':
        PROXYIP = '127.0.0.1'
    PROXYPORT = int(datos[3]['puerto'])

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((PROXYIP, PROXYPORT))

        try:

            if METHOD == 'REGISTER':
                ManageRegister(datos)
            elif METHOD == 'INVITE':
                ManageInvite(datos)
            elif METHOD == 'BYE':
                ManageBye(datos)
        except ConnectionRefusedError:
            Message = 'No server listening at ' + PROXYIP
            Message += ' port ' + str(PROXYPORT)
            print(Message)
            uaserver.AddtoLog(datos[4]['path'], Message, 'Error')
