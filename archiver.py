#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 19 20:08:38 2021

@author: emilejetzer
"""

from pathlib import Path
import shutil
import itertools


racine = Path.home() / 'Library' / 'Mobile Documents' / \
    'iCloud~is~workflow~my~workflows' / 'Documents'
boite_de_dépôt = racine / 'Journal de bord/'
archive = boite_de_dépôt / 'Heures comptées'

fichiers_textes = boite_de_dépôt.glob('*.txt')
fichiers_photos = boite_de_dépôt.glob('*.png')

# Archiver les fichiers
for f in itertools.chain(fichiers_textes, fichiers_photos):
    print(f'Déplacer {f} vers {archive}...')
    shutil.move(f, archive)
