#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 08:00:29 2021

@author: emilejetzer
"""

import pandas as pd
from pathlib import Path
from datetime import datetime as Dt

racine = Path.home() / 'Library' / 'Mobile Documents' / \
    'iCloud~is~workflow~my~workflows' / 'Documents'
boite_de_dépôt = racine / 'Journal de bord/'
archive = boite_de_dépôt / 'Heures comptées'
destination = Path.home() / 'OneDrive - polymtl.ca' / 'Heures'


fichiers_textes = list(boite_de_dépôt.glob('*.txt'))
fichiers_photos = list(boite_de_dépôt.glob('*.png'))
fichiers_tâches_complétées = [
    f for f in fichiers_textes if 'complétée' in str(f)]

entrées = []

for chemin in fichiers_tâches_complétées:
    nouvelle_entrée = {}

    with chemin.open() as f:
        étampe = Dt.fromtimestamp(chemin.stat().st_birthtime)
        nouvelle_entrée['Date'] = étampe

        for ligne in f.readlines():
            div = ligne.strip().split(':', 1)
            if len(div) > 1:
                champ, valeur = div
            else:
                champ, valeur = div.pop(), ''

            nouvelle_entrée[champ] = valeur.strip(' "')

            if champ == 'Atelier':
                nouvelle_entrée[champ] = bool(int(nouvelle_entrée[champ]))
            elif any(x in champ for x in ('heures', 'min')):
                nouvelle_entrée[champ] = float(
                    nouvelle_entrée[champ].replace(',', '.'))

    entrées.append(nouvelle_entrée)

données = pd.DataFrame(entrées)

données['Catégorie'] = ''

if 'Précisions si pour département' not in données.columns:
    données['Précision si pour département'] = ''

données['Facturé'] = False

if "Nbr d'heures " in données.columns:
    if "Nbr d'heures" not in données.columns:
        données["Nbr d'heures"] = données["Nbr d'heures "]
    else:
        données["Nbr d'heures"].fillna(données["Nbr d'heures "])

moment = Dt.now()
données.to_excel(str(destination / f'résumé {moment:%Y-%m-%d %H_%M}.xlsx'))

données.loc[:, ['Payeur',
                'Date',
                'Description des travaux effectués',
                'Catégorie',
                'Demandeur',
                "Nbr d'heures",
                'Précision si pour département',
                'Facturé']]\
    .to_excel(str(destination / f'prêt {moment:%Y-%m-%d %H_%M}.xlsx'))
