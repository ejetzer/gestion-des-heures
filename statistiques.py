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


def regroupements(x):
    return df.loc[x, 'Date'].week, df.loc[x, 'Payeur']


résumé = df.loc[:, ['Payeur', 'Date', "Nbr d'heures"]
                ].groupby(regroupements).sum()
résumé.index = pd.MultiIndex.from_tuples(résumé.index,
                                         names=['Semaine', 'Payeur'])
sommes_hebdomadaires = résumé.groupby('Semaine').sum()

for semaine in sommes_hebdomadaires.index:
    résumé.loc[semaine, 'Proportions'] = résumé["Nbr d'heures"] / \
        sommes_hebdomadaires.loc[semaine, "Nbr d'heures"]

résumé.to_excel(str(activités / f'stats {moment:%Y-%m-%d %H_%M}.xlsx'))
