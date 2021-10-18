#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 26 13:09:01 2021.

@author: emilejetzer
"""

import configparser
import tkinter
import tkinter.messagebox
import datetime
import pathlib
import os.path
import traceback

from pathlib import Path

from calendrier import Calendrier
from mise_a_jour import FeuilleDeTemps
from git import Repository

class Formulaire(tkinter.Frame):

    def __init__(self, configuration, *args, **kargs):
        super().__init__(*args, **kargs)
        self.charger_configuration(configuration)

        self.répertoire_local = Repository(pathlib.Path(self.config['Polytechnique']['Destination']).expanduser())
        self.répertoire_local.pull()

        self.répertoire_distant = Repository(pathlib.Path(self.config['Polytechnique']['Réseau']).expanduser())
        self.répertoire_distant.pull()

        self.créer_champs()

    def màj(self):
        self.bouton_maj.configure(fg='red', text='Mise à jour en cours...')

        try:
            cal_cfg = self.config['Calendrier']

            racine = Path(cal_cfg['ics']).expanduser()
            calendrier = Calendrier(cal_cfg['compte'], cal_cfg['cal'], racine)

            with FeuilleDeTemps(calendrier, **self.config['Polytechnique']) as feuille:
                self.bouton_maj.configure(fg='red', text='[1/4] Extraction en cours...')
                feuille.extraire()
                self.bouton_maj.configure(fg='red', text='[2/4] Enregistrement en cours...')
                feuille.enregistrer()
                self.bouton_maj.configure(fg='red', text='[3/4] Mise à jour en cours...')
                feuille.màj()
                self.bouton_maj.configure(fg='red', text='[4/4] Archivage en cours...')
                feuille.archiver()
        except Exception as e:
            détails = ''.join(traceback.format_tb(e.__traceback__))
            tkinter.messagebox.showerror('Un problème s\'est produit', f'{type(e)}: {e}\n{détails}')

        self.répertoire_local.commit('Màj automatique', '-a')
        self.répertoire_distant.pull()
        self.bouton_maj.configure(fg='green', text='Mettre à jour')

    def créer_champs(self):
        self.variables, self.entrées, self.étiquettes = {}, {}, {}

        i = 0
        for i, col in enumerate(eval(self.config['Polytechnique']['Colonnes'])):
            self.variables[col] = tkinter.StringVar()
            self.entrées[col] = tkinter.Entry(textvariable=self.variables[col])
            self.étiquettes[col] = tkinter.Label(text=col)

            self.étiquettes[col].grid(row=i, column=0, sticky='NE')
            self.entrées[col].grid(row=i, column=1, sticky='NEW')

            if col == 'Date':
                self.variables[col].set(datetime.datetime.now().isoformat())
            elif col in eval(self.config['Polytechnique']['Colonnes']) and col in self.config['Polytechnique']:
                self.variables[col].set(self.config['Polytechnique'][col])

        def effacer():
            for col, var in self.variables.items():
                if col == 'Date':
                    var.set(datetime.datetime.now().isoformat())
                elif col in eval(self.config['Polytechnique']['Colonnes']) and col in self.config['Polytechnique']:
                    var.set(self.config['Polytechnique'][col])
                else:
                    var.set('')

        self.bouton_effacer = tkinter.Button(text='Effacer', command=effacer)
        self.bouton_effacer.grid(row=i+1, column=0, sticky='EW')

        def soumettre():
            self.ajouter_entrée(**{c: v.get() for c, v in self.variables.items()})
            effacer()

        self.bouton_soumettre = tkinter.Button(text='Soumettre', command=soumettre)
        self.bouton_soumettre.grid(row=i+1, column=1, sticky='EW')

        self.bouton_maj = tkinter.Button(text='Mettre à jour', command=lambda: self.màj())
        self.bouton_maj.grid(row=i+2, column=0, columnspan=2, sticky='EW')
        self.bouton_maj.configure(fg='green')

        self.after(1000* 60 * 60 * 8, lambda: self.màj())


    def ajouter_entrée(self, **kargs):
        maintenant = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4)))
        nouveau_fichier = pathlib.Path(os.path.expanduser(self.config['Polytechnique']['Boîte de dépôt'])) / f'{maintenant:%Y-%m-%dT%H_%M_%S%z} Tâche complétée.txt'

        texte = ''.join(f'{c}: {v}\n' for c, v in kargs.items())
        with nouveau_fichier.open('w') as doc:
            doc.write(texte)

    def charger_configuration(self, fichier):
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config.read(fichier)

    def destroy(self):
        self.bouton_maj.configure(fg='red')
        self.màj()
        self.répertoire_local.commit('Màj automatique', '-a')
        self.répertoire_distant.pull()
        self.répertoire_local.pull()
        super().destroy()


if __name__ == '__main__':
    racine = tkinter.Tk()
    racine.title('Entrée des heures')
    fenêtre = Formulaire('Configuration.txt', master=racine)
    fenêtre.mainloop()
