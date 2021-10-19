#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérifications des heures de travail.

Created on Tue Oct 19 12:53:56 2021

@author: ejetzer
"""

import warnings
import configparser

from datetime import datetime, date
from pathlib import Path
from collections.abc import Callable, Iterable, Sequence

import pandas

from pandas import Series, DataFrame

from mise_a_jour import FeuilleDeTemps
from calendrier import Calendrier

class AvertissementAdministratif(UserWarning):

    def __init__(self, rangée: Series, *args, **kargs):
        super().__init__(*args, **kargs)

class TravailLaFinDeSemaine(AvertissementAdministratif):
    pass

class JourTropCourt(AvertissementAdministratif):
    pass

class JourTropLong(AvertissementAdministratif):
    pass

class SemaineTropCourte(AvertissementAdministratif):
    pass

class SemaineTropLongue(AvertissementAdministratif):
    pass

class Doublon(AvertissementAdministratif):
    pass



def pas_de_travail_la_fin_de_semaine(feuille: DataFrame):
    heures_quotidiennes = feuille.loc[:, ['Date', 'Heures']].groupby('Date').sum()
    fds = heures_quotidiennes.index.map(lambda x: x.weekday() in [5, 6])
    heures_fds = heures_quotidiennes.loc[fds, :]
    return heures_fds

def au_moins_sept_heures_par_jour(feuille: DataFrame):
    heures_quotidiennes = feuille.loc[:, ['Date', 'Heures']].groupby('Date').sum()
    sem = heures_quotidiennes.index.map(lambda x: x.weekday() not in [5, 6])
    heures_sem = heures_quotidiennes.loc[sem, :]
    peu = heures_sem.Heures < 7
    heures_peu = heures_sem.loc[peu, :]
    return heures_peu

def au_plus_dix_heures_par_jour(feuille: DataFrame):
    heures_quotidiennes = feuille.loc[:, ['Date', 'Heures']].groupby('Date').sum()
    sem = heures_quotidiennes.index.map(lambda x: x.weekday() not in [5, 6])
    heures_sem = heures_quotidiennes.loc[sem, :]
    trop = heures_sem.Heures > 10
    heures_trop = heures_sem.loc[trop, :]
    return heures_trop

def au_moins_trente_heures_par_semaine(feuille: DataFrame):
    heures_hebdomadaires = feuille.loc[:, ['Date', 'Heures']].groupby(lambda x: feuille.at[x, 'Date'].isocalendar().week).sum()
    peu = heures_hebdomadaires.Heures < 30
    heures_peu = heures_hebdomadaires.loc[peu, :]
    return heures_peu

def au_plus_quarante_cinq_heures_par_semaine(feuille: DataFrame):
    heures_hebdomadaires = feuille.loc[:, ['Date', 'Heures']].groupby(lambda x: feuille.at[x, 'Date'].isocalendar().week).sum()
    trop = heures_hebdomadaires.Heures > 45
    heures_trop = heures_hebdomadaires.loc[trop, :]
    return heures_trop


if __name__ == '__main__':
    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    cfg.read('Configuration.txt')

    cal_cfg = cfg['Calendrier']
    racine = Path(cal_cfg['ics']).expanduser()
    calendrier = Calendrier(cal_cfg['compte'], cal_cfg['cal'], racine)

    with FeuilleDeTemps(calendrier, **cfg['Polytechnique']) as feuille:
        feuille.charger()

        print(pas_de_travail_la_fin_de_semaine(feuille.tableau))
        print(au_moins_sept_heures_par_jour(feuille.tableau))
        print(au_plus_dix_heures_par_jour(feuille.tableau))
        print(au_moins_trente_heures_par_semaine(feuille.tableau))
        print(au_plus_quarante_cinq_heures_par_semaine(feuille.tableau))
