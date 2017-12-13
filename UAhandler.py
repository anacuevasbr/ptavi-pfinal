#!/usr/bin/python3
# -*- coding: utf-8 -*-

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

if __name__ == "__main__":
    """
    Programa principal
    """
    parser = make_parser()
    uahandler = UAxmlhandler()
    parser.setContentHandler(uahandler)
    parser.parse(open('ua1.xml'))
    print(uahandler.get_tags())
