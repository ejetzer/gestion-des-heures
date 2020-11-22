#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-
"""
Mise à jour de la base de données d'heures pour le travail

@auteur: Émile Jetzer
"""

import argparse
import time
import configparser

import paramiko #  Protocole SSH


def attendre(canal: paramiko.channel.Channel,
             attente: float = 1,
             buf: int = 1024):
    """


    Parameters
    ----------
    canal : paramiko.channel.Channel
        DESCRIPTION.
    attente : float, optional
        DESCRIPTION. The default is 1.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    sortie = b''
    while not (canal.recv_ready() and canal.send_ready()):
        if canal.recv_ready():
            sortie += canal.recv(buf)
        else:
            time.sleep(attente)

    return str(sortie, encoding='utf-8')


def exécuter(commande: str,
             canal: paramiko.channel.Channel,
             attente: float = 1):
    """


    Parameters
    ----------
    commande : str
        DESCRIPTION.
    canal : paramiko.channel.Channel
        DESCRIPTION.
    attente : float, optional
        DESCRIPTION. The default is 1.
    saut_de_ligne_inclus : TYPE, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    if not commande.endswith('\n'):
        commande += '\n'
    canal.send(commande)
    return attendre(canal, attente)


def définir_arguments():
    """


    Returns
    -------
    TYPE
        DESCRIPTION.

    """
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
    """


    Parameters
    ----------
    modèle : str
        DESCRIPTION.
    arguments : argparse.Namespace
        DESCRIPTION.
    config : configparser.ConfigParser
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    args = {'repertoire': config['ssh']['répertoire'],
            'table': config['mysql']['table'],
            'temps': arguments.h[0],
            'desc': arguments.description,
            'atelier': int(arguments.atelier),
            'requete': config['mysql']['ajout'],
            'colonnes': '`Temps`, `Description`, `Atelier`'}
    return modèle.read().format(**args).split('\n')


def main():
    """


    Returns
    -------
    None.

    """
    arguments = définir_arguments()
    config = configparser.ConfigParser()
    config.read(arguments.config)

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.connect(config['ssh']['serveur'])

    with open(config['script']['modèle']) as modèle:
        instructions = adapter_modèle(modèle, arguments, config)

    with client.invoke_shell() as canal:
        print(attendre(canal), end='')
        for instruction in instructions:
            print(exécuter(instruction, canal), end='')

    client.close()


if __name__ == '__main__':
    main()
