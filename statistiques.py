#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 19 20:06:52 2021

@author: emilejetzer
"""

import pandas as pd
from pathlib import Path
from datetime import datetime as Dt

racine = Path.home() / 'Library' / 'Mobile Documents' / \
    'iCloud~is~workflow~my~workflows' / 'Documents'
boite_de_dépôt = racine / 'Journal de bord/'
activités = Path.home() / 'OneDrive - polymtl.ca' / 'Heures'
fichier = 'prêt *-*-* *_*.xlsx'
archive = boite_de_dépôt / 'Heures comptées'
moment = Dt.now()

df = pd.concat([pd.read_excel(f, 0) for f in activités.glob(fichier)],
               sort=False,
               ignore_index=True)\
    .iloc[:, 1:]


def semaines_et_groupes(x):
    return df.loc[x, 'Date'].week, df.loc[x, 'Payeur']


proportions = df.loc[:, ['Payeur', 'Date', "Nbr d'heures"]
                     ].groupby(semaines_et_groupes).sum()
proportions.index = pd.MultiIndex.from_tuples(proportions.index,
                                              names=['Semaine', 'Payeur'])
sommes_hebdomadaires = proportions.groupby('Semaine').sum()

for semaine in sommes_hebdomadaires.index:
    proportions.loc[semaine, 'Proportions'] = proportions["Nbr d'heures"] / \
        sommes_hebdomadaires.loc[semaine, "Nbr d'heures"]


def dates(x):
    return df.loc[x, 'Date'].date()


présences = df.loc[:, ['Date', "Nbr d'heures"]].groupby(dates).sum()
présences['Différences'] = présences["Nbr d'heures"] - 7

présences['+'] = 0
présences['-'] = 0

présences.loc[présences.Différences > 0,
              '+'] = présences.loc[présences.Différences > 0, 'Différences']
présences.loc[présences.Différences < 0,
              '-'] = présences.loc[présences.Différences < 0, 'Différences']

with pd.ExcelWriter(str(activités / f'stats {moment:%Y-%m-%d %H_%M}.xlsx')) as excel:
    proportions.to_excel(excel, sheet_name='Proportions')
    présences.to_excel(excel, sheet_name='Présences')
