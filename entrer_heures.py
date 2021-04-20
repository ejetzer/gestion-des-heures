#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 19 05:51:45 2021

@author: emilejetzer
"""

from pathlib import Path
from datetime import datetime as Dt

champs = ('Temps (min)',
          'Payeur',
          'Demandeur',
          'Description des travaux effectués',
          'Atelier')

icloud = Path('~').expanduser() / 'Library' / 'Mobile Documents'
raccourcis = icloud / 'iCloud~is~workflow~my~workflows' / 'Documents'
journal_de_bord = raccourcis / 'Journal de bord'


class Tâche(dict):

    def __init__(self, **kargs):
        super().__init__(**kargs)

    def sauvegarder(self, f: Path):
        with f.open('w') as doc:
            for clé, val in self.items():
                print(f'{clé}: {val}', file=doc)


def ligne_de_commande():
    while input('Compléter une tâche? [oui|non] ').startswith('o'):
        tâche = Tâche()

        for clé in champs:
            val = input(f'{clé}: ')

            if clé == 'Atelier':
                val = int(val)
            elif clé == 'Temps (min)':
                val = float(val)

            tâche[clé] = val

        nom = f'{Dt.now():%Y-%m-%dT%H_%M_%S%z} Tâche complétée.txt'
        tâche.sauvegarder(journal_de_bord / nom)


if __name__ == '__main__':
    ligne_de_commande()
