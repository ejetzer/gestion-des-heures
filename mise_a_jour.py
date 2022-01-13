#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Programme de mise à jour des heures pour Polytechnique.

Created on Mon Jul 26 10:29:13 2021

@author: emilejetzer
"""

import configparser
import pathlib
import datetime
import re
import itertools
import shutil

import os.path

from pathlib import Path

import pandas
import openpyxl

from openpyxl.utils.dataframe import dataframe_to_rows
from pandas import DataFrame

from calendrier import Calendrier


def assainir_nom(nom):
    'Assainit un nom de fichier (sans l\'extension)'
    return ''.join([('_' if x in '_:/' else x) for x in nom])


def importations_heures(x):
    if isinstance(x, str):
        x = x.strip()

        if ',' in x:
            x = x.replace(',', '.')

        if x.endswith('.'):
            x = x + '0'

    if not x:
        x = 0

    return float(x)


fonctions_importation = {'Atelier': lambda x: bool(int('0' + str(x).strip())),
                         'Heures': importations_heures,
                         'Payeur': lambda x: ', '.join(x.strip().split(' ')[::-1]),
                         'Description des travaux effectués': lambda x: x.strip('"'),
                         'Date': lambda x: datetime.datetime.fromisoformat(x).date()}


class FeuilleDeTemps:

    def __init__(self, calendrier: Calendrier, **config):
        self.config: dict[str, str] = config
        self.destination: Path = Path(self.config['Destination']).expanduser()
        self.fichier_temps: Path = self.destination / \
            self.config['TempsTechnicien']
        self.archive: Path = Path(self.config['Archive']).expanduser()
        self.nom_feuille: str = self.config['Feuille']
        self.colonnes_excel: str = self.config['Colonnes Excel']
        self.rangée_min: int = int(self.config['Première rangée'])
        self.colonne_max: int = int(self.config['Dernière colonne'])
        self.boîte_de_dépôt: Path = Path(
            self.config['Boîte de dépôt']).expanduser()

        self.calendrier = calendrier
        self.données = None

    @property
    def fichiers_texte(self) -> iter:
        yield from self.boîte_de_dépôt.glob('*.txt')

    @property
    def fichiers_photo(self) -> iter:
        yield from self.boîte_de_dépôt.glob('*.png')
        yield from self.boîte_de_dépôt.glob('*.jpeg')

    @property
    def fichiers_des_tâches_complétées(self) -> iter:
        yield from (f for f in self.fichiers_texte if 'compl' in f.stem)

    def extraire(self, fichiers: list[Path] = None, **défaut) -> DataFrame:
        if fichiers is None:
            fichiers = self.fichiers_des_tâches_complétées
        if défaut is None or défaut == {}:
            défaut = self.config

        entrées = []

        for chemin in fichiers:
            nouvelle_entrée = {c: défaut.get(c, None)
                               for c in eval(défaut['Colonnes'])}
            nouvelle_entrée['Date'] = datetime.datetime.fromtimestamp(
                chemin.stat().st_birthtime).date()

            with chemin.open() as f:
                for ligne in f.readlines():
                    expression = r'^\s*(.+?)\s*:\s*(.+?)\s*$'
                    match = re.match(expression, ligne)
                    champ, valeur = match.group(1, 2)
                    nouvelle_entrée[champ] = fonctions_importation.get(
                        champ, lambda x: x.strip())(valeur)

            entrées.append(nouvelle_entrée)

        données = pandas.DataFrame(entrées)

        if entrées:
            # données.loc[:, 'Heures'] = données.loc[:, "Nbr d'heures"]
            données.loc[données.Atelier,
                        'Atelier'] = données.loc[données.Atelier, 'Heures']
            données.loc[données.Atelier == False, 'Atelier'] = 0
            données = données.loc[:, eval(défaut['Colonnes'])]

        self.données = données
        return données

    def répartition(self, données: DataFrame = None) -> DataFrame:
        if données is None:
            données = self.données

        def semaines_et_groupes(x): return données.loc[x, 'Date'].isocalendar()[
            1], données.loc[x, 'Payeur']

        proportions = données.loc[:, ['Payeur', 'Date', 'Heures']].groupby(
            semaines_et_groupes).sum()
        proportions.index = pandas.MultiIndex.from_tuples(
            proportions.index, names=['Semaine', 'Payeur'])
        sommes_hebdomadaires = proportions.groupby('Semaine').sum()

        for semaine in sommes_hebdomadaires.index:
            proportions.loc[semaine, 'Proportions'] = proportions['Heures'] / \
                sommes_hebdomadaires.loc[semaine, 'Heures']

        return proportions

    def compte(self, données: DataFrame = None) -> DataFrame:
        if données is None:
            données = self.données

        def dates(x): return données.loc[x, 'Date']

        présences = données.loc[:, ['Date', 'Heures']].groupby(dates).sum()
        présences['Différences'] = présences['Heures'] - 7

        présences['+'] = 0
        présences['-'] = 0

        présences.loc[présences.Différences > 0, '+'] =\
            présences.loc[présences.Différences > 0, 'Différences']
        présences.loc[présences.Différences < 0, '-'] =\
            présences.loc[présences.Différences < 0, 'Différences']

        return présences

    def charger(self,
                données: DataFrame = None,
                fichier_temps: Path = None,
                nom_feuille: str = None,
                colonnes_excel: str = None,
                rangée_min: int = None,
                colonne_max: int = None) -> DataFrame:
        if données is None:
            données = self.données
        if fichier_temps is None:
            fichier_temps = self.fichier_temps
        if nom_feuille is None:
            nom_feuille = self.nom_feuille
        if colonnes_excel is None:
            colonnes_excel = self.colonnes_excel
        if rangée_min is None:
            rangée_min = self.rangée_min
        if colonne_max is None:
            colonne_max = self.colonne_max

        cahier = openpyxl.load_workbook(fichier_temps)
        feuille = cahier[nom_feuille]

        colonnes = [col.value for col in feuille[colonnes_excel][0]]
        valeurs = {c: [] for c in colonnes}
        for ligne in feuille.iter_rows(min_row=rangée_min, max_col=colonne_max, values_only=True):
            ligne = ligne + tuple('' for i in range(11-len(ligne)))
            for colonne, cellule in zip(colonnes, ligne):
                valeurs[colonne].append(cellule)

        tableau = pandas.DataFrame(valeurs)
        tableau.loc[:, 'Date'] = tableau.loc[:, 'Date'].map(
            lambda x: pandas.to_datetime(x).date())
        tableau = tableau.sort_values('Date').drop_duplicates()
        self.tableau = tableau

        return tableau, cahier, feuille

    def màj(self,
            données: DataFrame = None,
            fichier_temps: Path = None,
            nom_feuille: str = None,
            colonnes_excel: str = None,
            rangée_min: int = None,
            colonne_max: int = None) -> DataFrame:
        if données is None:
            données = self.données
        if fichier_temps is None:
            fichier_temps = self.fichier_temps
        if nom_feuille is None:
            nom_feuille = self.nom_feuille
        if colonnes_excel is None:
            colonnes_excel = self.colonnes_excel
        if rangée_min is None:
            rangée_min = self.rangée_min
        if colonne_max is None:
            colonne_max = self.colonne_max

        tableau, cahier, feuille = self.charger(
            données, fichier_temps, nom_feuille,
            colonnes_excel, rangée_min, colonne_max)

        if données is not None:
            tableau = tableau.append(données)

        tableau.loc[:, 'Date'] = tableau.loc[:, 'Date'].map(
            lambda x: pandas.to_datetime(x).date())
        tableau = tableau.sort_values('Date').drop_duplicates()

        for i, ligne in enumerate(dataframe_to_rows(tableau,
                                                    index=False,
                                                    header=False)):
            for col, cel in zip('ABCDEFGHIJK', ligne):
                feuille[f'{col}{rangée_min+i}'] = cel

        cahier.save(fichier_temps)

        self.tableau = tableau
        self.données = None

        return tableau

    def enregistrer(self, données: DataFrame = None, destination: Path = None):
        if données is None:
            données = self.données
        if destination is None:
            destination = self.destination

        if données.empty:
            raise ValueError('Aucune donnée à enregistrer.')

        proportions = self.répartition(données)
        présences = self.compte(données)

        moment = datetime.datetime.now()

        # Dans un fichier Excel daté
        fichier = destination / f'màj {moment:%Y-%m-%d %H_%M}.xlsx'
        with pandas.ExcelWriter(fichier) as excel:
            données.to_excel(excel, sheet_name='Données')
            proportions.to_excel(excel, sheet_name='Proportions')
            présences.to_excel(excel, sheet_name='Présences')

        # Comme des fichiers ics pour le calendrier
        for _, item in données.iterrows():
            titre = '✅ ' + \
                assainir_nom(item['Description des travaux effectués'])
            durée = datetime.timedelta(hours=item['Heures'])
            nouveau = self.calendrier.créer_événement(titre, moment, durée)
            fichier = destination / \
                f'màj {moment:%Y-%m-%d %H_%M} {titre[2:]}.ics'
            with fichier.open('w') as f:
                f.write(str(nouveau))

    def archiver(self, *args, archive: Path = None):
        if archive is None:
            archive = self.archive

        if len(args) == 0:
            args = (self.fichiers_texte, self.fichiers_photo)

        for f in itertools.chain(*args):
            shutil.move(str(f), str(archive))

    def __enter__(self):
        self.extraire()
        return self

    def __exit__(self, exception_type, value, traceback):
        return None


def main(config):
    cal_cfg = config['Calendrier']

    racine = Path(cal_cfg['ics']).expanduser()
    calendrier = Calendrier(cal_cfg['compte'], cal_cfg['cal'], racine)

    with FeuilleDeTemps(calendrier, **config['Polytechnique']) as feuille:
        feuille.extraire()
        feuille.enregistrer()
        feuille.màj()
        feuille.archiver()


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read('Configuration.txt')
    main(config)
