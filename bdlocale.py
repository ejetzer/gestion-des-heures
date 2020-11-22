#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 21 16:14:41 2020

@author: ejetzer
"""

import argparse
#import time
import configparser
#import asyncio
from typing import Union, Sequence

#import paramiko #  Protocole SSH
import sqlite3 as db
#import MySQLdb as db
import pandas as pd

class BaseDeDonnées:

    def __init__(self):
        self.args = argparse.ArgumentParser(description='Gérer la base de données')
        self.args.add_argument('--config',
                             type=str, default='heures.config',
                             dest='config',
                             help='Fichier de configuration à utiliser')
        self.config = configparser.ConfigParser()

    def parse_args(self):
        arguments = self.args.parse_args()
        fichier_config = arguments.config
        self.config.read(fichier_config)

        return arguments

    def connect(self):
        url_database = self.config['mysql']['bd']
        self.conn = db.connect(url_database)

    def réinitialiser(self):
        script_réinit = self.config['mysql']['init']
        with open(script_réinit) as fichier_réinit:
            self.executescript(fichier_réinit.read())

    def cursor(self, factory=db.Cursor):
        return self.conn.cursor(factory)

    def execute(self, sql: str, parameters: tuple = tuple(), *args, **kargs):
        rés = self.conn.execute(sql, parameters, *args, **kargs)
        self.commit()
        return rés

    def executemany(self, sql: str,
                    seq_of_parameters: Sequence[Union[Sequence, dict]] = tuple(),
                    *args, **kargs):
        rés = self.conn.executemany(sql, seq_of_parameters, *args, **kargs)
        self.commit()
        return rés

    def executescript(self, sql_script: str, *args, **kargs):
        rés = self.conn.executescript(sql_script, *args, **kargs)
        self.commit()
        return rés

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def select(self, cols: Union[Sequence, str], table: str,
               lim: int = 1000, chunksize: int = 20):
        if not isinstance(cols, str):
            cols = '{}'.format(', '.join(f'`{c}`' for c in cols))

        requête = f'select {cols} from `{table}` limit {lim}'
        for chunk in pd.read_sql_query(requête, self.conn,
                                       index_col='id', chunksize=chunksize):
            yield chunk

    def insert(self, table: str, **data):
        cols = '({})'.format(', '.join(f'`{c}`' for c in data.keys()))
        vals = '({})'.format(', '.join(f':{c}' for c in data.keys()))
        requête = f'insert into {table} {cols} values {vals}'

        clés = data.keys()
        vals = data.values()
        gen = ({c: v for c, v in zip(clés, vs)} for vs in zip(*vals))

        self.executemany(requête, gen)

    def update(self, table: str, where: str, **data):
        cols = ', '.join(f'{c}=:{c}' for c in data.keys() if not c.startswith('where'))
        requête = f'update {table} set {cols} where {where}'

        clés = data.keys()
        vals = data.values()
        gen = ({c: v for c, v in zip(clés, vs)} for vs in zip(*vals))

        #print(requête)
        #print(data)

        #for d in gen:
        #    self.execute(requête, d)

        self.executemany(requête, gen)

    def groupes(self):
        yield from self.select('*', 'groupes')

    def nouveau_groupe(self, nom: Union[str, Sequence],
                       responsable: Union[str, Sequence] = None,
                       description: Union[str, Sequence] = None):
        if not isinstance(nom, Sequence) or isinstance(nom, str):
            nom = [nom]
        if not isinstance(responsable, Sequence) or isinstance(responsable, str):
            responsable = [responsable]
        if not isinstance(description, Sequence) or isinstance(description, str):
            description = [description]

        while len(nom) > len(responsable):
            responsable.append(None)
        while len(nom) > len(description):
            description.append(None)

        self.insert('groupes', nom=nom, responsable=responsable, description=description)

    def labos(self):
        yield from self.select('*', 'laboratoires')

    def nouveau_labo(self, local: Union[str, Sequence],
                     groupe: Union[str, Sequence],
                     responsable: Union[str, Sequence]):
        if not isinstance(local, Sequence) or isinstance(local, str):
            local = [local]
        if not isinstance(groupe, Sequence) or isinstance(groupe, str):
            groupe = [groupe]
        assert len(local) == len(groupe)

        groupe_existe = [False for i in groupe]
        for g_df in self.groupes():
            for i, g in enumerate(groupe):
                if g in g_df.nom.values:
                    groupe_existe[i] = True
        if not all(groupe_existe):
            raise db.DataError(f"Le groupe '{groupe}' n'existe pas.")

        if not isinstance(responsable, Sequence) or isinstance(responsable, str):
            responsable = [responsable]

        while len(local) > len(responsable):
            responsable.append(None)

        self.insert('laboratoires', local=local, groupe=groupe, responsable=responsable)

    def montages(self):
        yield from self.select('*', 'montages')

    def nouveau_montage(self, nom: Union[str, Sequence],
                        groupe: Union[str, Sequence],
                        laboratoire: Union[str, Sequence],
                        responsable: Union[str, Sequence] = None,
                        description: Union[str, Sequence] = None):
        if not isinstance(nom, Sequence) or isinstance(nom, str):
            nom = [nom]
        if not isinstance(groupe, Sequence) or isinstance(groupe, str):
            groupe = [groupe]
        if not isinstance(laboratoire, Sequence) or isinstance(laboratoire, str):
            laboratoire = [laboratoire]
        assert len(nom) == len(groupe)
        assert len(nom) == len(laboratoire)

        groupe_existe = [False for i in groupe]
        for g_df in self.groupes():
            for i, g in enumerate(groupe):
                if g in g_df.nom.values:
                    groupe_existe[i] = True
        if not all(groupe_existe):
            raise db.DataError(f"Le groupe {groupe} n'existe pas.")

        labo_existe = [False for i in laboratoire]
        for l_df in self.labos():
            for i, l in enumerate(laboratoire):
                if l in l_df.local.values:
                    labo_existe[i] = True
        if not all(labo_existe):
            raise db.DataError(f"Le laboratoire {laboratoire} n'existe pas.")

        if not isinstance(responsable, Sequence) or isinstance(responsable, str):
            responsable = [responsable]
        if not isinstance(description, Sequence) or isinstance(description, str):
            description = [description]

        while len(nom) > len(responsable):
            responsable.append(None)
        while len(nom) > len(description):
            description.append(None)

        self.insert('montages', nom=nom, groupe=groupe, laboratoire=laboratoire, responsable=responsable, description=description)

    def projets(self):
        yield from self.select('*', 'projets')

    def nouveau_projet(self, nom: Union[str, Sequence],
                       montage: Union[str, Sequence],
                       responsable: Union[str, Sequence] = None,
                       description: Union[str, Sequence] = None):
        if not isinstance(nom, Sequence) or isinstance(nom, str):
            nom = [nom]
        if not isinstance(montage, Sequence) or isinstance(montage, str):
            montage = [montage]
        assert len(nom) == len(montage)

        montage_existe = [False for i in montage]
        for m_df in self.montages():
            for i, m in enumerate(montage):
                if m in m_df.nom.values:
                    montage_existe[i] = True
        if not all(montage_existe):
            raise db.DataError(f"Le montage {montage} n'existe pas.")

        if not isinstance(responsable, Sequence) or isinstance(responsable, str):
            responsable = [responsable]
        if not isinstance(description, Sequence) or isinstance(description, str):
            description = [description]

        while len(nom) > len(responsable):
            responsable.append(None)
        while len(nom) > len(description):
            description.append(None)

        self.insert('projets', nom=nom, montage=montage, responsable=responsable, description=description)

    def taches(self):
        yield from self.select('*', 'taches')

    def nouvelle_tache(self, description: Union[str, Sequence],
                       projet: Union[str, Sequence],
                       parent: Union[str, Sequence] = None,
                       temps: Union[float, Sequence] = None,
                       fini: Union[bool, Sequence] = False):
        if not isinstance(description, Sequence) or isinstance(description, str):
            description = [description]
        if not isinstance(projet, Sequence) or isinstance(projet, str):
            projet = [projet]
        if not isinstance(parent, Sequence):
            parent = [parent]

        while len(description) > len(parent):
            parent.append(None)

        projet_existe = [False for i in projet]
        for p_df in self.projets():
            for i, p in enumerate(projet):
                if p in p_df.nom.values:
                    projet_existe[i] = True
        if not all(projet_existe):
            raise db.DataError(f"Le projet {projet} n'existe pas.")

        parent_existe = [(i is None) for i in parent]
        for p_df in self.taches():
            for i, p in enumerate(parent):
                if (p in p_df.nom.values) or (p is None):
                    parent_existe[i] = True
        if not all(parent_existe):
            raise db.DataError(f"Le parent {parent} n'existe pas.")

        if not isinstance(temps, Sequence):
            temps = [temps]
        if not isinstance(fini, Sequence):
            fini = [fini]

        while len(temps) > len(description):
            temps.append(0)
        while len(fini) > len(description):
            fini.append(False)

        self.insert('taches', description=description, projet=projet, parent=parent, temps=temps, fini=fini)

    def maj_tache(self, description: Union[str, Sequence],
                  temps: Union[float, Sequence],
                  fini: Union[bool, Sequence]):
        if not isinstance(description, Sequence) or isinstance(description, str):
            description = [description]
        if not isinstance(temps, Sequence):
            temps = [temps]
        if not isinstance(fini, Sequence):
            fini = [fini]

        while len(description) > len(temps):
            temps.append(None)
        while len(description) > len(fini):
            fini.append(False)

        t_df = pd.concat(self.select(('id', 'description', 'temps'), 'taches'))
        t_df_indices = t_df.description == description
        t_df = t_df[t_df_indices]
        description_classé, temps_classé, fini_classé = [], [], []
        for i, ligne in t_df.iterrows():
            description_classé.append(ligne.description)
            t = ligne.temps if ligne.temps is not None else 0
            index = description.index(ligne.description)
            temps_classé.append(temps[index] + t)
            fini_classé.append(fini[index])

        self.update('taches', 'description=:where_description', temps=temps_classé, fini=fini_classé, where_description=description_classé)
        self.commit()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self.conn.close()

def main():
    base_de_données = BaseDeDonnées()
    base_de_données.parse_args()
    with base_de_données:
        base_de_données.réinitialiser()

        base_de_données.nouveau_groupe('femtoQ', 'Denis Seletskiy')

        for g in base_de_données.groupes():
            pass#print(g)

        base_de_données.nouveau_labo('B-585', 'femtoQ', 'Denis Seletskiy')

        for l in base_de_données.labos():
            pass#print(l)

        base_de_données.nouveau_montage('SuperContinuum', 'femtoQ', 'B-585', 'Denis Seletskiy')

        for m in base_de_données.montages():
            pass#print(m)

        base_de_données.nouveau_projet('Projet test', 'SuperContinuum', 'Étienne Doiron')

        for p in base_de_données.projets():
            pass#print(p)

        base_de_données.nouvelle_tache('Tâche test', 'Projet test')

        for t in base_de_données.taches():
            print(t)

        base_de_données.maj_tache('Tâche test', 1, True)

        for t in base_de_données.taches():
            print(t)

        base_de_données.maj_tache('Tâche test', 2, False)

        for t in base_de_données.taches():
            print(t)

        base_de_données.maj_tache('Tâche test', 1, True)

        for t in base_de_données.taches():
            print(t)

if __name__ == '__main__':
    main()