#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 10:28:33 2021

@author: ejetzer
"""

import pandas as pd
from pathlib import Path
from datetime import datetime as Dt
import shutil
#import itertools


racine = Path.home() / 'Library' / 'Mobile Documents' / \
    'iCloud~is~workflow~my~workflows' / 'Documents'
boite_de_dépôt = racine / 'Journal de bord/'
activités = Path.home() / 'OneDrive - polymtl.ca' / 'Heures'
fichier = 'résumé *-*-* *_*.xlsx'
archive = boite_de_dépôt / 'Heures comptées'
moment = Dt.now()

df = pd.concat([pd.read_excel(f, 0) for f in activités.glob(fichier)],
               sort=False,
               ignore_index=True)

atelier = df.loc[df.Atelier.astype(bool), ['Payeur',
                                           'Date',
                                           'Description des travaux effectués',
                                           'Nbr d\'heures ']]
minutes = df.loc[df.Atelier.astype(bool), 'Temps (min)'] / 60.0
atelier['Nbr d\'heures '] = atelier['Nbr d\'heures '].fillna(minutes)\
                                                     .multiply(1.5)

with pd.ExcelWriter(activités / f'atelier {moment:%Y-%m-%d %H_%M}.xlsx') as excel:
    for groupe, heures in atelier.groupby('Payeur'):
        heures.to_excel(excel, sheet_name=groupe)

# Archiver les fichiers
for f in activités.glob(fichier):
    print(f'Déplacer {f} vers {archive}...')
    shutil.move(f, archive)
