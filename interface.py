#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 26 13:09:01 2021.

@author: emilejetzer
"""

import mise_a_jour
import tkinter


class Formulaire(tkinter.Frame):

    def __init__(self, configuration, *args, **kargs):
        super().__init__(*args, **kargs)

    def créer_champs(self):
        pass

    def ajouter_entrée(self):
        pass

    def quitter(self):
        pass

    def charger_configuration(self, fichier):
        pass


if __name__ == '__main__':
    racine = tkinter.Tk()
    fenêtre = Formulaire('Configuration.txt', master=racine)
    fenêtre.mainloop()
