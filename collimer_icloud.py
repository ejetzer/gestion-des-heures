#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 08:00:29 2021

@author: emilejetzer
"""

import pandas as pd
from pathlib import Path
from datetime import datetime as Dt
import shutil
import itertools

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

    entrées.append(nouvelle_entrée)

données = pd.DataFrame(entrées)
moment = Dt.now()
données.to_excel(str(destination / f'résumé {moment:%Y-%m-%d %H_%M}.xlsx'))


# Archiver les fichiers
for f in itertools.chain(fichiers_textes, fichiers_photos):
    print(f'Déplacer {f} vers {archive}...')
    shutil.move(f, archive)
