#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 08:00:29 2021

@author: emilejetzer
"""

import pandas as pd
from pathlib import Path
from datetime import datetime as Dt
import itertools
import shutil
from typing import Iterable, Union


def extraire(tâches_complétées: Iterable) -> pd.DataFrame:
    """
    Extrait les données de documents textes.

    Parameters
    ----------
    tâches_complétées : iter
        Chemins vers les fichiers textes.

    Returns
    -------
    pandas.DataFrame
        Données.

    """
    entrées = []

    for chemin in tâches_complétées:
        nouvelle_entrée: dict[str, Union[Dt, str, bool, float]] = {}

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
                    nouvelle_entrée[champ] =\
                        bool(int(str(nouvelle_entrée[champ])))
                elif any(x in champ for x in ('heures', 'min')):
                    nouvelle_entrée[champ] = float(
                        str(nouvelle_entrée[champ]).replace(',', '.'))

        entrées.append(nouvelle_entrée)

    return pd.DataFrame(entrées)


def formater(données: pd.DataFrame) -> pd.DataFrame:
    """
    Formate le DataFrame selon le modèle de Camila Rizzi.

    Parameters
    ----------
    données : pd.DataFrame
        Données telles que fournies par extraire.

    Returns
    -------
    données : pd.DataFrame
        Données formatées.

    """
    données = données.copy()

    données['Catégorie'] = ''

    if 'Précision si pour département' not in données.columns:
        données['Précision si pour département'] = ''

    données['Taux facturé'] = None
    données['Facturé'] = False
    données['Technicien'] = 'Jetzer, Émile'
    données['Autres'] = ''

    données.loc[:, 'Payeur'] = données['Payeur'].apply(
        lambda x: ', '.join(x.strip().split(' ')[::-1]))

    if "Nbr d'heures " in données.columns:
        if "Nbr d'heures" not in données.columns:
            données["Nbr d'heures"] = données["Nbr d'heures "]
        else:
            données["Nbr d'heures"] = données["Nbr d'heures"]\
                .fillna(données["Nbr d'heures "])

    données["Nbr total d'heures"] = données["Nbr d'heures"]
    données["Nbr d'heures \npassées dans l'atelier"] = 0
    données.loc[
        données.Atelier,
        "Nbr d'heures \npassées dans l'atelier"] = données.loc[
            données.Atelier,
            "Nbr total d'heures"]

    données['Date \n(AAAA-MM-DD)'] = données['Date']

    return données


def heures_atelier(données: pd.DataFrame) -> pd.DataFrame:
    """
    Filtre et assemble les heures passées à l'atelier.

    Parameters
    ----------
    données : pd.DataFrame
        Toutes les heures.

    Returns
    -------
    atelier : pd.DataFrame
        Heures passées à l'atelier, dans le format demandé par
        Catherine Caffiaux.

    """
    atelier = données.loc[données.Atelier.astype(bool),
                          ['Payeur',
                           'Date',
                           'Description des travaux effectués',
                           'Nbr d\'heures']]
    return atelier


def répartition(données: pd.DataFrame) -> pd.DataFrame:
    """
    Donne la proportion d'heures dans chaque groupe, par semaine.

    Parameters
    ----------
    données : pd.DataFrame
        Heures travaillées.

    Returns
    -------
    pd.DataFrame
        Proportions d'heures travaillées.

    """
    def semaines_et_groupes(x):
        return données.loc[x, 'Date'].week, données.loc[x, 'Payeur']

    proportions = données.loc[:, ['Payeur', 'Date', "Nbr d'heures"]
                              ].groupby(semaines_et_groupes).sum()
    proportions.index =\
        pd.MultiIndex.from_tuples(proportions.index,
                                  names=['Semaine', 'Payeur'])
    sommes_hebdomadaires = proportions.groupby('Semaine').sum()

    for semaine in sommes_hebdomadaires.index:
        proportions.loc[semaine,
                        'Proportions'] = proportions["Nbr d'heures"] / \
            sommes_hebdomadaires.loc[semaine, "Nbr d'heures"]

    return proportions


def compte_des_heures(données: pd.DataFrame) -> pd.DataFrame:
    """
    Donne le compte d'heures à chaque jour de travail, comparé à une
    journée standard.

    Parameters
    ----------
    données : pd.DataFrame
        Heures travaillées.

    Returns
    -------
    pd.DataFrame
        Heures en plus ou en moins, selon le modèle d'Élisabeth Delépine.

    """
    def dates(x):
        return données.loc[x, 'Date'].date()

    présences = données.loc[:, ['Date', "Nbr d'heures"]].groupby(dates).sum()
    présences['Différences'] = présences["Nbr d'heures"] - 7

    présences['+'] = 0
    présences['-'] = 0

    présences.loc[présences.Différences > 0, '+'] =\
        présences.loc[présences.Différences > 0, 'Différences']
    présences.loc[présences.Différences < 0, '-'] =\
        présences.loc[présences.Différences < 0, 'Différences']

    return présences


def archiver(*args, archive='.'):
    """Archive les fichiers."""
    for f in itertools.chain(*args):
        shutil.move(f, archive)


if __name__ == '__main__':
    racine = Path.home() / 'Library' / 'Mobile Documents' / \
        'iCloud~is~workflow~my~workflows' / 'Documents'
    boite_de_dépôt = racine / 'Journal de bord/'
    archive = boite_de_dépôt / 'Heures comptées'
    destination = Path.home() / 'OneDrive - polymtl.ca' / 'Heures'

    fichiers_textes = list(boite_de_dépôt.glob('*.txt'))
    fichiers_photos = list(boite_de_dépôt.glob('*.png'))
    fichiers_tâches_complétées = [
        f for f in fichiers_textes if 'complétée' in str(f)]

    données = extraire(fichiers_tâches_complétées)
    données = formater(données)
    #atelier = heures_atelier(données)
    proportions = répartition(données)
    présences = compte_des_heures(données)

    moment = Dt.now()

    fichier = destination / f'màj {moment:%Y-%m-%d %H_%M}.xlsx'
    with pd.ExcelWriter(fichier) as excel:
        données.to_excel(excel, sheet_name='Résumé')
        données.loc[:, ['Technicien',
                        'Payeur',
                        'Date',
                        'Description des travaux effectués',
                        'Demandeur',
                        "Nbr total d'heures",
                        "Nbr d'heures \npassées dans l'atelier",
                        'Précision si pour département',
                        'Taux facturé',
                        'Facturé',
                        'Autres']]\
            .to_excel(excel, sheet_name='Prêt')

#        for groupe, heures in atelier.groupby('Payeur'):
#            heures.to_excel(excel, sheet_name=f'Atelier {groupe}')

        proportions.to_excel(excel, sheet_name='Proportions')
        présences.to_excel(excel, sheet_name='Présences')

    archiver(fichiers_photos, fichiers_textes, archive=archive)
