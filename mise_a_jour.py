#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 26 10:29:13 2021

@author: emilejetzer
"""

import configparser
import pathlib
import os.path
import datetime
import re
import pandas
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import itertools
import shutil

import apple_calendar_integration # https://pypi.org/project/apple-calendar-integration/

fonctions_importation = {'Atelier': lambda x: bool(int('0' + str(x).strip())),
                         'Heures': lambda x: float(str(x.replace(',', '.'))),
                         'Payeur': lambda x: ', '.join(x.strip().split(' ')[::-1]),
                         'Description des travaux effectués': lambda x: x.strip('"'),
                         'Date': lambda x: datetime.datetime.fromisoformat(x).date()}

def extraire(fichiers, **défaut):
    entrées = []

    for chemin in fichiers:
        nouvelle_entrée = {c: défaut.get(c, None) for c in eval(défaut['Colonnes'])}
        nouvelle_entrée['Date'] = datetime.datetime.fromtimestamp(chemin.stat().st_birthtime).date()

        with chemin.open() as f:
            for ligne in f.readlines():
                expression = r'^\s*(.+?)\s*:\s*(.+?)\s*$'
                match = re.match(expression, ligne)
                champ, valeur = match.group(1, 2)
                nouvelle_entrée[champ] = fonctions_importation.get(champ, lambda x: x.strip())(valeur)

        entrées.append(nouvelle_entrée)

    données = pandas.DataFrame(entrées)

    if entrées:
        # données.loc[:, 'Heures'] = données.loc[:, "Nbr d'heures"]
        données.loc[données.Atelier, 'Atelier'] = données.loc[données.Atelier, 'Heures']
        données.loc[données.Atelier == False, 'Atelier'] = 0
        données = données.loc[:, eval(défaut['Colonnes'])]

    return données


def répartition(données):
    def semaines_et_groupes(x):
        return données.loc[x, 'Date'].isocalendar()[1], données.loc[x, 'Payeur']

    proportions = données.loc[:, ['Payeur', 'Date', 'Heures']].groupby(semaines_et_groupes).sum()
    proportions.index = pandas.MultiIndex.from_tuples(proportions.index, names=['Semaine', 'Payeur'])
    sommes_hebdomadaires = proportions.groupby('Semaine').sum()

    for semaine in sommes_hebdomadaires.index:
        proportions.loc[semaine, 'Proportions'] = proportions['Heures'] / sommes_hebdomadaires.loc[semaine, 'Heures']

    return proportions

def compte_des_heures(données):
    def dates(x):
        return données.loc[x, 'Date']

    présences = données.loc[:, ['Date', 'Heures']].groupby(dates).sum()
    présences['Différences'] = présences['Heures'] - 7

    présences['+'] = 0
    présences['-'] = 0

    présences.loc[présences.Différences > 0, '+'] =\
        présences.loc[présences.Différences > 0, 'Différences']
    présences.loc[présences.Différences < 0, '-'] =\
        présences.loc[présences.Différences < 0, 'Différences']

    return présences


def màj(données, fichier, nom_feuille, colonnes_excel, rangée_min, colonne_max):
    cahier = openpyxl.load_workbook(fichier)
    feuille = cahier[nom_feuille]

    colonnes = [col.value for col in feuille[colonnes_excel][0]]
    valeurs = {c: [] for c in colonnes}
    for ligne in feuille.iter_rows(min_row=rangée_min, max_col=colonne_max, values_only=True):
        ligne = ligne + tuple('' for i in range(11-len(ligne)))
        for colonne, cellule in zip(colonnes, ligne):
            valeurs[colonne].append(cellule)

    tableau = pandas.DataFrame(valeurs)
    tableau = tableau.append(données)
    tableau = tableau.sort_values('Date')

    for i, ligne in enumerate(dataframe_to_rows(tableau, index=False, header=False)):
        for col, cel in zip('ABCDEFGHIJK', ligne):
            feuille[f'{col}{rangée_min+i}'] = cel

    cahier.save(fichier)

    return tableau


def archiver(*args, archive='.'):
    for f in itertools.chain(*args):
        shutil.move(str(f), str(archive))


def main(config):
    config_poly = config['Polytechnique']
    racine = pathlib.Path(os.path.expanduser(config_poly['Racine']))
    boite_de_dépôt = pathlib.Path(os.path.expanduser(config_poly['Boîte de dépôt']))
    archive = pathlib.Path(os.path.expanduser(config_poly['Archive']))
    destination = pathlib.Path(os.path.expanduser(config_poly['Destination']))
    colonnes_finales = eval(config_poly['Colonnes'])
    nom_feuille = config_poly['Feuille']
    colonnes_excel = config_poly['Colonnes Excel']
    rangée_min = config_poly.getint('Première rangée')
    colonne_max = config_poly.getint('Dernière colonne')
    fichier_temps = destination / config_poly['TempsTechnicien']

    fichiers_textes = list(boite_de_dépôt.glob('*.txt'))
    fichiers_photos = list(boite_de_dépôt.glob('*.png')) + \
        list(boite_de_dépôt.glob('*.jpeg'))
    fichiers_tâches_complétées = [f for f in fichiers_textes if 'compl' in f.stem]

    données = extraire(fichiers_tâches_complétées, **config_poly)

    if not données.empty:
        proportions = répartition(données)
        présences = compte_des_heures(données)

        moment = datetime.datetime.now()

        fichier = destination / f'màj {moment:%Y-%m-%d %H_%M}.xlsx'
        with pandas.ExcelWriter(fichier) as excel:
            données.to_excel(excel, sheet_name='Données')
            proportions.to_excel(excel, sheet_name='Proportions')
            présences.to_excel(excel, sheet_name='Présences')

        màj(données, fichier_temps, nom_feuille, colonnes_excel, rangée_min, colonne_max)

        archiver(fichiers_photos, fichiers_textes, archive=archive)

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read('Configuration.txt')
    main(config)
