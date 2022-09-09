#!/usr/bin/env python
# -*- encoding: utf-8 -*-

### Opérations sur les fichiers
import os
from os import path
from json import *
import pandas

### Interface graphique
from tkinter import *
from tkinter import ttk
# from tkinter import tix   # Obsolète, à remplacer
from tkinter.messagebox import *
from tkinter.filedialog import *
from screeninfo import get_monitors

### Création de PDF
import PIL
# from Pillow import Image
from reportlab.pdfgen import canvas as cvpdf
from reportlab.lib.pagesizes import A4
from win32com.client import Dispatch   # pip install pywin32

### Imports pour CRAPPy
import crappy
import customblocks
import custom_generator
import custom_pid
import custom_dashboard
from test_RAZ import remise_a_zero
# import custom_multiplex
import custom_grapher
import custom_recorder

### Divers
from numpy import pi
import time
import datetime
import re
from threading import Event, Thread

### Debug
import sys
import random

### Potentiellement à virer. À vérifer
import xlsxwriter



# Coefficients de changement d'unité
COEF_VOLTS_TO_MILLIMETERS = 200
COEF_MILLIMETERS_TO_VOLTS = 1 / COEF_VOLTS_TO_MILLIMETERS
COEF_VOLTS_TO_TONS = 2
COEF_TONS_TO_VOLTS = 1 / COEF_VOLTS_TO_TONS

# Les trois constantes suivantes sont pour verrou_production
ON = 1
OFF = 0
RESTART = 3
verrou_production = OFF

# Constantes pour les choix de consignes
NOMBRE_DE_CONSIGNES_MAXIMAL = 1000
TYPES_DE_CONSIGNE = {"constant" : "palier",
                     "ramp" : "rampe",
                     "cyclic" : "cycle de paliers",
                     "cyclic_ramp" : "cycle de rampes",
                     "sine" : "sinus"}
LABEL_SORTIE_EN_CHARGE = "sortie_charge_transformee"
LABEL_SORTIE_EN_POSITION = "sortie_position_transformee"
DEBUT_CONDITION_TEMPS = len("delay=")
DEBUT_CONDITION_CHARGE = len(LABEL_SORTIE_EN_CHARGE) + 1
DEBUT_CONDITION_POSITION = len(LABEL_SORTIE_EN_POSITION) + 1

# Types d'asservissement
ASSERVISSEMENT_EN_CHARGE = 1
ASSERVISSEMENT_EN_DEPLACEMENT = 2

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
# Chemins des fichiers
SEPARATEUR = "\\" # "\\" for windows, "/" for linux
DOSSIER_CONFIG_ET_CONSIGNES = lecture_donnee("dossier_config_et_consignes.txt") + SEPARATEUR
DOSSIER_ENREGISTREMENTS = lecture_donnee("dossier_enregistrements.txt") + SEPARATEUR
# print (DOSSIER_ENREGISTREMENTS)

liste_des_blocs_crappy_utilises = []  
launch_crappy_event = Event()
start_generator = False
# stop_crappy_event = Event()
enregistrement_effectue = False
charge_max = -10
position_min = 2000
position_max = -10
# tonnage_limite = 20

alphabet=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
next_available_letter=0


def etalonnage_des_coefficients_de_transformation():
   """FR : Étalonne les coefficient de la fonction de passage de volts à tonnes.

   EN : Calibrates the function passing from volts to tons coefficients."""
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
### Fonctions de conversions d'unité
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
### Fonctions de vérification des entrées des utilisateurs
def _check_entree_float(new_value):
   """FR : Empêche l'utilisateur d'entrer des valeurs incorrectes.
   
   EN : Prevent the user from entering incorrect values."""
   if new_value == "" :
      return True
   if re.match("^[0-9]+\.?[0-9]*$", new_value) is None and re.match("^[0-9]*\.?[0-9]+$", new_value) is None :
      return False
   return True
#V
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
def _check_entree_charge_prod(new_value):
   """FR : Empêche l'utilisateur d'entrer des valeurs incorrectes.
   
   EN : Prevent the user from entering incorrect values."""
   if new_value == "" :
      return True
   if re.match("^[0-9]+\.?[0-9]*$", new_value) is None and re.match("^[0-9]*\.?[0-9]+$", new_value) is None :
      return False
   new_value = float(new_value)
   return new_value >= 0.0 and new_value <= 10.0
#V
def _check_entree_position(new_value):
   """FR : Empêche l'utilisateur d'entrer des valeurs incorrectes.
   
   EN : Prevent the user from entering incorrect values."""
   if new_value == "" :
      return True
   if re.match("^[0-9]+\.?[0-9]*$", new_value) is None and re.match("^[0-9]*\.?[0-9]+$", new_value) is None :
      return False
   new_value = float(new_value)
   return new_value >= 0.0 and new_value <= 2000.0
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
def _check_entree_vitesse_position(new_value):
   """FR : Empêche l'utilisateur d'entrer des valeurs incorrectes.
   
   EN : Prevent the user from entering incorrect values."""
   if new_value == "" or new_value == '-' :
      return True
   if re.match("^-?[0-9]+\.?[0-9]*$", new_value) is None and re.match("^-?[0-9]*\.?[0-9]+$", new_value) is None :
      return False
   new_value = float(new_value)
   return new_value >= -2000.0 and new_value <= 2000.0
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
def _card_to_pid_and_generator(dic):
   """FR : Étalonne la tension renvoyée par le capteur d'efforts.
   
   EN : Calibrates the voltage fed back by the effort sensor."""
   # global start_generator
   # if start_generator :
   #    return
   if "sortie_charge_brute" not in dic.keys() or "sortie_position_brute" not in dic.keys() :
      dic["t(s)"] = time.time()
      dic ["sortie_charge_brute"] = 0.0
      dic["sortie_position_brute"] = 0.0
      return dic
   x = 2 * dic["sortie_charge_brute"]
   dic[LABEL_SORTIE_EN_CHARGE] = float(etalonnage_a*(x**2) + etalonnage_b * x + etalonnage_c) / 2.0
   dic[LABEL_SORTIE_EN_POSITION] = float(transformation_capteur_de_position(dic["sortie_position_brute"]))
   # if dic[LABEL_SORTIE_EN_CHARGE] > (20 * COEF_TONS_TO_VOLTS) and (2 * COEF_MILLIMETERS_TO_VOLTS) < dic[LABEL_SORTIE_EN_POSITION] < (1900 * COEF_MILLIMETERS_TO_VOLTS) :
   #    stop_crappy()
   return dic

def _gen_to_graph_charge(dic = {}):
   if "consigne" not in dic.keys() :
      dic["t(s)"] = time.time()
      dic["consigne"] = 0.0
      dic ["Consigne (T)"] = 0.0
      return dic
   dic["Consigne (T)"] = COEF_VOLTS_TO_TONS * dic["consigne"]
    #TODO : fonction inverse de l'étalonnage
   return dic

def _gen_to_graph_position(dic = {}):
   if "consigne" not in dic.keys() :
      dic["t(s)"] = time.time()
      dic["consigne"] = 0.0
      dic ["Consigne (mm)"] = 0.0
      return dic
   dic["Consigne (mm)"] = COEF_VOLTS_TO_MILLIMETERS * dic["consigne"]
    #TODO : fonction inverse de l'étalonnage
   return dic

def _card_to_recorder_and_graph(dic) :
   dic = _card_to_pid_and_generator(dic)
   dic["Temps (s)"] = dic["t(s)"]
   dic["Charge (T)"] = 2 * dic[LABEL_SORTIE_EN_CHARGE]
   dic["Position (mm)"] = COEF_VOLTS_TO_MILLIMETERS * dic[LABEL_SORTIE_EN_POSITION]
   return dic

def _pid_to_card_charge(dic) :
   if 0.03 < dic["entree_charge"]  :
      dic["entree_charge"] += 0.03 #0.458
   else :
      dic["entree_charge"] = 0
   return dic

def _pid_to_card_decharge(dic) :
   if -0.03 > dic["entree_decharge"]  :
      dic["entree_decharge"] -= 1.11 #0.525
   else :
      dic["entree_decharge"] = 0
   dic["entree_decharge"] *= -1
   return dic

def _gen_to_dashboard_charge(dic) :
   if "consigne" not in dic.keys() :
      dic["t(s)"] = time.time()
      dic ["Consigne (T)"] = 0.0
      return dic
   dic["Consigne (T)"] = COEF_VOLTS_TO_TONS * dic["consigne"]
   return dic

def _gen_to_dashboard_position(dic) :
   if "consigne" not in dic.keys() :
      dic["t(s)"] = time.time()
      dic ["Consigne (mm)"] = 0.0
      return dic
   dic["Consigne (mm)"] = COEF_VOLTS_TO_MILLIMETERS * dic["consigne"]
   return dic

def _card_to_dashboard(dic) :
   global charge_max, position_max, position_min
   dic = _card_to_recorder_and_graph(dic)
   if dic["Charge (T)"] > charge_max :
      charge_max = dic["Charge (T)"]
   dic["Charge max (T)"] = charge_max
   sortie_position_en_mm = dic["Position (mm)"]
   if sortie_position_en_mm > position_max :
      position_max = sortie_position_en_mm
   dic["Position max (mm)"] = position_max
   if sortie_position_en_mm < position_min :
      position_min = sortie_position_en_mm
   dic["Position min (mm)"] = position_min
   return dic

def gen_to_multiplex(dic = None):
   if "consigne" not in dic.keys() :
      dic["t(s)"] = str(time.time())
      dic["consigne"] = str(0.0)
   return dic

### Fonctions de démarrage de Crappy
def demarrage_de_crappy_charge(consignes_generateur = None, fichier_d_enregistrement = None,
                              parametres_du_test = [], labels_a_enregistrer = None):
   """TODO"""
   gen = crappy.blocks.Generator(path = consignes_generateur,
                                 cmd_label = 'consigne',
                                 spam = True,
                                 freq = 50)
   liste_des_blocs_crappy_utilises.append(gen)

   carte_NI = crappy.blocks.IOBlock(name = "Nidaqmx",
                                    labels = ["t(s)", "sortie_charge_brute", 
                                             "sortie_position_brute"],
                                    cmd_labels = ["entree_decharge", "entree_charge"],
                                    initial_cmd = [0.0, 0.0],
                                    exit_values = [0.0, 0.0],
                                    channels=[{'name': 'Dev3/ao0'},
                                    {'name': 'Dev3/ao1'},
                                    {'name': 'Dev3/ai6'},
                                    {'name': 'Dev3/ai7'}],
                                    spam=True,
                                    freq = 50)
   liste_des_blocs_crappy_utilises.append(carte_NI)

   pid_charge = custom_pid.PID(kp=1,
                                 ki=0.01,
                                 kd=0.1,
                                 out_max=5,
                                 out_min=-5,
                                 i_limit=0.5,
                                 input_label = LABEL_SORTIE_EN_CHARGE,
                                 target_label = 'consigne',
                                 labels = ["t(s)", 'entree_charge'],
                                 freq = 50)
   liste_des_blocs_crappy_utilises.append(pid_charge)

   pid_decharge = custom_pid.PID(kp=0.3,
                                    ki=0.01,
                                    kd=0.1,
                                    out_max=5,
                                    out_min=-5,
                                    i_limit=0.5,
                                    target_label = 'consigne',
                                    labels = ["t(s)", 'entree_decharge'],
                                    input_label = LABEL_SORTIE_EN_CHARGE,
                                    freq = 50)
   liste_des_blocs_crappy_utilises.append(pid_decharge)

   y_charge = crappy.blocks.Multiplex(freq = 50)
   liste_des_blocs_crappy_utilises.append(y_charge)

   y_decharge = crappy.blocks.Multiplex(freq = 50)
   liste_des_blocs_crappy_utilises.append(y_decharge)

   graphe = custom_grapher.EmbeddedGrapher(("Temps (s)", "Consigne (T)"), 
                                         ("Temps (s)", "Charge (T)"),
                                         ("Temps (s)", "Position (mm)"),
                                          freq = 3)
   liste_des_blocs_crappy_utilises.append(graphe)

   y_record = crappy.blocks.Multiplex(freq = 50)
   liste_des_blocs_crappy_utilises.append(y_record)

   y_dashboard = crappy.blocks.Multiplex(freq = 50)
   liste_des_blocs_crappy_utilises.append(y_dashboard)

   pancarte = custom_dashboard.Dashboard(labels = ["Temps (s)", "Consigne (T)", "Position (mm)", 
                                                   "Charge (T)", "Charge max (T)", 
                                                   "Position min (mm)", "Position max (mm)"],
                                         freq = 5)
   liste_des_blocs_crappy_utilises.append(pancarte)

   affichage_secondaire = custom_dashboard.Dashboard(labels = ["Temps (s)", "Consigne (T)", "Position (mm)", 
                                                               "Charge (T)", "Charge max (T)", 
                                                               "Position min (mm)", "Position max (mm)"],
                                                     is_primary = False,
                                                     freq = 5)
   liste_des_blocs_crappy_utilises.append(affichage_secondaire)

   if fichier_d_enregistrement is not None :
      record = custom_recorder.CustomRecorder(filename = fichier_d_enregistrement,
                              labels = labels_a_enregistrer,
                              parametres_a_inscrire = parametres_du_test)
      liste_des_blocs_crappy_utilises.append(record)

   crappy.link(gen, y_charge, modifier = gen_to_multiplex)
   crappy.link(gen, y_decharge, modifier = gen_to_multiplex)
   crappy.link(carte_NI, y_charge, modifier=_card_to_pid_and_generator)
   crappy.link(carte_NI, y_decharge, modifier=_card_to_pid_and_generator)
   crappy.link(y_charge, pid_charge)
   crappy.link(y_decharge, pid_decharge)
   crappy.link(pid_charge, carte_NI, modifier=_pid_to_card_charge)
   crappy.link(pid_decharge, carte_NI, modifier=_pid_to_card_decharge)
   crappy.link(carte_NI, gen, modifier=_card_to_pid_and_generator)

   crappy.link(gen, y_record, modifier = _gen_to_graph_charge)
   crappy.link(pid_charge, y_record, modifier=_pid_to_card_charge)
   crappy.link(pid_decharge, y_record, modifier=_pid_to_card_decharge)
   crappy.link(carte_NI, y_record, modifier = _card_to_recorder_and_graph) 
                           # [_card_to_recorder_and_graph, 
                           # crappy.modifier.Diff(label = LABEL_SORTIE_EN_CHARGE, 
                           #                      out_label = "derivee_voltage")])
   if fichier_d_enregistrement is not None :
      crappy.link(y_record, record)
   crappy.link(carte_NI, graphe, modifier=_card_to_recorder_and_graph)
   crappy.link(gen, graphe, modifier=_gen_to_graph_charge)
   crappy.link(gen, y_dashboard, modifier = _gen_to_dashboard_charge)
   crappy.link(carte_NI, y_dashboard, modifier = _card_to_dashboard)
   crappy.link(y_dashboard, pancarte)
   crappy.link(y_dashboard, affichage_secondaire)

   crappy.start()
   crappy.reset()

def demarrage_de_crappy_deplacement(consignes_generateur = None, fichier_d_enregistrement = None,
                        parametres_du_test = [], labels_a_enregistrer = None):
   """TODO"""
   gen = crappy.blocks.Generator(path = consignes_generateur,
                                 cmd_label = 'consigne',
                                 spam = True,
                                 freq = 50)
   liste_des_blocs_crappy_utilises.append(gen)

   carte_NI = crappy.blocks.IOBlock(name = "Nidaqmx",
                                    labels = ["t(s)", "sortie_charge_brute", 
                                             "sortie_position_brute"],
                                    cmd_labels = ["entree_decharge", "entree_charge"],
                                    initial_cmd = [0.0, 0.0],
                                    exit_values = [0.0, 0.0],
                                    channels = [{'name': 'Dev3/ao0'},
                                    {'name': 'Dev3/ao1'},
                                    {'name': 'Dev3/ai6'},
                                    {'name': 'Dev3/ai7'}],
                                    spam = True,
                                    freq = 50)
   liste_des_blocs_crappy_utilises.append(carte_NI)

   pid_charge = custom_pid.PID(kp=1,
                                 ki=0.01,
                                 kd=0.01,
                                 out_max=5,
                                 out_min=-5,
                                 i_limit=0.5,
                                 input_label = LABEL_SORTIE_EN_POSITION,
                                 target_label = 'consigne',
                                 labels = ["t(s)", 'entree_charge'],
                                 freq = 50)
   liste_des_blocs_crappy_utilises.append(pid_charge)

   pid_decharge = custom_pid.PID(kp=0.5,
                                    ki=0.0,
                                    kd=0.0,
                                    out_max=5,
                                    out_min=-5,
                                    i_limit=0.5,
                                    target_label = 'consigne',
                                    labels = ["t(s)", 'entree_decharge'],
                                    input_label = LABEL_SORTIE_EN_POSITION,
                                    freq = 50)
   liste_des_blocs_crappy_utilises.append(pid_decharge)

   y_charge = crappy.blocks.Multiplex(freq = 50)
   # y_charge = customblocks.YBlock(out_labels = ["t(s)", "consigne", LABEL_SORTIE_EN_POSITION],
   #                                freq = 50)
   liste_des_blocs_crappy_utilises.append(y_charge)

   y_decharge = crappy.blocks.Multiplex(freq = 50)
   # y_decharge = customblocks.YBlock(out_labels = ["t(s)", "consigne", LABEL_SORTIE_EN_POSITION],
   #                                freq = 50)
   liste_des_blocs_crappy_utilises.append(y_decharge)

   graphe = custom_grapher.EmbeddedGrapher(("Temps (s)", "consigne"), 
                                         ("Temps (s)", "Charge (T)"),
                                         ("Temps (s)", "Position (mm)"),
                                          freq = 3)
   liste_des_blocs_crappy_utilises.append(graphe)

   y_record = crappy.blocks.Multiplex(freq = 50)
   liste_des_blocs_crappy_utilises.append(y_record)

   y_dashboard = crappy.blocks.Multiplex(freq = 50)
   liste_des_blocs_crappy_utilises.append(y_record)

   pancarte = custom_dashboard.Dashboard(labels = ["Temps (s)", "Consigne (mm)", "Position (mm)", 
                                                   "Charge (T)", "Charge max (T)", 
                                                   "Position min (mm)", "Position max (mm)"],
                                         freq = 5)
   liste_des_blocs_crappy_utilises.append(pancarte)

   affichage_secondaire = custom_dashboard.Dashboard(labels = ["Temps (s)", "Consigne (mm)", "Position (mm)", 
                                                               "Charge (T)", "Charge max (T)", 
                                                               "Position min (mm)", "Position max (mm)"],
                                                     is_primary = False,
                                                     freq = 5)
   liste_des_blocs_crappy_utilises.append(affichage_secondaire)

   if fichier_d_enregistrement is not None :
      record = custom_recorder.CustomRecorder(filename = fichier_d_enregistrement,
                              labels = labels_a_enregistrer,
                              parametres_a_inscrire = parametres_du_test)
      liste_des_blocs_crappy_utilises.append(record)

   crappy.link(gen, y_charge)
   crappy.link(gen, y_decharge)
   crappy.link(carte_NI, y_charge, modifier=_card_to_pid_and_generator)
   crappy.link(carte_NI, y_decharge, modifier=_card_to_pid_and_generator)
   crappy.link(y_charge, pid_charge)
   crappy.link(y_decharge, pid_decharge)
   crappy.link(pid_charge, carte_NI, modifier=_pid_to_card_charge)
   crappy.link(pid_decharge, carte_NI, modifier=_pid_to_card_decharge)
   crappy.link(carte_NI, gen, modifier=_card_to_pid_and_generator)

   crappy.link(gen, y_record, modifier = _gen_to_graph_position)                       #
   crappy.link(pid_charge, y_record, modifier=_pid_to_card_charge)
   crappy.link(pid_decharge, y_record, modifier=_pid_to_card_decharge)
   crappy.link(carte_NI, y_record, modifier = _card_to_recorder_and_graph)             #
                           # [_card_to_recorder_and_graph, 
                           # crappy.modifier.Diff(label = LABEL_SORTIE_EN_POSITION, 
                           #                      out_label = "derivee_voltage")])
   if fichier_d_enregistrement is not None :
      crappy.link(y_record, record)
   crappy.link(carte_NI, graphe, modifier=_card_to_recorder_and_graph)
   crappy.link(gen, graphe, modifier=_gen_to_graph_position)
   crappy.link(gen, y_dashboard, modifier = _gen_to_dashboard_position)                #
   crappy.link(carte_NI, y_dashboard, modifier = _card_to_dashboard)                   #
   crappy.link(y_dashboard, pancarte)
   crappy.link(y_dashboard, affichage_secondaire)

   crappy.start()
   crappy.reset()

def gen_to_card_RaZ_et_MeT(dic):
   dic["entree_decharge"] = -dic["consigne"] if dic["consigne"] < 0 else 0
   dic["entree_charge"] = dic["consigne"] if dic["consigne"] > 0 else 0
   return dic

### Fake_machine
def carte_to_gen(dic):
   dic[LABEL_SORTIE_EN_POSITION] = 2 * dic["F(N)"] / 9.807 / 1000
   # if dic[LABEL_SORTIE_EN_POSITION]  > 2 :
   #    stop_crappy()
   #    dic[LABEL_SORTIE_EN_POSITION] = "safeguard"
   return dic

def carte_to_pid(dic):
   dic[LABEL_SORTIE_EN_POSITION] = dic["F(N)"] / 9.807 / 1000
   # print(dic[LABEL_SORTIE_EN_POSITION])
   return dic

def plastic(v: float, yield_strain: float = .005, rate: float = .02) -> float:
  if v > yield_strain:
    return ((v - yield_strain) ** 2 + rate ** 2) ** .5 - rate
  return 0

def demarrage_de_crappy_fake_machine(consignes_generateur = None, fichier_d_enregistrement = None,
                        parametres_du_test = [], labels_a_enregistrer = None):
   carte_NI = crappy.blocks.Fake_machine(k = 10000*450,
                                          l0 = 4000,
                                          maxstrain = 7,
                                          nu = 0.5,
                                          max_speed = 100,
                                          mode = 'speed',
                                          cmd_label = "entree_charge",
                                          plastic_law = plastic)
   liste_des_blocs_crappy_utilises.append(carte_NI)
   
   pid_charge = custom_pid.PID(kp=1,
                                 ki=0.0,
                                 kd=0.0,
                                 out_max=5,
                                 out_min=-5,
                                 i_limit=0.5,
                                 target_label = "consigne",
                                 labels = ["t(s)", 'entree_charge'],
                                 input_label = LABEL_SORTIE_EN_POSITION,
                                 freq = 50)
   liste_des_blocs_crappy_utilises.append(pid_charge)

   graphe = customblocks.EmbeddedGrapher(("t(s)", "consigne"), 
                              ("t(s)", LABEL_SORTIE_EN_POSITION),
                              freq = 3)
   liste_des_blocs_crappy_utilises.append(graphe)

   y_charge = crappy.blocks.Multiplex(freq = 50)
   liste_des_blocs_crappy_utilises.append(y_charge)

   y_record = crappy.blocks.Multiplex(freq = 50)
   liste_des_blocs_crappy_utilises.append(y_record)

   if fichier_d_enregistrement is not None :
      record = customblocks.CustomRecorder(filename = fichier_d_enregistrement,
                              labels = ["t(s)", 
                                 "x(mm)", 
                                 "F(N)",
                                 "entree_charge"],
                              parametres_a_inscrire = parametres_du_test)
      liste_des_blocs_crappy_utilises.append(record)

   pancarte = custom_dashboard.Dashboard(labels = ["t(s)", "F(N)", LABEL_SORTIE_EN_POSITION],
                                         is_primary = False,
                                         freq = 5)
   liste_des_blocs_crappy_utilises.append(pancarte)

   gen = crappy.blocks.Generator(path = consignes_generateur,
                                 cmd_label = 'consigne',
                                 spam = True,
                                 freq = 50)
   liste_des_blocs_crappy_utilises.append(gen)
   
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

def transformation_capteur_de_position(x):
#TODO : constantes WTF
   #convertion tension lue par le capteur ultrason -> tension étalonnée pour ne pas dépasser les valeurs limites en distance
   return (x-2.18)*5/4.08 

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
def modification_des_PID(parent):
   """FR : Fenêtre de choix des valeurs PID.
   
   EN : PID's values' choice window."""
   def validation_des_nouveaux_PID():
      """FR : Enregistre les valeurs des PID dans un fichier de config prédéfini.
      
      EN : Saves the PID's values in a predefined config file."""
      dic_PID ={}
      dic_PID["charge_P"] = charge_P.get()
      dic_PID["charge_I"] = charge_I.get()
      dic_PID["charge_D"] = charge_D.get()
      dic_PID["decharge_P"] = decharge_P.get()
      dic_PID["decharge_I"] = decharge_I.get()
      dic_PID["decharge_D"] = decharge_D.get()
      if type_de_materiau.get() == 0 :
         fichier_des_PID = DOSSIER_CONFIG_ET_CONSIGNES + "pid_mou.json"
      else :
         fichier_des_PID = DOSSIER_CONFIG_ET_CONSIGNES + "pid_rigide.json"
      with open(fichier_des_PID, 'w') as f :
         dump(dic_PID, f)
      fenetre_de_modification_des_PID.destroy()
   #V
   def valeurs_actuelles_des_PID():
      """FR : Affiche les valeurs de PID correspondantes au type de matériau choisi.
      
      EN : Prints the PID's values corresponding to the chosen material's type."""
      if type_de_materiau.get() == 0 :
         with open(DOSSIER_CONFIG_ET_CONSIGNES + "pid_mou.json", 'r') as fichier_PID :
            dic_PID = load (fichier_PID)
      else :
         with open(DOSSIER_CONFIG_ET_CONSIGNES + "pid_rigide.json", 'r') as fichier_PID :
            dic_PID = load (fichier_PID)
      charge_P.set(dic_PID["charge_P"])
      charge_I.set(dic_PID["charge_I"])
      charge_D.set(dic_PID["charge_D"])
      decharge_P.set(dic_PID["decharge_P"])
      decharge_I.set(dic_PID["decharge_I"])
      decharge_D.set(dic_PID["decharge_D"])
   #V
   
   fenetre_de_modification_des_PID = Toplevel(parent)

   type_de_materiau = IntVar()

   charge_P = DoubleVar()
   charge_I = DoubleVar()
   charge_D = DoubleVar()
   decharge_P = DoubleVar()
   decharge_I = DoubleVar()
   decharge_D = DoubleVar()
   dic_PID = {}
   with open(DOSSIER_CONFIG_ET_CONSIGNES + "pid_mou.json", 'r') as fichier_PID :
      dic_PID = load (fichier_PID)
   charge_P.set(dic_PID["charge_P"])
   charge_I.set(dic_PID["charge_I"])
   charge_D.set(dic_PID["charge_D"])
   decharge_P.set(dic_PID["decharge_P"])
   decharge_I.set(dic_PID["decharge_I"])
   decharge_D.set(dic_PID["decharge_D"])

   Radiobutton(fenetre_de_modification_des_PID, text = "PID des matériaux mou", variable = type_de_materiau, value = 0, command = valeurs_actuelles_des_PID).grid(row = 0, column = 0, columnspan = 6, sticky = "w", padx = 5, pady = 5)
   Radiobutton(fenetre_de_modification_des_PID, text = "PID des matériaux rigide", variable = type_de_materiau, value = 1, command = valeurs_actuelles_des_PID).grid(row = 1, column = 0, columnspan = 6, sticky = "w", padx = 5, pady = 5)

   Label(fenetre_de_modification_des_PID, text = "PID de charge").grid(row = 4, column = 0, padx = 5, pady = 5)
   Label(fenetre_de_modification_des_PID, text = "P").grid(row = 5, column = 1, padx = 5, pady = 5)
   Entry(fenetre_de_modification_des_PID, textvariable = charge_P, width = 5, validate = "key", validatecommand = (fenetre_de_modification_des_PID.register(_check_entree_float), '%P')).grid(row = 5, column = 2, padx = 5, pady = 5)
   Label(fenetre_de_modification_des_PID, text = "I").grid(row = 5, column = 3, padx = 5, pady = 5)
   Entry(fenetre_de_modification_des_PID, textvariable = charge_I, width = 5, validate = "key", validatecommand = (fenetre_de_modification_des_PID.register(_check_entree_float), '%P')).grid(row = 5, column = 4, padx = 5, pady = 5)
   Label(fenetre_de_modification_des_PID, text = "D").grid(row = 5, column = 5, padx = 5, pady = 5)
   Entry(fenetre_de_modification_des_PID, textvariable = charge_D, width = 5, validate = "key", validatecommand = (fenetre_de_modification_des_PID.register(_check_entree_float), '%P')).grid(row = 5, column = 6, padx = 5, pady = 5)
   
   Label(fenetre_de_modification_des_PID, text = "PID de charge").grid(row = 6, column = 0, padx = 5, pady = 5)
   Label(fenetre_de_modification_des_PID, text = "P").grid(row = 7, column = 1, padx = 5, pady = 5)
   Entry(fenetre_de_modification_des_PID, textvariable = decharge_P, width = 5, validate = "key", validatecommand = (fenetre_de_modification_des_PID.register(_check_entree_float), '%P')).grid(row = 7, column = 2, padx = 5, pady = 5)
   Label(fenetre_de_modification_des_PID, text = "I").grid(row = 7, column = 3, padx = 5, pady = 5)
   Entry(fenetre_de_modification_des_PID, textvariable = decharge_I, width = 5, validate = "key", validatecommand = (fenetre_de_modification_des_PID.register(_check_entree_float), '%P')).grid(row = 7, column = 4, padx = 5, pady = 5)
   Label(fenetre_de_modification_des_PID, text = "D").grid(row = 7, column = 5, padx = 5, pady = 5)
   Entry(fenetre_de_modification_des_PID, textvariable = decharge_D, width = 5, validate = "key", validatecommand = (fenetre_de_modification_des_PID.register(_check_entree_float), '%P')).grid(row = 7, column = 6, padx = 5, pady = 5)

   Button(fenetre_de_modification_des_PID, text = "Retour", command = fenetre_de_modification_des_PID.destroy).grid(row = 8, column = 0, columnspan = 3, padx = 5, pady = 5)
   Button(fenetre_de_modification_des_PID, text = "Valider", command = validation_des_nouveaux_PID).grid(row = 8, column = 4, columnspan = 3, padx = 5, pady = 5)

   with open(DOSSIER_CONFIG_ET_CONSIGNES + "pid_personnalise.json", 'r') as fichier_PID :
      dic_PID = load (fichier_PID)
#V
def demarrage_du_programme() :
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
         if mot_de_passe.get() == lecture_donnee(DOSSIER_CONFIG_ET_CONSIGNES + 'mdp_liste.txt') :
            fenetre1.destroy()
            return fonction_principale()
         else :
            showinfo(title='Échec', message='Mot de passe incorrect')
      
      mot_de_passe = StringVar() 
      fenetre_mdp=Toplevel(fenetre1)
      Label(fenetre_mdp, text = 'mot de passe').grid(row=0, column=0, padx =20, pady =10)
      entree_mot_de_passe = Entry(fenetre_mdp,textvariable=mot_de_passe,show='*', width=30)
      entree_mot_de_passe.grid(row=0, column=1, padx =20, pady =10)
      entree_mot_de_passe.focus_force()
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

   def retour_au_choix_de_mode():
      """FR : Retourne à la fenêtre du choix de mode.
      
      EN : Gets back to the mode choice window."""
      global verrou_production
      fenetre_des_entrees.destroy()
      verrou_production = RESTART
   #V
   def validation_des_entrees() :
      nonlocal dic_PID
      if choix_PID.get() == 2 :
         with open(DOSSIER_CONFIG_ET_CONSIGNES + "pid_personalise.json", 'w') as fichier_PID_perso :
            dump (dic_PID, fichier_PID_perso)
      fenetre_des_entrees.destroy()

   def diam_cabestan(afficher):
      ###affiche la valeur du diamètre de cabestan si la case est cochée
      if afficher :
         Label(cadre_choix_type_d_accroche,text="Diamètre cabestan (mm)").grid(row=15,column=0,padx =10, pady =10)
         Entry(cadre_choix_type_d_accroche, textvariable=diametre_du_cabestan, width=10).grid(row=15,column=1,padx =10, pady =10)
      else :
         for widget in cadre_choix_type_d_accroche.winfo_children()[-2:] :
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
   def choix_PID_custom():
      nonlocal dic_PID
      match choix_PID.get() :
         case 2 :
            Label(cadre_PID, text = "PID de charge").grid(row = 4, column = 0, padx = 5, pady = 5)
            Label(cadre_PID, text = "P").grid(row = 5, column = 1, padx = 5, pady = 5)
            Entry(cadre_PID, textvariable = charge_P, width = 5, validate = "key", validatecommand = (fenetre_des_entrees.register(_check_entree_float), '%P')).grid(row = 5, column = 2, padx = 5, pady = 5)
            Label(cadre_PID, text = "I").grid(row = 5, column = 3, padx = 5, pady = 5)
            Entry(cadre_PID, textvariable = charge_I, width = 5, validate = "key", validatecommand = (fenetre_des_entrees.register(_check_entree_float), '%P')).grid(row = 5, column = 4, padx = 5, pady = 5)
            Label(cadre_PID, text = "D").grid(row = 5, column = 5, padx = 5, pady = 5)
            Entry(cadre_PID, textvariable = charge_D, width = 5, validate = "key", validatecommand = (fenetre_des_entrees.register(_check_entree_float), '%P')).grid(row = 5, column = 6, padx = 5, pady = 5)
            
            Label(cadre_PID, text = "PID de charge").grid(row = 6, column = 0, padx = 5, pady = 5)
            Label(cadre_PID, text = "P").grid(row = 7, column = 1, padx = 5, pady = 5)
            Entry(cadre_PID, textvariable = decharge_P, width = 5, validate = "key", validatecommand = (fenetre_des_entrees.register(_check_entree_float), '%P')).grid(row = 7, column = 2, padx = 5, pady = 5)
            Label(cadre_PID, text = "I").grid(row = 7, column = 3, padx = 5, pady = 5)
            Entry(cadre_PID, textvariable = decharge_I, width = 5, validate = "key", validatecommand = (fenetre_des_entrees.register(_check_entree_float), '%P')).grid(row = 7, column = 4, padx = 5, pady = 5)
            Label(cadre_PID, text = "D").grid(row = 7, column = 5, padx = 5, pady = 5)
            Entry(cadre_PID, textvariable = decharge_D, width = 5, validate = "key", validatecommand = (fenetre_des_entrees.register(_check_entree_float), '%P')).grid(row = 7, column = 6, padx = 5, pady = 5)

            with open(DOSSIER_CONFIG_ET_CONSIGNES + "pid_personnalise.json", 'r') as fichier_PID :
               dic_PID = load (fichier_PID)
         case 1 :
            for widget in cadre_PID.winfo_children()[3:] :
               widget.destroy()
            with open(DOSSIER_CONFIG_ET_CONSIGNES + "pid_rigide.json", 'r') as fichier_PID :
               dic_PID = load (fichier_PID)
         case 0 :
            for widget in cadre_PID.winfo_children()[3:] :
               widget.destroy()
            with open(DOSSIER_CONFIG_ET_CONSIGNES + "pid_mou.json", 'r') as fichier_PID :
               dic_PID = load (fichier_PID)
      charge_P.set(dic_PID["charge_P"])
      charge_I.set(dic_PID["charge_I"])
      charge_D.set(dic_PID["charge_D"])
      decharge_P.set(dic_PID["decharge_P"])
      decharge_I.set(dic_PID["decharge_I"])
      decharge_D.set(dic_PID["decharge_D"])
   #V
   global verrou_production

   fenetre_des_entrees = Tk()
   fenetre_des_entrees.title("Configuration initiale")
   fenetre_des_entrees.protocol("WM_DELETE_WINDOW", exit)

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

   choix_PID = IntVar()
   charge_P = DoubleVar()
   charge_I = DoubleVar()
   charge_D = DoubleVar()
   decharge_P = DoubleVar()
   decharge_I = DoubleVar()
   decharge_D = DoubleVar()
   dic_PID = {}
   with open(DOSSIER_CONFIG_ET_CONSIGNES + "pid_mou.json", 'r') as fichier_PID :
      dic_PID = load (fichier_PID)
   charge_P.set(dic_PID["charge_P"])
   charge_I.set(dic_PID["charge_I"])
   charge_D.set(dic_PID["charge_D"])
   decharge_P.set(dic_PID["decharge_P"])
   decharge_I.set(dic_PID["decharge_I"])
   decharge_D.set(dic_PID["decharge_D"])
   
   Label( fenetre_des_entrees, text = "Titre").grid(row=1,column=0,padx =5, pady =5)
   entree_titre=Entry( fenetre_des_entrees, textvariable=titre, width=30, validate="key", validatecommand=(fenetre_des_entrees.register(_check_entree_string), '%P'))
   entree_titre.grid(row=1,column=1,padx =5, pady =5)

   Label( fenetre_des_entrees, text = "Nom de l'opérateur").grid(row=2,column=0,padx =5, pady =5)
   entree_nom=Entry( fenetre_des_entrees, textvariable=nom, width=30, validate="key", validatecommand=(fenetre_des_entrees.register(_check_entree_string), '%P'))
   entree_nom.grid(row=2,column=1,padx =5, pady =5)

   Label( fenetre_des_entrees, text = "Matériau").grid(row=4,column=0,padx =5, pady =5)
   entree_materiau=Entry( fenetre_des_entrees, textvariable=materiau, width=30, validate="key", validatecommand=(fenetre_des_entrees.register(_check_entree_string), '%P'))
   entree_materiau.grid(row=4,column=1,padx =5, pady =5)

   Label( fenetre_des_entrees, text = "Charge de rupture (en tonnes)").grid(row=6,column=0,padx =5, pady =5)
   entree_charge_rupture=Entry( fenetre_des_entrees, textvariable=charge_de_rupture, width=5, validate="key", validatecommand=(fenetre_des_entrees.register(_check_entree_charge), '%P'))
   entree_charge_rupture.grid(row=6,column=1,padx =5, pady =5, sticky = "w")

   Label(fenetre_des_entrees,text="Longueur de l'éprouvette (en m)").grid(row = 7, column = 0, padx = 5, pady = 5)
   Entry(fenetre_des_entrees, textvariable=longueur_utile, width=5, validate="key", validatecommand=(fenetre_des_entrees.register(_check_entree_longueur), '%P')).grid(row = 7, column = 1, padx = 5, pady = 5, sticky = "w")
         
   cadre_longueur_banc=LabelFrame( fenetre_des_entrees)
   cadre_longueur_banc.grid(row = 8, column = 0, columnspan = 3, padx = 5, pady = 5, sticky = "ew")
   Label(cadre_longueur_banc, text = 'Longueur utile du banc').grid(row=8,column=0,padx =5, pady =5)
   coche20m = Radiobutton(cadre_longueur_banc, text="<20m", variable=longueur_banc, value=1)
   coche20m.grid(row=8,column=1,padx =5, pady =5)
   coche22m = Radiobutton(cadre_longueur_banc, text="22m", variable=longueur_banc, value=2)
   coche22m.grid(row=9,column=1,padx =5, pady =5)
   coche24m = Radiobutton(cadre_longueur_banc, text="24m", variable=longueur_banc, value=3)
   coche24m.grid(row=10,column=1,padx =5, pady =5)
   coche26m = Radiobutton(cadre_longueur_banc, text="26m", variable=longueur_banc, value=4)
   coche26m.grid(row=11,column=1,padx =5, pady =5)  
   if verrou_production == OFF :
      coche9m = Radiobutton(cadre_longueur_banc, text="7m (pour une pièce métallique)", variable=longueur_banc, value=5)
      coche9m.grid(row=12,column=1,padx =5, pady =5)

      cadre_choix_type_d_accroche=LabelFrame(fenetre_des_entrees)
      cadre_choix_type_d_accroche.grid(row = 13, column = 0,columnspan = 3, padx = 5, pady = 5, sticky = "ew")
      Label(cadre_choix_type_d_accroche, text = "Système d'accroche").grid(row=13,column=0,padx =5, pady =5)
      coche_axial= Radiobutton(cadre_choix_type_d_accroche, text="Goupilles", variable=type_d_accroche, value=1, command = lambda : diam_cabestan(False))
      coche_axial.grid(row=13,column=1,padx =5, pady =5)
      coche_cabestan = Radiobutton(cadre_choix_type_d_accroche, text="Amarrage à cabestan", variable=type_d_accroche, value=2, command = lambda : diam_cabestan(True))
      coche_cabestan.grid(row=14,column=1,padx =5, pady =5)
      
      cordage_label=LabelFrame(fenetre_des_entrees)
      cordage_label.grid(row=16,column=0,columnspan=3,padx =5, pady =5, sticky = "ew")
      ttk.Checkbutton(cordage_label, text = "Test ISO-2307", variable = is_test_iso, onvalue = True, offvalue = False, command = iso_quai).grid(row = 0, column = 0, columnspan = 3, padx = 5, pady = 5, sticky = "w")

   cadre_PID = LabelFrame(fenetre_des_entrees)
   cadre_PID.grid(row = 17, column = 0, columnspan = 3, padx = 5, pady = 5, sticky = "ew")
   Radiobutton(cadre_PID, text = "Matériau mou", variable = choix_PID, value = 0, command = choix_PID_custom).grid(row = 0, column = 0, columnspan = 6, sticky = "w", padx = 5, pady = 5)
   Radiobutton(cadre_PID, text = "Matériau rigide", variable = choix_PID, value = 1, command = choix_PID_custom).grid(row = 1, column = 0, columnspan = 6, sticky = "w", padx = 5, pady = 5)
   if verrou_production == OFF :
      Radiobutton(cadre_PID, text = "PID personnalisé", variable = choix_PID, value = 2, command = choix_PID_custom).grid(row = 2, column = 0, columnspan = 6, sticky = "w", padx = 5, pady = 5)


   charger_le_dernier_test = BooleanVar()
   charger_le_dernier_test.set(True)
   if verrou_production == OFF :
      ttk.Checkbutton(fenetre_des_entrees, text = "Charger les consignes du dernier test", variable = charger_le_dernier_test, onvalue = True, offvalue = False).grid(row = 18, column = 0, columnspan = 2, padx = 5, pady = 5)

   
   precedent1_btn=Button(fenetre_des_entrees, text='Précédent', command=retour_au_choix_de_mode)
   precedent1_btn.grid(row=20, column=0,padx =5, pady =5)
   suivant1_btn=Button(fenetre_des_entrees, text='Suivant', command = validation_des_entrees)
   suivant1_btn.grid(row=20, column=1,padx =5, pady =5)

   menubar = Menu(fenetre_des_entrees)
   fenetre_des_entrees.config(menu=menubar)
   menu= Menu(menubar, tearoff=0)
   menubar.add_cascade(label="Autre", menu=menu)
   menu.add_command(label="Afficher la documentation",command=RTM_protocol)
   if verrou_production==0 :
      menu.add_command(label="Modifier les chemins d'accès",command=lambda: modification_des_chemins_d_acces(fenetre_des_entrees))
      menu.add_command(label="Modifier le mot de passe",command=lambda: modification_du_mot_de_passe(fenetre_des_entrees))

   fenetre_des_entrees.mainloop()
   
   return (titre.get(),nom.get(),materiau.get(),longueur_banc.get(),charge_de_rupture.get(),diametre_a_vide.get(),type_d_accroche.get(),est_episse.get(),diametre_du_cabestan.get(),longueur_utile.get(), is_test_iso.get(), charger_le_dernier_test.get())
#PV obligatoire (tix)
def fonction_principale(init_titre='', init_nom='', init_materiau='', 
      init_lg_banc=1, init_charge_rupt=0, init_diam_a_vide=0.0, init_accroche=1, 
      init_epissage=True, init_cabestan=40.0, init_lg_utile=0.0, init_type_d_asservissement = 0):
###fonction de fenêtre graphique

   def retour_aux_entrees():
      """FR : Relance la fonction principale et renvoie l'utilisateur sur la fenêtre
       de saisie des conditions.
       
      EN : Restarts the main function and brings back the user to the conditions
       entries window."""
      choix_des_documents_a_enregistrer.set(0) # Ne pas conserver les documents actuels
      if not sauvegarde_effectue :
         enregistrement_des_documents_choisis()
      fenetre_principale.destroy()
   #V
   def enregistrer_et_quitter():
      """FR : Fenêtre de choix des données à enregistrer avant de quitter ou relancer.
      
      EN : Window to choose which datas to save before quitting or launching another test."""
      def quitter():
         """FR : Enregistre et quitte.
         
         EN : Saves and quits."""
         choix_des_documents_a_enregistrer.set(check_val_brutes.get() + check_val_reelles.get())
         if not sauvegarde_effectue :
            enregistrement_des_documents_choisis()
         exit()
      #V
      def relancer_un_essai():
         """FR : Enregistre et renvoie l'utilisateur sur la fenêtre de saisie des
          conditions du test.
         
         EN : Saves and brings back the user to the test conditions' entries window."""
         choix_des_documents_a_enregistrer.set(check_val_brutes.get() + check_val_reelles.get())
         if not sauvegarde_effectue :
            enregistrement_des_documents_choisis()
         fenetre_de_sortie_du_programme.destroy()
         fenetre_principale.destroy()
         nonlocal test_effectue
         test_effectue = False
         launch_crappy_event.set()
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
   def choix_des_documents_a_conserver():
      """FR : Fenêtre de choix des documents à conserver.
      
      EN : Files to keep choice window."""
      def annulation():
         """FR : Restore le choix précédent et ferme cette fenêtre.
         
         EN : Sets back the previous choice and closes this window."""
         choix_des_documents_a_enregistrer.set(choix_actuel)
         fenetre_de_choix_des_doc_a_conserver.destroy()
      #V
      choix_actuel = choix_des_documents_a_enregistrer.get()
      fenetre_de_choix_des_doc_a_conserver=Toplevel(fenetre_principale)
      fenetre_de_choix_des_doc_a_conserver.protocol("WM_DELETE_WINDOW", annulation)
      
      Label(fenetre_de_choix_des_doc_a_conserver, text="Veuillez choisir les documents à enregistrer").grid(row=0,column=1,padx =10, pady =10)
      Radiobutton(fenetre_de_choix_des_doc_a_conserver, text="aucun document", variable=choix_des_documents_a_enregistrer, value=0).grid(row=1,column=1,padx =10, pady =10)
      Radiobutton(fenetre_de_choix_des_doc_a_conserver, text="valeurs étalonnées (fichier excel et csv)", variable=choix_des_documents_a_enregistrer, value=1).grid(row=2,column=1,padx =10, pady =10)
      if verrou_production==0 :
         Radiobutton(fenetre_de_choix_des_doc_a_conserver, text="valeurs affichées (fichier excel et csv)", variable=choix_des_documents_a_enregistrer, value=2).grid(row=3,column=1,padx =10, pady =10)
         Radiobutton(fenetre_de_choix_des_doc_a_conserver, text="valeurs affichées et étalonnées (fichier excel et csv)", variable=choix_des_documents_a_enregistrer, value=3).grid(row=4,column=1,padx =10, pady =10)
      Button(fenetre_de_choix_des_doc_a_conserver,text='Retour', command=annulation).grid(row=5,column=0,padx =10, pady =10)
      Button(fenetre_de_choix_des_doc_a_conserver,text='Suivant', command=fenetre_de_choix_des_doc_a_conserver.destroy).grid(row=5,column=2,padx =10, pady =10)
      fenetre_de_choix_des_doc_a_conserver.wait_window()
   #V
   def enregistrement_des_documents_choisis():
   ###fenêtre d'enregistrement des valeurs. Créé les courbes, ferme les documents csv et excel, détruit les documents non voulu.
      #TODO : Maintenant qu'on a un nom, faudrait ptet le remplir. Je vais essayer de voir si y a 
      #       d'exporter le .csv en .xlsx, puis de rajouter les courbes.
      # stop_crappy()
      if enregistrement_effectue :
         match choix_des_documents_a_enregistrer.get() :
            case 0 :
               suppression_d_un_fichier(nom_du_fichier_csv)
            case 1:
               donnees_du_test = pandas.read_csv(nom_du_fichier_csv, encoding = "latin-1", index_col = False)
               if test_effectue :
                  donnees_du_test.drop(columns = [donnees_du_test.columns[2], donnees_du_test.columns[4]], inplace = True)
               else :
                  donnees_du_test.drop(columns = [donnees_du_test.columns[1], donnees_du_test.columns[3]], inplace = True)
               donnees_du_test.to_csv(nom_du_fichier_csv, index = False, header = False)
            case 2 :
               donnees_du_test = pandas.read_csv(nom_du_fichier_csv, encoding = "latin-1", index_col = False)
               if test_effectue :
                  donnees_du_test.drop(columns = [donnees_du_test.columns[3], donnees_du_test.columns[5]], inplace = True)
               else :
                  donnees_du_test.drop(columns = [donnees_du_test.columns[2], donnees_du_test.columns[4]], inplace = True)
               donnees_du_test.to_csv(nom_du_fichier_csv, index = False, header = False)
            case 3 :
               donnees_du_test = pandas.read_csv(nom_du_fichier_csv, encoding = "latin-1", index_col = False)
         if choix_des_documents_a_enregistrer.get() != 0 :
            scribe = pandas.ExcelWriter(nom_du_fichier_xlsx, engine='xlsxwriter')
            donnees_du_test.to_excel(scribe, index = False, header = False)
            workbook = scribe.book
            worksheet = scribe.sheets["Sheet1"]
            chartsheet = workbook.add_chartsheet()
            premieres_valeurs = len(parametres)
            dernieres_valeurs = len(donnees_du_test.index)
            chart = workbook.add_chart({'type': 'scatter','subtype' : 'straight'})
            if test_effectue :
               match choix_des_documents_a_enregistrer.get() :
                  case 1 | 2 :
                     colonne1 = "=Sheet1!$A$" + str(premieres_valeurs) + ":$A$" + str(dernieres_valeurs) # Temps
                     colonne2 = "=Sheet1!$B$" + str(premieres_valeurs) + ":$B$" + str(dernieres_valeurs) # Consigne
                     colonne3 = "=Sheet1!$C$" + str(premieres_valeurs) + ":$C$" + str(dernieres_valeurs) # Charge
                     colonne4 = "=Sheet1!$D$" + str(premieres_valeurs) + ":$D$" + str(dernieres_valeurs) # Position
                  
                     # chart.add_series({
                     # 'name': 'Charge (T)',
                     # 'categories': ["Sheet1", premieres_valeurs, 0, dernieres_valeurs, 0],
                     # 'values': ["Sheet1", premieres_valeurs, 2, dernieres_valeurs, 2],
                     # 'line':   {'width': 0.5},
                     # })
                  case 3 :
                     colonne1 = "=Sheet1!$A$" + str(premieres_valeurs) + ":$A$" + str(dernieres_valeurs) # Temps
                     colonne2 = "=Sheet1!$B$" + str(premieres_valeurs) + ":$B$" + str(dernieres_valeurs) # Consigne
                     colonne3 = "=Sheet1!$D$" + str(premieres_valeurs) + ":$D$" + str(dernieres_valeurs) # Charge
                     colonne4 = "=Sheet1!$F$" + str(premieres_valeurs) + ":$F$" + str(dernieres_valeurs) # Position
               # if type_d_asservissement == ASSERVISSEMENT_EN_CHARGE :
               #    chart.add_series({
               #    'name': 'Consigne (T)',
               #    'categories': colonne1,
               #    'values': colonne2,
               #    'line':   {'width': 0.5},
               #    })
               # else :
               #    chart.add_series({
               #    'name': 'Consigne (mm)',
               #    'categories': colonne1,
               #    'values': colonne2,
               #    'line':   {'width': 0.5},
               #    })
               chart.add_series({
               'name': 'Charge (T)',
               'categories': colonne1,
               'values': colonne3,
               'line':   {'width': 0.5},
               })
               chart.add_series({
               'name': 'Position (mm)',
               'categories': colonne1,
               'values': colonne4,
               'line':   {'width': 0.5},
               'y2_axis': 1,
               })
            else :
               match choix_des_documents_a_enregistrer.get() :
                  case 1, 2 :
                     print("=Sheet1!$A$" + str(premieres_valeurs) + ":$A$" + str(dernieres_valeurs))
                     colonne1 = "=Sheet1!$A$" + str(premieres_valeurs) + ":$A$" + str(dernieres_valeurs)
                     colonne2 = "=Sheet1!$B$" + str(premieres_valeurs) + ":$B$" + str(dernieres_valeurs)
                     colonne3 = "=Sheet1!$C$" + str(premieres_valeurs) + ":$C$" + str(dernieres_valeurs)
                  case 3 :
                     colonne1 = "=Sheet1!$A$" + str(premieres_valeurs) + ":$A$" + str(dernieres_valeurs)
                     colonne2 = "=Sheet1!$C$" + str(premieres_valeurs) + ":$C$" + str(dernieres_valeurs)
                     colonne3 = "=Sheet1!$E$" + str(premieres_valeurs) + ":$E$" + str(dernieres_valeurs)
               chart.add_series({
               'name': 'Charge (T)',
               'categories': colonne1,
               'values': colonne2,
               'line':   {'width': 0.5},
               })
               chart.add_series({
               'name': 'Position (mm)',
               'categories': colonne1,
               'values': colonne3,
               'line':   {'width': 0.5},
               'y2_axis': 1,
               })

            chart.set_x_axis({
            'date_axis':  True,
            'num_format': '0.00',
            'name': 'Temps (s)'
            })
            chart.set_title ({'name': 'Résultat'})
            chart.set_y_axis({'name': 'charge (tonnes)'})
            chart.set_y2_axis({'name': 'déplacement (mm)'})
            
            # worksheet.insert_chart(1, 3, chart)
            chartsheet.set_chart(chart)
            chartsheet.activate()
            
            # workbook.close()
            scribe.close()

   def creation_de_certificat():
      ##fenêtre de choix du certificat créé
      def entrees_du_certificat():
      ########################
         match type_de_certificat.get() :
            case 1 :
               epreuve.set('Certificat de fatigue')
            case 2:
               epreuve.set('Certificat de rupture')
            case 3:
               epreuve.set("Certificat d'épreuve")
            case 4:
               epreuve.set('Certificat de préétirage')
           ###fenêtre des entrées du certificat 
         def creation_du_certificat_rempli():
            ###fonction de création du pdf
            if askyesno("Attention","Il faut enregistrer l'essai avant de créer le certificat. Continuer ?") :
               choix_des_documents_a_conserver()
               enregistrement_des_documents_choisis()
               nonlocal sauvegarde_effectue
               sauvegarde_effectue = True

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
               fenetre_de_choix_du_type_de_certificat.destroy()
               
               activer_bouton(bouton_enregistrer_et_quitter)
               desactiver_bouton(enregistrer_btn)
            
         def generate_pdf(date,com,maxi,ref,nature,mat_test,projet,operateur,mat_util,commande,contact3,contact2,contact1,adresse3,adresse2,adresse1,societe,normes,validite):
            ###fonction utilisant les entrées pour créer le pdf
            """
            letter :- (612.0, 792.0)
            A4 : 595.275590551 x 830.551181102
            """
            match type_de_certificat.get() :
               case 1 :
                  nom_pdf = DOSSIER_CONFIG_ET_CONSIGNES + str(datetime.datetime.now())[:11] + entrees[0] + "_Certificat_de_Fatigue.pdf"
               case 2 :
                  nom_pdf = DOSSIER_CONFIG_ET_CONSIGNES + str(datetime.datetime.now())[:11] + entrees[0] + "_Certificat_de_Rupture.pdf"
               case 3 :
                  nom_pdf = DOSSIER_CONFIG_ET_CONSIGNES + str(datetime.datetime.now())[:11] + entrees[0] + "_Certificat_d_Épreuve.pdf"
               case 4 :
                  nom_pdf = DOSSIER_CONFIG_ET_CONSIGNES + str(datetime.datetime.now())[:11] + entrees[0] + "_Certificat_de_Préétirage.pdf"

            c = cvpdf.Canvas(nom_pdf, pagesize=A4)
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
            im = PIL.Image.open(DOSSIER_CONFIG_ET_CONSIGNES + 'Logo-Ino-Rope-blanc.png')
            c.drawInlineImage(im,455,775, width=90, height=14)

            nom_png = DOSSIER_CONFIG_ET_CONSIGNES + str(datetime.datetime.now())[:11] + entrees[0] + ".png"
            generate_image(nom_png)
            im = PIL.Image.open(nom_png)   
            c.drawInlineImage(im,70,150, width=470, height=280)
            c.save()
            os.remove(nom_png)
            
         def generate_image(nom_image):
            ###fonction de génération du fichier png comprenant la courbe excel du test.
            nonlocal nom_du_fichier_xlsx
            excel = Dispatch("Excel.Application")
            excel.ActiveWorkbook
            xlsWB = excel.Workbooks.Open(nom_du_fichier_xlsx) 
            xlsWB.Sheets("sheet1")
            mychart = excel.Charts(1)
            mychart.Export(Filename = nom_image)

         fenetre_de_choix_du_type_de_certificat.destroy() 
         fenetre_des_entrees_du_certificat=Toplevel(fenetre_principale)

         Label(fenetre_des_entrees_du_certificat, text="Destinataire du certificat").grid(row=0,column=0,columnspan=5,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Société").grid(row=1,column=0,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Adresse").grid(row=2,column=0,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Rue").grid(row=2,column=1,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Ville").grid(row=3,column=1,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Code postal").grid(row=4,column=1,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Contact").grid(row=5,column=0,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Nom").grid(row=5,column=1,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="téléphone").grid(row=6,column=1,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="email").grid(row=7,column=1,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Commande").grid(row=8,column=0,padx =10, pady =10)
         
         Label(fenetre_des_entrees_du_certificat, text="Description de l'épreuve").grid(row=9,column=0,columnspan=5,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Banc de traction C10TL27").grid(row=10,column=0,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Opérateur").grid(row=11,column=0,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Projet").grid(row=12,column=0,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Matériel testé").grid(row=13,column=0,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Nature de l'expérience").grid(row=14,column=0,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Référence").grid(row=15,column=0,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Norme de charge_de_rupture validée").grid(row=16,column=0,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Date limite de validité").grid(row=17,column=0,padx =10, pady =10)
         Label(fenetre_des_entrees_du_certificat, text="Commentaire").grid(row=18,column=0,padx =10, pady =10)
         
         Entry(fenetre_des_entrees_du_certificat, textvariable=societe, width=30).grid(row=1,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=adresse1, width=30).grid(row=2,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=adresse2, width=30).grid(row=3,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=adresse3, width=30).grid(row=4,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=contact1, width=30).grid(row=5,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=contact2, width=30).grid(row=6,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=contact3, width=30).grid(row=7,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=commande, width=30) .grid(row=8,column=2,padx =10, pady =10)
         
         Entry(fenetre_des_entrees_du_certificat, textvariable=banc, width=30).grid(row=10,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=nom_prenom, width=30).grid(row=11,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=projet, width=30).grid(row=12,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=materiau, width=30).grid(row=13,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=epreuve, width=30).grid(row=14,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=reference, width=30).grid(row=15,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=normes, width=30).grid(row=16,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=validite, width=30).grid(row=17,column=2,padx =10, pady =10)
         Entry(fenetre_des_entrees_du_certificat, textvariable=commentaires_de_l_utilisateur, width=30).grid(row=18,column=2,padx =10, pady =10)
         
         Button(fenetre_des_entrees_du_certificat, text='Retour',command = fenetre_des_entrees_du_certificat.destroy).grid(row=19,column=0,padx =10, pady =10)
         Button(fenetre_des_entrees_du_certificat, text='Suivant',command = creation_du_certificat_rempli).grid(row=19,column=2,padx =10, pady =10)

      ########################
   
      fenetre_de_choix_du_type_de_certificat=Toplevel(fenetre_principale)
      fenetre_de_choix_du_type_de_certificat.title('Choix de certificat')
      
      Label(fenetre_de_choix_du_type_de_certificat, text="Veuillez choisir le type de certificat que vous voulez créer :", justify = CENTER).grid(row=1,column=1,columnspan=3,padx =10, pady =10)
      Radiobutton(fenetre_de_choix_du_type_de_certificat, text='Fatigue', variable=type_de_certificat, value=1).grid(row=2,column=1,columnspan=3,padx =10, pady =10)
      Radiobutton(fenetre_de_choix_du_type_de_certificat, text='Rupture', variable=type_de_certificat, value=2).grid(row=3,column=1,columnspan=3,padx =10, pady =10)
      Radiobutton(fenetre_de_choix_du_type_de_certificat, text='150% Charge de travail', variable=type_de_certificat, value=3).grid(row=4,column=1,columnspan=3,padx =10, pady =10)
      Radiobutton(fenetre_de_choix_du_type_de_certificat, text='Pré-étirage', variable=type_de_certificat, value=4).grid(row=5,column=1,columnspan=3,padx =10, pady =10)

      Button(fenetre_de_choix_du_type_de_certificat, text='Retour',command=fenetre_de_choix_du_type_de_certificat.destroy).grid(row=6,column=1,padx =10, pady =10)
      Button(fenetre_de_choix_du_type_de_certificat, text='Suivant',command=entrees_du_certificat).grid(row=6,column=3,padx =10, pady =10)

 #TODO : Gérer les différents PID et leur réglage. 
 #       Voir sensi_page() et reglage_des_coef_des_PID() dans les fonctions jetées.

   def modification_des_coeff_d_etalonnage():
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
            if verrou_production == ON :
               # 0 : mise en tension
               # 1 : palier à charge = 0
               # 2 : rampe jusqu'à la valeur demandée
               # 3 : palier à cette valeur
               # 4 : rampe  de retour à la position 0
               # 5 : rampe jusqu'à la valeur demandée
               # 6 : palier à cette valeur
               consignes_du_generateur[3]["value"] = consignes_du_generateur[2]["speed"]
               consignes_du_generateur[5] = consignes_du_generateur[2].copy()
               consignes_du_generateur[6]["value"] = consignes_du_generateur[2]["speed"]
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

            if type_d_asservissement == ASSERVISSEMENT_EN_CHARGE :
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
                           consigne_a_changer["condition"] = LABEL_SORTIE_EN_CHARGE + ">" + str(condition_superieure_a.get()/2)
                        case 2 :
                           consigne_a_changer["condition"] = LABEL_SORTIE_EN_CHARGE + "<" + str(condition_inferieure_a.get()/2)
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
                           consigne_a_changer["condition1"] = LABEL_SORTIE_EN_CHARGE + ">" + str(condition_superieure_a1.get()/2)
                        case 2 :
                           consigne_a_changer["condition1"] = LABEL_SORTIE_EN_CHARGE + "<" + str(condition_inferieure_a1.get()/2)
                        case 3 :
                           consigne_a_changer["condition1"] = "delay=" + str(condition_en_temps1.get())
                     
                     consigne_a_changer["speed2"] = tons_to_volts(speed2.get())
                     match type_de_condition2.get() :
                        case 0 :
                           consigne_a_changer["condition2"] = None
                        case 1 :
                           consigne_a_changer["condition2"] = LABEL_SORTIE_EN_CHARGE + ">" + str(condition_superieure_a2.get()/2)
                        case 2 :
                           consigne_a_changer["condition2"] = LABEL_SORTIE_EN_CHARGE + "<" + str(condition_inferieure_a2.get()/2)
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
            else :
               match consigne_a_changer['type'] :
                  case "constant" :
                     consigne_a_changer["value"] = COEF_MILLIMETERS_TO_VOLTS * value.get()
                     if type_de_condition.get() == 0 :
                        consigne_a_changer["condition"] = None
                     else :
                        consigne_a_changer["condition"] = "delay=" + str(condition_en_temps.get())
                  case "ramp" :
                     consigne_a_changer["speed"] = COEF_MILLIMETERS_TO_VOLTS * speed.get()
                     match type_de_condition.get() :
                        case 0 :
                           consigne_a_changer["condition"] = None
                        case 1 :
                           consigne_a_changer["condition"] = LABEL_SORTIE_EN_POSITION + ">" + str(COEF_MILLIMETERS_TO_VOLTS * condition_superieure_a.get())
                        case 2 :
                           consigne_a_changer["condition"] = LABEL_SORTIE_EN_POSITION + "<" + str(COEF_MILLIMETERS_TO_VOLTS * condition_inferieure_a.get())
                        case 3 :
                           consigne_a_changer["condition"] = "delay=" + str(condition_en_temps.get())
                  case "cyclic" :
                     consigne_a_changer["value1"] = COEF_MILLIMETERS_TO_VOLTS * value1.get()
                     consigne_a_changer["condition1"] = "delay=" + str(condition1.get())

                     consigne_a_changer["value2"] = COEF_MILLIMETERS_TO_VOLTS * value2.get()
                     consigne_a_changer["condition2"] = "delay=" + str(condition2.get())

                     consigne_a_changer["cycles"] = nombre_de_cycles.get()
                  case "cyclic_ramp" :
                     consigne_a_changer["speed1"] = COEF_MILLIMETERS_TO_VOLTS * speed1.get()
                     match type_de_condition1.get() :
                        case 0 :
                           consigne_a_changer["condition1"] = None
                        case 1 :
                           consigne_a_changer["condition1"] = LABEL_SORTIE_EN_POSITION + ">" + str(COEF_MILLIMETERS_TO_VOLTS * condition_superieure_a1.get())
                        case 2 :
                           consigne_a_changer["condition1"] = LABEL_SORTIE_EN_POSITION + "<" + str(COEF_MILLIMETERS_TO_VOLTS * condition_inferieure_a1.get())
                        case 3 :
                           consigne_a_changer["condition1"] = "delay=" + str(condition_en_temps1.get())
                     
                     consigne_a_changer["speed2"] = COEF_MILLIMETERS_TO_VOLTS * speed2.get()
                     match type_de_condition2.get() :
                        case 0 :
                           consigne_a_changer["condition2"] = None
                        case 1 :
                           consigne_a_changer["condition2"] = LABEL_SORTIE_EN_POSITION + ">" + str(COEF_MILLIMETERS_TO_VOLTS * condition_superieure_a2.get())
                        case 2 :
                           consigne_a_changer["condition2"] = LABEL_SORTIE_EN_POSITION + "<" + str(COEF_MILLIMETERS_TO_VOLTS * condition_inferieure_a2.get())
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
                     consigne_a_changer["amplitude"] = COEF_MILLIMETERS_TO_VOLTS * (pic_haut.get() - pic_bas.get())
                     consigne_a_changer["offset"] = COEF_MILLIMETERS_TO_VOLTS * ((pic_haut.get() + pic_bas.get()) / 2)
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
         if verrou_production == OFF :
            Label(fenetre_de_modification_d_une_consigne, text = "Type :").grid(row = 0, column = 0, padx = 5, pady = 5)
            Label(fenetre_de_modification_d_une_consigne, text = f" {TYPES_DE_CONSIGNE[consigne_a_changer['type']]}").grid(row = 0, column = 1, columnspan = 3, padx = 5, pady = 5)
         if type_d_asservissement == ASSERVISSEMENT_EN_CHARGE :
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
                  if verrou_production == OFF :
                     Label(fenetre_de_modification_d_une_consigne, text = "Vitesse en tonnes/secondes :").grid(row = 1, column = 0, padx = 5, pady = 5)
                     Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = speed, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_vitesse_charge), '%P')).grid(row = 1, column = 1, padx = 5, pady = 5)
                  condition_superieure_a = DoubleVar()
                  condition_inferieure_a = DoubleVar()
                  condition_en_temps = DoubleVar()
                  type_de_condition = IntVar()
                  if est_une_modif :
                     cond = consigne_a_changer["condition"]
                     if cond is None :
                        type_de_condition.set(0)
                     elif '>' in cond :
                        type_de_condition.set(1)
                        condition_superieure_a.set(2 * float(cond[DEBUT_CONDITION_CHARGE:]))
                     elif '<' in cond :
                        type_de_condition.set(2)
                        condition_inferieure_a.set(2 * float(cond[DEBUT_CONDITION_CHARGE:]))
                     else :
                        type_de_condition.set(3)
                        condition_en_temps.set(float(cond[DEBUT_CONDITION_TEMPS:]))
                  if verrou_production == OFF :
                     Label(fenetre_de_modification_d_une_consigne, text = "Condition d'arrêt :").grid(row = 2, column = 0, padx = 5, pady = 5)
                     Radiobutton(fenetre_de_modification_d_une_consigne, text = "aucune limite", variable = type_de_condition, value = 0).grid(row = 2, column = 1, columnspan = 4, padx = 5, pady = 5, sticky = 'w')
                     
                     Radiobutton(fenetre_de_modification_d_une_consigne, text = "      >", variable = type_de_condition, value = 1).grid(row = 3, column = 1, padx = 5, pady = 5, sticky = 'w')
                     Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_superieure_a, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 3, column = 2, padx = 5, pady = 5)
                     Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 3, column = 3, padx = 5, pady = 5, sticky = 'w')
                     
                     Radiobutton(fenetre_de_modification_d_une_consigne, text = "      <", variable = type_de_condition, value = 2).grid(row = 4, column = 1, padx = 5, pady = 5, sticky = 'w')
                     Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_inferieure_a, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 4, column = 2, padx = 5, pady = 5)
                     Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 4, column = 3, padx = 5, pady = 5, sticky = 'w')
                     
                     Radiobutton(fenetre_de_modification_d_une_consigne, text = "pendant", variable = type_de_condition, value = 3).grid(row = 5, column = 1, padx = 5, pady = 5, sticky = 'w')
                     Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_en_temps, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 5, column = 2, padx = 5, pady = 5)
                     Label(fenetre_de_modification_d_une_consigne, text = "s").grid(row = 5, column = 3, padx = 5, pady = 5, sticky = 'w')
                  else :
                     Label(fenetre_de_modification_d_une_consigne, text = "Tirer jusqu'à ").grid(row = 0, column = 0, padx = 5, pady = 5)
                     Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_superieure_a, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge_prod), '%P')).grid(row = 0, column = 1, padx = 5, pady = 5)
                     Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 0, column = 2, padx = 5, pady = 5, sticky = 'w')
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
                  condition_superieure_a1 = DoubleVar()
                  condition_inferieure_a1 = DoubleVar()
                  condition_en_temps1 = DoubleVar()
                  type_de_condition1 = IntVar()
                  condition_superieure_a2 = DoubleVar()
                  condition_inferieure_a2 = DoubleVar()
                  condition_en_temps2 = DoubleVar()
                  type_de_condition2 = IntVar()
                  nombre_de_cycles = IntVar()
                  if est_une_modif :
                     cond1 = consigne_a_changer["condition1"]
                     cond2 = consigne_a_changer["condition2"]
                     nombre_de_cycles.set(int(consigne_a_changer["cycles"]))
                     if '>' in cond1 :
                        type_de_condition1.set(1)
                        condition_superieure_a1.set(2 * float(cond1[DEBUT_CONDITION_CHARGE:]))
                     elif '<' in cond1 :
                        type_de_condition1.set(2)
                        condition_inferieure_a1.set(2 * float(cond1[DEBUT_CONDITION_CHARGE:]))
                     else :
                        type_de_condition1.set(3)
                        condition_en_temps1.set(float(cond1[DEBUT_CONDITION_TEMPS:]))
                     
                     if '>' in cond2 :
                        type_de_condition2.set(1)
                        condition_superieure_a2.set(2 * float(cond2[DEBUT_CONDITION_CHARGE:]))
                     elif '<' in cond2 :
                        type_de_condition2.set(2)
                        condition_inferieure_a2.set(2 * float(cond2[DEBUT_CONDITION_CHARGE:]))
                     else :
                        type_de_condition2.set(3)
                        condition_en_temps2.set(float(cond2[DEBUT_CONDITION_TEMPS:]))
                  else :
                     type_de_condition1.set(3)
                     type_de_condition2.set(3)
                     nombre_de_cycles.set(1)
                  
                  Label(fenetre_de_modification_d_une_consigne, text = "Condition de passage à la deuxième :").grid(row = 2, column = 0, padx = 5, pady = 5)
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "      >", variable = type_de_condition1, value = 1).grid(row = 2, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_superieure_a1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 2, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 2, column = 3, padx = 5, pady = 5, sticky = 'w')
                  
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "      <", variable = type_de_condition1, value = 2).grid(row = 3, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_inferieure_a1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 3, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 3, column = 3, padx = 5, pady = 5, sticky = 'w')
                  
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "pendant", variable = type_de_condition1, value = 3).grid(row = 4, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_en_temps1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 4, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "s").grid(row = 4, column = 3, padx = 5, pady = 5, sticky = 'w')

                  Label(fenetre_de_modification_d_une_consigne, text = "Condition d'arrêt :").grid(row = 6, column = 0, padx = 5, pady = 5)
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "      >", variable = type_de_condition2, value = 1).grid(row = 6, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_superieure_a2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 6, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "T").grid(row = 6, column = 3, padx = 5, pady = 5, sticky = 'w')
                  
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "      <", variable = type_de_condition2, value = 2).grid(row = 7, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_inferieure_a2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 7, column = 2, padx = 5, pady = 5)
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
                  Label(fenetre_de_modification_d_une_consigne, text = "Valeur minimale en tonnes :").grid(row = 2, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = pic_bas, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 2, column = 2, padx = 5, pady = 5, sticky = 'w')
                  Label(fenetre_de_modification_d_une_consigne, text = "Valeur maximale en tonnes :").grid(row = 3, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = pic_haut, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_charge), '%P')).grid(row = 3, column = 2, padx = 5, pady = 5, sticky = 'w')
                  Label(fenetre_de_modification_d_une_consigne, text = "Départ du sinus :").grid(row = 4, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'w')
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "Au centre, vers le haut", variable = phase, value = 0).grid(row = 4, column = 2, padx = 5, pady = 5, sticky = 'w')
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "En haut", variable = phase, value = 1).grid(row = 5, column = 2, padx = 5, pady = 5, sticky = 'w')
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "Au centre, vers le bas", variable = phase, value = 2).grid(row = 6, column = 2, padx = 5, pady = 5, sticky = 'w')
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "En bas", variable = phase, value = 3).grid(row = 7, column = 2, padx = 5, pady = 5, sticky = 'w')
                  condition_superieure_a = DoubleVar()
                  condition_inferieure_a = DoubleVar()
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
         else :
            match consigne_a_changer["type"] :
               case "constant" :
                  value = DoubleVar()
                  if est_une_modif :
                     value.set(COEF_VOLTS_TO_MILLIMETERS * consigne_a_changer['value'])
                  Label(fenetre_de_modification_d_une_consigne, text = "Valeur en millimètres :").grid(row = 1, column = 0, padx = 5, pady = 5)
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = value, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_position), '%P')).grid(row = 1, column = 1, padx = 5, pady = 5)
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
                     speed.set(COEF_VOLTS_TO_MILLIMETERS * consigne_a_changer['speed'])
                  if verrou_production == OFF :
                     Label(fenetre_de_modification_d_une_consigne, text = "Vitesse en millimètres/secondes :").grid(row = 1, column = 0, padx = 5, pady = 5)
                     Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = speed, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_vitesse_position), '%P')).grid(row = 1, column = 1, padx = 5, pady = 5)
                  condition_superieure_a = DoubleVar()
                  condition_inferieure_a = DoubleVar()
                  condition_en_temps = DoubleVar()
                  type_de_condition = IntVar()
                  if est_une_modif :
                     cond = consigne_a_changer["condition"]
                     if cond is None :
                        type_de_condition.set(0)
                     elif '>' in cond :
                        type_de_condition.set(1)
                        condition_superieure_a.set(COEF_VOLTS_TO_MILLIMETERS * float(cond[DEBUT_CONDITION_POSITION:]))
                     elif '<' in cond :
                        type_de_condition.set(2)
                        condition_inferieure_a.set(COEF_VOLTS_TO_MILLIMETERS * float(cond[DEBUT_CONDITION_POSITION:]))
                     else :
                        type_de_condition.set(3)
                        condition_en_temps.set(float(cond[DEBUT_CONDITION_TEMPS:]))
                  Label(fenetre_de_modification_d_une_consigne, text = "Condition d'arrêt :").grid(row = 2, column = 0, padx = 5, pady = 5)
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "aucune limite", variable = type_de_condition, value = 0).grid(row = 2, column = 1, columnspan = 4, padx = 5, pady = 5, sticky = 'w')
                  
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "      >", variable = type_de_condition, value = 1).grid(row = 3, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_superieure_a, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_position), '%P')).grid(row = 3, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "mm").grid(row = 3, column = 3, padx = 5, pady = 5, sticky = 'w')
                  
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "      <", variable = type_de_condition, value = 2).grid(row = 4, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_inferieure_a, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_position), '%P')).grid(row = 4, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "mm").grid(row = 4, column = 3, padx = 5, pady = 5, sticky = 'w')
                  
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "pendant", variable = type_de_condition, value = 3).grid(row = 5, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_en_temps, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 5, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "s").grid(row = 5, column = 3, padx = 5, pady = 5, sticky = 'w')
               case "cyclic" :
                  value1 = DoubleVar()
                  value2 = DoubleVar()
                  if est_une_modif :
                     value1.set(COEF_VOLTS_TO_MILLIMETERS * consigne_a_changer['value1'])
                     value2.set(COEF_VOLTS_TO_MILLIMETERS * consigne_a_changer['value2'])
                  Label(fenetre_de_modification_d_une_consigne, text = "Valeur en millimètres du premier palier :").grid(row = 1, column = 0, padx = 5, pady = 5)
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = value1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_position), '%P')).grid(row = 1, column = 1, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "Valeur en millimètres du deuxième palier :").grid(row = 3, column = 0, padx = 5, pady = 5)
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = value2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_position), '%P')).grid(row = 3, column = 1, padx = 5, pady = 5)
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
                     speed1.set(COEF_VOLTS_TO_MILLIMETERS * consigne_a_changer['speed1'])
                     speed2.set(COEF_VOLTS_TO_MILLIMETERS * consigne_a_changer['speed2'])
                  Label(fenetre_de_modification_d_une_consigne, text = "Vitesse en millimètres/secondes :").grid(row = 1, column = 0, padx = 5, pady = 5)
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = speed1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_vitesse_position), '%P')).grid(row = 1, column = 1, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "Vitesse en millimètres/secondes :").grid(row = 5, column = 0, padx = 5, pady = 5)
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = speed2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_vitesse_position), '%P')).grid(row = 5, column = 1, padx = 5, pady = 5)
                  condition_superieure_a1 = DoubleVar()
                  condition_inferieure_a1 = DoubleVar()
                  condition_en_temps1 = DoubleVar()
                  type_de_condition1 = IntVar()
                  condition_superieure_a2 = DoubleVar()
                  condition_inferieure_a2 = DoubleVar()
                  condition_en_temps2 = DoubleVar()
                  type_de_condition2 = IntVar()
                  nombre_de_cycles = IntVar()
                  if est_une_modif :
                     cond1 = consigne_a_changer["condition1"]
                     cond2 = consigne_a_changer["condition2"]
                     nombre_de_cycles.set(int(consigne_a_changer["cycles"]))
                     if '>' in cond1 :
                        type_de_condition1.set(1)
                        condition_superieure_a1.set(COEF_VOLTS_TO_MILLIMETERS * float(cond1[DEBUT_CONDITION_POSITION:]))
                     elif '<' in cond1 :
                        type_de_condition1.set(2)
                        condition_inferieure_a1.set(COEF_VOLTS_TO_MILLIMETERS * float(cond1[DEBUT_CONDITION_POSITION:]))
                     else :
                        type_de_condition1.set(3)
                        condition_en_temps1.set(float(cond1[DEBUT_CONDITION_TEMPS:]))
                     
                     if '>' in cond2 :
                        type_de_condition2.set(1)
                        condition_superieure_a2.set(COEF_VOLTS_TO_MILLIMETERS * float(cond2[DEBUT_CONDITION_POSITION:]))
                     elif '<' in cond2 :
                        type_de_condition2.set(2)
                        condition_inferieure_a2.set(COEF_VOLTS_TO_MILLIMETERS * float(cond2[DEBUT_CONDITION_POSITION:]))
                     else :
                        type_de_condition2.set(3)
                        condition_en_temps2.set(float(cond2[DEBUT_CONDITION_TEMPS:]))
                  else :
                     type_de_condition1.set(3)
                     type_de_condition2.set(3)
                     nombre_de_cycles.set(1)
                  
                  Label(fenetre_de_modification_d_une_consigne, text = "Condition de passage à la deuxième :").grid(row = 2, column = 0, padx = 5, pady = 5)
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "      >", variable = type_de_condition1, value = 1).grid(row = 2, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_superieure_a1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_position), '%P')).grid(row = 2, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "mm").grid(row = 2, column = 3, padx = 5, pady = 5, sticky = 'w')
                  
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "      <", variable = type_de_condition1, value = 2).grid(row = 3, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_inferieure_a1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_position), '%P')).grid(row = 3, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "mm").grid(row = 3, column = 3, padx = 5, pady = 5, sticky = 'w')
                  
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "pendant", variable = type_de_condition1, value = 3).grid(row = 4, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_en_temps1, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 4, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "s").grid(row = 4, column = 3, padx = 5, pady = 5, sticky = 'w')

                  Label(fenetre_de_modification_d_une_consigne, text = "Condition d'arrêt :").grid(row = 6, column = 0, padx = 5, pady = 5)
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "      >", variable = type_de_condition2, value = 1).grid(row = 6, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_superieure_a2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_position), '%P')).grid(row = 6, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "mm").grid(row = 6, column = 3, padx = 5, pady = 5, sticky = 'w')
                  
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "      <", variable = type_de_condition2, value = 2).grid(row = 7, column = 1, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = condition_inferieure_a2, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_position), '%P')).grid(row = 7, column = 2, padx = 5, pady = 5)
                  Label(fenetre_de_modification_d_une_consigne, text = "mm").grid(row = 7, column = 3, padx = 5, pady = 5, sticky = 'w')
                  
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
                     pic_haut.set(COEF_VOLTS_TO_MILLIMETERS * (consigne_a_changer['offset'] + consigne_a_changer['amplitude'] / 2))
                     pic_bas.set(COEF_VOLTS_TO_MILLIMETERS * (consigne_a_changer['offset'] - consigne_a_changer['amplitude'] / 2))
                     phase.set(int(consigne_a_changer['phase'] * 2 / pi + 0.05)) # +0.05 en cas d'approximation
                  Label(fenetre_de_modification_d_une_consigne, text = "Période en secondes :").grid(row = 1, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = periode, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_temps), '%P')).grid(row = 1, column = 2, padx = 5, pady = 5, sticky = 'w')
                  Label(fenetre_de_modification_d_une_consigne, text = "Valeur maximale en millimètres :").grid(row = 3, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = pic_bas, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_position), '%P')).grid(row = 2, column = 2, padx = 5, pady = 5, sticky = 'w')
                  Label(fenetre_de_modification_d_une_consigne, text = "Départ du sinus :").grid(row = 4, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'w')
                  Entry(fenetre_de_modification_d_une_consigne, width = 5, textvariable = pic_haut, validate="key", validatecommand=(fenetre_de_modification_d_une_consigne.register(_check_entree_position), '%P')).grid(row = 3, column = 2, padx = 5, pady = 5, sticky = 'w')
                  Label(fenetre_de_modification_d_une_consigne, text = "Valeur minimale en millimètres :").grid(row = 2, column = 0, columnspan = 2, padx = 5, pady = 5, sticky = 'w')
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "Au centre, vers le haut", variable = phase, value = 0).grid(row = 4, column = 2, padx = 5, pady = 5, sticky = 'w')
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "En haut", variable = phase, value = 1).grid(row = 5, column = 2, padx = 5, pady = 5, sticky = 'w')
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "Au centre, vers le bas", variable = phase, value = 2).grid(row = 6, column = 2, padx = 5, pady = 5, sticky = 'w')
                  Radiobutton(fenetre_de_modification_d_une_consigne, text = "En bas", variable = phase, value = 3).grid(row = 7, column = 2, padx = 5, pady = 5, sticky = 'w')
                  condition_superieure_a = DoubleVar()
                  condition_inferieure_a = DoubleVar()
                  condition_en_cycles = DoubleVar()
                  type_de_condition = IntVar()
                  if est_une_modif :
                     cond = consigne_a_changer["condition"]
                     if cond is None :
                        type_de_condition.set(0)
                     else :
                        type_de_condition.set(3)
                        condition_en_cycles.set(float(cond[DEBUT_CONDITION_TEMPS:]))
                  
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
         nonlocal consignes_du_generateur
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
         if verrou_production == ON :
            chemin_du_dernier_test += "consignes_du_test_precedent_production.json"
         elif type_d_asservissement == ASSERVISSEMENT_EN_CHARGE :
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

         if verrou_production == OFF :
            Button(cadre_interne_consignes, text = "Charger depuis un fichier", command = chargement_des_consignes).grid(row = 0, column = 0, padx = 5, pady = 12)
            Button(cadre_interne_consignes, text = "Insérer une consigne au départ", command = lambda : surcouche_ajout(0)).grid(row = 0, column = 1, padx = 5, pady = 12)
            Button(cadre_interne_consignes, text = "Enregistrer dans un fichier", command = enregistrement_des_consignes).grid(row = 0, column = 2, padx = 5, pady = 12)
            if len(consignes_du_generateur) :
               Label(cadre_interne_consignes, text = "Consigne(s) actuellement prévue(s) :").grid(row = 1, column = 0, columnspan = 3, padx = 5, pady = 4)
               indice_de_cette_consigne = 0
               for consigne_du_generateur in consignes_du_generateur :
                  indice_de_cette_consigne += 1
                  label_de_cette_consigne = ""
                  if type_d_asservissement == ASSERVISSEMENT_EN_CHARGE :
                     match consigne_du_generateur['type'] :
                        case "ramp" :
                           label_de_cette_consigne = f"Rampe simple de {2 * consigne_du_generateur['speed']}T/s"
                           condition_d_arret = consigne_du_generateur["condition"]
                           if condition_d_arret is None :
                              label_de_cette_consigne += ", dure indéfiniment"
                           elif condition_d_arret.startswith('delay') :
                              label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                           else :
                              label_de_cette_consigne += f" jusqu'à {str(2 * float(condition_d_arret[DEBUT_CONDITION_CHARGE:]))}T"
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
                              label_de_cette_consigne += f" jusqu'à {str(2 * float(condition_d_arret[DEBUT_CONDITION_CHARGE:]))}T"
                           label_de_cette_consigne += f", {2 * consigne_du_generateur['speed2']}T/s"
                           condition_d_arret = consigne_du_generateur["condition2"]
                           if condition_d_arret.startswith('delay') :
                              label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                           else :
                              label_de_cette_consigne += f" jusqu'à {str(2 * float(condition_d_arret[DEBUT_CONDITION_CHARGE:]))}T"
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
                  else :
                     match consigne_du_generateur['type'] :
                        case "ramp" :
                           label_de_cette_consigne = f"Rampe simple de {COEF_VOLTS_TO_MILLIMETERS * consigne_du_generateur['speed']}mm/s"
                           condition_d_arret = consigne_du_generateur["condition"]
                           if condition_d_arret is None :
                              label_de_cette_consigne += ", dure indéfiniment"
                           elif condition_d_arret.startswith('delay') :
                              label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                           else :
                              label_de_cette_consigne += f" jusqu'à {str(COEF_VOLTS_TO_MILLIMETERS * float(condition_d_arret[DEBUT_CONDITION_POSITION:]))}mm"
                        case "constant" :
                           label_de_cette_consigne = "Palier à "
                           label_de_cette_consigne += f"{COEF_VOLTS_TO_MILLIMETERS * consigne_du_generateur['value']}mm"
                           condition_d_arret = consigne_du_generateur["condition"]
                           if condition_d_arret is None :
                              label_de_cette_consigne += ", dure indéfiniment"
                           elif condition_d_arret.startswith('delay') :
                              label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                           else :
                              label_de_cette_consigne += f" maintenu jusqu'à atteindre {COEF_VOLTS_TO_MILLIMETERS * condition_d_arret[DEBUT_CONDITION_POSITION:]}T"
                        case "cyclic_ramp" :
                           label_de_cette_consigne = f"{consigne_du_generateur['cycles']} cycles de rampes : "
                           label_de_cette_consigne += f"{COEF_VOLTS_TO_MILLIMETERS * consigne_du_generateur['speed1']}mm/s"
                           condition_d_arret = consigne_du_generateur["condition1"]
                           if condition_d_arret.startswith('delay') :
                              label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                           else :
                              label_de_cette_consigne += f" jusqu'à {str(COEF_VOLTS_TO_MILLIMETERS * float(condition_d_arret[DEBUT_CONDITION_POSITION:]))}T"
                           label_de_cette_consigne += f", {COEF_VOLTS_TO_MILLIMETERS * consigne_du_generateur['speed2']}mm/s"
                           condition_d_arret = consigne_du_generateur["condition2"]
                           if condition_d_arret.startswith('delay') :
                              label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                           else :
                              label_de_cette_consigne += f" jusqu'à {str(COEF_VOLTS_TO_MILLIMETERS * float(condition_d_arret[DEBUT_CONDITION_POSITION:]))}T"
                        case "cyclic" :
                           label_de_cette_consigne = f"{consigne_du_generateur['cycles']} cycles de paliers : "
                           label_de_cette_consigne += f"{COEF_VOLTS_TO_MILLIMETERS * consigne_du_generateur['value1']}mm"
                           condition_d_arret = consigne_du_generateur["condition1"]
                           if condition_d_arret.startswith('delay') :
                              label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                           else :
                              label_de_cette_consigne += f" jusqu'à {COEF_VOLTS_TO_MILLIMETERS * condition_d_arret[DEBUT_CONDITION_POSITION:]}mm"
                           label_de_cette_consigne += f", {COEF_VOLTS_TO_MILLIMETERS * consigne_du_generateur['value2']}mm"
                           condition_d_arret = consigne_du_generateur["condition2"]
                           if condition_d_arret.startswith('delay') :
                              label_de_cette_consigne += f" pendant {condition_d_arret[DEBUT_CONDITION_TEMPS:]}s"
                           else :
                              label_de_cette_consigne += f" jusqu'à {COEF_VOLTS_TO_MILLIMETERS * condition_d_arret[DEBUT_CONDITION_POSITION:]}mm"
                        case "sine" :
                           label_de_cette_consigne = f"Sinus allant de {COEF_VOLTS_TO_MILLIMETERS * (consigne_du_generateur['offset'] - consigne_du_generateur['amplitude'] / 2)}mm à {COEF_VOLTS_TO_MILLIMETERS * (consigne_du_generateur['offset'] + consigne_du_generateur['amplitude'] / 2)}mm, de période {1 / consigne_du_generateur['freq']}s, démarrant "
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
                  # Label(cadre_de_cette_consigne, image = PhotoImage(file = DOSSIER_CONFIG_ET_CONSIGNES + "rampe simple.png")).grid(row = 1, column = 0, padx = 5, pady = 5)
                  Button(cadre_de_cette_consigne, text = "Supprimer cette consigne", command = lambda i = indice_de_cette_consigne - 1 : suppression_d_une_consigne(i)).grid(row = 1, column = 1, padx = 5, pady = 5)
                  Button(cadre_de_cette_consigne, text = "Modifier cette consigne", command = lambda i = indice_de_cette_consigne - 1 : surcouche_modification(i)).grid(row = 1, column = 2, padx = 5, pady = 5, sticky = 'e')
                  Button(cadre_interne_consignes, text = "Insérer une consigne", command = lambda i = indice_de_cette_consigne : surcouche_ajout(i)).grid(row = (2 * indice_de_cette_consigne + 1), column = 1, padx = 5, pady = 5, sticky = 'e')
                  cadre_interne_consignes.columnconfigure(0, weight=1)
                  cadre_interne_consignes.columnconfigure(1, weight=1)
                  cadre_interne_consignes.columnconfigure(2, weight=1)
         else :
            if len(consignes_du_generateur) :
               Label(cadre_interne_consignes, text = "Consigne actuellement prévue :").grid(row = 0, column = 0, columnspan = 3, padx = 5, pady = 4)
               label_de_cette_consigne = f"Tire le cable"# à {2 * consignes_du_generateur[2]['speed']}T/s"
               label_de_cette_consigne += f" jusqu'à {str(2 * float(consignes_du_generateur[2]['condition'][DEBUT_CONDITION_CHARGE:]))}T"
               Label(cadre_interne_consignes, text = label_de_cette_consigne).grid(row = 1, column = 0, columnspan = 3, padx = 5, pady = 4, sticky = 'we')

         Button(cadre_interne_consignes, text = "Annuler les changements", command = annulation_des_changements).grid(row = (2 * NOMBRE_DE_CONSIGNES_MAXIMAL + 2), column = 0, padx = 5, pady = 5)
         if verrou_production == OFF :
            Button(cadre_interne_consignes, text = "Tout supprimer", command = suppression_de_toutes_les_consignes).grid(row = (2 * NOMBRE_DE_CONSIGNES_MAXIMAL + 2), column = 1, padx = 5, pady = 5)
         else :
            Button(cadre_interne_consignes, text = "Modifier", command = lambda : surcouche_modification(2)).grid(row = (2 * NOMBRE_DE_CONSIGNES_MAXIMAL + 2), column = 1, padx = 5, pady = 5)
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
      if verrou_production == OFF :
         canevas = Canvas(fenetre_de_choix_des_consignes, width = 900, height = 500)
         canevas.grid(row = 0, column = 0, sticky = (N, S, E, W))
         canevas.rowconfigure(0, weight=1)
         canevas.columnconfigure(0, weight=1)
         y_scrollbar = ttk.Scrollbar(fenetre_de_choix_des_consignes, orient="vertical", command=canevas.yview)
         y_scrollbar.grid(column=1, row=0, sticky=(N, S, E))
         cadre_interne_consignes = ttk.Frame(canevas, width = 880)
         cadre_interne_consignes.pack(in_ = canevas, expand = True, fill = BOTH)
         
         cadre_interne_consignes.bind("<Configure>", lambda _: canevas.configure(scrollregion = canevas.bbox("all")))
         canevas.create_window((0, 0), window = cadre_interne_consignes, anchor = "nw")
         canevas.configure(yscrollcommand=y_scrollbar.set)

         cadre_interne_consignes.bind('<Enter>', lambda e : _bound_to_mousewheel(canevas, e))
         cadre_interne_consignes.bind('<Leave>', lambda e : _unbound_to_mousewheel(canevas, e))
      else :
         cadre_interne_consignes = ttk.Frame(fenetre_de_choix_des_consignes)
         cadre_interne_consignes.pack(expand = True)

      actualisation_des_boutons()
      fenetre_de_choix_des_consignes.mainloop()
   #V
   def crappy_launcher():
      """TODO"""
      # C'est ici qu'on peut changer les colonnes que l'on veut avoir dans le csv (et le xlsx).
      nonlocal parametres
      launch_crappy_event.wait()
      launch_crappy_event.clear()
      if test_effectue :
         global enregistrement_effectue
         enregistrement_effectue = True
         if type_d_asservissement == ASSERVISSEMENT_EN_CHARGE :
            labels_voulus = ["Temps (s)", "Consigne (T)", "sortie_charge_brute", "Charge (T)", "sortie_position_brute", "Position (mm)"]
            demarrage_de_crappy_charge(consignes_generateur = consignes_du_generateur, 
                           fichier_d_enregistrement = DOSSIER_ENREGISTREMENTS + str(datetime.datetime.now())[:11] + entrees[0] + ".csv",
                           parametres_du_test = parametres, 
                           labels_a_enregistrer = labels_voulus)
         else :
            labels_voulus = ["Temps (s)", "Consigne (mm)", "sortie_charge_brute", "Charge (T)", "sortie_position_brute", "Position (mm)"]
            demarrage_de_crappy_deplacement(consignes_generateur = consignes_du_generateur, 
                           fichier_d_enregistrement = DOSSIER_ENREGISTREMENTS + str(datetime.datetime.now())[:11] + entrees[0] + ".csv",
                           parametres_du_test = parametres, 
                           labels_a_enregistrer = labels_voulus)
      return

   # def crappy_stopper():
   #    stop_crappy_event.wait()
   #    stop_crappy_event.clear()
   #    stop_crappy()

   def start_crappy():
      """FR : Lance Crappy et empêche de le relancer dans le même test.
      
      EN : Launches Crappy and disables launching it again in the same test."""
      desactiver_bouton(bouton_de_demarrage_du_test)
      desactiver_bouton(bouton_de_lancement_de_l_enregistrement)
      desactiver_bouton(bouton_de_mise_en_tension_lente)
      desactiver_bouton(bouton_de_mise_en_tension_rapide)
      desactiver_bouton(bouton_de_retour_en_position_initiale)
      activer_bouton(bouton_d_arret_de_crappy)
      # desactiver_bouton(bouton_de_retour_en_position_initiale)
      # desactiver_bouton(bouton_de_mise_en_tension)
      nonlocal test_effectue
      test_effectue = True
      launch_crappy_event.set()
      time.sleep(5)
      fenetre_principale.lift()

   def demarrage_de_crappy_enregistrement_manuel():
      """TODO"""
      nonlocal parametres
      desactiver_bouton(bouton_de_demarrage_du_test)
      desactiver_bouton(bouton_de_lancement_de_l_enregistrement)
      desactiver_bouton(bouton_de_mise_en_tension_lente)
      desactiver_bouton(bouton_de_mise_en_tension_rapide)
      desactiver_bouton(bouton_de_retour_en_position_initiale)
      activer_bouton(bouton_d_arret_de_crappy)
      # desactiver_bouton(bouton_de_retour_en_position_initiale)
      # desactiver_bouton(bouton_de_mise_en_tension)

      carte_NI = crappy.blocks.IOBlock(name = "Nidaqmx",
                                       labels = ["t(s)", "sortie_charge_brute", 
                                                "sortie_position_brute"],
                                       channels = [{'name': 'Dev3/ai6'},
                                                   {'name': 'Dev3/ai7'}],
                                       spam = True,
                                       freq = 50)
      liste_des_blocs_crappy_utilises.append(carte_NI)

      graphe = customblocks.EmbeddedGrapher(("t(s)", LABEL_SORTIE_EN_CHARGE),
                                          ("t(s)", LABEL_SORTIE_EN_POSITION),
                                          freq = 3)
      liste_des_blocs_crappy_utilises.append(graphe)

      y_record = crappy.blocks.Multiplex(freq = 50)
      liste_des_blocs_crappy_utilises.append(y_record)

      pancarte = crappy.blocks.Dashboard(labels = ["Temps (s)", "Position (mm)", "Charge (T)", 
                                                   "Charge max (T)", "Position min (mm)", "Position max (mm)"],
                                       freq = 5)
      liste_des_blocs_crappy_utilises.append(pancarte)

      record = customblocks.CustomRecorder(filename = DOSSIER_ENREGISTREMENTS + str(datetime.datetime.now())[:11] + entrees[0] + ".csv",
                                          labels = ["t(s)", 
                                                    "sortie_charge_brute", 
                                                    "Charge (T)", 
                                                    "sortie_position_brute",
                                                    "Position (mm)"], 
                                          parametres_a_inscrire = parametres)
      liste_des_blocs_crappy_utilises.append(record)


      crappy.link(carte_NI, y_record, modifier = _card_to_recorder_and_graph)
      crappy.link(y_record, record)
      crappy.link(carte_NI, graphe, modifier=_card_to_recorder_and_graph)
      crappy.link(carte_NI, pancarte, modifier = _card_to_dashboard)

      global enregistrement_effectue
      enregistrement_effectue = True
      Thread(target = crappy.start).start()

   def stop_crappy():
      """FR : Arrête Crappy puis remet les distributeurs des valves à 0.
      
      EN : Stops Crappy and resets the valves' distributors."""
      activer_bouton(bouton_de_mise_en_tension_lente)
      activer_bouton(bouton_de_mise_en_tension_rapide)
      activer_bouton(bouton_de_retour_en_position_initiale)
      if not enregistrement_effectue :
         activer_bouton(bouton_de_demarrage_du_test)
         activer_bouton(bouton_de_lancement_de_l_enregistrement)
      
      # print("_______________\n" + str(liste_des_blocs_crappy_utilises) + "\n_____________")
      while len(liste_des_blocs_crappy_utilises) > 0 :
         bloc_a_supprimer = liste_des_blocs_crappy_utilises.pop()
         bloc_a_supprimer.stop()
         try :
            crappy.blocks.Block.instances.remove(bloc_a_supprimer)
         except KeyError:
            pass
      crappy.stop()
      crappy.reset()
      # TODO : remove "and enregistrement_effectue". Used only for debug purposes.
      if enregistrement_effectue and __name__ == "__main__":
         # remise_a_zero()
         gen = crappy.blocks.Generator(path=[{'type': 'constant',
                                             'value': 0,
                                             'condition': "delay=1"}],
                                       cmd_label='commande_en_charge',
                                       spam=True)

         carte_NI = crappy.blocks.IOBlock(name="Nidaqmx",
                                          cmd_labels=["commande_en_charge", "commande_en_charge"],
                                          initial_cmd=[0.0, 0.0],
                                          exit_values=[0.0, 0.0],
                                          channels=[{'name': 'Dev3/ao0'},
                                                   {'name': 'Dev3/ao1'},
                                                   {'name': 'Dev3/ai6'},
                                                   {'name': 'Dev3/ai7'}])

         crappy.link(gen, carte_NI)
         Thread(target = crappy.start).start()
         time.sleep(3)
         carte_NI.stop()
         gen.stop()
         crappy.stop()
         crappy.reset()
         return

   def gros_bouton_rouge():
      """TODO"""
      # activer_bouton(bouton_enregistrer_et_quitter)
      desactiver_bouton(bouton_d_arret_de_crappy)
      # activer_bouton(enregistrer_btn)
      # activer_bouton(mise_a_0_btn)
      # activer_bouton(mise_a_tension_btn)
      menu1.entryconfigure(2, state=NORMAL)
      if enregistrement_effectue :
         menu3.entryconfigure("Certificat", state = NORMAL)

      stop_crappy()

   def retour_en_position_initiale():
      """TODO"""
      desactiver_bouton(bouton_de_demarrage_du_test)
      desactiver_bouton(bouton_de_lancement_de_l_enregistrement)
      desactiver_bouton(bouton_de_mise_en_tension_lente)
      desactiver_bouton(bouton_de_mise_en_tension_rapide)
      desactiver_bouton(bouton_de_retour_en_position_initiale)
      activer_bouton(bouton_d_arret_de_crappy)
      # desactiver_bouton(bouton_de_retour_en_position_initiale)
      # desactiver_bouton(bouton_de_mise_en_tension)

      gen_retour_en_position_initiale = crappy.blocks.Generator(
            path = [{"type": "ramp", 
                     "speed": -0.25, 
                     "condition" : LABEL_SORTIE_EN_POSITION + "<" + str(5 * COEF_MILLIMETERS_TO_VOLTS)},
                     {'type': 'constant',
                     'value': 0,
                     'condition': "delay=1"}],
            cmd_label = 'consigne',
            spam = True,
            freq = 50)
      liste_des_blocs_crappy_utilises.append(gen_retour_en_position_initiale)

      carte_retour_en_position_initiale = crappy.blocks.IOBlock(
            name = "Nidaqmx",
            labels = ["t(s)", "sortie_charge_brute", "sortie_position_brute"],
            cmd_labels = ["entree_decharge", "entree_charge"],
            initial_cmd = [0.0, 0.0],
            exit_values = [0.0, 0.0],
            channels=[{'name': 'Dev3/ao0'},
                     {'name': 'Dev3/ao1'},
                     {'name': 'Dev3/ai6'},
                     {'name': 'Dev3/ai7'}],
            spam = True,
            freq = 50)
      liste_des_blocs_crappy_utilises.append(carte_retour_en_position_initiale)

      crappy.link(gen_retour_en_position_initiale, carte_retour_en_position_initiale, modifier = gen_to_card_RaZ_et_MeT)
      crappy.link(carte_retour_en_position_initiale, gen_retour_en_position_initiale, modifier = _card_to_pid_and_generator)
      Thread(target = crappy.start).start()
      
   def mise_en_tension_rapide():
      """TODO"""
      desactiver_bouton(bouton_de_demarrage_du_test)
      desactiver_bouton(bouton_de_lancement_de_l_enregistrement)
      desactiver_bouton(bouton_de_mise_en_tension_lente)
      desactiver_bouton(bouton_de_mise_en_tension_rapide)
      desactiver_bouton(bouton_de_retour_en_position_initiale)
      activer_bouton(bouton_d_arret_de_crappy)

      gen_mise_en_tension_rapide = crappy.blocks.Generator(
            path = [{"type": "ramp", 
                     "speed": 0.5, 
                     "condition" : LABEL_SORTIE_EN_CHARGE + ">" + str(0.2 * COEF_TONS_TO_VOLTS)},
                     {'type': 'constant',
                     'value': 0,
                     'condition': "delay=0.1"}],
            cmd_label = 'consigne',
            spam = True,
            freq = 50)
      liste_des_blocs_crappy_utilises.append(gen_mise_en_tension_rapide)

      carte_mise_en_tension_rapide = crappy.blocks.IOBlock(
            name = "Nidaqmx",
            labels = ["t(s)", "sortie_charge_brute", "sortie_position_brute"],
            cmd_labels = ["entree_decharge", "entree_charge"],
            initial_cmd = [0.0, 0.0],
            exit_values = [0.0, 0.0],
            channels=[{'name': 'Dev3/ao0'},
                     {'name': 'Dev3/ao1'},
                     {'name': 'Dev3/ai6'},
                     {'name': 'Dev3/ai7'}],
            spam = True,
            freq = 50)
      liste_des_blocs_crappy_utilises.append(carte_mise_en_tension_rapide)

      crappy.link(gen_mise_en_tension_rapide, carte_mise_en_tension_rapide, modifier = gen_to_card_RaZ_et_MeT)
      crappy.link(carte_mise_en_tension_rapide, gen_mise_en_tension_rapide, modifier = _card_to_pid_and_generator)
      Thread(target = crappy.start).start()

   def mise_en_tension_lente():
      """TODO"""
      desactiver_bouton(bouton_de_demarrage_du_test)
      desactiver_bouton(bouton_de_lancement_de_l_enregistrement)
      desactiver_bouton(bouton_de_mise_en_tension_lente)
      desactiver_bouton(bouton_de_mise_en_tension_rapide)
      desactiver_bouton(bouton_de_retour_en_position_initiale)
      activer_bouton(bouton_d_arret_de_crappy)

      gen_mise_en_tension_lente = crappy.blocks.Generator(
            path = [{"type": "ramp", 
                     "speed": 0.1, 
                     "condition" : LABEL_SORTIE_EN_CHARGE + ">" + str(0.03 * COEF_TONS_TO_VOLTS)},
                     {'type': 'constant',
                     'value': 0,
                     'condition': "delay=0.1"}],
            cmd_label = 'consigne',
            spam = True,
            freq = 50)
      liste_des_blocs_crappy_utilises.append(gen_mise_en_tension_lente)

      carte_mise_en_tension_lente = crappy.blocks.IOBlock(
            name = "Nidaqmx",
            labels = ["t(s)", "sortie_charge_brute", "sortie_position_brute"],
            cmd_labels = ["entree_decharge", "entree_charge"],
            initial_cmd = [0.0, 0.0],
            exit_values = [0.0, 0.0],
            channels=[{'name': 'Dev3/ao0'},
                     {'name': 'Dev3/ao1'},
                     {'name': 'Dev3/ai6'},
                     {'name': 'Dev3/ai7'}],
            spam = True,
            freq = 50)
      liste_des_blocs_crappy_utilises.append(carte_mise_en_tension_lente)

      crappy.link(gen_mise_en_tension_lente, carte_mise_en_tension_lente, modifier = gen_to_card_RaZ_et_MeT)
      crappy.link(carte_mise_en_tension_lente, gen_mise_en_tension_lente, modifier = _card_to_pid_and_generator)
      Thread(target = crappy.start).start()

##################################################################################################################################

   type_d_asservissement = init_type_d_asservissement # 1 : en charge ; 2 : en déplacement
   premieres_consignes_validees = False
   while premieres_consignes_validees == False :
      entrees = configuration_initiale(init_titre, init_nom,
         init_materiau, init_lg_banc, init_charge_rupt, init_diam_a_vide, 
         init_accroche, init_epissage, init_cabestan, init_lg_utile)
      if verrou_production == RESTART:
         return demarrage_du_programme()
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
         if verrou_production == OFF :
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
            type_d_asservissement = ASSERVISSEMENT_EN_CHARGE
            with open(DOSSIER_CONFIG_ET_CONSIGNES + "consignes_du_test_precedent_production.json", 'r') as fichier_des_consignes_du_dernier_test :
               consignes_du_generateur = load(fichier_des_consignes_du_dernier_test)
            choix_des_consignes_du_generateur()
      else :
         type_d_asservissement = choix_du_type_d_asservissement(type_d_asservissement)
         consignes_du_generateur = []
         if type_d_asservissement != 0 :
            choix_des_consignes_du_generateur()      

   if len(consignes_du_generateur) > 0 :
      consigne_de_fin = 0
      match consignes_du_generateur[-1]["type"] :
         case "ramp" | "sine" :
            condition = consignes_du_generateur[-1]["condition"]
            if condition is not None :
               if "<" in condition :
                  consigne_de_fin = condition.split("<")[1]
               elif ">" in condition :
                  consigne_de_fin = condition.split(">")[1]
            consignes_du_generateur.append({"type" : "constant",
                                          "value" : consigne_de_fin,
                                          "condition" : None})
         case "cyclic_ramp" :
            condition = consignes_du_generateur[-1]["condition2"]
            if condition is not None :
               if "<" in condition :
                  consigne_de_fin = condition.split("<")[1]
               elif ">" in condition :
                  consigne_de_fin = condition.split(">")[1]
            consignes_du_generateur.append({"type" : "constant",
                                          "value" : consigne_de_fin,
                                          "condition" : None})
   print(consignes_du_generateur)
   
   # global tonnage_limite
   # match entrees[3] :
   #    case 1 :
   #       tonnage_limite = 20
   #    case 2 :
   #       tonnage_limite = 16.6
   #    case 3 :
   #       tonnage_limite = 14
   #    case 4 :
   #       tonnage_limite = 12
   #    case 5 :
   #       tonnage_limite = 10

   # pour créer le .xlsx :
   nom_du_fichier_csv = DOSSIER_ENREGISTREMENTS + str(datetime.datetime.now())[:11] + entrees[0] + ".csv"
   if path.exists(nom_du_fichier_csv):
      # If the file already exists, append a number to the name
      nom_du_fichier, extension = path.splitext(nom_du_fichier_csv)
      i = 1
      while path.exists(nom_du_fichier + "_%05d" % i + extension):
         i += 1
      nom_du_fichier_csv = nom_du_fichier + "_%05d" % i + extension
   nom_du_fichier_xlsx = nom_du_fichier_csv[:-4] + ".xlsx"
   print (nom_du_fichier_xlsx)
   # Ces paramètres seront inscrit dans le csv (et le xlsx) comme premières lignes.
   parametres = []
   parametres.append("Titre, " + entrees[0] + ", , , , ")
   parametres.append("Date, " + str(datetime.datetime.today()) + ", , , , ")
   parametres.append("Nom, " + entrees[1] + ", , , , ")
   parametres.append("Materiau, " + entrees[2] + ", , , , ")
   parametres.append("Charge de rupture, " + str(entrees[4]) + ", , , , ")
   parametres.append("Longueur de l'éprouvette, " + str(entrees[9]) + ", , , , ")
   parametres.append("Capteur de déplacement, Détecteur ultrasonique, , , , ")
   parametres.append("  référence, UC_2000_L2_U_V15, , , , ")
   parametres.append("Capteur de charge, Indicateur pour signal analogique, , , , ")
   parametres.append("  référence, INDI_PAXS, , , , ")
   if entrees[6] == 1 :
      parametres.append("Méthode d'accroche, Goupilles, , , , ")
   else :
      parametres.append("Méthode d'accroche, Cabestan " + str(str(entrees[8])) + "mm, , , , ")
   if entrees[10]:
      pass # rajouter des trucs pour ISO-2307
   parametres.append(' , , , , , ')
   
   sauvegarde_effectue = False
   test_effectue = False  # Mis à True avant de lancer l'essai. S'il n'y a pas de test,
                          # reste à False pour que le thread se termine avant de 
                          # relancer un essai. 
                          # Voir crappy_launcher() pour plus de détails. 
   crappy_launch_thread = Thread(target = crappy_launcher, daemon = True)
   crappy_launch_thread.start()
   # Thread(target = crappy_stopper, daemon = True).start()



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

   # Le reste trié
   choix_des_documents_a_enregistrer=IntVar()
   # choix_des_documents_a_enregistrer.set(0)
   charge_de_rupture=DoubleVar()
   charge_de_rupture.set(entrees[4])
   valeur_maximale_de_déplacement=DoubleVar() # Valeur maximale en déplacement
   valeur_maximale_de_déplacement.set(-10000)
   valeur_minimale_de_déplacement=DoubleVar() # Valeur minimale en déplacement
   valeur_minimale_de_déplacement.set(2000)
   valeur_maximale_de_charge=DoubleVar()
   valeur_maximale_de_charge.set(-10000)

   # vrac
   mode_manuel=StringVar()
   mode_manuel.set('off')

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

   # nom=crea_nom(1)
   # workbook = xlsxwriter.Workbook(nom)
   # chartsheet = workbook.add_chartsheet()
   # feuille = workbook.add_worksheet()

   # init_xlsx()
   # init_csv(entrees[0],entrees[1],entrees[2],str(entrees[3]))
   
   ##### Organisation de l'affichage #####
   liste_des_ecrans = get_monitors()
   indice_ecran = 0
   while indice_ecran < len(liste_des_ecrans) and not liste_des_ecrans[indice_ecran].is_primary :
      indice_ecran +=1    # Cherche l'écran principal.
   largeur_de_l_ecran = liste_des_ecrans[indice_ecran].width
   # largeur_de_l_ecran = 1440
   canvas=Canvas(fenetre_principale, height=int(largeur_de_l_ecran * 9/16 / 2),width = largeur_de_l_ecran / 3)
   canvas.grid(column=0, row=0, columnspan = 1, sticky=(N, W, E, S))
   width_scrollbar = ttk.Scrollbar(fenetre_principale, orient = HORIZONTAL, command = canvas.xview)
   width_scrollbar.grid(column=0, row=1, sticky=(W, E))
   cadre_interne = Frame(canvas)
   canvas.configure(xscrollcommand = width_scrollbar.set)
   cadre_interne.bind('<Configure>', lambda _: canvas.configure(scrollregion = canvas.bbox("all")))
   canvas.create_window((0,0), window = cadre_interne, anchor='nw')

   # Quand on modifie la taille de la fenêtre, la scrollbar reste de la même taille et 
   # le reste s'agrandit.
   fenetre_principale.rowconfigure(0, weight=1)
   fenetre_principale.rowconfigure(1, weight=0)
   fenetre_principale.columnconfigure(0, weight=1)
   canvas.rowconfigure(0, weight=1)
   canvas.columnconfigure(0, weight=1)

   bouton_de_demarrage_du_test=Button(cadre_interne, text = "Lancer le test", command = start_crappy)
   bouton_de_lancement_de_l_enregistrement=Button(cadre_interne, text="Enregistrement manuel", command = demarrage_de_crappy_enregistrement_manuel)
   bouton_de_mise_en_tension_rapide=Button(cadre_interne, text="Mise en tension rapide", command = mise_en_tension_rapide)
   bouton_de_mise_en_tension_lente=Button(cadre_interne, text="Mise en tension lente", command = mise_en_tension_lente)
   bouton_de_retour_en_position_initiale=Button(cadre_interne, text="Retour en position 0", command = retour_en_position_initiale)
   bouton_d_arret_de_crappy=Button(cadre_interne, text='Pause', command=gros_bouton_rouge,bg='red')
   bouton_enregistrer_et_quitter=Button(cadre_interne, text='Quitter et enregistrer', command=enregistrer_et_quitter)
   # mise_a_0_btn=Button(cadre_interne, text=' Mise à 0 ',command=mise_a_0_fct)
   # mise_a_tension_btn=Button(cadre_interne, text=' Mise à tension ',command=mise_a_tension_fct)
   # bouton_parametrage_consigne = Button(cadre_interne, text=' ',bg='red',command=choix_du_type_d_asservissement)
   enregistrer_btn=Button(cadre_interne, text=' ', command=choix_des_documents_a_conserver)
   
   img1 = PhotoImage(file= DOSSIER_CONFIG_ET_CONSIGNES + "icone_enregistrer.png") # make sure to add "/" not "\"
   enregistrer_btn.config(image=img1)
   img2 = PhotoImage(file= DOSSIER_CONFIG_ET_CONSIGNES + "icone_engrenage.png") # make sure to add "/" not "\"
   # bouton_parametrage_consigne.config(image=img2)
   img3 = PhotoImage(file= DOSSIER_CONFIG_ET_CONSIGNES + "icone_retour.png") # make sure to add "/" not "\"
   # mise_a_0_btn.config(image=img3)
   img6 = PhotoImage(file= DOSSIER_CONFIG_ET_CONSIGNES + "icone_play.png") # make sure to add "/" not "\"
   # bouton_de_demarrage_du_test.config(image=img6)
   img7 = PhotoImage(file= DOSSIER_CONFIG_ET_CONSIGNES + "icone_stop.png") # make sure to add "/" not "\"
   bouton_d_arret_de_crappy.config(image=img7)
   img8 = PhotoImage(file= DOSSIER_CONFIG_ET_CONSIGNES + "icone_tension.png") # make sure to add "/" not "\"
   # mise_a_tension_btn.config(image=img8)
   # img11 = PhotoImage(file= DOSSIER_CONFIG_ET_CONSIGNES + "pree_image.png") # make sure to add "/" not "\"
   # img21 = PhotoImage(file= DOSSIER_CONFIG_ET_CONSIGNES + "rampe_image.png") # make sure to add "/" not "\"
   # img22 = PhotoImage(file= DOSSIER_CONFIG_ET_CONSIGNES + "palier_image.png") # make sure to add "/" not "\"
   # img23 = PhotoImage(file= DOSSIER_CONFIG_ET_CONSIGNES + "iso_image.png") # make sure to add "/" not "\"
   # img31 = PhotoImage(file= DOSSIER_CONFIG_ET_CONSIGNES + "fatigue_image.png") # make sure to add "/" not "\"
   
   bouton_de_demarrage_du_test.grid(row=0,column=13,padx =5, pady =5)
   if verrou_production == OFF :
      bouton_de_lancement_de_l_enregistrement.grid(row=1,column=13,padx =5, pady =5)
      bouton_de_mise_en_tension_rapide.grid(row=2,column=13,padx =5, pady =5)
      bouton_de_mise_en_tension_lente.grid(row=3,column=13,padx =5, pady =5)
      bouton_de_retour_en_position_initiale.grid(row=4,column=13,padx =5, pady =5)
   bouton_d_arret_de_crappy.grid(row=0,column=14,columnspan=2,padx =5, pady =5)
   bouton_enregistrer_et_quitter.grid(row=2,column=14,padx =5, pady =5)
   # bouton_parametrage_consigne.grid(row=1,column=14,padx =5, pady =5)
   enregistrer_btn.grid(row=1,column=14,padx =5, pady =5)
   # mise_a_0_btn.grid(row=0,column=17,padx =5, pady =5)
   # mise_a_tension_btn.grid(row=1,column=17,padx =5, pady =5)

   # desactiver_bouton(bouton_de_lancement_de_l_enregistrement)
   desactiver_bouton(bouton_d_arret_de_crappy)
   
   menubar = Menu(fenetre_principale)

   menu1 = Menu(menubar, tearoff=0)
   menu1.add_command(label="Type d'asservissement")#,command = choix_du_type_d_asservissement)
   menubar.add_cascade(label="Consigne", menu=menu1)

   
   menu2 = Menu(menubar, tearoff=0)
   menu2.add_command(label="Choix documents",command=choix_des_documents_a_conserver)
   menubar.add_cascade(label="Enregistrer", menu=menu2)
   
   menu3 = Menu(menubar, tearoff=0)
   menu3.add_command(label="Certificat",command=creation_de_certificat)
   menu3.entryconfigure("Certificat", state = DISABLED)
   # menu3.add_command(label="Ecran secondaire",command=fenetre_d_affichage_secondaire)
   menubar.add_cascade(label="Créer", menu=menu3)
   
   menu4 = Menu(menubar, tearoff=0)
   menu4.add_command(label="Aide",command=RTM_protocol)
   if verrou_production==0 :
      # menu4.add_command(label="Régler sensibilité PID",command=sensi_page)
      # menu4.add_command(label="Régler coefficients PID",command=reglage_des_coef_des_PID)
      menu4.add_command(label="Modifier les chemins d'accès",command=lambda: modification_des_chemins_d_acces(fenetre_principale))
      menu4.add_command(label="Modifier le mot de passe",command=lambda : modification_du_mot_de_passe(fenetre_principale))
      menu4.add_command(label="Modifier étalonnage du banc",command=modification_des_coeff_d_etalonnage)
      menu4.add_command(label="Modifier les PID",command=lambda : modification_des_PID(fenetre_principale))
   menu4.add_separator()
   menu4.add_command(label="Fenêtre précédente",command=retour_aux_entrees)
   menu4.add_command(label="Quitter",command=enregistrer_et_quitter)
   menubar.add_cascade(label="Autre", menu=menu4)
   
   fenetre_principale.config(menu=menubar)
   
   fenetre_principale.mainloop()

   # thread_de_lancement_de_crappy.join()
   launch_crappy_event.clear()
   # crappy_launch_thread.join()
   return fonction_principale(*entrees[:10], type_d_asservissement)


if __name__ == '__main__':
   demarrage_du_programme()