#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import sys
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

if __name__ == "__main__":
    """
    Programa principal
    """
    if len(sys.argv) != 4:
        sys.exit('Usage: python3 uaclient.py config metodo opcion')

    datos = parsercreator(sys.argv[1])
    print(datos)

    USER = datos[0]['username']
    PASSWORD = datos[0]['passwd']
    METHOD = sys.argv[2]
    SERVERIP = datos[1]['ip']
    if SERVERIP == '':
        SERVERIP = '127.0.0.1'
    SERVERPORT = int(datos[1]['puerto'])
    PROXYIP= datos[3]['ip']
    if PROXYIP == '':
        PROXYIP = '127.0.0.1'
    PROXYPORT = int(datos[3]['puerto'])
    print(PROXYIP)
    print(PROXYPORT)
    # Contenido que vamos a enviar
    if METHOD == 'REGISTER':
        Message = METHOD + ' sip:' + USER + ':' + str(SERVERPORT) + ' SIP/2.0\r\n' + 'Expires: ' + sys.argv[3] + '\r\n\r\n'

    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((PROXYIP, PROXYPORT))

        my_socket.send(bytes(Message, 'utf-8'))
        data = my_socket.recv(1024)
        Message = data.decode('utf-8')

