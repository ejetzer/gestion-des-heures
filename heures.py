#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import paramiko
import databases
import time
import configparser

def attendre(canal: paramiko.channel.Channel, attente: float = 1):
    while not canal.recv_ready():
        time.sleep(attente)
    
    sortie = b''
    while canal.recv_ready():
        sortie += canal.recv(1024)
    
    while not canal.send_ready():
        time.sleep(attente)
    
    return str(sortie, encoding='utf-8')

def exécuter(commande: str,
             canal: paramiko.channel.Channel,
             attente: float = 1,
             saut_de_ligne_inclus=False):
    if not saut_de_ligne_inclus: commande += '\n'
    canal.send(commande)
    return attendre(canal, attente)

def main():
    config = configparser.ConfigParser()
    config.read('heures.config')
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(config['ssh']['serveur'])
    
    with client.invoke_shell() as canal,\
         open('programme_paramiko.zsh') as instructions:
        print(attendre(canal), end='')
        for instruction in instructions:
            print(exécuter(instruction, canal, saut_de_ligne_inclus=True), end='')
    
    client.close()

if __name__ == '__main__':
    main()