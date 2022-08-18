#!/usr/bin/env python
# -*- encoding: utf-8 -*-

### Opérations sur les fichiers
import os
from os import path
from json import *
import pandas as pd

### Interface graphique
from tkinter import *
from tkinter import ttk
# from tkinter import tix   # Obsolète, à remplacer
from tkinter.messagebox import *
from tkinter.filedialog import *

### Création de PDF
import PIL
# from Pillow import Image
from reportlab import pdfgen
from reportlab.lib.pagesizes import A4

### Imports pour CRAPPy
import crappy
import customblocks
import matplotlib

### Divers
from numpy import pi
import time
import datetime
import re
from threading import Event, Thread

### Debug
import sys
import random
from screeninfo import get_monitors

### Potentiellement à virer. À vérifer
# import nidaqmx
# import xlsxwriter
# from win32com.client import Dispatch

matplotlib.use("Agg")

COEF_VOLTS_TO_MILLIMETERS=200
RESET = 0
ON = 1   # Ces trois constantes sont pour verrou_production (anciennement lock)
OFF = 0
RESTART = 3
NOMBRE_DE_CONSIGNES_MAXIMAL = 1000
TYPES_DE_CONSIGNE = {"constant" : "palier",
                     "ramp" : "rampe",
                     "cyclic" : "cycle de paliers",
                     "cyclic_ramp" : "cycle de rampes",
                     "sine" : "sinus"}
LABEL_SORTIE_EN_CHARGE = "sortie_charge_transformee"
DEBUT_CONDITION_TEMPS = len("delay=")
DEBUT_CONDITION_CHARGE = len(LABEL_SORTIE_EN_CHARGE) + 1
ASSERVISSEMENT_EN_CHARGE = 1
ASSERVISSEMENT_EN_DEPLACEMENT = 2
SEPARATEUR = "\\" # "\\" for windows, "/" for linux

verrou_production = OFF
alphabet=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
next_available_letter=0
def lecture_donnee(file_name):
   """FR : Renvoie la dernière entrée du fichier texte indiqué. Les fichiers utilisant
   cette fonction ne doivent être modifiés que par les fonctions de cette application.

   EN : Returns the last entry in the indicated text file. Files using this function musn't
   be modified except by functions of this application."""
   with open(file_name,'r') as f :
      lines=f.readlines()
      data=lines[-1][11:-1]  # Datas are formated as "yyyy-mm-dd <data>\n".
   return data
#V
DOSSIER_CONFIG_ET_CONSIGNES = lecture_donnee("dossier_config_et_consignes.txt") + SEPARATEUR
print(DOSSIER_CONFIG_ET_CONSIGNES)
launch_crappy_event = Event()

def etalonnage_des_coefficients_de_transformation():
   """FR : Étalonne les coefficient de la fonction transformation_voltage_tonnage.

   EN : Calibrates the transformation_voltage_tonnage function's coefficients."""
   #fonction calculant la valeur de charge réelle lue. 
   #Prend en x la tension délivrée par l'Indi-Paxs.
   #Sort la tension correspondant à la charge réelle.
   global etalonnage_a, etalonnage_b, etalonnage_c
   etalonnage_a = float(lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'etal_a.txt'))
   etalonnage_b = float(lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'etal_b.txt'))
   etalonnage_c = float(lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'etal_c.txt'))
#V
etalonnage_a, etalonnage_b, etalonnage_c = 0, 0, 0
etalonnage_des_coefficients_de_transformation()

def RTM_protocol():
   """FR : Ouvre le manuel du banc.

   EN : Opens the bench's manual."""
   os.startfile(lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'chemin_manuel.txt') + SEPARATEUR + lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'nom_manuel.txt')) 
   return 0
#V   
def ecriture_donnee(file_name, data) :
   """FR : Écrit la donnée précédée de la date dans le fichier texte indiqué. Les 
   fichiers utilisant cette fonction ne doivent être modifiés que par les fonctions 
   de cette application.

   EN : Writes the data preceded by the date in the indicated text file. Files using this function musn't
   be modified except by functions of this application."""
   with open(file_name,'a') as f :
      # Les 11 premiers caractères sont la date au format "2022-07-04 ".
      f.write(str(datetime.datetime.now())[:11] + ' ' + data + "\n")
#V
def suppression_d_un_fichier(file_name) :
      """FR : Supprime ce fichier.
      
      EN : Deletes that file."""
      try :
         os.remove(file_name)
      except FileNotFoundError :
         showwarning("Attention", "Fichier " + file_name + " non trouvé")
#V
def volts_to_tons(volts) :
   """FR : Convertit des volts en tonnes.
   
   EN : Converts volts in tons."""
   return 2 * volts
#V
def tons_to_volts(tons) :
   """FR : Convertit des tonnes en volts.
   
   EN : Converts tons in volts."""
   return round(tons/2, 2)
#V
### Fonctions utilisées pour les entrées des utilisateurs
def _check_entree_charge(new_value):
   """FR : Empêche l'utilisateur d'entrer des valeurs incorrectes.
   
   EN : Prevent the user from entering incorrect values."""
   if new_value == "" :
      return True
   if re.match("^[0-9]+\.?[0-9]*$", new_value) is None and re.match("^[0-9]*\.?[0-9]+$", new_value) is None :
      return False
   new_value = float(new_value)
   return new_value >= 0.0 and new_value <= 20.0
#V
def _check_entree_longueur(new_value):
   """FR : Empêche l'utilisateur d'entrer des valeurs incorrectes.
   
   EN : Prevent the user from entering incorrect values."""
   if new_value == "" :
      return True
   if re.match("^[0-9]+\.?[0-9]*$", new_value) is None and re.match("^[0-9]*\.?[0-9]+$", new_value) is None :
      return False
   new_value = float(new_value)
   return new_value >= 0.0 and new_value <= 26.0
#V
def _check_entree_vitesse_charge(new_value):
   """FR : Empêche l'utilisateur d'entrer des valeurs incorrectes.
   
   EN : Prevent the user from entering incorrect values."""
   if new_value == "" or new_value == '-' :
      return True
   if re.match("^-?[0-9]+\.?[0-9]*$", new_value) is None and re.match("^-?[0-9]*\.?[0-9]+$", new_value) is None :
      return False
   new_value = float(new_value)
   return new_value >= -20.0 and new_value <= 20.0
#V
def _check_entree_temps(new_value):
   """FR : Empêche l'utilisateur d'entrer des valeurs incorrectes.
   
   EN : Prevent the user from entering incorrect values."""
   if new_value == "" :
      return True
   if re.match("^[0-9]+\.?[0-9]*$", new_value) is None and re.match("^[0-9]*\.?[0-9]+$", new_value) is None  :
      return False
   new_value = float(new_value)
   return new_value >= 0.0
#V
def _check_entree_cycles(new_value):
   """FR : Empêche l'utilisateur d'entrer des valeurs incorrectes.
   
   EN : Prevent the user from entering incorrect values."""
   if new_value == "" :
      return True
   if re.match("^[0-9]*$", new_value) is None :
      return False
   new_value = int(new_value)
   return new_value > 0
#V
def _check_entree_string(new_value):
   """FR : Empêche l'utilisateur d'entrer des valeurs incorrectes.
   
   EN : Prevent the user from entering incorrect values."""
   if new_value == "" :
      return True
   if re.match("^[-A-Za-z0-9éèêëàùôÎïÉÈÊËÀÙÔÎÏ ]*$", new_value) is None :
      return False
   return True
#V
### Fonctions gérant le défilement
def _bound_to_mousewheel(widget, event):
   """FR : Lie le défilement de la fenêtre à la molette de la souris lorsque le curseur est sur 
   cette fenêtre.
   
   EN : Binds the window's scrolling to the mousewheel when the cursor is over that window."""
   widget.bind_all("<MouseWheel>", lambda e : _on_mousewheel(widget, e))
#V
def _unbound_to_mousewheel(widget, event):
   """FR : Délie le défilement de la fenêtre à la molette de la souris lorsque le curseur sort 
   de cette fenêtre.
   
   EN : Binds the window's scrolling to the mousewheel when the cursor leaves that window."""
   widget.unbind_all("<MouseWheel>")
#V
def _on_mousewheel(widget, event):
   """FR : Fait défiler la fenêtre avec la molette.
   
   EN : Scrolls the window with the mousewheel."""
   widget.yview_scroll(int(-1*(event.delta/80)), "units")
#V
### Fonctions servant de modificateurs aux liens CRAPPy
#TODO : variables d'étalonnage plutôt que constantes
#        préciser les unités et d'autres trucs
def _card_to_pid(dic):
   """FR : Étalonne la tension renvoyée par le capteur d'efforts.
   
   EN : Calibrates the voltage fed back by the effort sensor."""
   if "sortie_charge" not in dic.keys() :
      dic["t(s)"] = time.time()
      dic ["sortie_charge_transformee"] = 0.0
      return dic
   x = 2 * dic["sortie_charge"]
   dic["sortie_charge_transformee"] = (0.0037*(x**2)+1.0255*x-0.0644)/2
   return dic  # Faire des test pour vérifier s'il y a vraiment besoin du 2 * <> /2.

def _gen_to_graph_in_tons(dic):
   if "consigne" not in dic.keys() :
      dic["t(s)"] = time.time()
      dic ["Consigne(transformée)"] = 0.0
      return dic
   x = 2 * dic["consigne"]
   dic["Consigne(transformée)"] = (etalonnage_a * (x**2) + etalonnage_b * x + etalonnage_c)
   return dic

def _card_to_recorder_and_graph(dic) :
   dic["Charge(tonnes)"] = 2 * _card_to_pid(dic)["sortie_charge_transformee"]
   # dic["sortie_deplacement"] = <fonction de la sortie en déplacement>
   return dic

def _pid_to_card_charge(dic) :
   if 0.03 < dic["entree_charge"]  :
      dic["entree_charge"] += 0.44 #0.458
   else :
      dic["entree_charge"] = 0
   return dic

def _pid_to_card_decharge(dic) :
   if -0.03 > dic["entree_decharge"]  :
      dic["entree_decharge"] -= 0.49 #0.525
   else :
      dic["entree_decharge"] = 0
   dic["entree_decharge"] *= -1
   return dic

### Reste

def demarrage_de_crappy_charge(consignes_generateur = None, fichier_d_enregistrement = None,
                        parametres_du_test = [], labels_a_enregistrer = None):
   """TODO"""
   gen = crappy.blocks.Generator(path = consignes_generateur,
                                 cmd_label = 'consigne',
                                 spam = True,
                                 freq = 50)

   carte_NI = crappy.blocks.IOBlock(name = "Nidaqmx",
                                    labels = ["t(s)", "sortie_charge", 
                                             "sortie_deplacement"],
                                    cmd_labels = ["entree_decharge", "entree_charge"],
                                    initial_cmd = [0.0, 0.0],
                                    exit_values = [0.0, 0.0],
                                    channels=[{'name': 'Dev1/ao0'},
                                    {'name': 'Dev1/ao1'},
                                    {'name': 'Dev1/ai6'},
                                    {'name': 'Dev1/ai7'}],
                                    spam=True,
                                    freq = 50)

   pid_charge = crappy.blocks.PID(kp=1,
                                 ki=0.01,
                                 kd=0.01,
                                 out_max=5,
                                 out_min=-5,
                                 i_limit=0.5,
                                 target_label='consigne',
                                 labels=["t(s)", 'entree_charge'],
                                 input_label='sortie_charge_transformee',
                                 freq = 50)

   pid_decharge = crappy.blocks.PID(kp=0.5,
                                    ki=0.0,
                                    kd=0.0,
                                    out_max=5,
                                    out_min=-5,
                                    i_limit=0.5,
                                    target_label='consigne',
                                    labels=["t(s)", 'entree_decharge'],
                                    input_label='sortie_charge_transformee',
                                    freq = 50)

   y_charge = customblocks.YBlock(out_labels = ["t(s)", "consigne", 
                                                "sortie_charge_transformee"],
                                 freq = 50)

   y_decharge = customblocks.YBlock(out_labels = ["t(s)", "consigne", 
                                                "sortie_charge_transformee"],
                                    freq = 50)
   
   graphe = customblocks.EmbeddedGrapher(("t(s)", "consigne"), 
                                          ("t(s)", "sortie_charge_transformee"),
                                          freq = 3)

   y_charge = customblocks.YBlock(out_labels = ["t(s)", "consigne", "sortie_charge_transformee"], freq = 50)

   y_record = crappy.blocks.Multiplex(freq = 50)

   if fichier_d_enregistrement is not None :
      record = customblocks.CustomRecorder(filename = fichier_d_enregistrement,
                              labels = labels_a_enregistrer,
                              # ["t(s)", 
                              #    "x(mm)", 
                              #    "F(N)",
                              #    "entree_charge"],
                              parametres_a_inscrire = parametres_du_test
                              # , labels = labels_a_enregistrer
                              )
  

   crappy.link(gen, y_charge)
   crappy.link(gen, y_decharge)
   crappy.link(carte_NI, y_charge, modifier=_card_to_pid)
   crappy.link(carte_NI, y_decharge, modifier=_card_to_pid)
   crappy.link(y_charge, pid_charge)
   crappy.link(y_decharge, pid_decharge)
   crappy.link(pid_charge, carte_NI, modifier=_pid_to_card_charge)
   crappy.link(pid_decharge, carte_NI, modifier=_pid_to_card_decharge)
   crappy.link(carte_NI, gen, modifier=_card_to_pid)

   crappy.link(pid_charge, y_record, modifier=_pid_to_card_charge)
   crappy.link(pid_decharge, y_record, modifier=_pid_to_card_decharge)
   crappy.link(carte_NI, y_record, modifier=
                           [_card_to_recorder_and_graph, 
                           crappy.modifier.Diff(label="sortie_charge_transformee", 
                                                out_label="derivee_voltage")])
   if fichier_d_enregistrement is not None :
      crappy.link(y_record, record)
   crappy.link(carte_NI, graphe, modifier=_card_to_recorder_and_graph)
   crappy.link(gen, graphe, modifier=_gen_to_graph_in_tons)

   crappy.start()
   crappy.reset()

def demarrage_de_crappy_deplacement(consignes_generateur = None, fichier_d_enregistrement = None,
                        parametres_du_test = [], labels_a_enregistrer = None
                        # ,fenetre_d_integration = None, canevas_d_integration = None
                        ):
   if False :
      gen = crappy.blocks.Generator(path = consignes_generateur,
                                 cmd_label = 'consigne',
                                 spam = True,
                                 freq = 50)

      carte_NI = crappy.blocks.IOBlock(name = "Nidaqmx",
                                       labels = ["t(s)", "sortie_charge", 
                                                "sortie_deplacement"],
                                       cmd_labels = ["entree_decharge", "entree_charge"],
                                       initial_cmd = [0.0, 0.0],
                                       exit_values = [0.0, 0.0],
                                       channels=[{'name': 'Dev1/ao0'},
                                       {'name': 'Dev1/ao1'},
                                       {'name': 'Dev1/ai6'},
                                       {'name': 'Dev1/ai7'}],
                                       spam=True,
                                       freq = 50)

      pid_charge = crappy.blocks.PID(kp=1,
                              ki=0.01,
                              kd=0.01,
                              out_max=5,
                              out_min=-5,
                              i_limit=0.5,
                              target_label='consigne',
                              labels=["t(s)", 'entree_charge'],
                              input_label='sortie_charge_transformee',
                              freq = 50)

      pid_decharge = crappy.blocks.PID(kp=0.5,
                              ki=0.0,
                              kd=0.0,
                              out_max=5,
                              out_min=-5,
                              i_limit=0.5,
                              target_label='consigne',
                              labels=["t(s)", 'entree_decharge'],
                              input_label='sortie_charge_transformee',
                              freq = 50)

      y_charge = YBlock(out_labels = ["t(s)", "consigne", "sortie_charge_transformee"],
                              freq = 50)

      y_decharge = YBlock(out_labels = ["consigne", "sortie_charge_transformee"],
                              freq = 50)
   
   gen = crappy.blocks.Generator(path = consignes_generateur,
                              cmd_label = 'consigne',
                              # spam = True,
                              freq = 50)

   carte_NI = crappy.blocks.Fake_machine(k = 10000*450,
                                          l0 = 4000,
                                          maxstrain = 7,
                                          nu = 0.5,
                                          max_speed = 100,
                                          mode = 'speed',
                                          cmd_label = "entree_charge",
                                          plastic_law = plastic)
   
   pid_charge = crappy.blocks.PID(kp=1,
                                 ki=0.0,
                                 kd=0.0,
                                 out_max=5,
                                 out_min=-5,
                                 i_limit=0.5,
                                 target_label="consigne",
                                 labels=["t(s)", 'entree_charge'],
                                 input_label='sortie_charge_transformee',
                                 freq = 50)

   graphe = customblocks.EmbeddedGrapher(("t(s)", "consigne"), 
                              ("t(s)", "sortie_charge_transformee"),
                              freq = 3
                              # ,figure = fenetre_d_integration,
                              # canevas = canevas_d_integration
                              )

   # y_charge = customblocks.YBlock(out_labels = ["t(s)", "consigne", "sortie_charge_transformee"], freq = 50)
   y_charge = crappy.blocks.Multiplex(freq = 50)

   y_record = crappy.blocks.Multiplex(freq = 50)

   # if fichier_d_enregistrement is not None :
   #    record = customblocks.CustomRecorder(filename = fichier_d_enregistrement,
   #                            labels = ["t(s)", 
   #                               "x(mm)", 
   #                               "F(N)",
   #                               "entree_charge"],
   #                            parametres_a_inscrire = parametres_du_test
   #                            # , labels = labels_a_enregistrer
   #                            )

   crappy.link(gen, y_charge)
   crappy.link(carte_NI, y_charge, modifier = carte_to_gen)
   crappy.link(y_charge, pid_charge)
   crappy.link(pid_charge, carte_NI)
   crappy.link(carte_NI, gen, modifier = carte_to_gen)
   crappy.link(pid_charge, y_record)
   crappy.link(carte_NI, y_record)
   # if fichier_d_enregistrement is not None :
      # crappy.link(y_record, record)
   crappy.link(carte_NI, graphe, modifier = carte_to_pid)
   crappy.link(gen, graphe)   

   # crappy.link(gen, y_charge)
   # # crappy.link(gen, y_decharge)
   # # if type_d_asservissement == ASSERVISSEMENT_EN_CHARGE :    ## or match-case, maybe
   # crappy.link(carte_NI, y_charge, modifier=_card_to_pid)
   # crappy.link(carte_NI, y_decharge, modifier=_card_to_pid)
   # # else :
   # # crappy.link(carte_NI, y_charge, modifier=card_to_pid_in_millimeters)
   # # crappy.link(carte_NI, y_decharge, modifier=card_to_pid_in_millimeters)
   # crappy.link(y_charge, pid_charge)
   # crappy.link(y_decharge, pid_decharge)
   # crappy.link(pid_charge, carte_NI, modifier=_pid_to_card_charge)
   # crappy.link(pid_decharge, carte_NI, modifier=_pid_to_card_decharge)
   # crappy.link(carte_NI, gen, modifier=_card_to_pid)

   # crappy.link(pid_charge, y_record, modifier=_pid_to_card_charge)
   # crappy.link(pid_decharge, y_record, modifier=_pid_to_card_decharge)
   # crappy.link(carte_NI, y_record, modifier=
   #                         [_card_to_recorder_and_graph, 
   #                         crappy.modifier.Diff(label="sortie_charge_transformee", 
   #                                              out_label="derivee_voltage")])
   # if fichier_d_enregistrement is not None :
   #    crappy.link(y_record, record)
   # if fenetre_d_integration :
   #    crappy.link(carte_NI, graphe, modifier=_card_to_recorder_and_graph)
   #    crappy.link(gen, graphe, modifier=_gen_to_graph_in_tons)
   #    crappy.link(gen, graphe)

   crappy.start()
   crappy.reset()

def carte_to_gen(dic):
   dic["sortie_charge_transformee"] = 2 * dic["F(N)"] / 9.807 / 1000
   # print(dic["sortie_charge_transformee"])
   return dic

def carte_to_pid(dic):
   dic["sortie_charge_transformee"] = dic["F(N)"] / 9.807 / 1000
   # print(dic["sortie_charge_transformee"])
   return dic

def plastic(v: float, yield_strain: float = .005, rate: float = .02) -> float:
  if v > yield_strain:
    return ((v - yield_strain) ** 2 + rate ** 2) ** .5 - rate
  return 0

def demarrage_de_crappy_fake_machine(consignes_generateur = None, fichier_d_enregistrement = None,
                        parametres_du_test = [], labels_a_enregistrer = None):
   gen = crappy.blocks.Generator(path = consignes_generateur,
                              cmd_label = 'consigne',
                              # spam = True,
                              freq = 50)

   carte_NI = crappy.blocks.Fake_machine(k = 10000*450,
                                          l0 = 4000,
                                          maxstrain = 7,
                                          nu = 0.5,
                                          max_speed = 100,
                                          mode = 'speed',
                                          cmd_label = "entree_charge",
                                          plastic_law = plastic)
   
   pid_charge = crappy.blocks.PID(kp=1,
                                 ki=0.0,
                                 kd=0.0,
                                 out_max=5,
                                 out_min=-5,
                                 i_limit=0.5,
                                 target_label="consigne",
                                 labels=["t(s)", 'entree_charge'],
                                 input_label='sortie_charge_transformee',
                                 freq = 50)

   graphe = customblocks.EmbeddedGrapher(("t(s)", "consigne"), 
                              ("t(s)", "sortie_charge_transformee"),
                              freq = 3
                              # ,figure = fenetre_d_integration,
                              # canevas = canevas_d_integration
                              )

   # y_charge = customblocks.YBlock(out_labels = ["t(s)", "consigne", "sortie_charge_transformee"], freq = 50)
   y_charge = crappy.blocks.Multiplex(freq = 50)

   y_record = crappy.blocks.Multiplex(freq = 50)

   if fichier_d_enregistrement is not None :
      record = customblocks.CustomRecorder(filename = fichier_d_enregistrement,
                              labels = ["t(s)", 
                                 "x(mm)", 
                                 "F(N)",
                                 "entree_charge"],
                              parametres_a_inscrire = parametres_du_test
                              # , labels = labels_a_enregistrer
                              )

   pancarte = crappy.blocks.Dashboard(labels = ["t(s)", "F(N)", "sortie_charge_transformee"],
                                       freq = 5)

   crappy.link(gen, y_charge)
   crappy.link(carte_NI, y_charge, modifier = carte_to_gen)
   crappy.link(y_charge, pid_charge)
   crappy.link(pid_charge, carte_NI)
   crappy.link(carte_NI, gen, modifier = carte_to_gen)
   crappy.link(pid_charge, y_record)
   crappy.link(carte_NI, y_record)
   if fichier_d_enregistrement is not None :
      crappy.link(y_record, record)
   crappy.link(carte_NI, graphe, modifier = carte_to_pid)
   crappy.link(gen, graphe)   
   crappy.link(y_record, pancarte)

   crappy.start()
   crappy.reset()

def coef_PID_par_defaut():
   """FR : Renvoie la liste des coefficients par défaut de tous les PID.
   
   EN : Returns the list of the default coefficients of all PIDs."""
   liste_coef=[]
   #######################charge/decharge################
   ############charge#########
   ###position
   P_charge_pos=6
   I_charge_pos=0
   D_charge_pos=0
   liste_coef.append(P_charge_pos)
   liste_coef.append(I_charge_pos)
   liste_coef.append(D_charge_pos)
   ###charge_de_rupture
   P_charge_rupture=1
   I_charge_rupture=0.01
   D_charge_rupture=0.01
   liste_coef.append(P_charge_rupture)
   liste_coef.append(I_charge_rupture)
   liste_coef.append(D_charge_rupture)
   ###préétirage
   P_charge_pree=0.2
   I_charge_pree=0.001
   D_charge_pree=1
   liste_coef.append(P_charge_pree)
   liste_coef.append(I_charge_pree)
   liste_coef.append(D_charge_pree)
   ###fatigue
   P_charge_fatigue=0.5  
   I_charge_fatigue=0.001
   D_charge_fatigue=0.5
   liste_coef.append(P_charge_fatigue)
   liste_coef.append(I_charge_fatigue)
   liste_coef.append(D_charge_fatigue)
   ###palier
   P_charge_pal=1
   I_charge_pal=0.001
   D_charge_pal=0.1
   liste_coef.append(P_charge_pal)
   liste_coef.append(I_charge_pal)
   liste_coef.append(D_charge_pal)
   ############décharge#########
   ###position
   P_decharge_pos=2
   I_decharge_pos=0
   D_decharge_pos=0
   liste_coef.append(P_decharge_pos)
   liste_coef.append(I_decharge_pos)
   liste_coef.append(D_decharge_pos)
   ###charge_de_rupture
   P_decharge_rupture=0
   I_decharge_rupture=0
   D_decharge_rupture=0
   liste_coef.append(P_decharge_rupture)
   liste_coef.append(I_decharge_rupture)
   liste_coef.append(D_decharge_rupture)
   ###préétirage
   P_decharge_pree=0.05
   I_decharge_pree=0
   D_decharge_pree=0.003
   liste_coef.append(P_decharge_pree)
   liste_coef.append(I_decharge_pree)
   liste_coef.append(D_decharge_pree)
   ###fatigue
   P_decharge_fatigue=0.09
   I_decharge_fatigue=0.0
   D_decharge_fatigue=0.5
   liste_coef.append(P_decharge_fatigue)
   liste_coef.append(I_decharge_fatigue)
   liste_coef.append(D_decharge_fatigue)
   ###palier
   P_decharge_pal=0.1
   I_decharge_pal=0.0001
   D_decharge_pal=0.0
   liste_coef.append(P_decharge_pal)
   liste_coef.append(I_decharge_pal)
   liste_coef.append(D_decharge_pal)
   
   #######################maintien################
   ############charge#########
   ###position
   P_charge_pos=0.5
   I_charge_pos=0.05
   D_charge_pos=0.01
   liste_coef.append(P_charge_pos)
   liste_coef.append(I_charge_pos)
   liste_coef.append(D_charge_pos)
   ###charge_de_rupture
   P_charge_rupture=0.1
   I_charge_rupture=0.001
   D_charge_rupture=0.01
   liste_coef.append(P_charge_rupture)
   liste_coef.append(I_charge_rupture)
   liste_coef.append(D_charge_rupture)
   ###préétirage
   P_charge_pree=0.5
   I_charge_pree=0.05
   D_charge_pree=0.01
   liste_coef.append(P_charge_pree)
   liste_coef.append(I_charge_pree)
   liste_coef.append(D_charge_pree)
   ###fatigue
   P_charge_fatigue=0.5  
   I_charge_fatigue=0.05
   D_charge_fatigue=0.01
   liste_coef.append(P_charge_fatigue)
   liste_coef.append(I_charge_fatigue)
   liste_coef.append(D_charge_fatigue)
   ###palier
   P_charge_pal=0.5  
   I_charge_pal=0.05
   D_charge_pal=0.01
   liste_coef.append(P_charge_pal)
   liste_coef.append(I_charge_pal)
   liste_coef.append(D_charge_pal)
   ############décharge#########
   ###position
   P_decharge_pos=0.1
   I_decharge_pos=0
   D_decharge_pos=0
   liste_coef.append(P_decharge_pos)
   liste_coef.append(I_decharge_pos)
   liste_coef.append(D_decharge_pos)
   ###charge_de_rupture
   P_decharge_rupture=0.1
   I_decharge_rupture=0
   D_decharge_rupture=0
   liste_coef.append(P_decharge_rupture)
   liste_coef.append(I_decharge_rupture)
   liste_coef.append(D_decharge_rupture)
   ###préétirage
   P_decharge_pree=0.1
   I_decharge_pree=0
   D_decharge_pree=0
   liste_coef.append(P_decharge_pree)
   liste_coef.append(I_decharge_pree)
   liste_coef.append(D_decharge_pree)
   ###fatigue
   P_decharge_fatigue=0.05
   I_decharge_fatigue=0.01 
   D_decharge_fatigue=0.01
   liste_coef.append(P_decharge_fatigue)
   liste_coef.append(I_decharge_fatigue)
   liste_coef.append(D_decharge_fatigue)
   ###palier
   P_decharge_pal=0.1
   I_decharge_pal=0
   D_decharge_pal=0
   liste_coef.append(P_decharge_pal)
   liste_coef.append(I_decharge_pal)
   liste_coef.append(D_decharge_pal)
   
   return liste_coef
#V  
def capteur_fct(x):
#TODO : constantes WTF
   #convertion tension lue par le capteur ultrason -> tension étalonnée pour ne pas dépasser les valeurs limites en distance
   fonction=(x-2.18)*5/4.08
   return fonction 

def num_tonnes(x):
#TODO : constantes WTF liées à l'iso 2307
   ###fonction de conversion du numéro de référence à la tension de référence.
   fonction=(0.01*x**2/8)/9.807  # +-5%
   return fonction
  
def verif_pos(position_list,value) :
   """FR : Vérifie si la position du chariot est à "value".
   
   EN : Asserts if the test trolley is at "value"."""
   valid=0
   while valid < len(position_list) and position_list[valid] >= value-1 and position_list[valid] <= value+1 :
            valid+=1
   if valid==len(position_list) :
      return True
   return False
#V
def verif_valeur(load_list,value):
   """FR : Vérifie si la charge est à "value".
   
   EN : Asserts if the load is at "value"."""
   valid=0
   while valid < len(load_list) and \
      (value != 0 and load_list[valid]>=value-0.1 and load_list[valid]<=value+0.1 \
      or load_list[valid]>=0.01307 and load_list[valid]<=0.01309) :
         valid += 1
   if valid==len(load_list) :
      return True
   return False
#V
def verif_rupture(liste) :
   """FR : Vérifie s'il y a charge_de_rupture.
   
   EN : Asserts if charge_de_rupture happens."""
   for i in range(len(liste)-1):
      if liste[i+1]<liste[i]*0.3 and liste[i+1]>1 :
         return True
   return False
#V
def desactiver_bouton(btn):
   """FR : Désactive le bouton.
   
   EN : Deactivate the button."""
   btn["state"] = "disabled"
#V 
def activer_bouton(btn):
   """FR : Active le bouton.
   
   EN : Activate the button."""
   btn["state"] = "normal"
#V          
def modification_du_mot_de_passe(parent):
   """FR : Fenêtre de changement du mot de passe.
   
   EN : Password change window."""
   def enregistrer_mot_de_passe():
      """FR : Enregistre le nouveau mot de passe dans un fichier de config prédéfini.
      
      EN : Saves the new password in a predefined config file."""
      ecriture_donnee('mdp_liste.txt', mdp_val.get())
      fen_mdp.destroy()
   
   fen_mdp=Toplevel(parent)
   fen_mdp.lift()
   
   mdp_val=StringVar()
   
   Label(fen_mdp, text="Choisissez le nouveau mot de passe").grid(row=1,column=0,padx =10, pady =10)
   password_entry = Entry(fen_mdp, textvariable=mdp_val, width=30)
   password_entry.grid(row=1,column=1,padx =10, pady =10)
   password_entry.focus()
   
   Button(fen_mdp, text='Retour', command=fen_mdp.destroy).grid(row=4,column=0,padx =10, pady =10)
   Button(fen_mdp, text='Enregistrer', command=enregistrer_mot_de_passe).grid(row=4,column=1,padx =10, pady =10)
#V
def modification_des_chemins_d_acces(parent):
   """FR : Fenêtre de choix du dossier d'enregistrement et du chemin d'accès au 
   manuel du banc.
   
   EN : Saved files' directory and bench's manual access path choice window."""
   
   def chemin_suivant() :
      """FR : Enregistre les chemins dans un fichier de config prédéfini.
      
      EN : Saves the paths in a predefined config file."""
      
      ecriture_donnee('chemin_enre.txt', chemin_enre.get())
      ecriture_donnee('chemin_manuel.txt', chemin_aide.get())
      ecriture_donnee('nom_manuel.txt', nom_manuel.get())
      fen_chem.destroy()

   fen_chem=Toplevel(parent)
   
   chemin_enre=StringVar()
   chemin_aide=StringVar()
   nom_manuel=StringVar()
   chemin_enre.set(lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'chemin_enre.txt'))
   chemin_aide.set(lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'chemin_manuel.txt'))
   nom_manuel.set(lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'nom_manuel.txt'))
   
   Label(fen_chem, text="Choisissez le chemin des documents enregistrés").grid(row=1,column=0,padx =10, pady =10)
   Entry(fen_chem, textvariable=chemin_enre, width=100).grid(row=1,column=1,padx =10, pady =10)
   Label(fen_chem, text="Choisissez le chemin du manuel d'aide").grid(row=2,column=0,padx =10, pady =10)
   Entry(fen_chem, textvariable=chemin_aide, width=100).grid(row=2,column=1,padx =10, pady =10)
   Label(fen_chem, text="Choisissez le nom du manuel d'aide (ne pas oublier le .docx ou le .pdf)").grid(row=3,column=0,padx =10, pady =10)
   Entry(fen_chem, textvariable=nom_manuel, width=100).grid(row=3,column=1,padx =10, pady =10)
   Button(fen_chem, text='Retour',command=fen_chem.destroy).grid(row=4,column=0,padx =10, pady =10)
   Button(fen_chem, text='Enregistrer',command=chemin_suivant).grid(row=4,column=1,padx =10, pady =10)
#V
def fct_depart() :
   """FR : Fenêtre de choix du mode. Est lancée au début du programme.
   
   EN : Mode choice window. Is launched at the start of the program."""
   
   def utilisation_pour_R_et_D():
    #TODO : lock buttons from fenetre1 at creation and unlock them when this window 
    # is closed through any mean other than the validation of the password.
    # IDEA : use withdraw on the first window.
      """FR: Lance le mode R&D protégé par un mot de passe. 
      
      EN : Launches the R&D mode protected by a password.""" 
      def verification_mot_de_passe ():
         """FR : Vérifie le mot de passe.
         
         EN : Verifies the password."""
         global verrou_production
         verrou_production = OFF
         if mot_de_passe.get()==lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'mdp_liste.txt') :
            fenetre1.destroy()
            return fonction_principale()
         else :
            showinfo(title='Échec', message='Mot de passe incorrect')
      
      mot_de_passe = StringVar() 
      fenetre_mdp=Toplevel(fenetre1)
      Label(fenetre_mdp, text = 'mot de passe').grid(row=0, column=0, padx =20, pady =10)
      Entry(fenetre_mdp,textvariable=mot_de_passe,show='*', width=30).grid(row=0, column=1, padx =20, pady =10)
      Button(fenetre_mdp,text="Valider",command=verification_mot_de_passe).grid(row=1, column=1,padx =0, pady =10)
      Button(fenetre_mdp,text='Quitter', command=fenetre_mdp.destroy).grid(row=1, column=0,padx =0, pady =10)
   #PV   facultatif
   def utilisation_pour_production():
      """FR : Lance le mode Production.
      
      EN : Launches the Production mode."""
      global verrou_production
      verrou_production = ON
      fenetre1.destroy()
      return fonction_principale()
   #V
   fenetre1 = Tk()
   fenetre1.title("Sélection du mode")
   Label(fenetre1, text = "Veuillez sélectionner le mode d'utilisation",justify = CENTER).grid(row=0, column=0, padx =20, pady =10,columnspan=2)
   
   R_et_D_btn=Button(fenetre1,text="R&D",command=utilisation_pour_R_et_D)
   prod_btn=Button(fenetre1, text='Production', command=utilisation_pour_production)
   
 #TODO : tooltips. Tix has been deprecated for years.
   # bal = tix.Balloon(fenetre1)
   # bal.bind_widget(R_et_D_btn, msg="Cliquez ici pour effectuer tous types de tests (Attention : les sécurités sont désactivées)")
   # bal.bind_widget(prod_btn, msg="Cliquez ici pour effectuer un préétirage")
   
   R_et_D_btn.grid(row=1, column=0,padx =0, pady =10 )
   prod_btn.grid(row=1, column=1,padx =0, pady =10 )
   
 #TODO : tearoff's removal should be globalized
   menubar = Menu(fenetre1)
   aide= Menu(menubar, tearoff=0)
   aide.add_command(label="Afficher la documentation",command=RTM_protocol)
   menubar.add_cascade(label="Aide", menu=aide)
   fenetre1.configure(menu=menubar)
   
   fenetre1.mainloop() 
#PV  obligatoire (tix)
def configuration_initiale (init_titre, init_nom, 
      init_materiau, init_lg_banc, init_charge_rupt, init_diam_a_vide, 
      init_accroche, init_epissage, init_cabestan, init_lg_utile) :
   """FR : Fenêtre de configuration des valeurs initiales de l'essai.
   
   EN : Test's initial values configuration window."""
   global verrou_production
   
   def retour_au_choix_de_mode():
      """FR : Retourne à la fenêtre du choix de mode.
      
      EN : Gets back to the mode choice window."""
      global verrou_production
      fenetre2.destroy()
      verrou_production = RESTART
   #V
   def diam_cabestan(afficher):
      ###affiche la valeur du diamètre de cabestan si la case est cochée
      if afficher :
         Label(accroche_label,text="Diamètre cabestan (mm)").grid(row=15,column=0,padx =10, pady =10)
         Entry(accroche_label, textvariable=diametre_du_cabestan, width=10).grid(row=15,column=1,padx =10, pady =10)
      else :
         for widget in accroche_label.winfo_children()[-2:] :
            widget.destroy()
   #PV   facultatif
   def iso_quai():
      # Is okay
      """ """
      if is_test_iso.get() :
         Label( cordage_label, text = "Cordage épissé").grid(row = 1, column = 0, padx =10, pady =10)
         Radiobutton(cordage_label, text="Oui", variable=est_episse, value=True).grid(row = 1, column = 1, padx = 5, pady = 5)
         Radiobutton(cordage_label, text="Non", variable=est_episse, value=False).grid(row = 1, column = 2,padx = 5, pady = 5)
         Label(cordage_label, text = "Numéro de référence").grid(row = 3, column = 0, padx = 5, pady = 5)
         Entry(cordage_label, textvariable=diametre_a_vide, width=10).grid(row = 3, column = 2 ,padx = 5, pady = 5)
      else :
         for widget in cordage_label.winfo_children()[1:] :
            widget.destroy()
   #PV   facultatif
   fenetre2 = Tk()
   fenetre2.title("Configuration initiale")
   fenetre2.protocol("WM_DELETE_WINDOW", exit)

   titre = StringVar()
   titre.set(init_titre)
   nom = StringVar()
   nom.set(init_nom)
   materiau = StringVar()
   materiau.set(init_materiau)
   longueur_banc = IntVar()
   longueur_banc.set(init_lg_banc)
   charge_de_rupture = DoubleVar() 
   charge_de_rupture.set(init_charge_rupt)
   diametre_a_vide = DoubleVar()
   diametre_a_vide.set(init_diam_a_vide)
   type_d_accroche = IntVar()
   type_d_accroche.set(init_accroche)
   est_episse = BooleanVar()
   est_episse.set(init_epissage)
   diametre_du_cabestan = DoubleVar()
   diametre_du_cabestan.set(init_cabestan)
   longueur_utile = DoubleVar()
   longueur_utile.set(init_lg_utile)
   is_test_iso = BooleanVar()
   
   Label( fenetre2, text = "Titre").grid(row=1,column=0,padx =5, pady =5)
   entree_titre=Entry( fenetre2, textvariable=titre, width=30, validate="key", validatecommand=(fenetre2.register(_check_entree_string), '%P'))
   entree_titre.grid(row=1,column=1,padx =5, pady =5)

   Label( fenetre2, text = "Nom de l'opérateur").grid(row=2,column=0,padx =5, pady =5)
   entree_nom=Entry( fenetre2, textvariable=nom, width=30, validate="key", validatecommand=(fenetre2.register(_check_entree_string), '%P'))
   entree_nom.grid(row=2,column=1,padx =5, pady =5)

   Label( fenetre2, text = "Matériau").grid(row=4,column=0,padx =5, pady =5)
   entree_materiau=Entry( fenetre2, textvariable=materiau, width=30, validate="key", validatecommand=(fenetre2.register(_check_entree_string), '%P'))
   entree_materiau.grid(row=4,column=1,padx =5, pady =5)

   Label( fenetre2, text = "Charge de rupture (en tonnes)").grid(row=6,column=0,padx =5, pady =5)
   entree_charge_rupture=Entry( fenetre2, textvariable=charge_de_rupture, width=5, validate="key", validatecommand=(fenetre2.register(_check_entree_charge), '%P'))
   entree_charge_rupture.grid(row=6,column=1,padx =5, pady =5, sticky = "w")

   Label(fenetre2,text="Longueur utile de l'éprouvette (en m)").grid(row = 7, column = 0, padx = 5, pady = 5)
   Entry(fenetre2, textvariable=longueur_utile, width=5, validate="key", validatecommand=(fenetre2.register(_check_entree_longueur), '%P')).grid(row = 7, column = 1, padx = 5, pady = 5, sticky = "w")
         
   cadre_longueur_banc=LabelFrame( fenetre2)
   cadre_longueur_banc.grid(row=8,column=0,columnspan=3,padx =5, pady =5)
   Label(cadre_longueur_banc, text = 'Longueur utile du banc').grid(row=8,column=0,padx =5, pady =5)
   coche20m = Radiobutton(cadre_longueur_banc, text="<20m", variable=longueur_banc, value=1)
   coche20m.grid(row=8,column=1,padx =5, pady =5)
   coche22m = Radiobutton(cadre_longueur_banc, text="22m", variable=longueur_banc, value=2)
   coche22m.grid(row=9,column=1,padx =5, pady =5)
   coche24m = Radiobutton(cadre_longueur_banc, text="24m", variable=longueur_banc, value=3)
   coche24m.grid(row=10,column=1,padx =5, pady =5)
   coche26m = Radiobutton(cadre_longueur_banc, text="26m", variable=longueur_banc, value=4)
   coche26m.grid(row=11,column=1,padx =5, pady =5)  
   if verrou_production==0 :
      coche9m = Radiobutton(cadre_longueur_banc, text="7m (pour une pièce métallique)", variable=longueur_banc, value=5)
      coche9m.grid(row=12,column=1,padx =5, pady =5)

      accroche_label=LabelFrame(fenetre2)
      accroche_label.grid(row = 13, column = 0,columnspan = 3, padx = 5, pady = 5, sticky = "ew")
      Label(accroche_label, text = "Système d'accroche").grid(row=13,column=0,padx =5, pady =5)
      coche_axial= Radiobutton(accroche_label, text="Goupilles", variable=type_d_accroche, value=1, command = lambda : diam_cabestan(False))
      coche_axial.grid(row=13,column=1,padx =5, pady =5)
      coche_cabestan = Radiobutton(accroche_label, text="Amarrage à cabestan", variable=type_d_accroche, value=2, command = lambda : diam_cabestan(True))
      coche_cabestan.grid(row=14,column=1,padx =5, pady =5)
      
      cordage_label=LabelFrame(fenetre2)
      cordage_label.grid(row=16,column=0,columnspan=3,padx =5, pady =5, sticky = "ew")
      ttk.Checkbutton(cordage_label, text = "Test ISO-2307", variable = is_test_iso, onvalue = True, offvalue = False, command = iso_quai).grid(row = 0, column = 0, columnspan = 3, padx = 5, pady = 5, sticky = "w")
   charger_le_dernier_test = BooleanVar()
   charger_le_dernier_test.set(True)
   ttk.Checkbutton(fenetre2, text = "Charger les consignes du dernier test", variable = charger_le_dernier_test, onvalue = True, offvalue = False).grid(row = 18, column = 0, columnspan = 2, padx = 5, pady = 5)

   
   precedent1_btn=Button(fenetre2, text='Précédent', command=retour_au_choix_de_mode)
   precedent1_btn.grid(row=20, column=0,padx =5, pady =5)
   suivant1_btn=Button(fenetre2, text='Suivant', command=fenetre2.destroy)
   suivant1_btn.grid(row=20, column=1,padx =5, pady =5)

   menubar = Menu(fenetre2)
   fenetre2.config(menu=menubar)
   menu= Menu(menubar, tearoff=0)
   menubar.add_cascade(label="Autre", menu=menu)
   menu.add_command(label="Afficher la documentation",command=RTM_protocol)
   if verrou_production==0 :
      menu.add_command(label="Modifier les chemins d'accès",command=lambda: modification_des_chemins_d_acces(fenetre2))
      menu.add_command(label="Modifier le mot de passe",command=lambda: modification_du_mot_de_passe(fenetre2))
   
   # bal = tix.Balloon(fenetre2)
   # bal.bind_widget(precedent1_btn, msg="Retour au menu précédent")
   # bal.bind_widget(suivant1_btn, msg="Aller vers la fenêtre d'acquisition")
   # bal.bind_widget(entree_titre, msg="Entrez ici le titre du document")
   # bal.bind_widget(entree_nom, msg="Entrez ici le nom de l'opérateur")
   # bal.bind_widget(entree_materiau, msg="Entrez ici le matériau testé")
   # bal.bind_widget(entree_charge_rupture, msg="Entrez ici la charge de charge_de_rupture du matériau testé. Une sécurité est mise en place pour ne jamais dépasser 50% de cette charge")
   # bal.bind_widget(entree_prenom, msg="Entrez ici le prénom de l'opérateur")
   # bal.bind_widget(entree_diametre, msg="Le numéro de référence représente le diamètre à vide du cordage")

   # if verrou_production==0 :
   #    bal.bind_widget(coche9m, msg="Cochez cette case si le matériau testé est en métal")
   
   fenetre2.mainloop()
   
   return (titre.get(),nom.get(),materiau.get(),longueur_banc.get(),charge_de_rupture.get(),diametre_a_vide.get(),type_d_accroche.get(),est_episse.get(),diametre_du_cabestan.get(),longueur_utile.get(), is_test_iso.get(), charger_le_dernier_test.get())
#PV obligatoire (tix)
def fonction_principale(init_titre='', init_nom='', init_materiau='', 
      init_lg_banc=1, init_charge_rupt=0, init_diam_a_vide=0.0, init_accroche=1, 
      init_epissage=True, init_cabestan=40.0, init_lg_utile=0.0, init_type_d_asservissement = 0):
###fonction de fenêtre graphique

   def transformation_voltage_tonnage(x):
      """FR : Passe du voltage à des tonnes/2.
      
      EN : Passes from voltage to tons/2."""
      return (etalonnage_a * (x**2) + etalonnage_b * x + etalonnage_c)
   #V
   def retour_aux_entrees():
      """FR : Relance la fonction principale et renvoie l'utilisateur sur la fenêtre
       de saisie des conditions.
       
      EN : Restarts the main function and brings back the user to the conditions
       entries window."""
      choix_des_documents_a_enregistrer.set(0) # Ne pas conserver les documents actuels
      enregistrer_fct()
      fenetre_principale.destroy()
   #V
   def lecture_a_vide():
         ###fonction renvoyant la valeur lue lorsqu'aucun programme n'est lancé
         data=recup_data()
         valeur_en_cours=transformation_voltage_tonnage(data[6]*2)
         
         zone_charge_valeur.delete('valeur_charge_actuelle')
         zone_charge_valeur.create_text(250,75,text=round(valeur_en_cours,2),font=('Arial','100'),tags='valeur_charge_actuelle')
         
         valeur_en_cours=round(COEF_VOLTS_TO_MILLIMETERS*capteur_fct(data[7]))
            
         zone_valeur.delete('valeur_actuelle')
         zone_valeur.create_text(75,25,text=valeur_en_cours,font=('Arial','20'),tags='valeur_actuelle')
         if lire_a_vide.get() == True :
            zone_valeur.after(500,lecture_a_vide)

   def distance_fct():
      ###Fenêtre de consigne en position. 
      ####################################
      def distance_suite() :
         ###Fonction qui renvoie la valeur souhaitée si elle se trouve dans l'intervalle de 10-1900 mm
         if pos_var.get()<=1900 and pos_var.get()>=10 :
            consigne_fen_bis.destroy()
            zone_rappel_1.delete('zone1')
            zone_rappel_1.create_text(125,10,text='Consigne (mm): '+str(pos_var.get()),tags='zone1')
         else :
            showwarning('Attention !',"Consigne en position hors de l'intervalle ! Veuillez entrer une nouvelle valeur")
      def retour_fct() :
         ###Renvoi à la fenêtre précédente
         consigne_fen_bis.destroy()
         return parametrage_fct()
      ####################################

      consigne_fen_bis=Toplevel(fenetre_principale)
      consigne_fen_bis.title('Choix déplacement')
      Label(consigne_fen_bis, text="Veuillez choisir la valeur de position du chariot en mm (entre 10 et 1900) ",fg='blue').grid(row=0,padx =10, pady =10)
      Spinbox(consigne_fen_bis, from_=10,to=1900,increment=1, textvariable=pos_var, width=30).grid(row=1,padx =10, pady =10)
      Button(consigne_fen_bis,text='Retour', command=parametrage_fct).grid(row=4,column=0,padx =10, pady =10)
      Button(consigne_fen_bis,text='Enregistrer', command=distance_suite).grid(row=4,column=2,padx =10, pady =10)
      bouton_parametrage_consigne['bg']='green'
      consigne_choix.set(61)
      activer_bouton(start_btn)
      rappel_consigne.delete('consigne')
      rappel_consigne.create_text(125,10,text='Consigne position',tags='consigne') 
      
   def parametrage_fct ():
      ###Fenêtre de choix de la forme de la consigne
      global verrou_production
      
      def parametrage_suite() :
         ###renvoie la fenêtre suivante
      ####################################
         consigne_fen.destroy()
         parametrage_suite1()
      ####################################
      
      def retour_fct() :
         ###renvoie la fenêtre précédente
      ####################################
         consigne_fen.destroy()
         choix_du_type_d_asservissement()
      ####################################
      
      consigne_fen=Toplevel(fenetre_principale)
      Label(consigne_fen, text="Veuillez choisir la forme du signal de la consigne").grid(row=0,column=1,padx =10, pady =10)
      Radiobutton(consigne_fen, text="Préétirage", variable=consigne_choix, value=11).grid(row=1,column=1,padx =10, pady =10)
      
      if verrou_production==0 :
         Radiobutton(consigne_fen, text="Consigne rampe simple", variable=consigne_choix, value=21).grid(row=2,column=1,padx =10, pady =10)
         Radiobutton(consigne_fen, text="Consigne par paliers", variable=consigne_choix, value=22).grid(row=3,column=1,padx =10, pady =10)
         Radiobutton(consigne_fen, text="Rupture iso-2307", variable=consigne_choix, value=23).grid(row=4,column=1,padx =10, pady =10)
         Radiobutton(consigne_fen, text="Fatigue", variable=consigne_choix, value=31).grid(row=5,column=1,padx =10, pady =10)
      
      Button(consigne_fen,text='Suivant', command=parametrage_suite).grid(row=8,column=2,padx =10, pady =10)
      Button(consigne_fen,text='Retour', command=retour_fct).grid(row=8,column=0,padx =10, pady =10)
      
      menu1.entryconfigure(3, state=NORMAL)

   def parametrage_suite1():
      ###fenêtre de choix des valeurs de la consigne
      choix=consigne_choix.get()
      consigne_fen_bis=Toplevel(fenetre_principale)
      
      def retour_fct() :
         ### renvoie la fenêtre précédente
         consigne_fen_bis.destroy()
         parametrage_fct()
         
      def suivant():
         ### vérifie les valeurs, enregistre les valeurs et détruit la fenêtre
         if limite_val.get()>20 or limite_val.get()<0:
            showwarning('Attention','La valeur limite dépasse les 20 tonnes !')
            return 0
         try :
            if (int(temps_voulu.get()[:1])>60 or int(temps_voulu.get()[3:])>60) :
               showwarning('Attention','Temps indiqué ('+temps_voulu.get()+') incorrect ! Veuillez respecter le format mm:ss')
               return 0
            if (int(temps_palier_final.get()[:1])>60 or int(temps_palier_final.get()[3:])>60) :
               showwarning('Attention','Temps indiqué ('+temps_voulu.get()+') incorrect ! Veuillez respecter le format mm:ss')
               return 0
         except :
            if (consigne_choix.get()==11 or consigne_choix.get()==22 or consigne_choix.get()==31) :
               showwarning('Attention','Temps indiqué incorrect ! Veuillez respecter le format mm:ss')
               return 0
            
            
         if consigne_choix.get()==11 :
            zone_rappel_1.delete('zone1')
            zone_rappel_1.create_text(125,10,text='Consigne (tonnes): '+str(limite_val.get()),tags='zone1')
            zone_rappel_2.delete('zone2')
            zone_rappel_2.create_text(125,10,text='Temps maintien (mm:ss): '+str(temps_voulu.get()),tags='zone2')
         
         if consigne_choix.get()==21 :
            zone_rappel_1.delete('zone1')
            zone_rappel_1.create_text(125,10,text='Pente (tonnes/s): '+str(pente_val.get()),tags='zone1')
            zone_rappel_2.delete('zone2')
            zone_rappel_2.create_text(125,10,text='Valeur limite (tonnes): '+str(limite_val.get()),tags='zone2')
            
         if consigne_choix.get()==22 :
            zone_rappel_1.delete('zone1')
            zone_rappel_1.create_text(125,10,text='Pas des paliers (tonnes): '+str(consigne_val.get()),tags='zone1')
            zone_rappel_2.delete('zone2')
            zone_rappel_2.create_text(125,10,text='Pente (tonnes/s): '+str(pente_val.get()),tags='zone2')
            zone_rappel_3.delete('zone3')
            zone_rappel_3.create_text(125,10,text='Temps de maintien (mm:ss) : '+str(temps_voulu.get()),tags='zone3')
            zone_rappel_4.delete('zone4')
            zone_rappel_4.create_text(125,10,text='Valeur limite (tonnes) : '+str(limite_val.get()),tags='zone4')
            zone_rappel_5.delete('zone5')
            zone_rappel_5.create_text(125,10,text='Temps final : '+str(temps_palier_final.get()),tags='zone5')
            
         if consigne_choix.get()==23 :
            zone_rappel_1.delete('zone1')
            zone_rappel_1.create_text(125,10,text='Nombre de cycles : '+str(nb_cycles.get()),tags='zone1')
            if episse.get()==True:
               zone_rappel_2.delete('zone2')
               zone_rappel_2.create_text(125,10,text='Vitesse chariot (mm/min): '+str(pourc_var.get()),tags='zone2')
            
         if consigne_choix.get()==31 :
            zone_rappel_1.delete('zone1')
            zone_rappel_1.create_text(125,10,text='Valeur haute (tonnes) : '+str(limite_val.get()),tags='zone1')
            zone_rappel_2.delete('zone2')
            zone_rappel_2.create_text(125,10,text='Valeur basse (tonnes) : '+str(limite_basse.get()),tags='zone2')
            zone_rappel_3.delete('zone3')
            zone_rappel_3.create_text(125,10,text='Temps de maintien (mm:ss) : '+str(temps_voulu.get()),tags='zone3')
            zone_rappel_4.delete('zone4')
            zone_rappel_4.create_text(125,10,text='Nombre de cycles : '+str(nb_cycles.get()),tags='zone4')
         
         
         consigne_fen_bis.destroy()
         return 0
         
      if choix==11:

         consigne_fen_bis.title('Préétirage')
         Label(consigne_fen_bis, text="Veuillez choisir la valeur de la consigne (en tonnes) ").grid(row=0,padx =10, pady =10)
         Spinbox(consigne_fen_bis, from_=0,to=20,increment=0.01, textvariable=limite_val, width=30).grid(row=1,padx =10, pady =10)
         Label(consigne_fen_bis, text="Veuillez choisir le temps de préétirage (en mm:ss)").grid(row=2,padx =10, pady =10)
         Entry( consigne_fen_bis,textvariable= temps_voulu, width=30).grid(row=3,padx =10, pady =10)
         Button(consigne_fen_bis,text='Retour', command=retour_fct).grid(row=4,column=0,padx =10, pady =10)
         Button(consigne_fen_bis,text='Enregistrer', command=suivant).grid(row=4,column=2,padx =10, pady =10)
         btn=Button(consigne_fen_bis,text='btn')
         btn.config(image=img11)
         btn.grid(row=0,column=1,columnspan=2,rowspan=4,padx =10,pady =10)
         bouton_parametrage_consigne['bg']='green'
         activer_bouton(start_btn)
         valeur_minimale_de_déplacement.set(2000)
         rappel_consigne.delete('consigne')
         rappel_consigne.create_text(125,10,text='Consigne préétirage',tags='consigne') 
         
      if choix==21:

         consigne_fen_bis.title('Rupture rampe simple')
         Label(consigne_fen_bis, text="Veuillez choisir la valeur de la pente (en tonnes par secondes)").grid(row=1,padx =10, pady =10)
         Spinbox(consigne_fen_bis, from_=0,to=10,increment=0.01, textvariable=pente_val, width=30).grid(row=2,padx =10, pady =10)
         Label(consigne_fen_bis, text="Veuillez choisir une valeur limite de charge (en tonnes)").grid(row=3,padx =10, pady =10)
         Spinbox(consigne_fen_bis, from_=0,to=20,increment=0.1, textvariable=limite_val, width=30).grid(row=4,padx =10, pady =10)
         Label(consigne_fen_bis, text="Veuillez choisir le temps de maintien (en mm:ss)").grid(row=5,padx =10, pady =10)
         Entry( consigne_fen_bis,textvariable= temps_voulu, width=30).grid(row=6,padx =10, pady =10)
         Button(consigne_fen_bis,text='Retour', command=retour_fct).grid(row=7,column=0,padx =10, pady =10)
         Button(consigne_fen_bis,text='Enregistrer', command=suivant).grid(row=7,column=2,padx =10, pady =10)
         btn=Button(consigne_fen_bis,text='btn')
         btn.config(image=img21)
         btn.grid(row=1,column=1,columnspan=2,rowspan=5,padx =10,pady =10)
         limite_val.set(10)
         bouton_parametrage_consigne['bg']='green'
         activer_bouton(start_btn)
         normes.set('')
         valeur_minimale_de_déplacement.set(2000)
         rappel_consigne.delete('consigne')
         rappel_consigne.create_text(125,10,text='Consigne rampe simple',tags='consigne') 
            
      if choix==22:

         consigne_fen_bis.title('Rupture rampe par paliers')
         Label(consigne_fen_bis, text="Veuillez choisir la valeur du pas des paliers (en tonnes)").grid(row=0,padx =10, pady =10)
         Spinbox(consigne_fen_bis, from_=0,to=20,increment=0.01,  textvariable=consigne_val, width=30).grid(row=1,padx =10, pady =10)
         Label(consigne_fen_bis, text="Veuillez choisir la valeur de la pente (en tonnes par secondes)").grid(row=2,padx =10, pady =10)
         Spinbox(consigne_fen_bis, from_=0,to=1000,increment=0.01,  textvariable=pente_val, width=30).grid(row=3,padx =10, pady =10)
         Label(consigne_fen_bis, text="Veuillez choisir le temps de palier (en mm:ss)").grid(row=4,padx =10, pady =10)
         Entry( consigne_fen_bis, textvariable= temps_voulu, width=30).grid(row=5,padx =10, pady =10)
         Label(consigne_fen_bis, text="Veuillez choisir une valeur limite de charge (en tonnes)").grid(row=6,padx =10, pady =10)
         Spinbox(consigne_fen_bis, from_=0,to=20,increment=0.1, textvariable=limite_val, width=30).grid(row=7,padx =10, pady =10)
         Label(consigne_fen_bis, text="Veuillez choisir le temps de maintien final(en mm:ss)").grid(row=8,padx =10, pady =10)
         Entry( consigne_fen_bis,textvariable= temps_palier_final, width=30).grid(row=9,padx =10, pady =10)
         Button(consigne_fen_bis,text='Retour', command=retour_fct).grid(row=10,column=0,padx =10, pady =10)
         Button(consigne_fen_bis,text='Enregistrer', command=suivant).grid(row=10,column=2,columnspan=2,padx =10, pady =10)
         btn=Button(consigne_fen_bis,text='btn')
         btn.config(image=img22)
         btn.grid(row=0,column=1,columnspan=2,rowspan=20,padx =10,pady =10)
         limite_val.set(10)
         bouton_parametrage_consigne['bg']='green'
         activer_bouton(start_btn)
         normes.set('')
         valeur_minimale_de_déplacement.set(2000)
         rappel_consigne.delete('consigne')
         rappel_consigne.create_text(125,10,text='Consigne charge_de_rupture par paliers',tags='consigne') 
         
      if choix==23:
         consigne_fen_bis.title('iso-2307')
         if episse.get()==True :
            
            pourc2=utile.get()*0.02*1000
            pourc12=utile.get()*0.12*1000
            pas_scale=Scale(consigne_fen_bis,orient='horizontal',from_=pourc2, to=pourc12, resolution=1,length=150,variable=pourc_var,label='Vitesse (mm/min)')
            pas_scale.grid(row=3,column=0,padx =10, pady =10)

         coche_label=LabelFrame(consigne_fen_bis, text = "Nombre de cycles (cycles compris entre "+str(round(num_tonnes(int(num_ref.get())),4))+" tonnes et "+str(charge_de_rupture.get()/2)+" tonnes")
         coche_label.grid(row=4,column=0,padx =10, pady =10)
         Radiobutton(coche_label, text="3", variable=nb_cycles, value=3).grid(row=4,column=0,padx =10, pady =10)
         Radiobutton(coche_label, text="10", variable=nb_cycles, value=10).grid(row=5,column=0,padx =10, pady =10)
         Label(consigne_fen_bis, text="Veuillez choisir une valeur limite de charge (en tonnes)").grid(row=6,column=0,padx =10, pady =10)
         Spinbox(consigne_fen_bis, from_=0,to=20,increment=0.1, textvariable=limite_val, width=30).grid(row=7,column=0,padx =10, pady =10)
         Button(consigne_fen_bis,text='Retour', command=retour_fct).grid(row=8,column=0,padx =10, pady =10)
         Button(consigne_fen_bis,text='Enregistrer', command=suivant).grid(row=8,column=5,padx =10, pady =10)
         btn=Button(consigne_fen_bis,text='btn')
         btn.config(image=img23)
         btn.grid(row=3,column=5,rowspan=10,padx =10,pady =10)
         limite_val.set(10)
         bouton_parametrage_consigne['bg']='green'
         activer_bouton(start_btn)
         normes.set('iso-2307')
         valeur_minimale_de_déplacement.set(2000)
         rappel_consigne.delete('consigne')
         rappel_consigne.create_text(125,10,text='Consigne charge_de_rupture iso-2307',tags='consigne') 
         
      if choix==31:
         consigne_fen_bis.title('Fatigue')
         Label(consigne_fen_bis, text="Veuillez choisir la valeur HAUTE de la consigne (en tonnes)").grid(row=0,padx =10, pady =10)
         Spinbox(consigne_fen_bis, from_=0,to=20,increment=0.01, textvariable=limite_val, width=30).grid(row=1,padx =10, pady =10)
         Label(consigne_fen_bis, text="Veuillez choisir la valeur BASSE de la consigne (en tonnes)").grid(row=2,padx =10, pady =10)
         Spinbox( consigne_fen_bis,from_=0,to=20,increment=0.01, textvariable= limite_basse, width=30).grid(row=3,padx =10, pady =10)
         Label(consigne_fen_bis, text="Veuillez choisir le nombre de cycles").grid(row=4,padx =10, pady =10)
         Spinbox( consigne_fen_bis,from_=0,to=1000000,increment=1, textvariable= nb_cycles, width=30).grid(row=5,padx =10, pady =10)
         Label(consigne_fen_bis, text="Veuillez choisir le temps de maintient (en mm:ss)").grid(row=6,padx =10, pady =10)
         Entry( consigne_fen_bis, textvariable= temps_voulu, width=30).grid(row=7,padx =10, pady =10)
         Button(consigne_fen_bis,text='Retour', command=retour_fct).grid(row=8,column=0,padx =10, pady =10)
         Button(consigne_fen_bis,text='Enregistrer', command=suivant).grid(row=8,column=2,padx =10, pady =10)
         btn=Button(consigne_fen_bis,text='btn')
         btn.config(image=img31)
         btn.grid(row=0,column=1,columnspan=2,rowspan=10,padx =10,pady =10)
         bouton_parametrage_consigne['bg']='green'
         activer_bouton(start_btn)
         valeur_minimale_de_déplacement.set(2000)
         rappel_consigne.delete('consigne')
         rappel_consigne.create_text(125,10,text='Consigne fatigue',tags='consigne')
            
   def enregistrer_et_quitter():
      """FR : Fenêtre de choix des données à enregistrer avant de quitter ou relancer.
      
      EN : Window to choose which datas to save before quitting or launching another test."""
      def quitter():
         """FR : Enregistre et quitte.
         
         EN : Saves and quits."""
         choix_des_documents_a_enregistrer.set(check_val_brutes.get() + check_val_reelles.get())
         enregistrer_fct()
         exit()
      #V
      def relancer_un_essai():
         """FR : Enregistre et renvoie l'utilisateur sur la fenêtre de saisie des
          conditions du test.
         
         EN : Saves and brings back the user to the test conditions' entries window."""
         choix_des_documents_a_enregistrer.set(check_val_brutes.get() + check_val_reelles.get())
         enregistrer_fct()
         fenetre_de_sortie_du_programme.destroy()
         fenetre_principale.destroy()
      #V
      fenetre_de_sortie_du_programme = Toplevel(fenetre_principale)
      fenetre_de_sortie_du_programme.lift()

      check_val_brutes = IntVar()
      check_val_brutes.set(2 if choix_des_documents_a_enregistrer.get() >= 2 else 0)
      check_val_reelles = IntVar()
      check_val_reelles.set(1 if choix_des_documents_a_enregistrer.get() %2 == 1 else 0)
      Label(fenetre_de_sortie_du_programme, text="Veuillez choisir les valeurs à conserver :").grid(row=0,column=0, columnspan=3, padx =10, pady =10)
      ttk.Checkbutton(fenetre_de_sortie_du_programme, text="Valeurs réelles", variable=check_val_reelles, onvalue=1, offvalue=0).grid(row=2,column=0, columnspan=3, padx =10, pady =10)
      if verrou_production==0 :
         ttk.Checkbutton(fenetre_de_sortie_du_programme, text="Valeurs non étalonnées", variable=check_val_brutes, onvalue=2, offvalue=0).grid(row=3,column=0, columnspan=3, padx =10, pady =10)
      Button(fenetre_de_sortie_du_programme,text='Annuler', command=fenetre_de_sortie_du_programme.destroy).grid(row=5,column=0,padx =10, pady =10)
      Button(fenetre_de_sortie_du_programme,text='Relancer un essai', command=relancer_un_essai).grid(row=5,column=1,padx =10, pady =10)
      Button(fenetre_de_sortie_du_programme,text='Quitter', command=quitter).grid(row=5,column=2,padx =10, pady =10)
   #V        
   def choix_enregistrer_fct():
      """FR : Fenêtre de choix des documents à conserver.
      
      EN : Files to keep choice window."""
      def annulation() :
         """FR : Restore le choix précédent et ferme cette fenêtre.
         
         EN : Sets back the previous choice and closes this window."""
         choix_des_documents_a_enregistrer.set(choix_actuel)
         enregistrer_fen.destroy()
      #V
      choix_actuel = choix_des_documents_a_enregistrer.get()
      enregistrer_fen=Toplevel(fenetre_principale)
      enregistrer_fen.protocol("WM_DELETE_WINDOW", annulation)
      
      Label(enregistrer_fen, text="Veuillez choisir les documents à enregistrer").grid(row=0,column=1,padx =10, pady =10)
      Radiobutton(enregistrer_fen, text="aucun document", variable=choix_des_documents_a_enregistrer, value=0).grid(row=1,column=1,padx =10, pady =10)
      Radiobutton(enregistrer_fen, text="valeurs étalonnées (fichier excel et csv)", variable=choix_des_documents_a_enregistrer, value=1).grid(row=2,column=1,padx =10, pady =10)
      if verrou_production==0 :
         Radiobutton(enregistrer_fen, text="valeurs affichées (fichier excel et csv)", variable=choix_des_documents_a_enregistrer, value=2).grid(row=3,column=1,padx =10, pady =10)
         Radiobutton(enregistrer_fen, text="valeurs affichées et étalonnées (fichier excel et csv)", variable=choix_des_documents_a_enregistrer, value=3).grid(row=4,column=1,padx =10, pady =10)
      Button(enregistrer_fen,text='Retour', command=annulation).grid(row=5,column=0,padx =10, pady =10)
      Button(enregistrer_fen,text='Suivant', command=enregistrer_fen.destroy).grid(row=5,column=2,padx =10, pady =10)
   #V
   def enregistrer_fct():
   ###fenêtre d'enregistrement des valeurs. Créé les courbes, ferme les documents csv et excel, détruit les documents non voulu.
      # pour créer le .xlsx :
      nom_du_fichier_xlsx = lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + "chemin_enre.txt"
                              ) + str(datetime.datetime.now())[:11] + entrees[0] + ".xlsx"
      if path.exists(nom_du_fichier_xlsx):
         # If the file already exists, append a number to the name
         nom_du_fichier, extension = path.splitext(nom_du_fichier_xlsx)
         i = 1
         while path.exists(nom_du_fichier + "_%05d" % i + extension):
            i += 1
         nom_du_fichier_xlsx = nom_du_fichier + "_%05d" % i + extension
      # print(nom_du_fichier_xlsx, "debug xlsx")
      #TODO : Maintenant qu'on a un nom, faudrait ptet le remplir. Je vais essayer de voir si y a 
      #       d'exporter le .csv en .xlsx, puis de rajouter les courbes.
         
      if False : # Juste pour pouvoir collapse la fonction. Mettre en commentaire empêche de collapse.
         chart= workbook.add_chart({'type': 'scatter','subtype' : 'straight'})
         colonne1="".join(['=Sheet1!','$D$','2',':','$D$',str(compteur_pointeur.get())])
         colonne2="".join(['=Sheet1!','$E$','2',':','$E$',str(compteur_pointeur.get())])
         colonne3="".join(['=Sheet1!','$F$','2',':','$F$',str(compteur_pointeur.get())])
         colonne4="".join(['=Sheet1!','$G$','2',':','$G$',str(compteur_pointeur.get())])
         
         chart.add_series({
         'name': 'valeur charge (tonnes)',
         'categories': colonne1,
         'values': colonne2,
         'line':   {'width': 0.5},
         })
         if mode_manuel.get()=='off':
            chart.add_series({
            'name': 'consigne (tonnes)',
            'categories': colonne1,
            'values': colonne4,
            'line':   {'width': 0.5},
            })
         chart.add_series({
         'name': 'valeur déplacement (mm)',
         'categories': colonne1,
         'values': colonne3,
         'line':   {'width': 0.5},
         'y2_axis': 1,
         })
         chart.set_x_axis({
         'date_axis':  True,
         'num_format': 'hh:mm:ss',
         'name': 'temps en hh:mm:ss'
         })
         chart.set_title ({'name': 'Résultat'})
         chart.set_y_axis({'name': 'charge (tonnes)'})
         chart.set_y2_axis({'name': 'déplacement (mm)'})
         
         feuille.write(7,1,commentaires_de_l_utilisateur.get())
         chartsheet.set_chart(chart)
         chartsheet.activate()
         
         workbook.close()
         fichier_csv_1.close()
         fichier_csv_2.close()
         fichier_csv_3.close()
         match choix_des_documents_a_enregistrer.get() :
            case 0 :
               suppression_d_un_fichier(nom)
               suppression_d_un_fichier(nom_csv)
               suppression_d_un_fichier(nom_csv2)
               suppression_d_un_fichier(nom_csv3)
            case 1 :
               suppression_d_un_fichier(nom_csv2)
               suppression_d_un_fichier(nom_csv3)
            case 2 :
               suppression_d_un_fichier(nom_csv)
               suppression_d_un_fichier(nom_csv2)
            case 3 :
               suppression_d_un_fichier(nom_csv)
               suppression_d_un_fichier(nom_csv3)
      
   def do_pause():
      ###fonction permettant de faire pause sur l'animation
      
      # output(RESET)

      
      # activer_bouton(bouton_enregistrer_et_quitter)
      # desactiver_bouton(pause_btn)
      # activer_bouton(bouton_parametrage_consigne)
      # activer_bouton(enregistrer_btn)
      # activer_bouton(mise_a_0_btn)
      # activer_bouton(mise_a_tension_btn)
      # menu1.entryconfigure(4, state=NORMAL)
      # if bouton_parametrage_consigne['bg']=='green' or mode_manuel.get()=='on' :
      #    activer_bouton(start_btn)
      crappy.stop()
         
   def start_fct():
      """ """
      # demarrage_de_crappy(consignes_du_generateur, 
      #                      fichier_d_enregistrement = str(datetime.datetime.now())[:11] + entrees[0] + ".csv",
      #                 #TODO : add lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + "chemin_enre.txt")
      #                      parametres_du_test = parametres, labels_a_enregistrer = labels_voulus
      #                      # ,fenetre_d_integration = super_figure_ou_sera_placee_la_courbe,
      #                      # canevas_d_integration = cadre_courbe
      #                      )
      # desactiver_bouton(start_btn)
      launch_crappy_event.set()

   def certif_fct ():
      ###fenêtre de choix du certificat créé
      def entree_certif ():
      ########################
         ###fonction renvoyant à la fenêtre suivante
         match type_de_certificat.get() :
            case 1 :
               epreuve.set('Certificat de fatigue')
            case 2:
               epreuve.set('Certificat de rupture')
            case 3:
               epreuve.set("Certificat d'épreuve")
            case 4:
               epreuve.set('Certificat de préétirage')
         
         fen_choix_certif.destroy()
           ###fenêtre des entrées du certificat 
         def suivant_fct():
            ###fonction de création du pdf
            if askyesno('Attention',"Assurez vous d'avoir coché un choix d'enregistrement avant la création du certificat ! De plus, la création d'un certififat entraîne un arrêt du programme. Êtes vous sûr(e) de vouloir continuer ?") :

               today=datetime.datetime.now()

               an=str(today.year)[2:]
               mois=str(today.month)
               jour=str(today.day)
               
               if len(mois)==1:
                  mois = '0' + mois
                  
               if len(jour)==1:
                  jour = '0' + jour
                  
               date = jour + '/' + mois + '/' + an
               generate_pdf(date,commentaires_de_l_utilisateur.get(),str(valeur_maximale_de_charge.get()),reference.get(),epreuve.get(),materiau.get(),projet.get(),nom_prenom.get(),banc.get(),commande.get(),contact3.get(),contact2.get(),contact1.get(),adresse3.get(),adresse2.get(),adresse1.get(),societe.get(),normes.get(),validite.get())
               showinfo('Bravo','Certificat créé !')
               fen_choix_certif.destroy()
               
               desactiver_bouton(start_btn)
               activer_bouton(bouton_enregistrer_et_quitter)
               desactiver_bouton(pause_btn)
               desactiver_bouton(bouton_parametrage_consigne)
               desactiver_bouton(enregistrer_btn)
         
         def retour_certif ():
            ###renvoi à la fenêtre précédente 
            fen_choix_certif.destroy()
            certif_fct()
            
         def generate_pdf(date,com,maxi,ref,nature,mat_test,projet,operateur,mat_util,commande,contact3,contact2,contact1,adresse3,adresse2,adresse1,societe,normes,validite):
            ###fonction utilisant les entrées pour créer le pdf
            """
            letter :- (612.0, 792.0)
            A4 : 595.275590551 x 830.551181102
            """
            enregistrer_fct()
            
            if type_de_certificat.get()==1:
               nom_pdf="".join([nom[:len(nom)-20]+'_','Certificat_','Fatigue','.pdf'])
            if type_de_certificat.get()==2:
               nom_pdf="".join([nom[:len(nom)-20]+'_','Certificat_','Rupture','.pdf'])
            if type_de_certificat.get()==3:
               nom_pdf="".join([nom[:len(nom)-20]+'_','Certificat_','Epreuve','.pdf'])
            if type_de_certificat.get()==4:
               nom_pdf="".join([nom[:len(nom)-20]+'_','Certificat_','Préétirage','.pdf'])
               
            
            c = pdfgen.canvas.Canvas(nom_pdf, pagesize=A4)
            ###rectangles de couleur
            ###titres en gris
            c.setFillColorRGB(0.9,0.9,0.9)
            c.rect(52,560,498,14,fill=1)
            c.rect(52,709,498,15,fill=1)
            ###bordereau en bleu
            #2,48,98
            c.setFillColorRGB(0.00784,0.188,0.384)
            c.rect(52,750,498,42,fill=1)
            c.setFillColorRGB(0.99,0.99,0.99)
            c.setStrokeColorRGB(0.99,0.99,0.99)
            c.setFont('Times-Roman', 17)
            c.drawString(185,765,"Certificat d'épreuve")
            c.setFont('Times-Roman', 8)
            c.drawString(455,765,"24 rue Jacques Noël Sané")
            c.drawString(455,755,"29900 - CONCARNEAU")
            c.line(450,750,450,792)
            
            c.setFillColorRGB(0.1,0.1,0.1)
            c.setStrokeColorRGB(0.1,0.1,0.1)
            c.setFont('Helvetica-Bold', 8)

            c.drawString(130,108,com)
            c.drawString(185,448,validite)
            c.drawString(185,462,normes)
            c.drawString(185,476,ref)
            c.drawString(185,491,nature)
            c.drawString(185,505,mat_test)
            c.drawString(185,519,projet)
            c.drawString(184.5,534,operateur)
            c.drawString(185,548,mat_util)
            
            c.drawString(185,594,commande)
            c.drawString(185,609,contact3)
            c.drawString(185,624,contact2)
            c.drawString(185,638,contact1)
            c.drawString(185,653,adresse3)
            c.drawString(185,668,adresse2)
            c.drawString(185,682,adresse1)
            c.drawString(185,697,societe)
            
            c.drawString(400,63,'Fait à Concarneau, le ' + date)
            c.drawString(130,123,maxi)
            c.drawString(150,123,'tonnes')
            c.drawString(55,697,'Société :')
            c.drawString(55,682,'Adresse :')
            c.drawString(55,638,'Contact :')
            c.drawString(55,594,'Commande :')
            c.drawString(55,548,'Matériel :')
            c.drawString(55,534,'Opérateur :')
            c.drawString(55,519,'Projet :')
            c.drawString(55,505,'Materiel testé :')
            c.drawString(55,491,"Nature de l'épreuve :")
            c.drawString(55,476,"Référence de l'épreuve :")
            c.drawString(55,462,"Normes de charge_de_rupture validée :")
            c.drawString(55,447,"Date limite de validité :")
            c.drawString(55,123,'Charge maximum :')
            c.drawString(55,108,'Commentaires :')
            
            c.drawString(280,713,"A l'attention de :")
            c.drawString(270,564,"Description de l'épreuve :")
            
            ### grandes lignes horizontales partie haute 
            c.line(52,591,550,591)
            c.line(52,606,550,606)
            c.line(52,650,550,650)
            c.line(52,694,550,694)
            c.line(52,709,550,709)
            c.line(52,724,550,724)
            
            ### grandes lignes horizontales partie basse
            c.line(52,574,550,574)
            c.line(52,560,550,560)
            c.line(52,545,550,545)
            c.line(52,531,550,531)
            c.line(52,516,550,516)
            c.line(52,502,550,502)
            c.line(52,487,550,487)
            c.line(52,473,550,473)
            c.line(52,459,550,459)
            c.line(52,445,550,445)
            
            ### petites lignes horizontales partie haute
            c.line(182,621,550,621)
            c.line(182,635,550,635)
            c.line(182,665,550,665)
            c.line(182,679,550,679)
            
            ###lignes verticales partie haute
            c.line(52,724,52,591)
            c.line(182,709,182,591)
            c.line(550,724,550,591)
            
            ###lignes verticales partie basse
            c.line(52,574,52,445)
            c.line(182,560,182,445)
            c.line(550,574,550,445)
            
            ###logo Ino-Rope
            im = PIL.Image.open('Logo-Ino-Rope-blanc.png')
            c.drawInlineImage(im,455,775, width=90, height=14)
      
            nom_png="".join([nom[:len(nom)-5],'.png'])
            # generate_image(nom_png)
            im = PIL.Image.open(nom_png)   
            c.drawInlineImage(im,70,150, width=470, height=280)
            c.save()
            os.remove(nom_png)
            
         # def generate_image(nom_image):
         #    ###fonction de génération du fichier png comprenant la courbe excel du test.
         #    nom_final=''.join([nom])
         #    excel = Dispatch("Excel.Application")
         #    excel.ActiveWorkbook
         #    xlsWB = excel.Workbooks.Open(nom_final) 
         #    xlsWB.Sheets("sheet1")
         #    mychart = excel.Charts(1)
         #    mychart.Export(Filename="".join([nom_image]))
            
            
         fen_choix_certif=Toplevel(fenetre_principale)

         Label(fen_choix_certif, text="Destinataire du certificat").grid(row=0,column=0,columnspan=5,padx =10, pady =10)
         Label(fen_choix_certif, text="Société").grid(row=1,column=0,padx =10, pady =10)
         Label(fen_choix_certif, text="Adresse").grid(row=2,column=0,padx =10, pady =10)
         Label(fen_choix_certif, text="Rue").grid(row=2,column=1,padx =10, pady =10)
         Label(fen_choix_certif, text="Ville").grid(row=3,column=1,padx =10, pady =10)
         Label(fen_choix_certif, text="Code postal").grid(row=4,column=1,padx =10, pady =10)
         Label(fen_choix_certif, text="Contact").grid(row=5,column=0,padx =10, pady =10)
         Label(fen_choix_certif, text="Nom").grid(row=5,column=1,padx =10, pady =10)
         Label(fen_choix_certif, text="téléphone").grid(row=6,column=1,padx =10, pady =10)
         Label(fen_choix_certif, text="email").grid(row=7,column=1,padx =10, pady =10)
         Label(fen_choix_certif, text="Commande").grid(row=8,column=0,padx =10, pady =10)
         
         Label(fen_choix_certif, text="Description de l'épreuve").grid(row=9,column=0,columnspan=5,padx =10, pady =10)
         Label(fen_choix_certif, text="Banc de traction C10TL27").grid(row=10,column=0,padx =10, pady =10)
         Label(fen_choix_certif, text="Opérateur").grid(row=11,column=0,padx =10, pady =10)
         Label(fen_choix_certif, text="Projet").grid(row=12,column=0,padx =10, pady =10)
         Label(fen_choix_certif, text="Matériel testé").grid(row=13,column=0,padx =10, pady =10)
         Label(fen_choix_certif, text="Nature de l'expérience").grid(row=14,column=0,padx =10, pady =10)
         Label(fen_choix_certif, text="Référence").grid(row=15,column=0,padx =10, pady =10)
         Label(fen_choix_certif, text="Norme de charge_de_rupture validée").grid(row=16,column=0,padx =10, pady =10)
         Label(fen_choix_certif, text="Date limite de validité").grid(row=17,column=0,padx =10, pady =10)
         Label(fen_choix_certif, text="Commentaire").grid(row=18,column=0,padx =10, pady =10)
         
         Entry(fen_choix_certif, textvariable=societe, width=30).grid(row=1,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=adresse1, width=30).grid(row=2,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=adresse2, width=30).grid(row=3,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=adresse3, width=30).grid(row=4,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=contact1, width=30).grid(row=5,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=contact2, width=30).grid(row=6,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=contact3, width=30).grid(row=7,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=commande, width=30) .grid(row=8,column=2,padx =10, pady =10)
         
         Entry(fen_choix_certif, textvariable=banc, width=30).grid(row=10,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=nom_prenom, width=30).grid(row=11,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=projet, width=30).grid(row=12,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=materiau, width=30).grid(row=13,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=epreuve, width=30).grid(row=14,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=reference, width=30).grid(row=15,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=normes, width=30).grid(row=16,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=validite, width=30).grid(row=17,column=2,padx =10, pady =10)
         Entry(fen_choix_certif, textvariable=commentaires_de_l_utilisateur, width=30).grid(row=18,column=2,padx =10, pady =10)
         
         Button(fen_choix_certif, text='Retour',command=retour_certif).grid(row=19,column=0,padx =10, pady =10)
         Button(fen_choix_certif, text='Suivant',command=suivant_fct).grid(row=19,column=2,padx =10, pady =10)
         
         
      ########################
   
      fen_choix_certif=Toplevel(fenetre_principale)
      fen_choix_certif.title('Choix de certificat')
      
      Label(fen_choix_certif, text="Veuillez choisir le certificat que vous voulez créer", justify = CENTER).grid(row=1,column=1,columnspan=3,padx =10, pady =10)
      Radiobutton(fen_choix_certif, text='Fatigue', variable=type_de_certificat, value=1).grid(row=2,column=1,columnspan=3,padx =10, pady =10)
      Radiobutton(fen_choix_certif, text='Rupture', variable=type_de_certificat, value=2).grid(row=3,column=1,columnspan=3,padx =10, pady =10)
      Radiobutton(fen_choix_certif, text='150% Charge de travail', variable=type_de_certificat, value=3).grid(row=4,column=1,columnspan=3,padx =10, pady =10)
      Radiobutton(fen_choix_certif, text='Pré-étirage', variable=type_de_certificat, value=4).grid(row=5,column=1,columnspan=3,padx =10, pady =10)

      Button(fen_choix_certif, text='Retour',command=fen_choix_certif.destroy).grid(row=6,column=1,padx =10, pady =10)
      Button(fen_choix_certif, text='Suivant',command=entree_certif).grid(row=6,column=3,padx =10, pady =10)

   def color_on() :
      ###fonction de coloration des boutons du mode manuel en mode 'on'
      off_button['bg']='gray'
      activer_bouton(start_btn)
      # output(RESET)
   
   def color_off() :
      ###fonction de coloration des boutons du mode manuel en mode 'off'
      on_button['bg']='gray'
      if bouton_parametrage_consigne['bg']=='green':
         activer_bouton(start_btn)
      else :
         desactiver_bouton(start_btn)
         
   def mise_a_0_fct():
      ###fonction de mise à la position 0 du chariot
      type_d_asservissement.set(2)
      consigne_choix.set(62)
      desactiver_bouton(mise_a_0_btn)
      desactiver_bouton(mise_a_tension_btn)
      rappel_asserv.delete('asservissement')
      rappel_asserv.create_text(125,10,text='Asservissement en position',tags='asservissement')
      rappel_consigne.delete('consigne')
      rappel_consigne.create_text(125,10,text=' ',tags='consigne')
      zone_rappel_1.delete('zone1')
      zone_rappel_1.create_text(125,10,text='Mise à 0 position',tags='zone1')
      zone_rappel_2.delete('zone2')
      zone_rappel_3.delete('zone3')
      zone_rappel_4.delete('zone4')
      do_pause()
      return start_fct()
      
   def mise_a_tension_fct():
      ### fonction de mise à la charge du chariot
      type_d_asservissement.set(2)
      consigne_choix.set(63)
      desactiver_bouton(mise_a_0_btn)
      desactiver_bouton(mise_a_tension_btn)
      rappel_asserv.delete('asservissement')
      rappel_asserv.create_text(125,10,text='Asservissement en position',tags='asservissement')
      rappel_consigne.delete('consigne')
      rappel_consigne.create_text(125,10,text=' ',tags='consigne')
      zone_rappel_1.delete('zone1')
      zone_rappel_1.create_text(125,10,text='Mise en tension',tags='zone1')
      zone_rappel_2.delete('zone2')
      zone_rappel_3.delete('zone3')
      zone_rappel_4.delete('zone4')
      do_pause()
      return start_fct()
   
 #TODO : Gérer les différents PID et leur réglage. 
 #       Voir sensi_page() et reglage_des_coef_des_PID() dans les fonctions jetées.

   def reinitialiser ():
      ###fonction de réinitialisation de la consigne et des valeurs utilisé lors de l'animation
      
      lire_a_vide.set(True)
      choix_des_documents_a_enregistrer.set(1)
      valeur_minimale_de_déplacement.set(2000)
      valeur_maximale_de_déplacement.set(-10000)
      valeur_maximale_de_charge.set(-10000)
      consigne_choix.set(0) 
      consigne_val.set(0) 
      memoire_consigne.set(0)
      pente_val.set(0)
      limite_val.set(0)
      decharge.set(0)
      limite_basse.set(0)
      nb_cycles.set(0)
      temps_voulu.set('00:00')
      temps_palier_final.set('00:00')
      pos_var.set(0)
      rappel_asserv.delete('asservissement')
      rappel_asserv.create_text(125,10,text=' ',tags='asservissement')
      rappel_consigne.delete('consigne')
      rappel_consigne.create_text(125,10,text=' ',tags='consigne') 
      zone_rappel_1.delete('zone1')
      zone_rappel_1.create_text(125,10,text=' ',tags='zone1')
      zone_rappel_2.delete('zone2')
      zone_rappel_2.create_text(125,10,text=' ',tags='zone2')
      zone_rappel_3.delete('zone3')
      zone_rappel_3.create_text(125,10,text=' ',tags='zone3')
      zone_rappel_4.delete('zone4')
      zone_rappel_4.create_text(125,10,text=' ',tags='zone4')
      
      desactiver_bouton(start_btn)
      activer_bouton(bouton_enregistrer_et_quitter)
      desactiver_bouton(pause_btn)
      
      menu1.entryconfigure(1, state=DISABLED)
      menu1.entryconfigure(2, state=DISABLED)
      menu1.entryconfigure(3, state=DISABLED)
      
      showinfo('Info','Consigne réinitialisée !')
      return 0
   
   def fenetre_d_affichage_secondaire():
      """FR : Crée une fenêtre secondaire affichant la consigne en plus gros.
      
      EN : Creates a secondary window that prints the setpoint bigger."""
      def anim_second():
         data=recup_data()
         valeur_en_cours=transformation_voltage_tonnage(data[6]*2)
         canvas_second.delete('valeur_charge_actuelle')
         canvas_second.create_text(500,500,text=round(valeur_en_cours,2),font=('Arial','200'),tags='valeur_charge_actuelle')
         canvas_second.after(500,anim_second)
      #V
      fenetre_affichage_secondaire=Toplevel(fenetre_principale)
      canvas_second=Canvas(fenetre_affichage_secondaire,height=1000,width=1000,bg='#ffffff')
      canvas_second.grid()
      anim_second()
   #V
   def modif_etalonnage_fct():
      ###fenêtre de modification du mot de passe
      def modif_etalonnage_suite():
         ecriture_donnee('etal_a.txt', etal_a_val.get())
         ecriture_donnee('etal_b.txt', etal_b_val.get())
         ecriture_donnee('etal_c.txt', etal_c_val.get())
         fen_etal.destroy()
      
      fen_etal=Toplevel(fenetre_principale)
      
      etal_a_val=StringVar()
      etal_a_val.set(lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'etal_a.txt'))
      etal_b_val=StringVar()
      etal_b_val.set(lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'etal_b.txt'))
      etal_c_val=StringVar()
      etal_c_val.set(lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'etal_c.txt'))
      
      label_etal=Label(fen_etal, text="La fonction d'étalonnage est sous la forme ax²+bx+c")
      
      label_a_etal=Label(fen_etal, text="Entrez la valeur de a")
      etal_a_entree = Entry(fen_etal, textvariable=etal_a_val, width=30)
      label_b_etal=Label(fen_etal, text="Entrez la valeur de b")
      etal_b_entree = Entry(fen_etal, textvariable=etal_b_val, width=30)
      label_c_etal=Label(fen_etal, text="Entrez la valeur de c")
      etal_c_entree = Entry(fen_etal, textvariable=etal_c_val, width=30)
     
      retour_btn=Button(fen_etal, text='Retour',command=fen_etal.destroy)
      suivant_btn=Button(fen_etal, text='Enregistrer',command=modif_etalonnage_suite)
      
      label_etal.grid(row=0,column=0,padx =10, pady =10)
      label_a_etal.grid(row=1,column=0,padx =10, pady =10)
      etal_a_entree.grid(row=1,column=1,padx =10, pady =10)
      label_b_etal.grid(row=2,column=0,padx =10, pady =10)
      etal_b_entree.grid(row=2,column=1,padx =10, pady =10)
      label_c_etal.grid(row=3,column=0,padx =10, pady =10)
      etal_c_entree.grid(row=3,column=1,padx =10, pady =10)
      retour_btn.grid(row=4,column=0,padx =10, pady =10)
      suivant_btn.grid(row=4,column=1,padx =10, pady =10)
   
   def choix_du_type_d_asservissement(type_d_asservissement_actuel = 0):
      """FR : Fenêtre pour choisir si l'asservissement doit se faire en position ou
      en charge.
      
      EN : Window to choose if the driving is to be done in charge or position."""
      def validation_du_choix():
         """FR : Adapte les menus et ouvre la fenêtre de paramétrage du type d'asservissement
         choisi.
         
         EN : Adapts the menus and opens the settings window corresponding to the chosen
         driving type."""
         fen_choix_asserv.destroy()
      #V
      def annulation() :
         """FR : Restore le type d'asservissement précédent avant de quitter.
         
         EN : Restores the previous driving type before quitting."""
         type_d_asservissement.set(type_d_asservissement_actuel)
         fen_choix_asserv.destroy()
      #V

      fen_choix_asserv=Tk()
      type_d_asservissement = IntVar()
      type_d_asservissement.set(type_d_asservissement_actuel)

      Label(fen_choix_asserv, text="Veuillez selectionner le type d'asservissement").grid(row=1,column=1,rowspan=2,padx=10,pady=10)
      Radiobutton(fen_choix_asserv, text="Asservissement en charge",fg='green', variable=type_d_asservissement, value=1).grid(row=3,column=1,padx=10,pady=10)
      Radiobutton(fen_choix_asserv, text="Asservissement en  position",fg='red', variable=type_d_asservissement, value=2).grid(row=4,column=1,padx=10,pady=10)
      Button(fen_choix_asserv, text='Retour',command = annulation).grid(row=5,column=0,padx=10,pady=10)
      Button(fen_choix_asserv, text='Suivant',command = fen_choix_asserv.destroy).grid(row=5,column=2,padx=10,pady=10)
      fen_choix_asserv.protocol("WM_DELETE_WINDOW", annulation)
      fen_choix_asserv.mainloop()
      return type_d_asservissement.get()
   #V
   def choix_des_consignes_du_generateur():
      """FR : Fenêtre de configuration des consignes à suivre pendant l'essai.
      
      EN : Setup window for the setpoints to follow during the test."""
      def surcouche_ajout(indice_de_cette_consigne):
         """FR : Évite de rajouter une consigne si l'utilisateur annule.
         
         EN : Avoids adding a setpoint if the user cancels."""
         def choix_du_type_de_consigne(type_de_la_consigne_ajoutee):
            """FR : Ouvre la fenêtre d'ajout de consigne correspondante et place cette consigne au bon endroit
            dans la liste des consignes.
            
            EN : Opens the corresponding setpoint adding window and places this setpoint at the right place in 
            the list of setpoints."""
            consigne_a_modifier = ajout_ou_modification_d_une_consigne({"type" : type_de_la_consigne_ajoutee})
                  
            if consigne_a_modifier is not None :
               consignes_du_generateur.append(consigne_a_modifier)
               for i in range (len(consignes_du_generateur)-1, indice_de_cette_consigne, -1) :
                  consignes_du_generateur[i], consignes_du_generateur[i - 1] = consignes_du_generateur[i - 1], consignes_du_generateur[i]
               return actualisation_des_boutons()
         #V
         type_de_consigne = IntVar()

         fenetre_du_choix_du_type_de_consigne = Toplevel(fenetre_de_choix_des_consignes)
         fenetre_du_choix_du_type_de_consigne.title("Ajout d'une consigne")
         fenetre_du_choix_du_type_de_consigne.protocol("WM_DELETE_WINDOW", lambda : [type_de_consigne.set(-1), fenetre_du_choix_du_type_de_consigne.destroy()])
         
         Label(fenetre_du_choix_du_type_de_consigne, width = 30, text = "Veuillez choisir une consigne.").grid(row = 0, column = 0, columnspan = 3, padx = 5, pady = 10)
         Button(fenetre_du_choix_du_type_de_consigne, width = 20, text = "Palier", command = lambda : [fenetre_du_choix_du_type_de_consigne.destroy(), choix_du_type_de_consigne("constant")]).grid(row = 1, column = 0, columnspan = 3, padx = 5, pady = 5)
         Button(fenetre_du_choix_du_type_de_consigne, width = 20, text = "Rampe simple", command = lambda : [fenetre_du_choix_du_type_de_consigne.destroy(), choix_du_type_de_consigne("ramp")]).grid(row = 2, column = 0, columnspan = 3, padx = 5, pady = 5)
         Button(fenetre_du_choix_du_type_de_consigne, width = 20, text = "Cycles de paliers", command = lambda : [fenetre_du_choix_du_type_de_consigne.destroy(), choix_du_type_de_consigne("cyclic")]).grid(row = 3, column = 0, columnspan = 3, padx = 5, pady = 5)
         Button(fenetre_du_choix_du_type_de_consigne, width = 20, text = "Cycles de rampes", command = lambda : [fenetre_du_choix_du_type_de_consigne.destroy(), choix_du_type_de_consigne("cyclic_ramp")]).grid(row = 4, column = 0, columnspan = 3, padx = 5, pady = 5)
         Button(fenetre_du_choix_du_type_de_consigne, width = 20, text = "Sinus", command = lambda : [fenetre_du_choix_du_type_de_consigne.destroy(), choix_du_type_de_consigne("sine")]).grid(row = 5, column = 0, columnspan = 3, padx = 5, pady = 5)
      #V
      def surcouche_modification(indice_de_cette_consigne):
         """FR : Évite de modifier la consigne si l'utilisateur annule.
         
         EN : Avoids modifying the setpoint if the user cancels."""
         nonlocal consignes_du_generateur
         consigne_a_modifier = ajout_ou_modification_d_une_consigne(dict(consignes_du_generateur[indice_de_cette_consigne]))
         if consigne_a_modifier is not None :
            consignes_du_generateur[indice_de_cette_consigne] = consigne_a_modifier
            return actualisation_des_boutons()
      #V
      def ajout_ou_modification_d_une_consigne(consigne_a_changer):
         """FR : Fenêtre permettant de définir ou modifier les paramètres de la consigne du type 
         selectionné. 
         
         EN : Window allowing to define or modify the parameters of the setpoint of the chosen type."""
         def ajout_ou_modification_validee():
            """FR : Valide cette consigne et enregistre ses valeurs dans le dictionnaire à renvoyer.
            
            EN : Validates this setpoint and saves its values in the dictonnary to return."""
            nonlocal validation, consigne_a_changer, fenetre_de_modification_d_une_consigne
            validation = True

            match consigne_a_changer['type'] :
               case "constant" :
                  consigne_a_changer["value"] = tons_to_volts(value.get())
                  if type_de_condition.get() == 0 :
                     consigne_a_changer["condition"] = None
                  else :
                     consigne_a_changer["condition"] = "delay=" + str(condition_en_temps.get())
               case "ramp" :
                  consigne_a_changer["speed"] = tons_to_volts(speed.get())
                  match type_de_condition.get() :
                     case 0 :
                        consigne_a_changer["condition"] = None
                     case 1 :
                        consigne_a_changer["condition"] = LABEL_SORTIE_EN_CHARGE + ">" + str(condition_superieure_a_charge.get())
                     case 2 :
                        consigne_a_changer["condition"] = LABEL_SORTIE_EN_CHARGE + "<" + str(condition_inferieure_a_charge.get())
                     case 3 :
                        consigne_a_changer["condition"] = "delay=" + str(condition_en_temps.get())
               case "cyclic" :
                  consigne_a_changer["value1"] = tons_to_volts(value1.get())
                  consigne_a_changer["condition1"] = "delay=" + str(condition1.get())

                  consigne_a_changer["value2"] = tons_to_volts(value2.get())
                  consigne_a_changer["condition2"] = "delay=" + str(condition2.get())

                  consigne_a_changer["cycles"] = nombre_de_cycles.get()
               case "cyclic_ramp" :
                  consigne_a_changer["speed1"] = tons_to_volts(speed1.get())
                  match type_de_condition1.get() :
                     case 0 :
                        consigne_a_changer["condition1"] = None
                     case 1 :
                        consigne_a_changer["condition1"] = LABEL_SORTIE_EN_CHARGE + ">" + str(condition_superieure_a_charge1.get())
                     case 2 :
                        consigne_a_changer["condition1"] = LABEL_SORTIE_EN_CHARGE + "<" + str(condition_inferieure_a_charge1.get())
                     case 3 :
                        consigne_a_changer["condition1"] = "delay=" + str(condition_en_temps1.get())
                  
                  consigne_a_changer["speed2"] = tons_to_volts(speed2.get())
                  match type_de_condition2.get() :
                     case 0 :
                        consigne_a_changer["condition2"] = None
                     case 1 :
                        consigne_a_changer["condition2"] = LABEL_SORTIE_EN_CHARGE + ">" + str(condition_superieure_a_charge2.get())
                     case 2 :
                        consigne_a_changer["condition2"] = LABEL_SORTIE_EN_CHARGE + "<" + str(condition_inferieure_a_charge2.get())
                     case 3 :
                        consigne_a_changer["condition2"] = "delay=" + str(condition_en_temps2.get())
                  
                  consigne_a_changer["cycles"] = nombre_de_cycles.get()
               case "sine" :
                  if pic_bas.get() > pic_haut.get() :
                     showwarning("Attention", "Le pic haut doit être supérieur au pic bas")
                     validation = False
                     return
                  if periode.get() == 0 :
                     consigne_a_changer["freq"] = 0
                  else :
                     consigne_a_changer["freq"] = 1/periode.get()
                  consigne_a_changer["amplitude"] = tons_to_volts(pic_haut.get() - pic_bas.get())
                  consigne_a_changer["offset"] = tons_to_volts((pic_haut.get() + pic_bas.get()) / 2)
                  consigne_a_changer["phase"] = phase.get() * pi / 2
                  match type_de_condition.get() :
                     case 0 :
                        consigne_a_changer["condition"] = None
                     case 3 :
                        consigne_a_changer["condition"] = "delay=" + str(condition_en_cycles.get() * periode.get())
            fenetre_de_modification_d_une_consigne.destroy()
         #V
         validation = False
         est_une_modif = len(consigne_a_changer) > 1 # False si ajout, True si modification
         fenetre_de_modification_d_une_consigne = Toplevel(fenetre_de_choix_des_consignes)
         if est_une_modif :
            fenetre_de_modification_d_une_consigne.title("Modification d'une consigne")
         else :
            fenetre_de_modification_d_une_consigne.title("Ajout d'une consigne")
         Label(fenetre_de_modification_d_une_consigne, text = "Type :").grid(row = 0, column = 0, padx = 5, pady = 5)
         Label(fenetre_de_modification_d_une_consigne, text = f" {TYPES_DE_CONSIGNE[consigne_a_changer['type']]}").grid(row = 0, column = 1, columnspan = 3, padx = 5, pady = 5)

         match consigne_a_changer["type"] :
            case "constant" :
               value = DoubleVar()
               if est_une_modif :
                  value.set(volts_to_tons(consigne_a_changer['value']))
               Label(fenetre_de_modification_d_une_consigne, text = "Valeur en tonnes :").grid(row = 1, column = 0, padx = 5, pady = 5)
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = value, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 1, column = 1, padx = 5, pady = 5)
               condition_en_temps = DoubleVar()
               type_de_condition = IntVar()
               if est_une_modif :
                  cond = consigne_a_changer["condition"]
                  if cond is None :
                     type_de_condition.set(0)
                  else :
                     type_de_condition.set(3)
                     condition_en_temps.set(float(cond[DEBUT_CONDITION_TEMPS:]))
               Label(fenetre_de_modification_d_une_consigne, text = "Condition d'arrêt :").grid(row = 2, column = 0, padx = 5, pady = 5)
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "aucune limite", variable = type_de_condition, value = 0).grid(row = 2, column = 1, columnspan = 4, padx = 5, pady = 5, sticky = 'w')

               Radiobutton(fenetre_de_modification_d_une_consigne, text = "pendant", variable = type_de_condition, value = 3).grid(row = 5, column = 1, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_en_temps, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 5, column = 2, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "s").grid(row = 5, column = 3, padx = 5, pady = 5, sticky = 'w')
            case "ramp" :
               speed = DoubleVar()
               if est_une_modif :
                  speed.set(volts_to_tons(consigne_a_changer['speed']))
               Label(fenetre_de_modification_d_une_consigne, text = "Vitesse en tonnes/secondes :").grid(row = 1, column = 0, padx = 5, pady = 5)
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = speed, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_vitesse_charge), '%P')).grid(row = 1, column = 1, padx = 5, pady = 5)
               condition_superieure_a_charge = DoubleVar()
               condition_inferieure_a_charge = DoubleVar()
               condition_en_temps = DoubleVar()
               type_de_condition = IntVar()
               if est_une_modif :
                  cond = consigne_a_changer["condition"]
                  if cond is None :
                     type_de_condition.set(0)
                  elif '>' in cond :
                     type_de_condition.set(1)
                     condition_superieure_a_charge.set(float(cond[DEBUT_CONDITION_CHARGE:]))
                  elif '<' in cond :
                     type_de_condition.set(2)
                     condition_inferieure_a_charge.set(float(cond[DEBUT_CONDITION_CHARGE:]))
                  else :
                     type_de_condition.set(3)
                     condition_en_temps.set(float(cond[DEBUT_CONDITION_TEMPS:]))
               
               Label(fenetre_de_modification_d_une_consigne, text = "Condition d'arrêt :").grid(row = 2, column = 0, padx = 5, pady = 5)
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "aucune limite", variable = type_de_condition, value = 0).grid(row = 2, column = 1, columnspan = 4, padx = 5, pady = 5, sticky = 'w')
               
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "      >", variable = type_de_condition, value = 1).grid(row = 3, column = 1, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_superieure_a_charge, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 3, column = 2, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 3, column = 3, padx = 5, pady = 5, sticky = 'w')
               
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "      <", variable = type_de_condition, value = 2).grid(row = 4, column = 1, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_inferieure_a_charge, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 4, column = 2, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 4, column = 3, padx = 5, pady = 5, sticky = 'w')
               
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "pendant", variable = type_de_condition, value = 3).grid(row = 5, column = 1, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_en_temps, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 5, column = 2, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "s").grid(row = 5, column = 3, padx = 5, pady = 5, sticky = 'w')
            case "cyclic" :
               value1 = DoubleVar()
               value2 = DoubleVar()
               if est_une_modif :
                  value1.set(volts_to_tons(consigne_a_changer['value1']))
                  value2.set(volts_to_tons(consigne_a_changer['value2']))
               Label(fenetre_de_modification_d_une_consigne, text = "Valeur en tonnes du premier palier :").grid(row = 1, column = 0, padx = 5, pady = 5)
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = value1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 1, column = 1, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "Valeur en tonnes du deuxième palier :").grid(row = 3, column = 0, padx = 5, pady = 5)
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = value2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 3, column = 1, padx = 5, pady = 5)
               condition1 = DoubleVar()
               condition2 = DoubleVar()
               nombre_de_cycles = IntVar()
               if est_une_modif :
                  condition1.set(float(consigne_a_changer["condition1"][DEBUT_CONDITION_TEMPS:]))
                  condition2.set(float(consigne_a_changer["condition2"][DEBUT_CONDITION_TEMPS:]))
                  nombre_de_cycles.set(int(consigne_a_changer["cycles"]))
               else :
                  nombre_de_cycles.set(1)

               Label(fenetre_de_modification_d_une_consigne, text = "Durée du premier palier :").grid(row = 2, column = 0, padx = 5, pady = 5)
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 2, column = 1, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "s").grid(row = 2, column = 2, padx = 5, pady = 5, sticky = 'w')

               Label(fenetre_de_modification_d_une_consigne, text = "Durée du deuxième palier :").grid(row = 4, column = 0, padx = 5, pady = 5)
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 4, column = 1, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "s").grid(row = 4, column = 2, padx = 5, pady = 5, sticky = 'w')

               Label(fenetre_de_modification_d_une_consigne, text = "Nombre de cycles :").grid(row = 5, column = 0, padx = 5, pady = 5)
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = nombre_de_cycles, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_cycles), '%P')).grid(row = 5, column = 1, padx = 5, pady = 5)
            case "cyclic_ramp" :
               speed1 = DoubleVar()
               speed2 = DoubleVar()
               if est_une_modif :
                  speed1.set(volts_to_tons(consigne_a_changer['speed1']))
                  speed2.set(volts_to_tons(consigne_a_changer['speed2']))
               Label(fenetre_de_modification_d_une_consigne, text = "Vitesse en tonnes/secondes :").grid(row = 1, column = 0, padx = 5, pady = 5)
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = speed1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_vitesse_charge), '%P')).grid(row = 1, column = 1, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "Vitesse en tonnes/secondes :").grid(row = 5, column = 0, padx = 5, pady = 5)
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = speed2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_vitesse_charge), '%P')).grid(row = 5, column = 1, padx = 5, pady = 5)
               condition_superieure_a_charge1 = DoubleVar()
               condition_inferieure_a_charge1 = DoubleVar()
               condition_en_temps1 = DoubleVar()
               type_de_condition1 = IntVar()
               condition_superieure_a_charge2 = DoubleVar()
               condition_inferieure_a_charge2 = DoubleVar()
               condition_en_temps2 = DoubleVar()
               type_de_condition2 = IntVar()
               nombre_de_cycles = IntVar()
               if est_une_modif :
                  cond1 = consigne_a_changer["condition1"]
                  cond2 = consigne_a_changer["condition2"]
                  nombre_de_cycles.set(int(consigne_a_changer["cycles"]))
                  if '>' in cond1 :
                     type_de_condition1.set(1)
                     condition_superieure_a_charge1.set(float(cond1[DEBUT_CONDITION_CHARGE:]))
                  elif '<' in cond1 :
                     type_de_condition1.set(2)
                     condition_inferieure_a_charge1.set(float(cond1[DEBUT_CONDITION_CHARGE:]))
                  else :
                     type_de_condition1.set(3)
                     condition_en_temps1.set(float(cond1[DEBUT_CONDITION_TEMPS:]))
                  
                  if '>' in cond2 :
                     type_de_condition2.set(1)
                     condition_superieure_a_charge2.set(float(cond2[DEBUT_CONDITION_CHARGE:]))
                  elif '<' in cond2 :
                     type_de_condition2.set(2)
                     condition_inferieure_a_charge2.set(float(cond2[DEBUT_CONDITION_CHARGE:]))
                  else :
                     type_de_condition2.set(3)
                     condition_en_temps2.set(float(cond2[DEBUT_CONDITION_TEMPS:]))
               else :
                  type_de_condition1.set(3)
                  type_de_condition2.set(3)
                  nombre_de_cycles.set(1)
               
               Label(fenetre_de_modification_d_une_consigne, text = "Condition de passage à la deuxième :").grid(row = 2, column = 0, padx = 5, pady = 5)
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "      >", variable = type_de_condition1, value = 1).grid(row = 2, column = 1, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_superieure_a_charge1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 2, column = 2, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 2, column = 3, padx = 5, pady = 5, sticky = 'w')
               
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "      <", variable = type_de_condition1, value = 2).grid(row = 3, column = 1, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_inferieure_a_charge1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 3, column = 2, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 3, column = 3, padx = 5, pady = 5, sticky = 'w')
               
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "pendant", variable = type_de_condition1, value = 3).grid(row = 4, column = 1, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_en_temps1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 4, column = 2, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "s").grid(row = 4, column = 3, padx = 5, pady = 5, sticky = 'w')

               Label(fenetre_de_modification_d_une_consigne, text = "Condition d'arrêt :").grid(row = 6, column = 0, padx = 5, pady = 5)
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "      >", variable = type_de_condition2, value = 1).grid(row = 6, column = 1, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_superieure_a_charge2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 6, column = 2, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 6, column = 3, padx = 5, pady = 5, sticky = 'w')
               
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "      <", variable = type_de_condition2, value = 2).grid(row = 7, column = 1, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_inferieure_a_charge2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 7, column = 2, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 7, column = 3, padx = 5, pady = 5, sticky = 'w')
               
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "pendant", variable = type_de_condition2, value = 3).grid(row = 8, column = 1, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_en_temps2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 8, column = 2, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "s").grid(row = 8, column = 3, padx = 5, pady = 5, sticky = 'w')

               Label(fenetre_de_modification_d_une_consigne, text = "Nombre de cycles :").grid(row = 10, column = 0, padx = 5, pady = 5)
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = nombre_de_cycles, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_cycles), '%P')).grid(row = 10, column = 1, padx = 5, pady = 5)
            case "sine" :
               periode = DoubleVar()
               pic_haut = DoubleVar()
               pic_bas = DoubleVar()
               phase = IntVar()
               if est_une_modif :
                  if consigne_a_changer['freq'] :
                     periode.set(1/consigne_a_changer['freq'])
                  pic_haut.set(volts_to_tons(consigne_a_changer['offset'] + consigne_a_changer['amplitude'] / 2))
                  pic_bas.set(volts_to_tons(consigne_a_changer['offset'] - consigne_a_changer['amplitude'] / 2))
                  phase.set(int(consigne_a_changer['phase'] * 2 / pi + 0.05)) # +0.05 en cas d'approximation
               Label(fenetre_de_modification_d_une_consigne, text = "Période en secondes :").grid(row = 1, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = periode, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 1, column = 2, padx = 5, pady = 5, sticky = 'w')
               Label(fenetre_de_modification_d_une_consigne, text = "Valeur maxinimale en tonnes :").grid(row = 2, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = pic_haut, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 2, column = 2, padx = 5, pady = 5, sticky = 'w')
               Label(fenetre_de_modification_d_une_consigne, text = "Valeur minimale en tonnes :").grid(row = 3, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = pic_bas, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 3, column = 2, padx = 5, pady = 5, sticky = 'w')
               Label(fenetre_de_modification_d_une_consigne, text = "Départ du sinus :").grid(row = 4, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'w')
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "Au centre, vers le haut", variable = phase, value = 0).grid(row = 4, column = 2, padx = 5, pady = 5, sticky = 'w')
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "En haut", variable = phase, value = 1).grid(row = 5, column = 2, padx = 5, pady = 5, sticky = 'w')
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "Au centre, vers le bas", variable = phase, value = 2).grid(row = 6, column = 2, padx = 5, pady = 5, sticky = 'w')
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "En bas", variable = phase, value = 3).grid(row = 7, column = 2, padx = 5, pady = 5, sticky = 'w')
               condition_superieure_a_charge = DoubleVar()
               condition_inferieure_a_charge = DoubleVar()
               condition_en_cycles = DoubleVar()
               type_de_condition = IntVar()
               if est_une_modif :
                  cond = consigne_a_changer["condition"]
                  if cond is None :
                     type_de_condition.set(0)
                  else :
                     type_de_condition.set(3)
                     condition_en_temps.set(float(cond[DEBUT_CONDITION_TEMPS:]))
               
               Label(fenetre_de_modification_d_une_consigne, text = "Condition d'arrêt :").grid(row = 8, column = 0, columnspan = 2, padx = 5, pady = 5)
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "aucune limite", variable = type_de_condition, value = 0).grid(row = 8, column = 2, columnspan = 4, padx = 5, pady = 5, sticky = 'w')
               Radiobutton(fenetre_de_modification_d_une_consigne, text = "pendant", variable = type_de_condition, value = 3).grid(row = 11, column = 2, padx = 5, pady = 5, sticky = 'w')
               Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_en_cycles, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 11, column = 3, padx = 5, pady = 5)
               Label(fenetre_de_modification_d_une_consigne, text = "cycle(s)").grid(row = 11, column = 4, padx = 5, pady = 5, sticky = 'w')
         
         Button(fenetre_de_modification_d_une_consigne, text = "Annuler", command = fenetre_de_modification_d_une_consigne.destroy).grid(row = 100, column = 0, columnspan = 2, padx = 5, pady = 5)
         Button(fenetre_de_modification_d_une_consigne, text = "Valider", command = ajout_ou_modification_validee).grid(row = 100, column = 2, columnspan = 3, padx = 5, pady = 5)
         
         fenetre_de_modification_d_une_consigne.wait_window()
         if validation :
            return consigne_a_changer
      #V
      def suppression_de_toutes_les_consignes():
         """FR : Supprime toutes les consignes.
         
         EN : Deletes all the setpoints."""
         nonlocal consignes_du_generateur
         consignes_du_generateur = []
         return actualisation_des_boutons()
      #V
      def annulation_des_changements():
         """FR : Annule les changements et restore la lsite de consignes précédente.
         
         EN : Cancels the changes and restores the list to its former state."""
         nonlocal consignes_du_generateur, premieres_consignes_validees
         consignes_du_generateur = consignes_precedentes
         fenetre_de_choix_des_consignes.destroy()
      #V
      def suppression_d_une_consigne(indice_consigne):
         """FR : Supprime la consigne donnée.
         
         EN : Deletes the given setpoint."""
         nonlocal consignes_du_generateur
         consignes_du_generateur.pop(indice_consigne)
         return actualisation_des_boutons()
      #V
      def chargement_des_consignes():
         """FR : Ouvre une fenêtre de sélection de fichier pour choisir une liste de consignes à charger.
         
         EN : Opens a file selection window to choose a list of setpoints to load."""
         chemin_du_fichier = askopenfilename(title = "Consignes à charger", initialdir = DOSSIER_CONFIG_ET_CONSIGNES, filetypes = [("fichier json", "*.json")])
         if chemin_du_fichier :
            with open(chemin_du_fichier, 'r') as fichier_de_consignes :
               nonlocal consignes_du_generateur
               consignes_potentielles = load(fichier_de_consignes)
               for i in range(len(consignes_potentielles)) :
                  if "type" not in consignes_potentielles[i].keys():
                     showwarning("Fichier incorrect : aucune consigne trouvée.")
                     break
                  elif i == len(consignes_potentielles) - 1 :
                     consignes_du_generateur = consignes_potentielles
            actualisation_des_boutons()
      #V
      def enregistrement_des_consignes():
         """FR : Ouvre une fenêtre de sélection de fichier pour choisir où enregistrer la liste de consignes actuelle.
         
         EN : Opens a file selection window to choose where to save the current list of setpoints."""
         chemin_du_fichier = asksaveasfilename(initialdir = DOSSIER_CONFIG_ET_CONSIGNES, filetypes = [("fichier json", "*.json")], defaultextension = ".json")
         if chemin_du_fichier :
            with open(chemin_du_fichier, 'w') as fichier_de_consignes :
               dump(consignes_du_generateur, fichier_de_consignes)
      #V
      def validation_des_consignes():
         """FR : Enregistre ces consignes en tant que dernier test et lance la fenêtre principale.
         
         EN : Saves those setpoints as the last test and launches the main window."""
         nonlocal premieres_consignes_validees
         premieres_consignes_validees = True
         chemin_du_dernier_test = DOSSIER_CONFIG_ET_CONSIGNES
         if type_d_asservissement == ASSERVISSEMENT_EN_CHARGE :
            chemin_du_dernier_test += "consignes_du_test_precedent_charge.json"
         else :
            chemin_du_dernier_test += "consignes_du_test_precedent_deplacement.json"
         with open(chemin_du_dernier_test, 'w') as fichier_des_consignes_du_dernier_test :
            dump(consignes_du_generateur, fichier_des_consignes_du_dernier_test)
         fenetre_de_choix_des_consignes.destroy()
      #V
      def actualisation_des_boutons():
         """FR : Gère l'affichage des consignes et de leurs boutons associés.
         
         EN : Manages the display of the setpoints and their associated buttons."""
         for widget in cadre_interne_consignes.winfo_children() :
            widget.destroy()

         Button(cadre_interne_consignes, text = "Insérer une consigne au départ", command = lambda : surcouche_ajout(0)).grid(row = 0, column = 1, padx = 5, pady = 12)
         if verrou_production == OFF :
            Button(cadre_interne_consignes, text = "Charger depuis un fichier", command = chargement_des_consignes).grid(row = 0, column = 0, padx = 5, pady = 12)
            Button(cadre_interne_consignes, text = "Enregistrer dans un fichier", command = enregistrement_des_consignes).grid(row = 0, column = 2, padx = 5, pady = 12)
         if len(consignes_du_generateur) :
            Label(cadre_interne_consignes, text = "Consigne(s) actuellement prévue(s) :").grid(row = 1, column = 0, columnspan = 3, padx = 5, pady = 4)
            indice_de_cette_consigne = 0
            for consigne_du_generateur in consignes_du_generateur :
               indice_de_cette_consigne += 1
               label_de_cette_consigne = ""
               match consigne_du_generateur['type'] :
                  case "ramp" :
                     label_de_cette_consigne = f"Rampe simple de {2 * consigne_du_generateur['speed']}T/s"
                     condition_d_arret = consigne_du_generateur["condition"]
                     if condition_d_arret is None :
                        label_de_cette_consigne += ", dure indéfiniment"
                     elif condition_d_arret.startswith('delay') :
                        label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                     else :
                        label_de_cette_consigne += f" jusqu'à {condition_d_arret[DEBUT_CONDITION_CHARGE:]}T"
                  case "constant" :
                     label_de_cette_consigne = "Palier à "
                     label_de_cette_consigne += f"{2 * consigne_du_generateur['value']}T"
                     condition_d_arret = consigne_du_generateur["condition"]
                     if condition_d_arret is None :
                        label_de_cette_consigne += ", dure indéfiniment"
                     elif condition_d_arret.startswith('delay') :
                        label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                     else :
                        label_de_cette_consigne += f" maintenu jusqu'à atteindre {condition_d_arret[DEBUT_CONDITION_CHARGE:]}T"
                  case "cyclic_ramp" :
                     label_de_cette_consigne = f"{consigne_du_generateur['cycles']} cycles de rampes : "
                     label_de_cette_consigne += f"{2 * consigne_du_generateur['speed1']}T/s"
                     condition_d_arret = consigne_du_generateur["condition1"]
                     if condition_d_arret.startswith('delay') :
                        label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                     else :
                        label_de_cette_consigne += f" jusqu'à {condition_d_arret[DEBUT_CONDITION_CHARGE:]}T"
                     label_de_cette_consigne += f", {2 * consigne_du_generateur['speed2']}T/s"
                     condition_d_arret = consigne_du_generateur["condition2"]
                     if condition_d_arret.startswith('delay') :
                        label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                     else :
                        label_de_cette_consigne += f" jusqu'à {condition_d_arret[DEBUT_CONDITION_CHARGE:]}T"
                  case "cyclic" :
                     label_de_cette_consigne = f"{consigne_du_generateur['cycles']} cycles de paliers : "
                     label_de_cette_consigne += f"{2 * consigne_du_generateur['value1']}T"
                     condition_d_arret = consigne_du_generateur["condition1"]
                     if condition_d_arret.startswith('delay') :
                        label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                     else :
                        label_de_cette_consigne += f" jusqu'à {condition_d_arret[DEBUT_CONDITION_CHARGE:]}T"
                     label_de_cette_consigne += f", {2 * consigne_du_generateur['value2']}T"
                     condition_d_arret = consigne_du_generateur["condition2"]
                     if condition_d_arret.startswith('delay') :
                        label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                     else :
                        label_de_cette_consigne += f" jusqu'à {condition_d_arret[DEBUT_CONDITION_CHARGE:]}T"
                  case "sine" :
                     label_de_cette_consigne = f"Sinus allant de {2 * (consigne_du_generateur['offset'] - consigne_du_generateur['amplitude'] / 2)}T à {2 * (consigne_du_generateur['offset'] + consigne_du_generateur['amplitude'] / 2)}T, de période {1 / consigne_du_generateur['freq']}s, démarrant "
                     match int(consigne_du_generateur['phase'] * 2 / pi + 0.05) :
                        case 0 :
                           label_de_cette_consigne += "croissant au centre"
                        case 1 :
                           label_de_cette_consigne += "à son maximum"
                        case 2 :
                           label_de_cette_consigne += "décroissant au centre"
                        case 3 :
                           label_de_cette_consigne += "à son minimum"
                     condition_d_arret = consigne_du_generateur["condition"]
                     if condition_d_arret is None :
                        label_de_cette_consigne += ", dure indéfiniment"
                     else :
                        label_de_cette_consigne += f" pendant {round(float(condition_d_arret[DEBUT_CONDITION_TEMPS:]) * consigne_du_generateur['freq'], 2)} cycles"

               cadre_de_cette_consigne = LabelFrame(cadre_interne_consignes)
               cadre_de_cette_consigne.grid(row = (2 * indice_de_cette_consigne), column = 0, columnspan = 3, padx = 5, pady = 4, sticky = 'w' + 'e')
               Label(cadre_de_cette_consigne, text = label_de_cette_consigne).grid(row = 1, column = 0, padx = 5, pady = 4, sticky = 'w')
               label_du_numero_de_bloc = Label(cadre_interne_consignes, text = f"Bloc {indice_de_cette_consigne}")
               label_du_numero_de_bloc.grid(row = (2 * indice_de_cette_consigne), column = 0, padx = 5, pady = 0, sticky = 'nw')
               # fenetre_de_choix_des_consignes.wm_attributes('-transparentcolor', label_du_numero_de_bloc['bg'])
               # Label(cadre_de_cette_consigne, image = PhotoImage(file = "C:\\Users\\R&D\\Desktop\\Stage Inorope\\icones boutons\\rampe simple.png")).grid(row = 1, column = 0, padx = 5, pady = 5)
               Button(cadre_de_cette_consigne, text = "Supprimer cette consigne", command = lambda i = indice_de_cette_consigne - 1 : suppression_d_une_consigne(i)).grid(row = 1, column = 1, padx = 5, pady = 5)
               Button(cadre_de_cette_consigne, text = "Modifier cette consigne", command = lambda i = indice_de_cette_consigne - 1 : surcouche_modification(i)).grid(row = 1, column = 2, padx = 5, pady = 5, sticky = 'e')
               Button(cadre_interne_consignes, text = "Insérer une consigne", command = lambda i = indice_de_cette_consigne : surcouche_ajout(i)).grid(row = (2 * indice_de_cette_consigne + 1), column = 1, padx = 5, pady = 5, sticky = 'e')
               cadre_interne_consignes.columnconfigure(0, weight=1)
               cadre_interne_consignes.columnconfigure(1, weight=1)
               cadre_interne_consignes.columnconfigure(2, weight=1)
         Button(cadre_interne_consignes, text = "Annuler les changements", command = annulation_des_changements).grid(row = (2 * NOMBRE_DE_CONSIGNES_MAXIMAL + 2), column = 0, padx = 5, pady = 5)
         Button(cadre_interne_consignes, text = "Tout supprimer", command = suppression_de_toutes_les_consignes).grid(row = (2 * NOMBRE_DE_CONSIGNES_MAXIMAL + 2), column = 1, padx = 5, pady = 5)
         Button(cadre_interne_consignes, text = "Valider", command = validation_des_consignes).grid(row = (2 * NOMBRE_DE_CONSIGNES_MAXIMAL + 2), column = 2, padx = 5, pady = 5)
      #V

      nonlocal consignes_du_generateur
      consignes_precedentes = consignes_du_generateur.copy()

      fenetre_de_choix_des_consignes = Tk()
      fenetre_de_choix_des_consignes.title("Fenetre de choix des consignes de l'essai")
      fenetre_de_choix_des_consignes.protocol("WM_delete_window", annulation_des_changements)
      fenetre_de_choix_des_consignes.rowconfigure(0, weight=1)
      fenetre_de_choix_des_consignes.columnconfigure(0, weight=1)
      fenetre_de_choix_des_consignes.columnconfigure(1, weight=0)

      canevas = Canvas(fenetre_de_choix_des_consignes, width = 750, height = 600)
      canevas.grid(row = 0, column = 0, sticky = (N, S, E, W))
      canevas.rowconfigure(0, weight=1)
      canevas.columnconfigure(0, weight=1)
      y_scrollbar = ttk.Scrollbar(fenetre_de_choix_des_consignes, orient="vertical", command=canevas.yview)
      y_scrollbar.grid(column=2, row=0, sticky=(N, S, E))
      cadre_interne_consignes = ttk.Frame(canevas)
      cadre_interne_consignes.pack(expand = True)
      
      cadre_interne_consignes.bind("<Configure>", lambda _: canevas.configure(scrollregion = canevas.bbox("all")))
      canevas.create_window((0, 0), window = cadre_interne_consignes, anchor = "nw")
      canevas.configure(yscrollcommand=y_scrollbar.set)

      cadre_interne_consignes.bind('<Enter>', lambda e : _bound_to_mousewheel(canevas, e))
      cadre_interne_consignes.bind('<Leave>', lambda e : _unbound_to_mousewheel(canevas, e))

      actualisation_des_boutons()
      fenetre_de_choix_des_consignes.mainloop()
   #V
   def crappy_launcher():
      parametres = []
      parametres.append("Titre, " + entrees[0])
      parametres.append("Date, " + str(datetime.datetime.today()))
      parametres.append("Nom, " + entrees[1])
      parametres.append("Materiau, " + entrees[2])
      parametres.append("Charge de rupture, " + str(entrees[4]))
      parametres.append("Longueur de l'éprouvette, " + str(entrees[9]))
      parametres.append("Capteur de déplacement, Détecteur ultrasonique")
      parametres.append("  référence, UC_2000_L2_U_V15")
      parametres.append("Capteur de charge, Indicateur pour signal analogique")
      parametres.append("  référence, INDI_PAXS")
      if entrees[6] == 1 :
         parametres.append("Méthode d'accroche, Goupilles")
      else :
         parametres.append("Méthode d'accroche, Cabestan " + str(str(entrees[8])) + "mm")
      if entrees[10]:
         pass # rajouter des trucs pour ISO-2307
      parametres.append('')
      labels_voulus = ["t(s)", "consigne", "sortie_charge", "sortie_charge_transformée", "sortie_deplacement"]
      # while True:
      launch_crappy_event.wait()
      launch_crappy_event.clear()
      if type_d_asservissement == ASSERVISSEMENT_EN_CHARGE :
       #TODO : demarrage_de_crappy_charge
         demarrage_de_crappy_charge(consignes_generateur = consignes_du_generateur, 
                        fichier_d_enregistrement = str(datetime.datetime.now())[:11] + entrees[0] + ".csv",
                           #TODO : add lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + "chemin_enre.txt")
                        parametres_du_test = parametres, 
                        labels_a_enregistrer = labels_voulus)
      else :
       #TODO : demarrage_de_crappy_deplacement
         demarrage_de_crappy_fake_machine(consignes_generateur = consignes_du_generateur, 
                        fichier_d_enregistrement = str(datetime.datetime.now())[:11] + entrees[0] + ".csv",
                           #TODO : add lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + "chemin_enre.txt")
                        parametres_du_test = parametres, 
                        labels_a_enregistrer = labels_voulus)

##################################################################################################################################

   type_d_asservissement = init_type_d_asservissement # 1 : en charge ; 2 : en déplacement

   premieres_consignes_validees = False
   while premieres_consignes_validees == False :
      entrees = configuration_initiale(init_titre, init_nom,
         init_materiau, init_lg_banc, init_charge_rupt, init_diam_a_vide, 
         init_accroche, init_epissage, init_cabestan, init_lg_utile)
      if verrou_production == RESTART:
         return fct_depart()
      if entrees[10] :
         try :
            fichier_des_consignes_du_test_iso = open(DOSSIER_CONFIG_ET_CONSIGNES + "test_iso-2307.json", 'r')
            consignes_du_generateur = load(fichier_des_consignes_du_test_iso)
            fichier_des_consignes_du_test_iso.close()
         except FileNotFoundError :
            showwarning("TODO", "Je n'ai pas encore eu le temps d'implémenter ce test.")
            consignes_du_generateur = []
         #TODO : précharger test ISO à la place
      elif entrees[11] :
         type_d_asservissement = choix_du_type_d_asservissement(type_d_asservissement)
         try :
            if type_d_asservissement == ASSERVISSEMENT_EN_CHARGE :
               fichier_des_consignes_du_dernier_test = open(DOSSIER_CONFIG_ET_CONSIGNES + "consignes_du_test_precedent_charge.json", 'r')
            elif type_d_asservissement == ASSERVISSEMENT_EN_DEPLACEMENT :
               fichier_des_consignes_du_dernier_test = open(DOSSIER_CONFIG_ET_CONSIGNES + "consignes_du_test_precedent_deplacement.json", 'r')
            if type_d_asservissement != 0 :
               consignes_du_generateur = load(fichier_des_consignes_du_dernier_test)
               fichier_des_consignes_du_dernier_test.close()
         except FileNotFoundError :
            showwarning("Ah ben tiens...", "Aucun test n'a été effectué précédemment.")
            consignes_du_generateur = []
         if type_d_asservissement != 0 :
            choix_des_consignes_du_generateur()
      else :
         type_d_asservissement = choix_du_type_d_asservissement(type_d_asservissement)
         consignes_du_generateur = []
         if type_d_asservissement != 0 :
            choix_des_consignes_du_generateur()      


   Thread(target = crappy_launcher, daemon = True).start()



   fenetre_principale = Tk()
   fenetre_principale.title("Contrôle du banc")
   fenetre_principale.protocol("WM_DELETE_WINDOW", enregistrer_et_quitter)
   
   # tests ISO
   utile=DoubleVar()
   utile.set(entrees[9])
   num_ref=DoubleVar()
   num_ref.set(entrees[5])
   episse=IntVar()
   episse.set(entrees[7])
   pourc_var=DoubleVar()

   # Le reste trié
   lire_a_vide=BooleanVar()
   choix_des_documents_a_enregistrer=IntVar()
   choix_des_documents_a_enregistrer.set(0)
   charge_de_rupture=DoubleVar()
   charge_de_rupture.set(entrees[4])
   # data=recup_data() # Données fournies par la carte sur les 8 canaux
   data =  [random.random()*5 for _ in range(8)]
   valeur_maximale_de_déplacement=DoubleVar() # Valeur maximale en déplacement
   valeur_maximale_de_déplacement.set(-10000)
   valeur_minimale_de_déplacement=DoubleVar() # Valeur minimale en déplacement
   valeur_minimale_de_déplacement.set(2000)
   valeur_maximale_de_charge=DoubleVar()
   valeur_maximale_de_charge.set(-10000)
   consigne_choix = IntVar() # le bordel qui devrait utiliser des flags

   # vrac
   consigne_val = DoubleVar()
   memoire_consigne=DoubleVar()
   pente_val=DoubleVar()
   limite_val=DoubleVar()
   decharge=IntVar()
   tonnage_max=IntVar()
   limite_basse=DoubleVar()
   nb_cycles=IntVar()
   temps_voulu = StringVar()
   temps_voulu.set('00:00')
   mode_manuel=StringVar()
   mode_manuel.set('off')
   temps_palier_final=StringVar()
   temps_palier_final.set('00:00')
   pos_var=DoubleVar()

   # PDF
   societe=StringVar()
   adresse1=StringVar()
   adresse2=StringVar()
   adresse3=StringVar()
   contact1=StringVar()
   contact2=StringVar()
   contact3=StringVar()
   commande=StringVar()
   banc=StringVar()
   banc.set("Banc de traction C10TL27")
   nom_prenom=StringVar()
   nom_prenom.set(entrees[1])
   projet=StringVar()
   materiau=StringVar()
   materiau.set(entrees[2])
   reference=StringVar()
   validite=StringVar()
   type_de_certificat=IntVar()
   type_de_certificat.set(2)
   epreuve=StringVar()
   # PDF + une autre itération
   normes=StringVar()
   commentaires_de_l_utilisateur = StringVar()

   
   match entrees[3] :
      case 1 :
         tonnage_max.set(20)
      case 2 :
         tonnage_max.set(16.6)
      case 3 :
         tonnage_max.set(14)
      case 4 :
         tonnage_max.set(12)
      case 5 :
         tonnage_max.set(10)
   
   # nom=crea_nom(1)
   # workbook = xlsxwriter.Workbook(nom)
   # chartsheet = workbook.add_chartsheet()
   # feuille = workbook.add_worksheet()

   # nom_csv=crea_nom(2)
   # fichier_csv_1=open(nom_csv,'w')
   
   # nom_csv2=crea_nom(3)
   # fichier_csv_2=open(nom_csv2,'w')
   
   # nom_csv3=crea_nom(4)
   # fichier_csv_3=open(nom_csv3,'w')
   
   # init_xlsx()
   # init_csv(entrees[0],entrees[1],entrees[2],str(entrees[3]))
   
   ##### Organisation de l'affichage #####
   # liste_des_ecrans = get_monitors()
   # indice_ecran = 0
   # while indice_ecran < len(liste_des_ecrans) and not liste_des_ecrans[indice_ecran].is_primary :
   #    indice_ecran +=1    # Cherche l'écran principal.
   # largeur_de_l_ecran = liste_des_ecrans[indice_ecran].width
   largeur_de_l_ecran = 1440
   canvas=Canvas(fenetre_principale, height=int(largeur_de_l_ecran * 9/16),width=largeur_de_l_ecran)
   canvas.grid(column=0, row=0, columnspan = 1, sticky=(N, W, E, S))
   width_scrollbar = ttk.Scrollbar(fenetre_principale, orient = HORIZONTAL, command = canvas.xview)
   width_scrollbar.grid(column=0, row=1, sticky=(W, E))
   cadre_interne = Frame(canvas)
   canvas.configure(xscrollcommand = width_scrollbar.set)
   cadre_interne.bind('<Configure>', lambda _: canvas.configure(scrollregion = canvas.bbox("all")))
   canvas.create_window((0,0), window = cadre_interne, anchor='nw')
   # frameID = canvas.create_window((0,0), window = cadre_interne, anchor='nw')
   # cadre_interne['bg'] = '#FFFF00' # debug
   # cadre_interne.grid(row = 0, column =0, sticky=(N, S, E, W))
   # canvas.bind ("<Configure>", lambda e: canvas.itemconfigure (frameID, width = e.width, height = e.height))
   
   # Quand on modifie la taille de la fenêtre, la scrollbar reste de la même taille et 
   # le reste s'agrandit.
   fenetre_principale.rowconfigure(0, weight=1)
   fenetre_principale.rowconfigure(1, weight=0)
   fenetre_principale.columnconfigure(0, weight=1)
   canvas.rowconfigure(0, weight=1)
   canvas.columnconfigure(0, weight=1)

   val_actuelle_label=LabelFrame(cadre_interne, text = 'Valeur position (mm)', fg='red')
   mini_label=LabelFrame(cadre_interne, text = 'Valeur minimale', fg='red')
   maxi_label=LabelFrame(cadre_interne, text = 'Valeur maximale', fg='red')
   val_actuelle_charge_label=LabelFrame(cadre_interne, text = 'Valeur charge (t)', fg='green')
   maxi_charge_label=LabelFrame(cadre_interne, text = 'Valeur maximale', fg='green')
   consigne_label=LabelFrame(cadre_interne, text = 'Consigne', fg='blue')
   temps_total_label=LabelFrame(cadre_interne, text = 'Temps total')
   temps_fin_label=LabelFrame(cadre_interne, text = 'Temps de fonctionnement (en min)')
   zone_com_label=LabelFrame(cadre_interne, text = 'Commentaires')
   temps_restant_label=LabelFrame(cadre_interne, text = 'Temps restant')
   cadre_mode_manuel=LabelFrame(cadre_interne, text='Mode Manuel')
   rappel_label=LabelFrame(cadre_interne, text='Consigne')
   rappel_asserv=Canvas(rappel_label,height=20,width=250,bg='#ffffff')
   rappel_consigne=Canvas(rappel_label,height=20,width=250,bg='#ffffff')      
   zone_rappel_1=Canvas(rappel_label,height=20,width=250,bg='#ffffff')
   zone_rappel_2=Canvas(rappel_label,height=20,width=250,bg='#ffffff')
   zone_rappel_3=Canvas(rappel_label,height=20,width=250,bg='#ffffff')
   zone_rappel_4=Canvas(rappel_label,height=20,width=250,bg='#ffffff')
   zone_rappel_5=Canvas(rappel_label,height=20,width=250,bg='#ffffff')
   rappel_asserv.create_text(125,10,text=' ',tags='asservissement')
   rappel_consigne.create_text(125,10,text=' ',tags='consigne') 
   zone_rappel_1.create_text(125,10,text=' ',tags='zone1')
   zone_rappel_2.create_text(125,10,text=' ',tags='zone2')
   zone_rappel_3.create_text(125,10,text=' ',tags='zone3')
   zone_rappel_4.create_text(125,10,text=' ',tags='zone4')
   zone_rappel_5.create_text(125,10,text=' ',tags='zone5')
   # cadre_courbe = Canvas(cadre_interne)
   # super_figure_ou_sera_placee_la_courbe = plt.figure()
   # cadre_courbe = FigureCanvasTkAgg(super_figure_ou_sera_placee_la_courbe, master = cadre_interne)
   # print(super_figure_ou_sera_placee_la_courbe)
   # super_figure_ou_sera_placee_la_courbe.add_subplot()

   zone_temps_restant=Canvas(temps_restant_label,height=20,width=100,bg='#ffffff')
   zone_temps_consigne=Canvas(temps_total_label,height=20,width=100,bg='#ffffff') 
   zone_valeur=Canvas(val_actuelle_label,height=50,width=150,bg='#ffffff')
   zone_charge_valeur=Canvas(val_actuelle_charge_label,height=150,width=500,bg='#ffffff')
   zone_max=Canvas(maxi_label,height=20,width=100,bg='#ffffff')
   zone_min=Canvas(mini_label,height=20,width=100,bg='#ffffff')            
   zone_charge_max=Canvas(maxi_charge_label,height=20,width=100,bg='#ffffff')
   zone_consigne=Canvas(consigne_label,height=20,width=100,bg='#ffffff') 

   zone_com=Entry( zone_com_label, textvariable= commentaires_de_l_utilisateur, width=25)
   
   start_btn=Button(cadre_interne, text='Start', command=start_fct)
   pause_btn=Button(cadre_interne, text='Pause', command=do_pause,bg='red')
   bouton_enregistrer_et_quitter=Button(cadre_interne, text='Quitter et enregistrer', command=enregistrer_et_quitter)
   mise_a_0_btn=Button(cadre_interne, text=' Mise à 0 ',command=mise_a_0_fct)
   mise_a_tension_btn=Button(cadre_interne, text=' Mise à tension ',command=mise_a_tension_fct)
   off_button = Radiobutton(cadre_mode_manuel, text=" Off ", variable=mode_manuel,indicatoron=False,value="off",command=color_off)
   on_button = Radiobutton(cadre_mode_manuel, text=" On ", variable=mode_manuel,indicatoron=False, bg='gray',value="on",command=color_on)
   # bouton_parametrage_consigne = Button(cadre_interne, text=' ',bg='red',command=choix_du_type_d_asservissement)
   enregistrer_btn=Button(cadre_interne, text=' ', command=choix_enregistrer_fct)
   
   img1 = PhotoImage(file="icone_enregistrer.png") # make sure to add "/" not "\"
   enregistrer_btn.config(image=img1)
   img2 = PhotoImage(file="icone_engrenage.png") # make sure to add "/" not "\"
   # bouton_parametrage_consigne.config(image=img2)
   img3 = PhotoImage(file="icone_retour.png") # make sure to add "/" not "\"
   mise_a_0_btn.config(image=img3)
   img6 = PhotoImage(file="icone_play.png") # make sure to add "/" not "\"
   start_btn.config(image=img6)
   img7 = PhotoImage(file="icone_stop.png") # make sure to add "/" not "\"
   pause_btn.config(image=img7)
   img8 = PhotoImage(file="icone_tension.png") # make sure to add "/" not "\"
   mise_a_tension_btn.config(image=img8)
   img11 = PhotoImage(file="pree_image.png") # make sure to add "/" not "\"
   img21 = PhotoImage(file="rampe_image.png") # make sure to add "/" not "\"
   img22 = PhotoImage(file="palier_image.png") # make sure to add "/" not "\"
   img23 = PhotoImage(file="iso_image.png") # make sure to add "/" not "\"
   img31 = PhotoImage(file="fatigue_image.png") # make sure to add "/" not "\"
   
   
   # bal = tix.Balloon(cadre_interne)
   # bal.bind_widget(start_btn, msg="Démarrer le test")
   # bal.bind_widget(pause_btn, msg="Arrêter le test")
   # bal.bind_widget(mise_a_0_btn, msg="Renvoie le chariot à la position 0")
   # bal.bind_widget(mise_a_tension_btn, msg="Avance le chariot jusqu'à détection de tension")
   # bal.bind_widget(off_button, msg="Désactive le mode d'acquisition en manuel")
   # bal.bind_widget(on_button, msg="Active l'acquisition en manuel")
   # bal.bind_widget(bouton_enregistrer_et_quitter, msg="Termine le programme et enregistre les courbes")
   # bal.bind_widget(bouton_parametrage_consigne, msg="Paramétrer la consigne")
   # bal.bind_widget(enregistrer_btn, msg="Options d'enregistrements")
   
   # bal.bind_widget(zone_temps_restant, msg="Temps restant avant la prochaine phase du programme en cours (en hh:mm:ss)")
   # bal.bind_widget(zone_temps_consigne, msg="Temps écoulé depuis la dernière phase du programme en cours (en hh:mm:ss)")
   # bal.bind_widget(zone_valeur, msg="Déplacement chariot actuel (mm)")
   # bal.bind_widget(zone_charge_valeur, msg="Charge actuelle (tonnes)")
   # bal.bind_widget(zone_charge_max, msg="Valeur de charge maximale atteinte (tonnes)")
   # bal.bind_widget(zone_max, msg="Valeur de position maximale du chariot au lancement du programme (mm)")
   # bal.bind_widget(zone_min, msg="Valeur de position minimale du chariot au lancement du programme (mm)")
   # bal.bind_widget(zone_com, msg="Entrez ici un commentaire qui sera ajouté au document enregistré")
   # bal.bind_widget(zone_consigne, msg="Affiche la consigne en cours")

   val_actuelle_label.grid(row=0,column=7,rowspan=2,padx =5, pady =5)
   val_actuelle_charge_label.grid(row=0,column=1,rowspan=2,padx =5, pady =5)
   zone_valeur.grid(row=0,column=7,rowspan=2,padx =5, pady =5)
   zone_charge_valeur.grid(row=0,column=1,rowspan=2,padx =5, pady =5)
   temps_total_label.grid(row=0,column=11,padx =5, pady =5)
   zone_temps_consigne.grid(row=0,column=11,padx =5, pady =5)
   temps_fin_label.grid(row=0,column=11,padx =5, pady =5)
   temps_restant_label.grid(row=1 ,column=11,padx =5, pady =5)
   zone_temps_restant.grid(row=1,column=11,padx =5, pady =5)
   
   mini_label.grid(row=1,column=9,padx =5, pady =5)
   maxi_label.grid(row=1,column=8,padx =5, pady =5)
   maxi_charge_label.grid(row=0,column=8,padx =5, pady =5)
   consigne_label.grid(row=0,column=9,padx =5, pady =5)
   zone_max.grid(row=1,column=8,padx =5, pady =5)
   zone_min.grid(row=1,column=8,padx =5, pady =5)
   zone_charge_max.grid(row=0,column=8,padx =5, pady =5)
   zone_consigne.grid(row=0,column=9,padx =5, pady =5)
   start_btn.grid(row=0,column=13,padx =5, pady =5)
   pause_btn.grid(row=0,column=14,columnspan=2,padx =5, pady =5)
   bouton_enregistrer_et_quitter.grid(row=2,column=18,padx =5, pady =5)
   # bouton_parametrage_consigne.grid(row=1,column=14,padx =5, pady =5)
   enregistrer_btn.grid(row=1,column=15,padx =5, pady =5)
   mise_a_0_btn.grid(row=0,column=17,padx =5, pady =5)
   mise_a_tension_btn.grid(row=1,column=17,padx =5, pady =5)
   cadre_mode_manuel.grid(row=0,column=18,padx =5, pady =5)
   off_button.grid(row=1,column=20,padx =5, pady =5)
   on_button.grid(row=1,column=19,padx =5, pady =5)
   zone_com.grid(row=1 ,column=18,columnspan=3,padx =5, pady =5)
   zone_com_label.grid(row=1 ,column=18,columnspan=3,padx =5, pady =5)
   
   rappel_label.grid(row=4 ,column=18,padx =5, pady =5)
   rappel_asserv.grid(row=5 ,column=18,padx =5, pady =5)
   rappel_consigne.grid(row=6 ,column=18,padx =5, pady =5)
   zone_rappel_1.grid(row=7 ,column=18,padx =5, pady =5)
   zone_rappel_2.grid(row=8 ,column=18,padx =5, pady =5)
   zone_rappel_3.grid(row=9 ,column=18,padx =5, pady =5)
   zone_rappel_4.grid(row=10 ,column=18,padx =5, pady =5)
   zone_rappel_5.grid(row=10 ,column=18,padx =5, pady =5)
   
   # cadre_courbe._tkcanvas.grid(row = 4, column = 0, columnspan = 15, padx = 0, pady = 0)
   
   activer_bouton(start_btn)
   activer_bouton(bouton_enregistrer_et_quitter)
   activer_bouton(pause_btn)
   
   menubar = Menu(fenetre_principale)

   menu1 = Menu(menubar, tearoff=0)
   
   menu1.add_command(label="Type d'asservissement")#,command=choix_du_type_d_asservissement)
   menu1.add_command(label="Choix du test",command=distance_fct)
   menu1.add_command(label="Valeurs consignes",command=parametrage_fct)
   menu1.add_command(label="Valeur charge",command=parametrage_suite1)
   menu1.add_command(label="Réinitialiser consigne",command=reinitialiser)
   menubar.add_cascade(label="Consigne", menu=menu1)
   
   menu1.entryconfigure(1, state=DISABLED)
   menu1.entryconfigure(2, state=DISABLED)
   menu1.entryconfigure(3, state=DISABLED)
   
   menu2 = Menu(menubar, tearoff=0)
   menu2.add_command(label="Choix documents",command=choix_enregistrer_fct)
   menubar.add_cascade(label="Enregistrer", menu=menu2)
   
   menu3 = Menu(menubar, tearoff=0)
   menu3.add_command(label="Certificat",command=certif_fct)
   menu3.add_command(label="Ecran secondaire",command=fenetre_d_affichage_secondaire)
   menubar.add_cascade(label="Créer", menu=menu3)
   
   menu4 = Menu(menubar, tearoff=0)
   menu4.add_command(label="Aide",command=RTM_protocol)
   if verrou_production==0 :
      # menu4.add_command(label="Régler sensibilité PID",command=sensi_page)
      # menu4.add_command(label="Régler coefficients PID",command=reglage_des_coef_des_PID)
      menu4.add_command(label="Modifier les chemins d'accès",command=lambda: modification_des_chemins_d_acces(fenetre_principale))
      menu4.add_command(label="Modifier le mot de passe",command=lambda : modification_du_mot_de_passe(fenetre_principale))
      menu4.add_command(label="Modifier étalonnage du banc",command=modif_etalonnage_fct)
   menu4.add_separator()
   menu4.add_command(label="Fenêtre précédente",command=retour_aux_entrees)
   menu4.add_command(label="Quitter",command=enregistrer_et_quitter)
   menubar.add_cascade(label="Autre", menu=menu4)
   
   fenetre_principale.config(menu=menubar)
   
   fenetre_principale.mainloop()

   launch_crappy_event.clear()
   return fonction_principale(*entrees[:10], type_d_asservissement)


if __name__ == '__main__':
   fct_depart()