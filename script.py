#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-

import argparse
import paramiko
import configparser

import heures

def définir_arguments():
    parseur = argparse.ArgumentParser(description='Ajouter une tâche complétée')
    parseur.add_argument('-a', '--atelier',
                         action='store_true', default=False, dest='atelier',
                         help='Si le travail était en atelier (par défaut: non)')
    parseur.add_argument('-d', '--description',
                         type=str, dest='description',
                         required=True,
                         help='La description des tâches accomplies')
    parseur.add_argument('h',
                         type=float, nargs=1,
                         help="Le nombre d'heures complétées")
    parseur.add_argument('--config',
                         type=str, default='heures.config',
                         dest='config',
                         help='Fichier de configuration à utiliser')
    return parseur.parse_args()

def adapter_modèle(modèle: str,
                   arguments: argparse.Namespace,
                   config: configparser.ConfigParser):
    args = {'répertoire': config['ssh']['répertoire'],
            'table': config['mysql']['table'],
            'temps': arguments.h[0],
            'desc': arguments.description,
            'atelier': int(arguments.atelier),
            'requête': config['mysql']['ajout']}
    return modèle.read().format(**args).split('\n')

def main():
    arguments = définir_arguments()
    config = configparser.ConfigParser()
    config.read(arguments.config)
    
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(config['ssh']['serveur'])
    
    with open(config['script']['modèle']) as modèle:
        instructions = adapter_modèle(modèle, arguments, config)
    
    with client.invoke_shell() as canal:
        print(heures.attendre(canal), end='')
        for instruction in instructions:
            print(heures.exécuter(instruction, canal, saut_de_ligne_inclus=False), end='')
    
    client.close()

if __name__ == '__main__':
    main()