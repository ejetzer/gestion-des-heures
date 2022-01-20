#!python
# -*- coding: utf-8 -*-
"""
Programme ou module pour ...

Créé le Fri Jan 14 07:12:10 2022

@author: ejetzer
"""

import time

from subprocess import run
from pathlib import Path


def connecter(adresse: str,
              chemin: Path,
              nom: str,
              mdp: str):
    if not isinstance(chemin, Path):
        chemin = Path(chemin).expanduser().resolve()

    if not chemin.exists():
        chemin.mkdir()
        run(['mount', '-t', 'smbfs', f'//{nom}:{mdp}@{adresse}', str(chemin)])

        while not chemin.is_mount():
            time.sleep(1)


def déconnecter(chemin: Path, **kargs):
    if not isinstance(chemin, Path):
        chemin = Path(chemin).expanduser().resolve()

    if chemin.is_mount():
        run(['umount', str(chemin)])
        chemin.rmdir()

        while chemin.exists():
            time.sleep(1)


if __name__ == '__main__':
    chemin = Path('~/Volumes/GeniePhysique').expanduser()
    connecter('phsfiles.phs.polymtl.ca/GeniePhysique',
              chemin,
              'p111806',
              input('mdp:'))

    print(chemin, ':')
    for i in chemin.iterdir():
        print('\t', i)

    # déconnecter(chemin)

    print(chemin.parent, ':')
    for i in chemin.parent.iterdir():
        print('\t', i, i.exists())
