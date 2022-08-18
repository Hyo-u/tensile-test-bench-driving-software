# -*- coding: utf-8 -*-


import os
from tkinter import *
from tkinter import tix
from tkinter.messagebox import *
import time
import datetime
import nidaqmx
import xlsxwriter 
import numpy as np
from scipy import signal
import math 
from simple_pid import PID
from win32com.client import Dispatch
from PIL import Image
from reportlab.pdfgen import canvas as cv
from reportlab.lib.pagesizes import A4

timer=None
liste=[]
lock=0
alphabet=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
indice=0
    
def etalonnage(x):
    #fonction calculant la valeur de charge réelle lue. 
    #Prend en x la tension délivrée par l'Indi-Paxs.
    #Sort la tension correspondant à la charge réelle.
    a=float(lecture_chemin('etal_a.txt')[:len(lecture_chemin('etal_a.txt'))])
    b=float(lecture_chemin('etal_b.txt')[:len(lecture_chemin('etal_b.txt'))])
    c=float(lecture_chemin('etal_c.txt')[:len(lecture_chemin('etal_c.txt'))])
    fonction=a*(x**2)+b*x+c
    
    return fonction

def coef_PID():
    ###renvoie la liste des coefficients par défaut de tous les PID
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
    ###rupture
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
    ###rupture
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
    ###rupture
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
    ###rupture
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

def lecture_chemin(doc):
    ###lit le fichier txt "doc" et renvoie le chemin lu
    fichier_chem=open(doc,'r')
    lignes=fichier_chem.readlines()
    chemin=lignes[len(lignes)-1][11:]
    fichier_chem.close()
    
    return chemin

def aide_fct():
    ###affichage du manuel du banc
    os.startfile(lecture_chemin('chemin_manuel.txt')+'\\'+lecture_chemin('nom_manuel.txt')[:len(lecture_chemin('nom_manuel.txt'))-1]) 
    return 0

def recup_data():
    ###fonction de lecture de la tension en input du boitier NI
    
        with nidaqmx.Task() as task1:

            task1.ai_channels.add_ai_voltage_chan("Dev1/ai0:7")
            data = task1.read()
        return data

def lecture_coef(nom_fichier):
    ###fonction de lecture des valeurs des coefficients de PID dans les fichiers txt
    fichier=open(nom_fichier,'r')
    lignes=fichier.readlines()
    j=0
    fin=len(lignes)-1
    for i in range(len(lignes[fin])):
        if lignes[fin][i]==' ':
            j=len(lignes[fin])-i
    fichier.close()
    return float(lignes[fin][len(lignes[fin])-j:len(lignes[fin])-1])

def lecture_sensi_charge():
    ###fonction de lecture de la sensibilité en charge
    fichier=open('sensi_charge.txt','r')
    print('lecture de la sensibilité')
    lignes=fichier.readlines()
    j=0
    fin=len(lignes)-1
    for i in range(len(lignes[fin])):
        if lignes[fin][i]==' ':
            j=len(lignes[fin])-i
    fichier.close()
    return lignes[fin][len(lignes[fin])-j:len(lignes[fin])-1]
    
def lecture_sensi_decharge():
    ###fonction de lecture de la sensibilité en décharge
    fichier=open('sensi_decharge.txt','r')
    lignes=fichier.readlines()
    j=0
    fin=len(lignes)-1
    for i in range(len(lignes[fin])):
        if lignes[fin][i]==' ':
            j=len(lignes[fin])-i
    fichier.close()
    return lignes[fin][len(lignes[fin])-j:len(lignes[fin])-1]
        
def capteur_fct (x):
    #convertion tension lue par le capteur ultrason -> tension étalonnée pour ne pas dépasser les valeurs limites en distance
    fonction=(x-2.18)*5/4.08
    return fonction 

def Vmm(x):
    #donne le coef multiplicateur pour passer de tension à mm.
    coef=200
    return coef

def num_tonnes(x):
    ###fonction de conversion du numéro de référence à la tension de référence.
    fonction=(0.01*x**2/8)/9.807
    return fonction

def suppr_file(nomdufichier) :
        ### fonction de suppression d'un fichier
        try :
            os.remove(nomdufichier)
            
        except FileNotFoundError :
            
            return print('fichier ',nomdufichier,' non trouvé')
        
def verif_pos(liste,valeur) :
    ###Fonction de vérification de la position du chariot.
    ###Elle renvoie 1 si le chariot est à "valeur" et 0 sinon.
    valid=0
    for val in range(len(liste)):
            if liste[val]>=valeur-1 and liste[val]<=valeur+1:
                valid+=1
    if valid==len(liste) :
        return 1
    return 0

def verif_valeur(liste,valeur):
    ###Fonction de vérification de la charge.
    ###Elle renvoie 1 si la charge est à "valeur" et 0 sinon.
    valid=0
    for val in range(len(liste)):
        if valeur==0 :
            if liste[val]>=0.01307 and liste[val]<=0.01309:
                valid+=1
        else :
            if liste[val]>=valeur-0.1 and liste[val]<=valeur+0.1:
                valid+=1
    if valid==len(liste) :
        return 1
    return 0

def verif_rupture(liste) :
    ###Cette fonction retourne 1 s'il y a détection de rupture et 0 sinon.
    for i in range(len(liste)-1):
        if liste[i+1]<liste[i]*0.3 and liste[i+1]>1 :
            return 1
    return 0

def desactive_bouton(btn):
    ###Fonction de désactivation d'un bouton
   btn["state"] = "disabled"
   
def active_bouton(btn):
    ###Fonction de d'activation d'un bouton
   btn["state"] = "normal"

def output(consigne,indice):
    ####fonction d'output du boitier NI
    
    with nidaqmx.Task() as task2, nidaqmx.Task() as task1, nidaqmx.Task() as task3:
        
        task1.ao_channels.add_ao_voltage_chan("Dev1/ao0") #decharge
        task2.ao_channels.add_ao_voltage_chan("Dev1/ao1") #charge
        task3.ai_channels.add_ai_voltage_chan("Dev1/ai0:7")
        data = task3.read()
        
        if indice==1 :
            if  Vmm(capteur_fct(data[7]))*capteur_fct(data[7])>2 or consigne==0 or lock ==0 :
                task1.write(consigne)
                task2.write(0)
                
            else : 
                
                output(0,1)
                
        
        if indice==2:
            if  Vmm(capteur_fct(data[7]))*capteur_fct(data[7])<1900 or consigne==0 or lock ==0 :
               
                task2.write(consigne)
                task1.write(0)
                
            else : 
                
                output(0,2)
                
    
def fct_depart() :
    ###1ère fenêtre principale
    def mdp_fct():
        ###mot de passe
        texte=lecture_chemin('mdp_liste.txt')[:len(lecture_chemin('mdp_liste.txt'))-1]
        return texte
    
    def RetD_fct():
    ###fenêtre mot de passe 
        def ok_fct ():
            ###fonction de vérification du mot de passe
            global lock
            lock=0
            if value.get()==mdp_fct():
                fenetre1.destroy()
                graph_RetD_fct()
            else :
                showinfo(title='Echec', message='Mot de passe incorrect')
        
        mdp=Toplevel(fenetre1)
        Label(mdp, text = 'mot de passe').grid(row=0, column=0, padx =20, pady =10)
        Entry( mdp,textvariable=value,show='*', width=30).grid(row=0, column=1, padx =20, pady =10)
        ok_btn=Button(mdp,text="Valider",command=ok_fct)
        ok_btn.grid(row=1, column=1,padx =0, pady =10)
        retour_btn=Button(mdp,text='Quitter', command=mdp.destroy)
        retour_btn.grid(row=1, column=0,padx =0, pady =10)
        
        
    def prod_fct():
    ###fonction de passage à la seconde fenêtre en mode prod
        global lock
        lock=1
        fenetre1.destroy()
        graph_RetD_fct()
        
    
    fenetre1 = tix.Tk(None,None,className='Fenetre de sélection')
    value = StringVar() 
    Label(fenetre1, text = 'Veuillez sélectionner le mode de fonctionnement de la machine',justify = CENTER).grid(row=0, column=0, padx =20, pady =10,columnspan=2)
    
    RetD_btn=Button(fenetre1,text="R&D",command=RetD_fct)
    prod_btn=Button(fenetre1, text='Production', command=prod_fct)
    
    bal = tix.Balloon(fenetre1)
    bal.bind_widget(RetD_btn, msg="Cliquez ici pour effectuer tous types de tests (Attention : les sécurités sont désactivées)")
    bal.bind_widget(prod_btn, msg="Cliquez ici pour effectuer un préétirage")
    
    RetD_btn.grid(row=1, column=0,padx =0, pady =10 )
    prod_btn.grid(row=1, column=1,padx =0, pady =10 )
    
    menubar = Menu(fenetre1)
    menu= Menu(menubar, tearoff=0)
    menu.add_command(label="Afficher documentation",command=aide_fct)
    menubar.add_cascade(label="Aide", menu=menu)
    fenetre1.config(menu=menubar)
    
    fenetre1.mainloop() 

def entree_RetD () :
    ###deuxième fenêtre principale
    global lock
    
    def modif_mdp_fct():
        ###fenêtre de modification du mot de passe
        def modif_mdp_suite():
            fichier=open('mdp_liste.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+mdp_val.get()+'\n')
            fichier.close()
            fen_mdp.destroy()
            return 0
        
        fen_mdp=Toplevel(fenetre2)
        
        fen_mdp.clipboard_append(' ')
        fen_mdp.clipboard_get()  # récupère le contenu du presse-papier4
        
        mdp_val=StringVar()
        mdp_val.set(lecture_chemin('mdp_liste.txt')[:len(lecture_chemin('mdp_liste.txt'))-1])
        
        label_mdp=Label(fen_mdp, text="Choisissez le nouveau mot de passe")
        mdp_entree = Entry(fen_mdp, textvariable=mdp_val, width=30)
      
        retour_btn=Button(fen_mdp, text='Retour',command=fen_mdp.destroy)
        suivant_btn=Button(fen_mdp, text='Enregistrer',command=modif_mdp_suite)
        
        label_mdp.grid(row=1,column=0,padx =10, pady =10)
        mdp_entree.grid(row=1,column=1,padx =10, pady =10)
        retour_btn.grid(row=4,column=0,padx =10, pady =10)
        suivant_btn.grid(row=4,column=1,padx =10, pady =10)
    
    def chemin_fct():
    ###fenêtre de choix du chemin des fonctions
        
        def chemin_suivant() :
            ###fonction d'écriture des sensibilité et de mise à jour des PID
            
            fichier=open('chemin_enre.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+chemin_enre.get()+'\n')
            fichier.close()
            fichier=open('chemin_manuel.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+chemin_aide.get()+'\n')
            fichier.close()
            fichier=open('nom_manuel.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+nom_manuel.get()+'\n')
            fichier.close()
            fen_chem.destroy()
            
            return 0

        fen_chem=Toplevel(fenetre2)
        
        fen_chem.clipboard_append(' ')
        fen_chem.clipboard_get()  # récupère le contenu du presse-papier4
        
        chemin_enre=StringVar()
        chemin_aide=StringVar()
        nom_manuel=StringVar()
        chemin_enre.set(lecture_chemin('chemin_enre.txt')[:len(lecture_chemin('chemin_enre.txt'))-1])
        chemin_aide.set(lecture_chemin('chemin_manuel.txt')[:len(lecture_chemin('chemin_manuel.txt'))-1])
        nom_manuel.set(lecture_chemin('nom_manuel.txt')[:len(lecture_chemin('nom_manuel.txt'))-1])
        
        
        label_enre=Label(fen_chem, text="Choisissez le chemin des documents enregistrés")
        enre_entree = Entry(fen_chem, textvariable=chemin_enre, width=100)
        
        label_aide=Label(fen_chem, text="Choisissez le chemin du manuel d'aide")
        aide_entree = Entry(fen_chem, textvariable=chemin_aide, width=100)
        
        label_nom_manuel=Label(fen_chem, text="Choisissez le nom du manuel d'aide (ne pas oublier le .docx ou le .pdf)")
        manuel_entree = Entry(fen_chem, textvariable=nom_manuel, width=100)
      
        retour_btn=Button(fen_chem, text='Retour',command=fen_chem.destroy)
        suivant_btn=Button(fen_chem, text='Enregistrer',command=chemin_suivant)
        
        label_enre.grid(row=1,column=0,padx =10, pady =10)
        enre_entree.grid(row=1,column=1,padx =10, pady =10)
        label_aide.grid(row=2,column=0,padx =10, pady =10)
        aide_entree.grid(row=2,column=1,padx =10, pady =10)
        label_nom_manuel.grid(row=3,column=0,padx =10, pady =10)
        manuel_entree.grid(row=3,column=1,padx =10, pady =10)
        retour_btn.grid(row=4,column=0,padx =10, pady =10)
        suivant_btn.grid(row=4,column=1,padx =10, pady =10)
        
    def precedent1_fct ():
        ###renvoie la fenêtre précedente
        global lock
        fenetre2.destroy()
        lock=3
    
    def diam_cabestan():
        ###affiche la valeur du diamètre de cabestant si la case est cochée
        Entry( accroche_label, textvariable=diam_var, width=10).grid(row=15,column=1,padx =10, pady =10)
        Label(accroche_label,text="Diamètre cabestan (mm)").grid(row=15,column=0,padx =10, pady =10)
        return 0

    def suivant1_fct ():
        ###fonction de vérification des entrées et passage à la dernière fenêtre
        if ID_var.get()=="":
            showwarning('Attention', 'Titre non valide !')
            return 0
        
        if nom_var.get()=="":
            showwarning('Attention', 'Nom non valide !')
            return 0
        
        if prenom_var.get()=="":
            showwarning('Attention', 'Prénom non valide !')
            return 0

        if materiel_var.get()=="":
            showwarning('Attention', 'Matériel non valide !')
            return 0
        
        if rupture_var.get()!="":
            try : 
                int(rupture_var.get())
                
            except ValueError : 
                showwarning('Attention', 'Charge de rupture non valide !')
                return 0
            
        if rupture_var.get()=="":
            showwarning('Attention', 'Charge de rupture non valide !')
            return 0
            
        if longueur_var.get()!='' :
            if longueur_var.get()=='1':
                longueur_var.set('20m')
            elif longueur_var.get()=='2':
                longueur_var.set('22m')    
            elif longueur_var.get()=='3':
                longueur_var.set('24m')
            elif longueur_var.get()=='4':
                longueur_var.set('26m')
            elif longueur_var.get()=='5':
                longueur_var.set('9m')
        else :
            showwarning('Attention', 'Il faut cocher une longueur de banc utilisée !')
            return 0
        

        if lock==0 :
            
            if ref_var.get()!="":
                try : 
                    if ref_var.get()<8 :
                        showwarning('Attention', 'la valeur minimale de numéro de référence utilisable par le banc est 8 !')
                        return 0
                    
                except ValueError : 
                    showwarning('Attention', 'Numéro de référence non valide !')
                    return 0
            
            if accroche_var.get()==0 :
                showwarning('Attention', "Il faut cocher une case sur le type d'accroche !")
                return 0
            
            if episse_var.get()==0 :
                showwarning('Attention', "Il faut préciser si l'éprouvette est épissée ou non !")
                return 0
        
            else :
                fenetre2.destroy()
                
        else :
            fenetre2.destroy()
                
                
            
                                
    fenetre2 = tix.Tk(None,None,className='Fenetre des entrées')
    fenetre2.clipboard_append(' ')
    fenetre2.clipboard_get()  # récupère le contenu du presse-papier
    
    diam_var = DoubleVar() 
    diam_var.set(40)
    utile_var = DoubleVar()
    accroche_var = IntVar() 
    episse_var = IntVar()
    ID_var = StringVar() 
    ID_var.set("a")
    nom_var = StringVar() 
    nom_var.set("a")
    prenom_var = StringVar() 
    prenom_var.set("a")
    materiel_var = StringVar() 
    materiel_var.set("a")
    rupture_var = StringVar() 
    rupture_var.set("10")
    ref_var = DoubleVar()
    longueur_var = StringVar()
    
    ID=Entry( fenetre2, textvariable=ID_var, width=30)
    Nom=Entry( fenetre2, textvariable=nom_var, width=30)
    Prenom=Entry( fenetre2, textvariable=prenom_var, width=30)
    Choix_materiel=Entry( fenetre2, textvariable=materiel_var, width=30)
    charge_rupture=Entry( fenetre2, textvariable=rupture_var, width=30)
    ref_num=Entry( fenetre2, textvariable=ref_var, width=30)
    
    Label( fenetre2, text = 'Titre').grid(row=1,column=0,padx =10, pady =10)
    Label( fenetre2, text = 'Nom opérateur').grid(row=2,column=0,padx =10, pady =10)
    Label( fenetre2, text = 'Prénom opérateur').grid(row=3,column=0,padx =10, pady =10)
    Label( fenetre2, text = 'Choix matériel').grid(row=4,column=0,padx =10, pady =10)
    Label( fenetre2, text = 'Charge de rupture (en tonne)').grid(row=6,column=0,padx =10, pady =10)
    
    long_banc=LabelFrame( fenetre2)
    Label( long_banc, text = 'Longueur utile du banc').grid(row=8,column=0,padx =10, pady =10)
    coche20m = Radiobutton(long_banc, text="<20m", variable=longueur_var, value=1)
    coche22m = Radiobutton(long_banc, text="22m", variable=longueur_var, value=2)
    coche24m = Radiobutton(long_banc, text="24m", variable=longueur_var, value=3)
    coche26m = Radiobutton(long_banc, text="26m", variable=longueur_var, value=4)
    
    if lock==0 :
        Label( fenetre2, text = 'Numéro de référence').grid(row=7,column=0,padx =10, pady =10)

        accroche_label=LabelFrame( fenetre2)
        cordage_label=LabelFrame( fenetre2)
        
        Label( accroche_label, text = "Système d'accroche").grid(row=13,column=0,padx =10, pady =10)
        Label( cordage_label, text = "Cordage épissé").grid(row=16,column=0,padx =10, pady =10)

        coche9m = Radiobutton(long_banc, text="7m (pour une pièce métallique)", variable=longueur_var, value=5)

        coche_axial= Radiobutton(accroche_label, text="Goupilles", variable=accroche_var, value=1)
        coche_cabestant = Radiobutton(accroche_label, text="Amarrage à cabestan", variable=accroche_var, value=2,command=diam_cabestan)
        
        coche_oui= Radiobutton(cordage_label, text="Oui", variable=episse_var, value=1)
        coche_non = Radiobutton(cordage_label, text="Non", variable=episse_var, value=2)
    
        Entry( cordage_label, textvariable=utile_var, width=10).grid(row=18,column=1,padx =10, pady =10)
        Label(cordage_label,text="Longueur utile de l'éprouvette (en m)").grid(row=18,column=0,padx =10, pady =10)
        
    precedent1_btn=Button(fenetre2, text='Précédent', command=precedent1_fct)
    suivant1_btn=Button(fenetre2, text='Suivant', command=suivant1_fct)
    
    ID.grid(row=1,column=1,padx =10, pady =10)
    Nom.grid(row=2,column=1,padx =10, pady =10)
    Prenom.grid(row=3,column=1,padx =10, pady =10)
    Choix_materiel.grid(row=4,column=1,padx =10, pady =10)
    charge_rupture.grid(row=6,column=1,padx =10, pady =10)
    if lock==0 :
        ref_num.grid(row=7,column=1,padx =10, pady =10)
    long_banc.grid(row=8,column=0,columnspan=3,padx =10, pady =10)
    coche20m.grid(row=8,column=1,padx =10, pady =10)
    coche22m.grid(row=9,column=1,padx =10, pady =10)
    coche24m.grid(row=10,column=1,padx =10, pady =10)
    coche26m.grid(row=11,column=1,padx =10, pady =10)
    if lock==0 :
        coche9m.grid(row=12,column=1,padx =10, pady =10)
        coche_axial.grid(row=13,column=1,padx =10, pady =10)
        coche_cabestant.grid(row=14,column=1,padx =10, pady =10)
        coche_oui.grid(row=16,column=1,padx =10, pady =10)
        coche_non.grid(row=17,column=1,padx =10, pady =10)
        
        accroche_label.grid(row=13,column=0,columnspan=3,padx =10, pady =10)
        cordage_label.grid(row=16,column=0,columnspan=3,padx =10, pady =10)
    precedent1_btn.grid(row=20, column=0,padx =10, pady =10)
    suivant1_btn.grid(row=20, column=1,padx =10, pady =10)
    
    menubar = Menu(fenetre2)
    menu= Menu(menubar, tearoff=0)
    menu.add_command(label="Afficher documentation",command=aide_fct)
    if lock==0 :
        menu.add_command(label="Modifier les chemins",command=chemin_fct)
        menu.add_command(label="Modifier le mot de passe",command=modif_mdp_fct)
    menubar.add_cascade(label="Autre", menu=menu)
    fenetre2.config(menu=menubar)
    
    bal = tix.Balloon(fenetre2)
    bal.bind_widget(precedent1_btn, msg="Retour au menu précédent")
    bal.bind_widget(suivant1_btn, msg="Aller vers la fenêtre d'acquisition")
    bal.bind_widget(ID, msg="Entrez ici le titre du document")
    bal.bind_widget(Nom, msg="Entrez ici le nom de l'opérateur")
    bal.bind_widget(Choix_materiel, msg="Entrez ici le matériel testé")
    bal.bind_widget(charge_rupture, msg="Entrez ici la charge de rupture du matériel testé. Une sécurité est mise en place pour ne jamais dépasser 50% de cette charge")
    bal.bind_widget(Prenom, msg="Entrez ici le prénom de l'opérateur")
    bal.bind_widget(ref_num, msg="Le numéro de référence représente le diamètre à vide du cordage")

    if lock==0 :
        bal.bind_widget(coche9m, msg="Cochez cette case si le matériel testé est en métal")
    
    fenetre2.mainloop()
    
    return (ID_var.get(),nom_var.get(),prenom_var.get(),materiel_var.get(),longueur_var.get(),rupture_var.get(),ref_var.get(),accroche_var.get(),episse_var.get(),diam_var.get(),utile_var.get())
    

    
def graph_RetD_fct():
###fonction de fenêtre graphique
                
    def precedent2_fct ():
        ###renvoie à la fenêtre précédente
        enregistrer_fct()
        fenetre_graph_retd.destroy()
        graph_RetD_fct()
        prec.set(1)
        return 0
        
    def lecture_a_vide():
            ###fonction renvoyant la valeur lue lorsqu'aucun programme n'est lancé
            data=recup_data()
            valeur_en_cours=etalonnage(data[6]*2)
            
            zone_charge_valeur.delete('valeur_charge_actuelle')
            zone_charge_valeur.create_text(250,75,text=round(valeur_en_cours,2),font=('Arial','100'),tags='valeur_charge_actuelle')
            
            valeur_en_cours=round(Vmm(capteur_fct(data[7]))*capteur_fct(data[7]))
                
            zone_valeur.delete('valeur_actuelle')
            zone_valeur.create_text(75,25,text=valeur_en_cours,font=('Arial','20'),tags='valeur_actuelle')
            if start_var.get()==0 :
                zone_valeur.after(500,lecture_a_vide)
            else :
                return 0 

    def do_zoom(event):
        ###Permet de faire un zoom sur la fenêtre
        global liste
        
        if roulette.get()!=1 :
            if askyesno(title='Attention',message="L'utilisation de la roulette impose un arrêt du programme (vous pourrez continuer de voir les valeurs mais l'essai sera suspendu définitivement), voulez-vous continuer ?") :
                factor = 1.001 ** event.delta
                canvas.scale(ALL, event.x, event.y, factor, factor)
                roulette.set(1)
                do_pause()
                liste=[]
                desactive_bouton(start_btn)
                active_bouton(stop_btn)
#                active_bouton(certificat_btn)
                desactive_bouton(pause_btn)
                
        if roulette.get()==1 :
            factor = 1.001 ** event.delta
            canvas.scale(ALL, event.x, event.y, factor, factor)
        
    def cadrillage():
        ###fonction de création du cadrillage initial du graphique 
        height, width=700,1600
        pas_x=50 
        marge_x=50
        marge_y=50
        
        for i in range(int(height/pas_x)):
            
            if i*pas_x+marge_y <= height-marge_y: #empêche la création de ligne excédentaires
                
                canvas.create_line(marge_x,i*pas_x+marge_y,width-marge_x,i*pas_x+marge_y,tags='init')  
                canvas.create_text(marge_x/2,i*pas_x+marge_y-7,text=str(2*(int(height/pas_x)-i-3)),fill='green',tags='init')
                canvas.create_text(marge_x/2,i*pas_x+marge_y+7,text=str(200*(int(height/pas_x)-i-3)),fill='red',tags='init')
                
                j=i
            
        canvas.create_line(marge_x,marge_y,marge_x,height-marge_y,arrow='first',tags='init')
        canvas.create_line(marge_x,j*pas_x+marge_y,width-marge_x,j*pas_x+marge_y,arrow='last',tags='init') 
        canvas.create_text(width-marge_x,j*pas_x+marge_y+20,text='temps en s')
        canvas.create_text(marge_x/2+50,marge_y-7-30,text='millimètres',fill='red')
        canvas.create_text(marge_x/2+50,marge_y+7-30,text='tonnes',fill='green')
        
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
            parametrage_fct()
            consigne_fen_bis.destroy()
        ####################################

        consigne_fen_bis=Toplevel(fenetre_graph_retd)
        consigne_fen_bis.title('Choix déplacement')
        Label(consigne_fen_bis, text="Veuillez choisir la valeur de position du chariot en mm (entre 10 et 1900) ",fg='blue').grid(row=0,padx =10, pady =10)
        Spinbox(consigne_fen_bis, from_=10,to=1900,increment=1, textvariable=pos_var, width=30).grid(row=1,padx =10, pady =10)
        Button(consigne_fen_bis,text='Retour', command=parametrage_fct).grid(row=4,column=0,padx =10, pady =10)
        Button(consigne_fen_bis,text='Enregistrer', command=distance_suite).grid(row=4,column=2,padx =10, pady =10)
        consigne_btn['bg']='green'
        consigne_choix.set(61)
        active_bouton(start_btn)
        rappel_consigne.delete('consigne')
        rappel_consigne.create_text(125,10,text='Consigne position',tags='consigne') 
        
    def parametrage_fct ():
        ###Fenêtre de choix de la forme de la consigne
        global lock
        
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
            choix_asserv_fct()
        ####################################
        
        consigne_fen=Toplevel(fenetre_graph_retd)
        Label(consigne_fen, text="Veuillez choisir la forme du signal de la consigne").grid(row=0,column=1,padx =10, pady =10)
        Radiobutton(consigne_fen, text="Préétirage", variable=consigne_choix, value=11).grid(row=1,column=1,padx =10, pady =10)
        
        if lock==0 :
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
        consigne_fen_bis=Toplevel(fenetre_graph_retd)
        
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
                if episse.get()==1:
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
            consigne_btn['bg']='green'
            active_bouton(start_btn)
            mini.set(2000)
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
            consigne_btn['bg']='green'
            active_bouton(start_btn)
            normes.set('')
            mini.set(2000)
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
            consigne_btn['bg']='green'
            active_bouton(start_btn)
            normes.set('')
            mini.set(2000)
            rappel_consigne.delete('consigne')
            rappel_consigne.create_text(125,10,text='Consigne rupture par paliers',tags='consigne') 
            
        if choix==23:
            consigne_fen_bis.title('iso-2307')
            if episse.get()==1 :
                
                pourc2=utile.get()*0.02*1000
                pourc12=utile.get()*0.12*1000
                pas_scale=Scale(consigne_fen_bis,orient='horizontal',from_=pourc2, to=pourc12, resolution=1,length=150,variable=pourc_var,label='Vitesse (mm/min)')
                pas_scale.grid(row=3,column=0,padx =10, pady =10)

            coche_label=LabelFrame(consigne_fen_bis, text = "Nombres de cycles (compris entre "+str(round(num_tonnes(int(num_ref.get())),4))+" tonnes et "+str(rupture.get()/2)+" tonnes")
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
            consigne_btn['bg']='green'
            active_bouton(start_btn)
            normes.set('iso-2307')
            mini.set(2000)
            rappel_consigne.delete('consigne')
            rappel_consigne.create_text(125,10,text='Consigne rupture iso-2307',tags='consigne') 
            
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
            consigne_btn['bg']='green'
            active_bouton(start_btn)
            mini.set(2000)
            rappel_consigne.delete('consigne')
            rappel_consigne.create_text(125,10,text='Consigne fatigue',tags='consigne') 
        

                
    def stop_fct ():
        ###fonction "quitter et enregistrer". 
        global liste
        
        demande=askyesnocancel(title='Attention',message='Souhaitez vous relancer un essai de traction ?' )
        
        if demande==True:
            liste=[]
            precedent2_fct()
            return 0
        
        elif demande==None:
            return 0
        
        else :
            
            fenetre_graph_retd.destroy()
            return 0
        
            
    def choix_enregistrer_fct():
        ###fenêtre de choix des documents enregistrés
            
        enregistrer_fen=Toplevel(fenetre_graph_retd)
        
        Label(enregistrer_fen, text="Veuillez choisir les documents à enregistrer").grid(row=0,column=1,padx =10, pady =10)
        
        Radiobutton(enregistrer_fen, text="aucun document", variable=choix_enregistrer, value=1).grid(row=1,column=1,padx =10, pady =10)
        Radiobutton(enregistrer_fen, text="valeurs étalonnées (fichier excel et csv)", variable=choix_enregistrer, value=0).grid(row=2,column=1,padx =10, pady =10)
        if lock==0 :
            Radiobutton(enregistrer_fen, text="valeurs affichees et étalonnées (fichier excel et csv)", variable=choix_enregistrer, value=2).grid(row=3,column=1,padx =10, pady =10)
            Radiobutton(enregistrer_fen, text="valeurs affichee (fichier excel et csv)", variable=choix_enregistrer, value=3).grid(row=4,column=1,padx =10, pady =10)
        Button(enregistrer_fen,text='Retour', command=enregistrer_fen.destroy).grid(row=5,column=0,padx =10, pady =10)
        Button(enregistrer_fen,text='Suivant', command=enregistrer_fen.destroy).grid(row=5,column=2,padx =10, pady =10)
        
        
    def enregistrer_fct():
    ###fenêtre d'enregistrement des valeurs. Créé les courbes, ferme les documents csv et excel, détruit les documents non voulu.
            print('chargement')
                    
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
            if switch.get()=='off':
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
            
            feuille.write(7,1,com.get())
            chartsheet.set_chart(chart)
            chartsheet.activate();
            
            workbook.close()
            fichier.close()
            fichier2.close()
            fichier3.close()
            
            if choix_enregistrer.get()==1 :
                suppr_file(nom)
                suppr_file(nom_csv)
                suppr_file(nom_csv2)
                suppr_file(nom_csv3)
                
            if choix_enregistrer.get()==2 :
                suppr_file(nom_csv)
                suppr_file(nom_csv3)
                
            if choix_enregistrer.get()==0 :
                suppr_file(nom_csv2)
                suppr_file(nom_csv3)
                
            if choix_enregistrer.get()==3 :
                suppr_file(nom_csv)
                suppr_file(nom_csv2)
        
        
    def do_pause():
        ###fonction permettant de faire pause sur l'animation
        global timer
        
        output(0,1)
        output(0,2)
        
        
        active_bouton(stop_btn)
        desactive_bouton(pause_btn)
        active_bouton(consigne_btn)
        active_bouton(enregistrer_btn)
        active_bouton(precedent2_btn)
        active_bouton(mise_a_0_btn)
        active_bouton(mise_a_tension_btn)
        active_telec.set(0)
        menu1.entryconfigure(4, state=NORMAL)
        
        if switch.get()=='off' :
            active_bouton(gauche_btn)
            active_bouton(droite_btn)
    
        if timer:
            canvas.after_cancel(timer)
            timer = None
            start_var.set(0)
            lecture_a_vide()
      
        if consigne_btn['bg']=='green' or switch.get()=='on' :
            active_bouton(start_btn)
            
    
    def convertisseur_secondes_temps(nb_sec):
        ###fonction de conversion d'un entier à heures,minutes,secondes
     q,s=divmod(nb_sec,60)
     h,m=divmod(q,60)
     return "%d:%d:%d" %(h,m,s)
 
    def animation ():
        ### fonction d'animation du graphique, de calcul de la consigne et d'asservissement
        global liste
        global timer

        #################initialisation de valeurs##########################################
        
        
        height=700
        marge_y=50
        offset=600
        x07,y07,x17,y17=canvas.coords(pointeur7)
        x06,y06,x16,y16=canvas.coords(pointeur6)
        x00,y00,x11,y11=canvas.coords(pointeur_consigne)
        data=recup_data()
        data6=etalonnage(data[6]*2)*25
        data7=capteur_fct(data[7])*50
        delay=1
        espace_i=2
        
        if consigne_choix.get()==21:
            longueur_liste=2
        elif consigne_choix.get()==31:
            longueur_liste=2
        else :
             longueur_liste=5
        
            
        texte_pointeur_fin="".join(["p",str(compteur_pointeur.get()),"p"])
        texte_pointeur_consigne="".join(["p",str(compteur_pointeur.get()),"p"])
        
        if len(liste_memoire)>4:
            liste_memoire.remove(liste_memoire[0])
        liste_memoire.append(Vmm(capteur_fct(data[7]))*capteur_fct(data[7]))
        if len(liste_charge)>longueur_liste:
            liste_charge.remove(liste_charge[0])
        liste_charge.append(etalonnage(data[6]*2))
        
        #################Sécu charge#######################################################
        
        if switch.get()=='off' :
            
            if data6/25>=longueur_banc.get() :
                
                do_pause()
                showwarning('Attention',('La longueur de banc utile ne permet pas une charge supérieure à '+str(longueur_banc.get())+' tonnes'))
                print(data6/25)
                return 0
            
        if verif_rupture(liste_charge)==1 and decharge.get()==0 and choix_asserv_val.get()==1:
            do_pause()
            showwarning('Attention','Rupture du matériau détectée, cliquez sur start pour terminer la décharge')
            print(data6/25)
            decharge.set(1)
            choix_asserv_val.set(2)
            start_fct()
            return 0
        
        #################initialisation du temps##########################################
        
        if compteur_pointeur.get()==(1380/2) :
            temps.set(time.time())
               
        else :
            if init.get()==0 :
                temps_bis.set(time.time())
            if active_telec.get()==0 and decharge.get()==0 :
                difference2.set(time.time()-temps_bis.get())

            difference.set(time.time()-temps.get())
            
        difference_val=difference.get()
        difference_val_bis=difference2.get()
        difference__val_palier=difference_palier.get()
        

        #################assignation valeur consigne en fonction des choix##########################################
        if switch.get()=='on' :
            consigne=0
        if switch.get()=='off' and active_telec.get()==0:
            
            if consigne_choix.get()==11 :
                temps_maintien=int(temps_voulu.get()[:2])*60+int(temps_voulu.get()[3:])
                if init.get()==0 :
                    consigne=limite_val.get()*25
                    if verif_valeur(liste_charge,limite_val.get())==1:
                        init.set(1)
                        temps_bis.set(time.time())
                        
                if init.get()==1 :
                    if difference_val_bis>=temps_maintien :    
                       init.set(4)
                       print('decharge',difference_val_bis)
                    consigne=limite_val.get()*25
              
                if init.get()==4 :                
                    decharge.set(1)
                    consigne=0
                memoire_consigne.set(consigne)
                
            if consigne_choix.get()==21 : 
                temps_maintien=int(temps_voulu.get()[:2])*60+int(temps_voulu.get()[3:])
                if init.get()==0 :
                    init.set(1)
                    temps_bis.set(time.time())
                if init.get()==1 :
                    if difference_val_bis<1 :
                        consigne=0
                    if difference_val_bis>=1:
                        consigne=pente_val.get()*(difference_val_bis-1)*25
                    if etalonnage(data[6]*2)>=limite_val.get():
                        temps_bis.set(time.time())
                        difference_val_bis=0
                        init.set(2)
                    memoire_consigne.set(consigne)
                    
                if init.get()==2 :
                    consigne=limite_val.get()*25
                    if difference_val_bis>=temps_maintien :
                        decharge.set(1)
                        consigne=0
                    memoire_consigne.set(consigne)
                    
            if consigne_choix.get()==22 :
                #rampe par paliers
                temps_maintien=int(temps_voulu.get()[:2])*60+int(temps_voulu.get()[3:])
                if init.get()==0 :
                    temps_bis.set(time.time())
                    init.set(1)
                    temps_palier.set(time.time())
                    if difference_val!= 0:
                        rab.set(difference_val)
                    else :
                        rab.set(1)
                    temps1.set(compteur_palier.get()*(temps_maintien)+consigne_val.get()/pente_val.get()+rab.get())
                    temps2.set(temps1.get()+temps_maintien)  
                    
                if init.get()!=3 : 
                    if difference_val<1:
                        consigne=0
                        temps_palier.set(time.time())
                        temps_bis.set(time.time())
                        
                    if difference_val<temps1.get() and difference_val>1 :
                        if difference_palier.get()==0:
                            consigne=pente_val.get()*(difference_val-rab.get())*25-(difference_palier.get()*pente_val.get()-compteur_palier.get()*consigne_val.get())*25
                        else :
                            consigne=pente_val.get()*(difference_val-1)*25-(difference_palier.get()*pente_val.get()-compteur_palier.get()*consigne_val.get()-pente_val.get())*25
                        memoire_consigne.set(consigne)
                        temps_palier.set(time.time())
                        temps_bis.set(time.time())
                        if consigne/25>=consigne_val.get()*(compteur_palier.get()+1) :
                            temps1.set(difference_val)
                            consigne=consigne_val.get()*(compteur_palier.get()+1)*25
                            memoire_consigne.set(consigne)
                            temps_bis.set(time.time())
                            difference_palier.set(time.time()-temps_palier.get())
                            temps2.set(temps1.get()+temps_maintien+difference_palier.get())
                            
        
                    if difference_val>=temps1.get() and difference_val<=temps2.get() and round(etalonnage(data[6]*2),1)!=consigne_val.get()*(compteur_palier.get()+1) and init.get()!=2:

                        consigne=consigne_val.get()*(compteur_palier.get()+1)*25
                        memoire_consigne.set(consigne)
                        temps_bis.set(time.time())
                        difference_palier.set(time.time()-temps_palier.get())
                        temps2.set(temps1.get()+temps_maintien+difference_palier.get())
                    
                        
                    if difference_val>=temps1.get() and difference_val<temps2.get() and (round(etalonnage(data[6]*2),1)==consigne_val.get()*(compteur_palier.get()+1) or init.get()==2):
                        consigne=consigne_val.get()*(compteur_palier.get()+1)*25
                        memoire_consigne.set(consigne)
                        init.set(2)
        
                    if difference_val>=temps2.get() and init.get()==2:
                        rab.set(rab.get()+difference__val_palier)
                        difference_palier.set(temps2.get())
                        compteur_palier.set(compteur_palier.get()+1)
                        temps1.set(compteur_palier.get()*(temps_maintien)+(compteur_palier.get()+1)*consigne_val.get()/pente_val.get()+1+rab.get())
                        temps2.set(temps1.get()+temps_maintien)
                        temps_bis.set(time.time())
                        consigne=memoire_consigne.get()
                        init.set(1)
                        
                    if etalonnage(data[6]*2)>=limite_val.get():
                        temps_bis.set(time.time())
                        difference_val_bis=0
                        consigne=limite_val.get()*25
                        init.set(3)
                
                if init.get()==3 :
                    temps_maintien=int(temps_palier_final.get()[:2])*60+int(temps_palier_final.get()[3:])
                    consigne=limite_val.get()*25
                    if difference_val_bis>=temps_maintien :
                        decharge.set(1)
                        consigne=0
                    memoire_consigne.set(consigne)
                    
                    
            if consigne_choix.get()==23 :
                
                ###1er étape : fatigue 
                
                if init.get()==0 :
                    consigne=rupture.get()*25/2
                    if etalonnage(data[6]*2)>=consigne/25:
                        init.set(1)
                        temps_bis.set(time.time())
                        
                if init.get()==1 :
                    consigne=rupture.get()*25/2
                    if difference_val_bis>=0 :    
                        init.set(2)
                       
                if init.get()==2 :
                    consigne=num_tonnes(num_ref.get())*25
                    if etalonnage(data[6]*2)<=consigne/25:
                        temps_bis.set(time.time())
                        difference_val_bis=0
                        init.set(3)
                        
                if init.get()==3 :
                    consigne=num_tonnes(num_ref.get())*25
                    
                    if difference_val_bis>=0 :
                        if compteur_cycles.get()==nb_cycles.get()-1:
                            init.set(4)
                        else :
                            init.set(0)
                            compteur_cycles.set(compteur_cycles.get()+1)
                                   
                if init.get()==4 :
                    consigne_choix.set(231)
                    init.set(0)
                    consigne=0
                    do_pause()
                    showinfo('Info','Cycle de fatigue terminé, cliquez sur start pour lancer la rupture')
                    return 0
                    
                memoire_consigne.set(consigne) 
                
            if consigne_choix.get()==231 :
                
                if init.get()==0 :
                    init.set(1)
                    temps_bis.set(time.time())
                    
                if init.get()==1 :
                    if difference_val_bis<1 :
                        consigne=0
                    if difference_val_bis>=1:
                        consigne=20*25
                        
                    memoire_consigne.set(consigne)
            
            if consigne_choix.get()==31 :
                ###fatigue cyclique
                temps_maintien=int(temps_voulu.get()[:2])*60+int(temps_voulu.get()[3:])
                if init.get()==0 :
                    consigne=limite_val.get()*25
                    if etalonnage(data[6]*2)>limite_val.get():
                        init.set(1)
                        temps_bis.set(time.time())
                        pid17.reset()
                        pid18.reset()
                        
                if init.get()==1 :
                    consigne=limite_val.get()*25
                    if difference_val_bis>=temps_maintien :    
                        init.set(2)
                       
                if init.get()==2 :
                    consigne=limite_basse.get()*25
                    if etalonnage(data[6]*2)<limite_basse.get():
                        temps_bis.set(time.time())
                        difference_val_bis=0
                        init.set(3)
                        pid17.reset()
                        pid18.reset()
                        
                if init.get()==3 :
                    consigne=limite_basse.get()*25
                    
                    if difference_val_bis>=temps_maintien :
                        if compteur_cycles.get()==nb_cycles.get()-1:
                            init.set(4)
                        else :
                            init.set(0)
                            compteur_cycles.set(compteur_cycles.get()+1)
                            
                        
                if init.get()==4 :
                    decharge.set(1)
#                    choix_asserv_val.set(2)
                    consigne=0
                
                memoire_consigne.set(consigne)  
            
            if consigne_choix.get()==61 :
                #consigne en position
                choix_asserv_val.set(2)
                if etalonnage(data[6]*2)<0.055 : #vérif charge 
                    
                    consigne=pos_var.get()*50/Vmm(capteur_fct(data[7]))
                    memoire_consigne.set(consigne)
                    if verif_pos(liste_memoire,consigne*4)==1:
                        do_pause()
                        showinfo('Commande position',"Positionement terminé")
                        reinitialiser()
                        return 0
                            
                else :
                    consigne=0
                    memoire_consigne.set(consigne)
                    print(etalonnage(data[6]*2))
                    do_pause()
                    showwarning('Attention !','Charge détectée, arrêt du chariot')
                    return 0
                
            if consigne_choix.get()==62 :
                #retour chariot
                choix_asserv_val.set(2)
                if etalonnage(data[6]*2)<0.055 : #vérif charge 
                    consigne=5*50/Vmm(capteur_fct(data[7]))
                    memoire_consigne.set(consigne)
                    if verif_pos(liste_memoire,consigne*4)==1:
                        do_pause()
                        showinfo('Commande position',"Positionement terminé")
                        reinitialiser()
                        return 0
                else :
                    consigne=0
                    memoire_consigne.set(consigne)
                    print(etalonnage(data[6]*2))
                    do_pause()
                    showwarning('Attention !','Charge détectée, arrêt du chariot')
                    reinitialiser()
                    
                    return 0
                
            if consigne_choix.get()==63 :
                #mise en tension chariot
                choix_asserv_val.set(2)
                if etalonnage(data[6]*2)<0.055 : #vérif charge 
                    consigne=1900*50/Vmm(capteur_fct(data[7]))
                    memoire_consigne.set(consigne)
                    if verif_pos(liste_memoire,consigne*4)==1:
                        do_pause()
                        showinfo('Commande position',"Positionement terminé")
                        reinitialiser()
                        return 0
                    
                else :
                    consigne=0
                    memoire_consigne.set(consigne)
                    print(etalonnage(data[6]*2))
                    do_pause()
                    showwarning('Attention !','Charge détectée, arrêt du chariot')
                    reinitialiser()
                    return 0
                
        if active_telec.get()!=0 :
            consigne=0
        ##################################saturation de la valeur consigne######################################
        if switch.get()=='off':
            if memoire_consigne.get()>limite_val.get()*25 and choix_asserv_val.get()==1 :#si valeur limite atteinte
                consigne=limite_val.get()*25
                memoire_consigne.set(consigne)
                
            ##################################consigne à 0 si phase de fin de programme#################
            
            if decharge.get()==1:
                consigne=0
                memoire_consigne.set(consigne)
            
            ##################################sécu si charge rupture atteinte#######################################
                    
            if (memoire_consigne.get()>=rupture.get()*25) and choix_asserv_val.get()==1 and lock !=0 :
                do_pause()
                showwarning('Attention','Charge consigne supérieure à la moitié de la charge de rupture ! Arrêt du programme.')
                print(data6/25)
                return 0
   
        #######################Récupération et affichage du temps restant ########################################
        
        if consigne_choix.get()!=23 and active_telec.get()==0 and choix_asserv_val.get()==1:
            temps_consigne=temps_maintien
            temps_restant=temps_consigne-difference2.get()
            temps_restant=convertisseur_secondes_temps(temps_restant)
            
            if temps_restant[0]=='-':
                temps_restant_val.set('0:0:0')
                zone_temps_restant.delete('temps_actuel')
                zone_temps_restant.create_text(50,10,text='0:0:0',tags='temps_actuel')
            else :
                temps_restant_val.set(temps_restant)
                zone_temps_restant.delete('temps_actuel')
                zone_temps_restant.create_text(50,10,text=temps_restant,tags='temps_actuel')
                
            zone_temps_consigne.delete('temps_consigne')
            zone_temps_consigne.create_text(50,10,text= convertisseur_secondes_temps(difference2.get()),tags='temps_consigne')
        
        ######################Arrêt si temps consigne atteint puis décharge #####################################
        
        if switch.get()=='off' :
            
            if  init.get()==4 and decharge.get()==0 :
                
                do_pause()
                output(0,1)
                output(0,2)
                showinfo('Fin minuteur', 'Programme terminé, cliquez sur start pour amorcer le début de la décharge') 
                decharge.set(1)
                choix_asserv_val.set(2)
                return 0
            
            
            if etalonnage(data[6]*2)<=0.055 and decharge.get()==1 and active_telec.get()==0 and choix_asserv_val.get()==1 :
  
                init.set(0)
                do_pause()
                showinfo('Fin minuteur', 'Décharge terminée')
                active_bouton(start_btn)
                active_bouton(stop_btn)
                desactive_bouton(pause_btn)
                reinitialiser()
                return 0
                    ######################écriture sur l'output##########################################
            else :
                if active_telec.get()==0 :
                    sortie=consigne/50
                    
                    if choix_asserv_val.get()==1 :
                        
                        if consigne_choix.get()==11 :
                            if etalonnage(data[6]*2)<consigne/25 :
                                pid5.setpoint=sortie
                                pid6.setpoint=sortie
                                if etalonnage(data[6]*2)>5 :
                                    pid5.Ki=I_char_pree.get()/(math.exp(etalonnage(data[6]*2)/1.5))
                                    pid5.Kp=P_char_pree.get()/(etalonnage(data[6]*2)/4)
                                else :
                                    pid5.Kp=P_char_pree.get()
                                pid1_sortie=pid5(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                pid2_sortie=pid6(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                
                            if etalonnage(data[6]*2)>=consigne/25 :
                                pid15.setpoint=sortie
                                pid16.setpoint=sortie
                                pid1_sortie=pid15(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                pid2_sortie=pid16(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                            
                        if consigne_choix.get()==21 :
                            
                            if etalonnage(data[6]*2)<limite_val.get() :
                                pid3.setpoint=sortie
                                pid1_sortie=pid3(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                pid2_sortie=pid4(etalonnage(data[6]*2)/2) #PID sur la charge réelle #PID sur la charge réelle
                            if etalonnage(data[6]*2)>=limite_val.get() :

                                pid13.setpoint=sortie
                                pid14.setpoint=sortie
                                pid1_sortie=pid13(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                pid2_sortie=pid14(etalonnage(data[6]*2)/2) #PID sur la charge réelle #PID sur la charge réelle
                            
                        if consigne_choix.get()==22 :
                            
                            if init.get()!=2 :
                                pid9.setpoint=sortie
                                pid10.setpoint=sortie
                                pid1_sortie=pid9(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                pid2_sortie=pid10(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                            if init.get()==2 :
                                
                                pid19.setpoint=sortie
                                pid20.setpoint=sortie
                                if etalonnage(data[6]*2)<consigne/25 :
                                    pid19.setpoint=sortie
                                    pid20.setpoint=sortie
                                if etalonnage(data[6]*2)>5 :
                                    pid19.Ki=I_char_pree.get()/(math.exp(etalonnage(data[6]*2)/1.5))
                                    pid20.Kp=P_char_pree.get()/(etalonnage(data[6]*2)/4)
                                else :
                                    pid19.Kp=P_char_pree.get()
                                pid1_sortie=pid19(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                pid2_sortie=pid20(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                            
                        if consigne_choix.get()==23 :
                            pid7.setpoint=sortie
                            pid8.setpoint=sortie
                            if episse.get()==1 :
                                char=(pourc_var.get()+395.93)/882.4
                                dech=(pourc_var.get()+1062.4)/2007.2
                                pid7.output_limits = (char-0.01, char+0.01) #brider la vitesse
                                pid8.output_limits = ((-1)*(dech+0.01), (-1)*dech-0.01) #brider la vitesse
                            if episse.get()==2:
                                pid7.output_limits = (0.73, 0.74) #brider la vitesse
                                #250/0.73
                                pid8.output_limits = (-0.66, -0.65) #brider la vitesse
                                #250/0.65 
                            pid1_sortie=pid7(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                            pid2_sortie=pid8(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                            
                        if consigne_choix.get()==231 :
                            pid7.setpoint=sortie
                            pid8.setpoint=sortie
                            if episse.get()==1 :
                                char=(pourc_var.get()+395.93)/882.4
                                dech=(pourc_var.get()+1062.4)/2007.2
                                pid7.output_limits = (char-0.01, char+0.01) #brider la vitesse
                                pid8.output_limits = ((-1)*(dech+0.01), (-1)*dech-0.01) #brider la vitesse
                            if episse.get()==2:
                                pid7.output_limits = (0.73, 0.74) #brider la vitesse
                                #250/0.73
                                pid8.output_limits = (-0.66, -0.65) #brider la vitesse
                                #250/0.65 
                            pid1_sortie=pid7(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                            pid2_sortie=pid8(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                            
                        if consigne_choix.get()==31 :
                            
                            if init.get()==0  :
                                pid7.setpoint=sortie
                                pid8.setpoint=sortie
                                if etalonnage(data[6]*2)>5 :
                                    pid7.Ki=I_char_fat.get()/(math.exp(etalonnage(data[6]*2)/1.5))
                                    pid7.Kp=P_char_fat.get()/(etalonnage(data[6]*2)/4)
                                else :
                                    pid7.Kp=P_char_fat.get()
                                    
                                pid1_sortie=pid7(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                pid2_sortie=pid8(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                
                            elif init.get()==2  :
                                pid7.setpoint=sortie
                                pid8.setpoint=sortie
                                pid1_sortie=pid7(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                pid2_sortie=pid8(etalonnage(data[6]*2)/2) #PID sur la charge réelle

                            elif init.get()==1 :
                                pid17.setpoint=sortie
                                pid18.setpoint=sortie
                                pid1_sortie=pid17(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                pid2_sortie=pid18(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                
                            elif init.get()==3 :
                                pid17.setpoint=sortie
                                pid18.setpoint=sortie
                                pid1_sortie=pid17(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                pid2_sortie=pid18(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                                pid2_sortie=sensi_decharge_val.get()-0.015
                                
                        if decharge.get()==1 :
                            pid2_sortie=-1
                            
                        if etalonnage(data[6]*2)/2<=sortie :
                            if pid1_sortie>=0 :
                                output(pid1_sortie,2)
                        elif etalonnage(data[6]*2)/2>sortie :
                            if etalonnage(data[6]*2)/2>sortie+0.01 :
                                if pid2_sortie<=0 :
                                    output(pid2_sortie*(-1),1)
                            else :
                                output(0,2) 
                                
                    elif choix_asserv_val.get()==2 :  
                        
                        if consigne_choix.get()==61 :
                            pid1.setpoint=sortie
                            pid2.setpoint=sortie
                            pid1_sortie=pid1(capteur_fct(data[7])) #PID sur la position
                            pid2_sortie=pid2(capteur_fct(data[7])) #PID sur la position
                            
                        elif consigne_choix.get()==62 :
                            pid1.setpoint=sortie
                            pid2.setpoint=sortie
                            pid1_sortie=pid1(capteur_fct(data[7])) #PID sur la position
                            pid2_sortie=pid2(capteur_fct(data[7])) #PID sur la position
                            
                        elif consigne_choix.get()==63 :
                            pid1.setpoint=sortie
                            pid2.setpoint=sortie
                            pid1.Kp=0.01
                            pid1_sortie=pid1(capteur_fct(data[7])) #PID sur la position
                            pid2_sortie=pid2(capteur_fct(data[7])) #PID sur la position
                            
                        else :
                            pid5.setpoint=sortie
                            pid6.setpoint=sortie
                            pid1_sortie=pid5(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                            pid2_sortie=pid6(etalonnage(data[6]*2)/2) #PID sur la charge réelle
                        
                        if capteur_fct(data[7])<=sortie :
                            output(pid1_sortie,2)
                        elif capteur_fct(data[7])>sortie :
                            if pid2_sortie<0 : 
                                output(pid2_sortie*(-1),1)
                        

        ######################Partie 1 animation : avant que tout bouge##########################################
        
        
            
        if x17<=1430 :
            
            tolerance=0.02
            
            
            if difference_val>=round(difference_val)-tolerance and difference_val<=round(difference_val)+tolerance:
                
                texte="".join(["t",str(round(difference_val)),"t"])
                
                if len(liste)==0:
                    liste.append(texte)
                    canvas.create_line(x17,marge_y,x17,height-marge_y,tags=texte) #lignes verticales
                    if difference_val%2==0 :
                        canvas.create_text(x17,height-marge_y/2,text=str(round(difference_val)),tags=texte) #créations chiffres
                    
                if liste[len(liste)-1]!=texte :
                    liste.append(texte)
                    canvas.create_line(x17,marge_y,x17,height-marge_y,tags=texte) #lignes verticales
                    if difference_val%2==0 :
                        canvas.create_text(x17,height-marge_y/2,text=str(round(difference_val)),tags=texte) #créations chiffres
                
                canvas.coords(pointeur7,x07+espace_i,offset-data7 ,x07+espace_i, offset-data7)
                canvas.create_line(x07 ,y07 ,x07+espace_i , offset-data7,fill='red',tags=texte_pointeur_fin)
                canvas.coords(pointeur6,x06+espace_i,offset-data6 ,x06+espace_i, offset-data6)
                canvas.create_line(x06 ,y06 ,x06+espace_i , offset-data6,fill='green',tags=texte_pointeur_fin)
                canvas.coords(pointeur_consigne,x00+espace_i,offset-consigne ,x00+espace_i, offset-consigne)
                canvas.create_line(x00 ,y00 ,x00+espace_i , offset-consigne,fill='blue',tags=texte_pointeur_consigne)
                
                
            else :
                canvas.coords(pointeur7,x07+espace_i ,offset-data7 ,x07+espace_i , offset-data7)
                canvas.create_line(x07 ,y07 ,x07+espace_i , offset-data7,fill='red',tags=texte_pointeur_fin)
                canvas.coords(pointeur6,x06+espace_i ,offset-data6 ,x06+espace_i , offset-data6)
                canvas.create_line(x06 ,y06 ,x06+espace_i , offset-data6,fill='green',tags=texte_pointeur_fin)
                canvas.coords(pointeur_consigne,x00+espace_i ,offset-consigne ,x00+espace_i , offset-consigne)
                canvas.create_line(x00 ,y00 ,x00+espace_i , offset-consigne,fill='blue',tags=texte_pointeur_consigne)
                 
    #####################Partie 2 animation : tout bouge####################################################################
    
        else :
            
            tolerance=0.1
            
            #################création nouvelle ligne verticale###############################################################
                                                                                                                            
            if difference_val>=round(difference_val)-tolerance and difference_val<=round(difference_val)+tolerance :
                                                                                                                            
                texte="".join(["t",str(round(difference_val)),"t"])                                                         
                                                                                                                            
                #####################anti doublon###################                                                        
                                                                                                                            
                if liste[len(liste)-1]!=texte:                                                                              
                    liste.append(texte)                                                                                     
                    canvas.create_line(x17,marge_y,x17,height-marge_y,tags=texte) #lignes verticales
                    if round(difference_val)%2==0 :                          
                        canvas.create_text(x17,height-marge_y/2,text=str(round(difference_val)),tags=texte) #créations chiffres  
                    
            #################Création ligne de tracé###########################################################################
             
            canvas.coords(pointeur7,x07+espace_i ,offset-data7 ,x07+espace_i , offset-data7)
            canvas.create_line(x07 ,y07 ,x07+espace_i , offset-data7,fill='red',tags=texte_pointeur_fin)
            canvas.coords(pointeur6,x06+espace_i ,offset-data6 ,x06+espace_i , offset-data6)
            canvas.create_line(x06 ,y06 ,x06+espace_i , offset-data6,fill='green',tags=texte_pointeur_fin)
            canvas.coords(pointeur_consigne,x00+espace_i,offset-consigne ,x00+espace_i, offset-consigne)
            canvas.create_line(x00 ,y00 ,x00+espace_i , offset-consigne,fill='blue',tags=texte_pointeur_consigne)
             
            ######################faire bouger le tracé#######################################################################
            
            for k in range (compteur.get(),compteur_pointeur.get()+2):
                texte="".join(["p",str(k),"p"])
                canvas.move(texte,-espace_i,0)
             
            ######################supprimer le tracé qui atteint le bout et actualise les coordonnées de l'existant##########################################
            
            canvas.coords(pointeur7,x07 ,offset-data7 ,x07 , offset-data7)
            canvas.coords(pointeur6,x06 ,offset-data6 ,x06 , offset-data6)
            canvas.coords(pointeur_consigne,x00 ,offset-consigne ,x00 , offset-consigne)
            texte="".join(["p",str(compteur.get()),"p"])
            canvas.delete(texte)
            
            ######################supprimer les lignes verticales qui atteignent le bout##########################################
            
            incr=0
            for l in range(len(liste)):
                
                coordonnee=canvas.bbox(liste[l])

                if coordonnee :
                    if coordonnee[0]<=47:
                        canvas.delete(liste[l])
                        incr=1
                canvas.move(liste[l],-espace_i,0)
            if incr==1 :
                liste.remove(liste[0])
            
        ######################compteurs de boucles +1##########################################
        
            compteur.set(compteur.get()+1)
        compteur_pointeur.set(compteur_pointeur.get()+1)
        
        ######################affichage exact,mini et maxi##########################################
        
        # pour la charge
        
        valeur_en_cours=etalonnage(data[6]*2)
            
        if valeur_en_cours>maxi_charge.get() :
            maxi_charge.set(round(valeur_en_cours,2))
            zone_charge_max.delete('max_charge_actuel')
            zone_charge_max.create_text(50,10,text=maxi_charge.get(),tags='max_charge_actuel')
            
        zone_charge_valeur.delete('valeur_charge_actuelle')
        zone_charge_valeur.create_text(250,75,text=round(valeur_en_cours,2),font=('Arial','100'),tags='valeur_charge_actuelle')
        
        # pour la distance chariot
        
        valeur_en_cours=round(Vmm(capteur_fct(data[7]))*capteur_fct(data[7]))
        
        if valeur_en_cours<mini.get() :
            mini.set(round(valeur_en_cours,2))
            zone_min.delete('mini_actuel')
            zone_min.create_text(50,10,text=mini.get(),tags='mini_actuel')
            
        if valeur_en_cours>maxi.get() :
            maxi.set(valeur_en_cours)
            zone_max.delete('max_actuel')
            zone_max.create_text(50,10,text=maxi.get(),tags='max_actuel')
            
        zone_valeur.delete('valeur_actuelle')
        zone_valeur.create_text(75,25,text=valeur_en_cours,font=('Arial','20'),tags='valeur_actuelle')
        
        # pour la consigne 
        
        zone_consigne.delete('consigne_val')
        if choix_asserv_val.get()==1 :
            zone_consigne.create_text(50,10,text=round(consigne/25,2),tags='consigne_val')
        if choix_asserv_val.get()==2 :
            zone_consigne.create_text(50,10,text=round(consigne*100/25,2),tags='consigne_val')
        
        ######################écriture valeur sur docs et bouclage fonction##########################################
        
        date=datetime.datetime.today()
        heures=str(date.hour)
        minutes=str(date.minute)
        secondes=str(date.second)
        milli=str(date.microsecond)
        hms="".join([heures,":",minutes,":",secondes,":",milli])
        
        if choix_asserv_val.get()==2 :
            #permet d'éviter d'avoir une valeur de consigne en charge de 2000 tonnes d'enregistré
            consigne=0
            
        feuille.write(compteur_pointeur.get()-int(1380/2)+2,3,date,date_format)
        feuille.write(compteur_pointeur.get()-int(1380/2)+2,4,etalonnage(data[6]*2))
        feuille.write(compteur_pointeur.get()-int(1380/2)+2,5,Vmm(capteur_fct(data[7]))*capteur_fct(data[7]))
        if switch.get()=='off' :
            feuille.write(compteur_pointeur.get()-int(1380/2)+2,6,consigne/25)
        fichier.write(";".join(["",hms,str(etalonnage(data[6]*2)),str(Vmm(capteur_fct(data[7]))*capteur_fct(data[7])),str(consigne/25)]) + "\n")
        fichier2.write(";".join(["",hms,str(data[6]*2),str(etalonnage(data[6]*2)),str(Vmm(capteur_fct(data[7]))*capteur_fct(data[7])),str(consigne/25)]) + "\n")
        fichier3.write(";".join(["",hms,str(data[6]*2),str(Vmm(capteur_fct(data[7]))*capteur_fct(data[7])),str(consigne/25)]) + "\n")
        
        timer=canvas.after(delay,animation)
            
    def start_fct ():
        
        global timer
        
        active_telec.set(0)
        
        try : 
            consigne=limite_val.get()
            
            if (rupture.get()*0.5>consigne and choix_asserv_val.get()==1) or choix_asserv_val.get()==2 or switch.get()=='on' or lock==0 :
                
                desactive_bouton(start_btn)
                desactive_bouton(stop_btn)
                active_bouton(pause_btn)
                desactive_bouton(gauche_btn)
                desactive_bouton(droite_btn)
                desactive_bouton(consigne_btn)
                desactive_bouton(enregistrer_btn)
                desactive_bouton(precedent2_btn)
                temps_bis.set(time.time()-difference2.get())
                temps.set(time.time()-difference.get()) #permet de reprendre au sur le bon temps malgré la pause
                temps_palier.set(time.time()-difference_palier.get())
                start_var.set(1)
                menu1.entryconfigure(4, state=DISABLED)
                
                
                
                pid1.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
                pid2.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
                pid3.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
                pid4.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
                pid5.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
                pid6.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
                pid7.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
                pid8.output_limits = (-5, sensi_decharge_val.get())
                pid9.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
                pid10.output_limits = (-5, sensi_decharge_val.get())
                pid11.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
                pid12.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
                pid13.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
                pid14.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
                pid15.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
                pid16.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
                pid17.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
                pid18.output_limits = (-5, sensi_decharge_val.get())
                pid19.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
                pid20.output_limits = (-5, sensi_decharge_val.get())
                
                animation()
    
            else :  
                do_pause()
                showwarning('Attention','Charge en consigne supérieure à la moitié de la charge de rupture ! Veuillez entrer une nouvelle valeur')
                print(consigne)
                print(rupture.get())
                print(choix_asserv_val.get())
                print(switch.get())
                            
        except ValueError :
            do_pause()
            showerror('Lancement impossible', 'Consigne non valide !')

    def certif_fct ():
        ###fenêtre de choix du certificat créé
        def entree_certif ():
        ########################
            ###fonction renvoyant à la fenêtre suivante
            if certif_val.get()==1:
                epreuve.set('Certificat de fatigue')
            if certif_val.get()==2:
                epreuve.set('Certificat de rupture')
            if certif_val.get()==3:
                epreuve.set("Certificat d'épreuve")
            if certif_val.get()==4:
                epreuve.set('Certificat de préétirage')
            
            fen_choix_certif.destroy()
            entree_certif1()
            
        ########################
    
        fen_choix_certif=Toplevel(fenetre_graph_retd)
        fen_choix_certif.title('Choix de certificat')
        
        certif_label = Label(fen_choix_certif, text="Veuillez choisir le certificat que vous voulez créer", justify = CENTER)
        
        fatigue_btn=Radiobutton(fen_choix_certif, text='Fatigue', variable=certif_val, value=1)
        rupture_btn=Radiobutton(fen_choix_certif, text='Rupture', variable=certif_val, value=2)
        surcharge_travail_btn=Radiobutton(fen_choix_certif, text='150% Charge de travail', variable=certif_val, value=3)
        preetirage_btn=Radiobutton(fen_choix_certif, text='Pré-étirage', variable=certif_val, value=4)
            
        retour_btn=Button(fen_choix_certif, text='Retour',command=fen_choix_certif.destroy)
        suivant_btn=Button(fen_choix_certif, text='Suivant',command=entree_certif)
        
        certif_label.grid(row=1,column=1,columnspan=3,padx =10, pady =10)
        fatigue_btn.grid(row=2,column=1,columnspan=3,padx =10, pady =10)
        rupture_btn.grid(row=3,column=1,columnspan=3,padx =10, pady =10)
        surcharge_travail_btn.grid(row=4,column=1,columnspan=3,padx =10, pady =10)
        preetirage_btn.grid(row=5,column=1,columnspan=3,padx =10, pady =10)
        
        retour_btn.grid(row=6,column=1,padx =10, pady =10)
        suivant_btn.grid(row=6,column=3,padx =10, pady =10)
    
    def telec_gauche():
        ###fonction de télécommande en décharge
        choix_asserv_val.set(1)
        desactive_bouton(start_btn)
        desactive_bouton(stop_btn)
        active_bouton(pause_btn)
        desactive_bouton(consigne_btn)
        desactive_bouton(enregistrer_btn)
        desactive_bouton(precedent2_btn)
        menu1.entryconfigure(4, state=DISABLED)
        temps.set(time.time()-difference.get()) #permet de reprendre au sur le bon temps malgré la pause
        
        if active_telec.get()==3:
            #########################sécu erreur clic#################
            print('erreur clic')
            output(0,1)
            
        else :
            output(pas_telecommande.get(),1)
        if active_telec.get()==0:
            active_telec.set(1)
            animation()
            
        active_telec.set(1)
        
    def telec_droite():
        ### fonction de télécommande en charge
        choix_asserv_val.set(1)
        desactive_bouton(start_btn)
        desactive_bouton(stop_btn)
        active_bouton(pause_btn)
        desactive_bouton(consigne_btn)
        desactive_bouton(enregistrer_btn)
        desactive_bouton(precedent2_btn)
        menu1.entryconfigure(4, state=DISABLED)
        temps.set(time.time()-difference.get()) #permet de reprendre au sur le bon temps malgré la pause
        
        if active_telec.get()==3:
            #########################sécu erreur clic#################
            print('erreur clic')
            output(0,2)

        else :
            output(pas_telecommande.get(),2)
        
        if active_telec.get()==0:
            active_telec.set(1)
            animation()
            
        active_telec.set(1)
        
  
    def relache(event):
        ###fonction s'activant lorsque l'utilisateur relache son clic de télécomande en charge et en décharge.
        ###Permet l'arrêt du chariot.
        if consigne_choix.get()==61 or consigne_choix.get()==62 :
            choix_asserv_val.set(2)
        active_telec.set(active_telec.get()+1)
        output(0,1)
        output(0,2)

        
    def choix_asserv_fct():
        ###fenêtre de choix d'asservissement 
        def choix_asserv_suite():
            ###fonction d'envoi a la fenêtre de choix de la consigne en fonction de l'asservissement choisi.
            if choix_asserv_val.get()!=0:
#                asservissement_btn['bg']='green'
                if consigne_btn['bg']=='green':
                    active_bouton(start_btn)
            fen_choix_asserv.destroy()
            
            if choix_asserv_val.get()==1:
                parametrage_fct()
                menu1.entryconfigure(1, state=DISABLED)
                menu1.entryconfigure(2, state=NORMAL)
                rappel_asserv.delete('asservissement')
                rappel_asserv.create_text(125,10,text='Asservissement en charge',tags='asservissement')
            if choix_asserv_val.get()==2:
                distance_fct()
                menu1.entryconfigure(1, state=NORMAL)
                menu1.entryconfigure(2, state=DISABLED)
                menu1.entryconfigure(3, state=DISABLED)
                rappel_asserv.delete('asservissement')
                rappel_asserv.create_text(100,10,text='Asservissement en position',tags='asservissement')
                
        fen_choix_asserv=Toplevel(fenetre_graph_retd)
        main_label = Label(fen_choix_asserv, text="Veuillez selectionner le mode d'asservissement")
        
        charge_coche=Radiobutton(fen_choix_asserv, text="Asservissement en charge",fg='green', variable=choix_asserv_val, value=1)
        deformation_coche=Radiobutton(fen_choix_asserv, text="Positionnement du chariot",fg='red', variable=choix_asserv_val, value=2)
        
        retour_btn=Button(fen_choix_asserv, text='Retour',command=fen_choix_asserv.destroy)
        suivant_btn=Button(fen_choix_asserv, text='Suivant',command=choix_asserv_suite)
        
        main_label.grid(row=1,column=1,rowspan=2,padx=10,pady=10)
        charge_coche.grid(row=3,column=1,padx=10,pady=10)
        deformation_coche.grid(row=4,column=1,padx=10,pady=10)
        
        retour_btn.grid(row=5,column=0,padx=10,pady=10)
        suivant_btn.grid(row=5,column=2,padx=10,pady=10)
        
        
    def entree_certif1 ():
        ###fenêtre des entrées du certificat 
        def suivant_fct():
            ###fonction de création du pdf
            if askyesno('Attention',"Assurez vous d'avoir coché un choix d'enregistrement avant la création du certificat ! De plus, la création d'un certififat entraîne un arrêt du programme, êtes vous sur de vouloir continuer ?") :
                
                today=datetime.datetime.now()

                an=str(today.year)[2:]
                mois=str(today.month)
                jour=str(today.day)
                
                if len(mois)==1:
                    mois="".join(['0',mois])
                    
                if len(jour)==1:
                    jour="".join(['0',jour])
                    
                date="".join([jour,'/',mois,'/',an])
                generate_pdf(date,com.get(),str(maxi_charge.get()),reference.get(),epreuve.get(),materiel.get(),projet.get(),nom_prenom.get(),banc.get(),commande.get(),contact3.get(),contact2.get(),contact1.get(),adresse3.get(),adresse2.get(),adresse1.get(),societe.get(),normes.get(),validite.get())
                showinfo('Bravo','Certificat créé !')
                fen_choix_certif.destroy()
                
                desactive_bouton(start_btn)
                active_bouton(stop_btn)
                desactive_bouton(pause_btn)
                desactive_bouton(gauche_btn)
                desactive_bouton(droite_btn)
                desactive_bouton(consigne_btn)
                desactive_bouton(enregistrer_btn)
                active_bouton(precedent2_btn)
                
            else :
                return 0
        
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
            
            if certif_val.get()==1:
                nom_pdf="".join([nom[:len(nom)-20]+'_','Certificat_','Fatigue','.pdf'])
            if certif_val.get()==2:
                nom_pdf="".join([nom[:len(nom)-20]+'_','Certificat_','Rupture','.pdf'])
            if certif_val.get()==3:
                nom_pdf="".join([nom[:len(nom)-20]+'_','Certificat_','Epreuve','.pdf'])
            if certif_val.get()==4:
                nom_pdf="".join([nom[:len(nom)-20]+'_','Certificat_','Préétirage','.pdf'])
                
            
            c = cv.Canvas(nom_pdf, pagesize=A4)
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
            c.drawString(55,462,"Normes de rupture validée :")
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
            im = Image.open('Logo-Ino-Rope-blanc.png')
            c.drawInlineImage(im,455,775, width=90, height=14)
    
            nom_png="".join([nom[:len(nom)-5],'.png'])
            generate_image(nom_png)
            im = Image.open(nom_png)   
            c.drawInlineImage(im,70,150, width=470, height=280)
            c.save()
            os.remove(nom_png)
            
        def generate_image(nom_image):
            ###fonction de génération du fichier png comprenant la courbe excel du test.
            nom_final=''.join([nom])
            excel = Dispatch("Excel.Application")
            excel.ActiveWorkbook
            xlsWB = excel.Workbooks.Open(nom_final) 
            xlsWB.Sheets("sheet1")
            mychart = excel.Charts(1)
            mychart.Export(Filename="".join([nom_image]))
            
            
        fen_choix_certif=Toplevel(fenetre_graph_retd)
        destinataire_label = Label(fen_choix_certif, text="Destinataire du certificat")
        societe_label = Label(fen_choix_certif, text="Société")
        adresse_label = Label(fen_choix_certif, text="Adresse")
        adresse_rue_label = Label(fen_choix_certif, text="Rue")
        adresse_ville_label = Label(fen_choix_certif, text="Ville")
        adresse_postal_label = Label(fen_choix_certif, text="Code postal")
        contact_label = Label(fen_choix_certif, text="Contact")
        contact_nom_label = Label(fen_choix_certif, text="Nom")
        contact_tel_label = Label(fen_choix_certif, text="téléphone")
        contact_email_label = Label(fen_choix_certif, text="email")
        commande_label = Label(fen_choix_certif, text="Commande")
        
        description_label = Label(fen_choix_certif, text="Description de l'épreuve")
        banc_label = Label(fen_choix_certif, text="Banc de traction C10TL27")
        operateur_label = Label(fen_choix_certif, text="Opérateur")
        projet_label = Label(fen_choix_certif, text="Projet")
        materiel_label = Label(fen_choix_certif, text="Matériel testé")
        epreuve_label = Label(fen_choix_certif, text="Nature de l'expérience")
        reference_label = Label(fen_choix_certif, text="Référence")
        normes_label = Label(fen_choix_certif, text="Norme de rupture validée")
        validite_label = Label(fen_choix_certif, text="Date limite de validité")
        commentaire_label = Label(fen_choix_certif, text="Commentaire")
        
        societe_entree = Entry(fen_choix_certif, textvariable=societe, width=30)
        adresse1_entree = Entry(fen_choix_certif, textvariable=adresse1, width=30)
        adresse2_entree = Entry(fen_choix_certif, textvariable=adresse2, width=30)
        adresse3_entree = Entry(fen_choix_certif, textvariable=adresse3, width=30)
        contact1_entree = Entry(fen_choix_certif, textvariable=contact1, width=30)
        contact2_entree = Entry(fen_choix_certif, textvariable=contact2, width=30)
        contact3_entree = Entry(fen_choix_certif, textvariable=contact3, width=30)
        commande_entree = Entry(fen_choix_certif, textvariable=commande, width=30) 
         
        banc_entree = Entry(fen_choix_certif, textvariable=banc, width=30) 
        operateur_entree = Entry(fen_choix_certif, textvariable=nom_prenom, width=30) 
        projet_entree = Entry(fen_choix_certif, textvariable=projet, width=30) 
        materiel_entree = Entry(fen_choix_certif, textvariable=materiel, width=30) 
        epreuve_entree = Entry(fen_choix_certif, textvariable=epreuve, width=30) 
        reference_entree = Entry(fen_choix_certif, textvariable=reference, width=30)
        normes_entree = Entry(fen_choix_certif, textvariable=normes, width=30)
        validite_entree = Entry(fen_choix_certif, textvariable=validite, width=30)
        commentaire_entree = Entry(fen_choix_certif, textvariable=com.get(), width=30)
        
        retour_btn=Button(fen_choix_certif, text='Retour',command=retour_certif)
        suivant_btn=Button(fen_choix_certif, text='Suivant',command=suivant_fct)
        
        destinataire_label.grid(row=0,column=0,columnspan=5,padx =10, pady =10)
        societe_label.grid(row=1,column=0,padx =10, pady =10)
        adresse_label.grid(row=2,column=0,padx =10, pady =10)
        adresse_rue_label.grid(row=2,column=1,padx =10, pady =10)
        adresse_ville_label.grid(row=3,column=1,padx =10, pady =10)
        adresse_postal_label.grid(row=4,column=1,padx =10, pady =10)
        contact_label.grid(row=5,column=0,padx =10, pady =10)
        contact_nom_label.grid(row=5,column=1,padx =10, pady =10)
        contact_tel_label.grid(row=6,column=1,padx =10, pady =10)
        contact_email_label.grid(row=7,column=1,padx =10, pady =10)
        commande_label.grid(row=8,column=0,padx =10, pady =10)
        
        description_label.grid(row=9,column=0,columnspan=5,padx =10, pady =10)
        banc_label.grid(row=10,column=0,padx =10, pady =10)
        operateur_label.grid(row=11,column=0,padx =10, pady =10)
        projet_label.grid(row=12,column=0,padx =10, pady =10)
        materiel_label.grid(row=13,column=0,padx =10, pady =10)
        epreuve_label.grid(row=14,column=0,padx =10, pady =10)
        reference_label.grid(row=15,column=0,padx =10, pady =10)
        normes_label.grid(row=16,column=0,padx =10, pady =10)
        validite_label.grid(row=17,column=0,padx =10, pady =10)
        commentaire_label.grid(row=18,column=0,padx =10, pady =10)
        
        societe_entree.grid(row=1,column=2,padx =10, pady =10)
        adresse1_entree.grid(row=2,column=2,padx =10, pady =10)
        adresse2_entree.grid(row=3,column=2,padx =10, pady =10)
        adresse3_entree.grid(row=4,column=2,padx =10, pady =10)
        contact1_entree.grid(row=5,column=2,padx =10, pady =10)
        contact2_entree.grid(row=6,column=2,padx =10, pady =10)
        contact3_entree.grid(row=7,column=2,padx =10, pady =10)
        commande_entree.grid(row=8,column=2,padx =10, pady =10)
         
        banc_entree.grid(row=10,column=2,padx =10, pady =10)
        operateur_entree.grid(row=11,column=2,padx =10, pady =10)
        projet_entree.grid(row=12,column=2,padx =10, pady =10)
        materiel_entree.grid(row=13,column=2,padx =10, pady =10)
        epreuve_entree.grid(row=14,column=2,padx =10, pady =10)
        reference_entree.grid(row=15,column=2,padx =10, pady =10)
        normes_entree.grid(row=16,column=2,padx =10, pady =10)
        validite_entree.grid(row=17,column=2,padx =10, pady =10)
        commentaire_entree.grid(row=18,column=2,padx =10, pady =10)
        
        retour_btn.grid(row=19,column=0,padx =10, pady =10)
        suivant_btn.grid(row=19,column=2,padx =10, pady =10)
        
    def crea_nom(i):
        ###fonction de création des noms des fichiers csv et xlsx
        def verif_doc (fichier,i):
            ###fonction qui vérifie que le nom utilisé n'est pas déjà créé
            global indice
            
            try :
                ouvert=open(fichier,'r')
                ouvert.close()
                indice+=1
                print('fichier deja cree')
                return crea_nom(i)
            except :
                print('nom=',fichier)
                return fichier
                
        today=datetime.datetime.now()
        an=str(today.year)[2:]
        mois=str(today.month)
        jour=str(today.day)
        
        chemin=lecture_chemin('chemin_enre.txt')[:len(lecture_chemin('chemin_enre.txt'))-1]+'\\'
        
        if len(mois)==1:
            mois="".join(['0',mois])
            
        if len(jour)==1:
            jour="".join(['0',jour])
        
        if i==1:
            nom="".join([chemin,an,mois,jour,'_',alphabet[indice],'_val_etalonnees','.xlsx'])
            verif=verif_doc(nom,i)
            return verif
        
        if i==2:
            nom="".join([chemin,an,mois,jour,'_',alphabet[indice],'_val_etalonnee','.csv'])
            verif=verif_doc(nom,i)
            return verif
        
        if i==3:
            nom="".join([chemin,an,mois,jour,'_',alphabet[indice],'_val_etalonnees_et_affichee','.csv'])
            verif=verif_doc(nom,i)
            return verif
        
        if i==4:
            nom="".join([chemin,an,mois,jour,'_',alphabet[indice],'_val_affichee','.csv'])
            verif=verif_doc(nom,i)
            return verif
        
    def init_xlsx():
        ###fonction d'initialisation du document excel

        feuille.write(0,3,'temps en hh:m:ss')
        feuille.write(0,4,'charge_indiquee (tonnes)')
        feuille.write(0,5,'valeur_deplacement (mm)')
        feuille.write(0,6,'consigne (tonnes)')
        
        feuille.write(0,0,'nom')
        feuille.write(1,0,'prenom')
        feuille.write(2,0,'Titre')
        feuille.write(3,0,'matériel')
        feuille.write(4,0,'longueur utile chariot')
        feuille.write(5,0,'rupture')
        feuille.write(6,0,'date')
        feuille.write(7,0,'commentaire')
        feuille.write(8,0,'nom capteur déplacement')
        feuille.write(9,0,'reference capteur déplacement')
        feuille.write(10,0,'nom capteur charge')
        feuille.write(11,0,'reference capteur charge')
        feuille.write(12,0,"méthode d'accroche")
        feuille.write(13,0,"longueur utile éprouvette")
        
        
        feuille.write(0,1,entrees[1])
        feuille.write(1,1,entrees[2])
        feuille.write(2,1,entrees[0])
        feuille.write(3,1,entrees[3])
        feuille.write(4,1,entrees[4])
        feuille.write(5,1,entrees[5])
        feuille.write(6,1,str(datetime.datetime.now()))
        feuille.write(8,1,'detecteur ultrasonique')
        feuille.write(9,1,'UC_2000_L2_U_V15')
        feuille.write(10,1,'Indicateur pour signal analgique')
        feuille.write(11,1,'INDI-PAXS')
        if entrees[7]==1 :    
            feuille.write(12,1,'Goupilles')
        if entrees[7]==2 :
            feuille.write(12,1,'Cabestant '+str(entrees[9])+' mm')
        feuille.write(13,1,entrees[10])
    
    def init_csv (Titre,Nom,Prenom,Materiel,Rupture):   
        ###fonction d'initialisation des fichiers csv
        if entrees[7]!=2 :    
            accroche_phrase='Goupilles'
        if entrees[7]==2 :
            accroche_phrase='Cabestant_'+str(entrees[9])+'_mm'

            
        texte="Titre;Nom;Prenom;Materiel;Rupture;Nom_capteur_deplacement;Ref_capteur_deplacement;Nom_capteur_charge;Ref_capteur_charge;Methode_accroche;Longueur_utile_prouvette;date\n"
        fichier.write(texte)
        texte=";".join([Titre,Nom,Prenom,Materiel,Rupture,'detecteur_ultrasonique','UC_2000_L2_U_V15','Indicateur_pour_signal_analogique','INDI_PAXS',accroche_phrase,str(entrees[10]),str(datetime.datetime.today())])+"\n"
        fichier.write(texte)
        fichier.write("\n")
        texte=";temps;charge_etalonnee_en_tonnes;valeur_deplacement_en_mm;consigne_en_tonnes\n"
        fichier.write(texte)

        texte="Titre;Nom;Prenom;Materiel;Rupture;Nom_capteur_deplacement;Ref_capteur_deplacement;Nom_capteur_charge;Ref_capteur_charge;Methode_accroche;Longueur_utile_prouvette;date\n"
        fichier2.write(texte)
        fichier3.write(texte)
        texte=";".join([Titre,Nom,Prenom,Materiel,Rupture,'detecteur_ultrasonique','UC_2000_L2_U_V15','Indicateur_pour_signal_analogique','INDI_PAXS',accroche_phrase,str(entrees[10]),str(datetime.datetime.today())])+"\n"
        fichier2.write(texte)
        fichier3.write(texte)
        fichier2.write("\n")
        fichier3.write("\n")
        texte=";temps;charge_affichee_en_tonnes;charge_etalonnee_en_tonnes;valeur_deplacement_en_mm;consigne_en_tonnes\n"
        fichier2.write(texte)
        texte=";temps;charge_affichee_en_tonnes;valeur_deplacement_en_mm;consigne_en_tonnes\n"
        fichier3.write(texte)
        
    def color_on() :
        ###fonction de coloration des boutons du mode manuel en mode 'on'
        off_button['bg']='gray'
        active_bouton(start_btn)
        desactive_bouton(gauche_btn)
        desactive_bouton(droite_btn)
        output(0,1)
        output(0,2)
        return 0
    
    def color_off() :
        ###fonction de coloration des boutons du mode manuel en mode 'off'
        on_button['bg']='gray'
        active_bouton(gauche_btn)
        active_bouton(droite_btn)
        if consigne_btn['bg']=='green':
            active_bouton(start_btn)
        else :
            desactive_bouton(start_btn)
        return 0
            
    def mise_a_0_fct():
        ###fonction de mise à la position 0 du chariot
        choix_asserv_val.set(2)
        consigne_choix.set(62)
        desactive_bouton(mise_a_0_btn)
        desactive_bouton(mise_a_tension_btn)
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
        start_fct()
        return 0
        
    def mise_a_tension_fct():
        ### fonction de mise à la charge du chariot
        choix_asserv_val.set(2)
        consigne_choix.set(63)
        desactive_bouton(mise_a_0_btn)
        desactive_bouton(mise_a_tension_btn)
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
        start_fct()
        
        return 0
    
    def sensi_page():
        ###fenêtre de choix de la sensibilité des PID
        
        def sensi_suivant() :
            ###fonction d'écriture des sensibilité et de mise à jour des PID
            print('réglage sensi pid')
            fichier=open('sensi_charge.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(sensi_charge_val.get())+'\n')
            fichier.close()
            fichier=open('sensi_decharge.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(sensi_decharge_val.get())+'\n')
            fichier.close()
            fen_sensi.destroy()
            sensi_charge_val.set(float(lecture_sensi_charge()))
            sensi_decharge_val.set(float(lecture_sensi_decharge()))

            pid1.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            pid2.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
            pid3.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            pid4.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
            pid5.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            pid6.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
            pid7.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            pid8.output_limits = (-5, sensi_decharge_val.get())
            pid9.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            pid10.output_limits = (-5, sensi_decharge_val.get())
            pid11.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            pid12.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
            pid13.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            pid14.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
            pid15.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            pid16.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
            pid17.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            pid18.output_limits = (-5, sensi_decharge_val.get())
            pid19.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            pid20.output_limits = (-5, sensi_decharge_val.get())
            
            return 0
            
        fen_sensi=Toplevel(fenetre_graph_retd)
        
        label_charge=Label(fen_sensi, text="Choisissez la nouvelle valeur minimale en charge")
        label_decharge=Label(fen_sensi, text="Choisissez la nouvelle valeur minimale en décharge")

        charge_entree = Entry(fen_sensi, textvariable=sensi_charge_val, width=30)
        decharge_entree = Entry(fen_sensi, textvariable=sensi_decharge_val, width=30)
      
        retour_btn=Button(fen_sensi, text='Retour',command=fen_sensi.destroy)
        suivant_btn=Button(fen_sensi, text='Enregistrer',command=sensi_suivant)
        
        label_charge.grid(row=1,column=0,padx =10, pady =10)
        label_decharge.grid(row=3,column=0,padx =10, pady =10)
        charge_entree.grid(row=1,column=1,padx =10, pady =10)
        decharge_entree.grid(row=3,column=1,padx =10, pady =10)
        retour_btn.grid(row=4,column=0,padx =10, pady =10)
        suivant_btn.grid(row=4,column=1,padx =10, pady =10)
    
    def coef_pid_fct():
        ###fenêtre de choix des coefficients des PID
        
        def pid_suivant() :
            ###Fonction d'écriture des coefficients et de mis à jour des PID
            print('réglage coefs pid')
            chemin=''
            chemint=''
            chemin_final=chemin+chemint
            
            fichier=open(chemin_final+'Pos_char_P.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_char_pos.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pos_char_I.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_char_pos.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pos_char_D.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_char_pos.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Pree_char_P.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_char_pree.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pree_char_I.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_char_pree.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pree_char_D.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_char_pree.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Rup_char_P.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_char_rup.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Rup_char_I.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_char_rup.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Rup_char_D.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_char_rup.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Fat_char_P.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_char_fat.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Fat_char_I.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_char_fat.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Fat_char_D.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_char_fat.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Pal_char_P.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_char_pal.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pal_char_I.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_char_pal.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pal_char_D.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_char_pal.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Pos_P_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_pos_char_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pos_I_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_pos_char_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pos_D_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_pos_char_dech.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Pree_P_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_pree_char_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pree_I_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_pree_char_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pree_D_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_pree_char_dech.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Rup_P_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_rup_char_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Rup_I_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_rup_char_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Rup_D_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_rup_char_dech.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Fat_P_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_fat_char_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Fat_I_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_fat_char_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Fat_D_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_fat_char_dech.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Pal_P_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_pal_char_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pal_I_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_pal_char_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pal_D_char_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_pal_char_dech.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Pos_maint_P.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_maint_pos.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pos_maint_I.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_maint_pos.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pos_maint_D.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_maint_pos.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Pree_maint_P.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_maint_pree.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pree_maint_I.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_maint_pree.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pree_maint_D.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_maint_pree.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Rup_maint_P.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_maint_rup.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Rup_maint_I.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_maint_rup.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Rup_maint_D.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_maint_rup.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Fat_maint_P.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_maint_fat.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Fat_maint_I.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_maint_fat.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Fat_maint_D.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_maint_fat.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Pal_maint_P.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_maint_pal.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pal_maint_I.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_maint_pal.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pal_maint_D.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_maint_pal.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Pos_P_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_pos_maint_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pos_I_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_pos_maint_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pos_D_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_pos_maint_dech.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Pree_P_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_pree_maint_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pree_I_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_pree_maint_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pree_D_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_pree_maint_dech.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Rup_P_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_rup_maint_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Rup_I_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_rup_maint_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Rup_D_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_rup_maint_dech.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Fat_P_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_fat_maint_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Fat_I_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_fat_maint_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Fat_D_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_fat_maint_dech.get())+'\n')
            fichier.close()
            
            fichier=open(chemin_final+'Pal_P_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(P_pal_maint_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pal_I_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(I_pal_maint_dech.get())+'\n')
            fichier.close()
            fichier=open(chemin_final+'Pal_D_maint_dech.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+' '+str(D_pal_maint_dech.get())+'\n')
            fichier.close()
            
            ##################################en charge####################################
            ##########################################PID position#########################
    
            pid1.Kp=P_char_pos.get()
            pid1.Ki=I_char_pos.get()
            pid1.Kd=D_char_pos.get()
            pid1.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            
            pid2.Kp=P_pos_char_dech.get()
            pid2.Ki=I_pos_char_dech.get()
            pid2.Kd=D_pos_char_dech.get()
            pid2.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
            
            ##########################################PID rupture#########################
            
            pid3.Kp=P_char_rup.get()
            pid3.Ki=I_char_rup.get()
            pid3.Kd=D_char_rup.get()
            pid3.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            
            pid4.Kp=P_rup_char_dech.get()
            pid4.Ki=I_rup_char_dech.get()
            pid4.Kd=D_rup_char_dech.get()
            pid4.output_limits = (-1, sensi_decharge_val.get()) #brider la vitesse
            
            ##########################################PID préétirage######################
            
            pid5.Kp=P_char_pree.get()
            pid5.Ki=I_char_pree.get()
            pid5.Kd=D_char_pree.get()
            pid5.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            
            pid6.Kp=P_pree_char_dech.get()
            pid6.Ki=I_pree_char_dech.get()
            pid6.Kd=D_pree_char_dech.get()
            pid6.output_limits = (-1, sensi_decharge_val.get()) #brider la vitesse
            
            ##########################################PID fatigue######################### 
            
            pid7.Kp=P_char_fat.get()
            pid7.Ki=I_char_fat.get()
            pid7.Kd=D_char_fat.get()
            pid7.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
        
            pid8.Kp=P_fat_char_dech.get()
            pid8.Ki=I_fat_char_dech.get()
            pid8.Kd=D_fat_char_dech.get()
            pid8.output_limits = (-1, sensi_decharge_val.get())
            
            ##########################################PID palier######################### 
            
            pid9.Kp=P_char_pal.get()
            pid9.Ki=I_char_pal.get()
            pid9.Kd=D_char_pal.get()
            pid9.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
        
            pid10.Kp=P_pal_char_dech.get()
            pid10.Ki=I_pal_char_dech.get()
            pid10.Kd=D_pal_char_dech.get()
            pid10.output_limits = (-1, sensi_decharge_val.get())
            
            ##################################en maintien####################################
            ##########################################PID position#########################
    
            pid11.Kp=P_maint_pos.get()
            pid11.Ki=I_maint_pos.get()
            pid11.Kd=D_maint_pos.get()
            pid11.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            
            pid12.Kp=P_pos_maint_dech.get()
            pid12.Ki=I_pos_maint_dech.get()
            pid12.Kd=D_pos_maint_dech.get()
            pid12.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
            
            ##########################################PID rupture#########################
            
            pid13.Kp=P_maint_rup.get()
            pid13.Ki=I_maint_rup.get()
            pid13.Kd=D_maint_rup.get()
            pid13.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            
            pid14.Kp=P_rup_maint_dech.get()
            pid14.Ki=I_rup_maint_dech.get()
            pid14.Kd=D_rup_maint_dech.get()
            pid14.output_limits = (-1, sensi_decharge_val.get()) #brider la vitesse
            
            ##########################################PID préétirage######################
            
            pid15.Kp=P_maint_pree.get()
            pid15.Ki=I_maint_pree.get()
            pid15.Kd=D_maint_pree.get()
            pid15.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
            
            pid16.Kp=P_pree_maint_dech.get()
            pid16.Ki=I_pree_maint_dech.get()
            pid16.Kd=D_pree_maint_dech.get()
            pid16.output_limits = (-1, sensi_decharge_val.get()) #brider la vitesse
            
            ##########################################PID fatigue######################### 
            
            pid17.Kp=P_maint_fat.get()
            pid17.Ki=I_maint_fat.get()
            pid17.Kd=D_maint_fat.get()
            pid17.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
        
            pid18.Kp=P_fat_maint_dech.get()
            pid18.Ki=I_fat_maint_dech.get()
            pid18.Kd=D_fat_maint_dech.get()
            pid18.output_limits = (-1, sensi_decharge_val.get())
            
            ##########################################PID palier######################### 
            
            pid19.Kp=P_maint_pal.get()
            pid19.Ki=I_maint_pal.get()
            pid19.Kd=D_maint_pal.get()
            pid19.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
        
            pid20.Kp=P_pal_maint_dech.get()
            pid20.Ki=I_pal_maint_dech.get()
            pid20.Kd=D_pal_maint_dech.get()
            pid20.output_limits = (-1, sensi_decharge_val.get())
            
            ##############################################################################
            
            fen_pid.destroy()
            return 0
        
        def reinit_val_fct():
            ###fonction permettant de récupérer les valeurs de coeffients par défaut et de les afficher sur les entrées de la fenêtre
            if showwarning('Attention','Êtes vous sur de vouloir réinitialiser ces valeurs ?') :
                
                liste=coef_PID()
                
                P_char_pos.set(liste[0])
                I_char_pos.set(liste[1])
                D_char_pos.set(liste[2])
                
                P_char_pree.set(liste[6])
                I_char_pree.set(liste[7])
                D_char_pree.set(liste[8])
                
                P_char_rup.set(liste[3])
                I_char_rup.set(liste[4])
                D_char_rup.set(liste[5])
                
                P_char_fat.set(liste[9])
                I_char_fat.set(liste[10])
                D_char_fat.set(liste[11])
                
                P_char_pal.set(liste[12])
                I_char_pal.set(liste[13])
                D_char_pal.set(liste[14])
                
                P_pos_char_dech.set(liste[15])
                I_pos_char_dech.set(liste[16])
                D_pos_char_dech.set(liste[17])
                
                P_pree_char_dech.set(liste[21])
                I_pree_char_dech.set(liste[22])
                D_pree_char_dech.set(liste[23])
                
                P_rup_char_dech.set(liste[18])
                I_rup_char_dech.set(liste[19])
                D_rup_char_dech.set(liste[20])
                
                P_fat_char_dech.set(liste[24])
                I_fat_char_dech.set(liste[25])
                D_fat_char_dech.set(liste[26])
                
                P_pal_char_dech.set(liste[27])
                I_pal_char_dech.set(liste[28])
                D_pal_char_dech.set(liste[29])
                
                P_maint_pos.set(liste[30])
                I_maint_pos.set(liste[31])
                D_maint_pos.set(liste[32])
                
                P_maint_pree.set(liste[36])
                I_maint_pree.set(liste[37])
                D_maint_pree.set(liste[38])
                
                P_maint_rup.set(liste[33])
                I_maint_rup.set(liste[34])
                D_maint_rup.set(liste[35])
                
                P_maint_fat.set(liste[39])
                I_maint_fat.set(liste[40])
                D_maint_fat.set(liste[41])
                
                P_maint_pal.set(liste[42])
                I_maint_pal.set(liste[43])
                D_maint_pal.set(liste[44])
                
                P_pos_maint_dech.set(liste[45])
                I_pos_maint_dech.set(liste[46])
                D_pos_maint_dech.set(liste[47])
                
                P_pree_maint_dech.set(liste[41])
                I_pree_maint_dech.set(liste[42])
                D_pree_maint_dech.set(liste[43])
                
                P_rup_maint_dech.set(liste[48])
                I_rup_maint_dech.set(liste[49])
                D_rup_maint_dech.set(liste[50])
                
                P_fat_maint_dech.set(liste[54])
                I_fat_maint_dech.set(liste[55])
                D_fat_maint_dech.set(liste[56])
                
                P_pal_maint_dech.set(liste[57])
                I_pal_maint_dech.set(liste[58])
                D_pal_maint_dech.set(liste[59])
            
            return 0
            
        
        fen_pid=Toplevel(fenetre_graph_retd)
        
        pos_frame=LabelFrame(fen_pid, text="Déplacement")
        pos_frame.grid(row=1,column=1,columnspan=3,padx =5, pady =5)
        pos_char_frame=LabelFrame(pos_frame, text="En charge/décharge")
        pos_char_frame.grid(row=1,column=1,columnspan=3,padx =5, pady =5)
        pos_maint_frame=LabelFrame(pos_frame, text="En maintien")
        pos_maint_frame.grid(row=1,column=5,columnspan=3,padx =5, pady =5)
        
        pree_frame=LabelFrame(fen_pid, text="Préétirage")
        pree_frame.grid(row=3,column=1,columnspan=3,padx =5, pady =5)
        pree_char_frame=LabelFrame(pree_frame, text="En charge/décharge")
        pree_char_frame.grid(row=3,column=1,columnspan=3,padx =5, pady =5)
        pree_maint_frame=LabelFrame(pree_frame, text="En maintien")
        pree_maint_frame.grid(row=3,column=5,columnspan=3,padx =5, pady =5)
        
        rup_frame=LabelFrame(fen_pid, text="Rupture")
        rup_frame.grid(row=5,column=1,columnspan=3,padx =5, pady =5)
        rup_char_frame=LabelFrame(rup_frame, text="En charge/décharge")
        rup_char_frame.grid(row=5,column=1,columnspan=3,padx =5, pady =5)
        rup_maint_frame=LabelFrame(rup_frame, text="En maintien")
        rup_maint_frame.grid(row=5,column=5,columnspan=3,padx =5, pady =5)
        
        fat_frame=LabelFrame(fen_pid, text="Fatigue")
        fat_frame.grid(row=7,column=1,columnspan=3,padx =5, pady =5)
        fat_char_frame=LabelFrame(fat_frame, text="En charge/décharge")
        fat_char_frame.grid(row=7,column=1,columnspan=3,padx =5, pady =5)
        fat_maint_frame=LabelFrame(fat_frame, text="En maintien")
        fat_maint_frame.grid(row=7,column=5,columnspan=3,padx =5, pady =5)
        
        pal_frame=LabelFrame(fen_pid, text="Paliers")
        pal_frame.grid(row=9,column=1,columnspan=3,padx =5, pady =5)
        pal_char_frame=LabelFrame(pal_frame, text="En charge/décharge")
        pal_char_frame.grid(row=9,column=1,columnspan=3,padx =5, pady =5)
        pal_maint_frame=LabelFrame(pal_frame, text="En maintien")
        pal_maint_frame.grid(row=9,column=5,columnspan=3,padx =5, pady =5)
        
        Label(pos_char_frame, text="Proportionnel").grid(row=1,column=1,padx =5, pady =5)
        Label(pos_char_frame, text="Intégral").grid(row=1,column=2,padx =5, pady =5)
        Label(pos_char_frame, text="Dérivé").grid(row=1,column=3,padx =5, pady =5)
        Label(pos_char_frame, text="Charge").grid(row=2,column=0,padx =5, pady =5)
        Label(pos_char_frame, text="Decharge").grid(row=3,column=0,padx =5, pady =5)
        
        Label(pree_char_frame, text="Proportionnel").grid(row=4,column=1,padx =5, pady =5)
        Label(pree_char_frame, text="Intégral").grid(row=4,column=2,padx =5, pady =5)
        Label(pree_char_frame, text="Dérivé").grid(row=4,column=3,padx =5, pady =5)
        Label(pree_char_frame, text="Charge").grid(row=5,column=0,padx =5, pady =5)
        Label(pree_char_frame, text="Decharge").grid(row=6,column=0,padx =5, pady =5)
        
        Label(rup_char_frame, text="Proportionnel").grid(row=6,column=1,padx =5, pady =5)
        Label(rup_char_frame, text="Intégral").grid(row=6,column=2,padx =5, pady =5)
        Label(rup_char_frame, text="Dérivé").grid(row=6,column=3,padx =5, pady =5)
        Label(rup_char_frame, text="Charge").grid(row=7,column=0,padx =5, pady =5)
        Label(rup_char_frame, text="Decharge").grid(row=8,column=0,padx =5, pady =5)
        
        Label(fat_char_frame, text="Proportionnel").grid(row=8,column=1,padx =5, pady =5)
        Label(fat_char_frame, text="Intégral").grid(row=8,column=2,padx =5, pady =5)
        Label(fat_char_frame, text="Dérivé").grid(row=8,column=3,padx =5, pady =5)
        Label(fat_char_frame, text="Charge").grid(row=9,column=0,padx =5, pady =5)
        Label(fat_char_frame, text="Decharge").grid(row=10,column=0,padx =5, pady =5)
        
        Label(pal_char_frame, text="Proportionnel").grid(row=10,column=1,padx =5, pady =5)
        Label(pal_char_frame, text="Intégral").grid(row=10,column=2,padx =5, pady =5)
        Label(pal_char_frame, text="Dérivé").grid(row=10,column=3,padx =5, pady =5)
        Label(pal_char_frame, text="Charge").grid(row=11,column=0,padx =5, pady =5)
        Label(pal_char_frame, text="Decharge").grid(row=12,column=0,padx =5, pady =5)
        
        Entry(pos_char_frame, textvariable=P_char_pos, width=10).grid(row=2,column=1,padx =5, pady =5)
        Entry(pos_char_frame, textvariable=I_char_pos, width=10).grid(row=2,column=2,padx =5, pady =5)
        Entry(pos_char_frame, textvariable=D_char_pos, width=10).grid(row=2,column=3,padx =5, pady =5)
        
        Entry(pree_char_frame, textvariable=P_char_pree, width=10).grid(row=5,column=1,padx =5, pady =5)
        Entry(pree_char_frame, textvariable=I_char_pree, width=10).grid(row=5,column=2,padx =5, pady =5)
        Entry(pree_char_frame, textvariable=D_char_pree, width=10).grid(row=5,column=3,padx =5, pady =5)
        
        Entry(rup_char_frame, textvariable=P_char_rup, width=10).grid(row=7,column=1,padx =5, pady =5)
        Entry(rup_char_frame, textvariable=I_char_rup, width=10).grid(row=7,column=2,padx =5, pady =5)
        Entry(rup_char_frame, textvariable=D_char_rup, width=10).grid(row=7,column=3,padx =5, pady =5)
        
        Entry(fat_char_frame, textvariable=P_char_fat, width=10).grid(row=9,column=1,padx =5, pady =5)
        Entry(fat_char_frame, textvariable=I_char_fat, width=10).grid(row=9,column=2,padx =5, pady =5)
        Entry(fat_char_frame, textvariable=D_char_fat, width=10).grid(row=9,column=3,padx =5, pady =5)
        
        Entry(pal_char_frame, textvariable=P_char_pal, width=10).grid(row=11,column=1,padx =5, pady =5)
        Entry(pal_char_frame, textvariable=I_char_pal, width=10).grid(row=11,column=2,padx =5, pady =5)
        Entry(pal_char_frame, textvariable=D_char_pal, width=10).grid(row=11,column=3,padx =5, pady =5)
        
        Entry(pos_char_frame, textvariable=P_pos_char_dech, width=10).grid(row=3,column=1,padx =5, pady =5)
        Entry(pos_char_frame, textvariable=I_pos_char_dech, width=10).grid(row=3,column=2,padx =5, pady =5)
        Entry(pos_char_frame, textvariable=D_pos_char_dech, width=10).grid(row=3,column=3,padx =5, pady =5)
        
        Entry(pree_char_frame, textvariable=P_pree_char_dech, width=10).grid(row=6,column=1,padx =5, pady =5)
        Entry(pree_char_frame, textvariable=I_pree_char_dech, width=10).grid(row=6,column=2,padx =5, pady =5)
        Entry(pree_char_frame, textvariable=D_pree_char_dech, width=10).grid(row=6,column=3,padx =5, pady =5)
        
        Entry(rup_char_frame, textvariable=P_rup_char_dech, width=10).grid(row=8,column=1,padx =5, pady =5)
        Entry(rup_char_frame, textvariable=I_rup_char_dech, width=10).grid(row=8,column=2,padx =5, pady =5)
        Entry(rup_char_frame, textvariable=D_rup_char_dech, width=10).grid(row=8,column=3,padx =5, pady =5)
        
        Entry(fat_char_frame, textvariable=P_fat_char_dech, width=10).grid(row=10,column=1,padx =5, pady =5)
        Entry(fat_char_frame, textvariable=I_fat_char_dech, width=10).grid(row=10,column=2,padx =5, pady =5)
        Entry(fat_char_frame, textvariable=D_fat_char_dech, width=10).grid(row=10,column=3,padx =5, pady =5)
        
        Entry(pal_char_frame, textvariable=P_pal_char_dech, width=10).grid(row=12,column=1,padx =5, pady =5)
        Entry(pal_char_frame, textvariable=I_pal_char_dech, width=10).grid(row=12,column=2,padx =5, pady =5)
        Entry(pal_char_frame, textvariable=D_pal_char_dech, width=10).grid(row=12,column=3,padx =5, pady =5)
        
        #########################################maintien#####################################################
        
        Label(pos_maint_frame, text="Proportionnel").grid(row=1,column=5,padx =5, pady =5)
        Label(pos_maint_frame, text="Intégral").grid(row=1,column=6,padx =5, pady =5)
        Label(pos_maint_frame, text="Dérivé").grid(row=1,column=7,padx =5, pady =5)
        
        Label(pree_maint_frame, text="Proportionnel").grid(row=4,column=5,padx =5, pady =5)
        Label(pree_maint_frame, text="Intégral").grid(row=4,column=6,padx =5, pady =5)
        Label(pree_maint_frame, text="Dérivé").grid(row=4,column=7,padx =5, pady =5)
        
        Label(rup_maint_frame, text="Proportionnel").grid(row=6,column=5,padx =5, pady =5)
        Label(rup_maint_frame, text="Intégral").grid(row=6,column=6,padx =5, pady =5)
        Label(rup_maint_frame, text="Dérivé").grid(row=6,column=7,padx =5, pady =5)
        
        Label(fat_maint_frame, text="Proportionnel").grid(row=8,column=5,padx =5, pady =5)
        Label(fat_maint_frame, text="Intégral").grid(row=8,column=6,padx =5, pady =5)
        Label(fat_maint_frame, text="Dérivé").grid(row=8,column=7,padx =5, pady =5)
        
        Label(pal_maint_frame, text="Proportionnel").grid(row=10,column=5,padx =5, pady =5)
        Label(pal_maint_frame, text="Intégral").grid(row=10,column=6,padx =5, pady =5)
        Label(pal_maint_frame, text="Dérivé").grid(row=10,column=7,padx =5, pady =5)
        
        Entry(pos_maint_frame, textvariable=P_maint_pos, width=10).grid(row=2,column=5,padx =5, pady =5)
        Entry(pos_maint_frame, textvariable=I_maint_pos, width=10).grid(row=2,column=6,padx =5, pady =5)
        Entry(pos_maint_frame, textvariable=D_maint_pos, width=10).grid(row=2,column=7,padx =5, pady =5)
        
        Entry(pree_maint_frame, textvariable=P_maint_pree, width=10).grid(row=5,column=5,padx =5, pady =5)
        Entry(pree_maint_frame, textvariable=I_maint_pree, width=10).grid(row=5,column=6,padx =5, pady =5)
        Entry(pree_maint_frame, textvariable=D_maint_pree, width=10).grid(row=5,column=7,padx =5, pady =5)
        
        Entry(rup_maint_frame, textvariable=P_maint_rup, width=10).grid(row=7,column=5,padx =5, pady =5)
        Entry(rup_maint_frame, textvariable=I_maint_rup, width=10).grid(row=7,column=6,padx =5, pady =5)
        Entry(rup_maint_frame, textvariable=D_maint_rup, width=10).grid(row=7,column=7,padx =5, pady =5)
        
        Entry(fat_maint_frame, textvariable=P_maint_fat, width=10).grid(row=9,column=5,padx =5, pady =5)
        Entry(fat_maint_frame, textvariable=I_maint_fat, width=10).grid(row=9,column=6,padx =5, pady =5)
        Entry(fat_maint_frame, textvariable=D_maint_fat, width=10).grid(row=9,column=7,padx =5, pady =5)
        
        Entry(pal_maint_frame, textvariable=P_maint_pal, width=10).grid(row=11,column=5,padx =5, pady =5)
        Entry(pal_maint_frame, textvariable=I_maint_pal, width=10).grid(row=11,column=6,padx =5, pady =5)
        Entry(pal_maint_frame, textvariable=D_maint_pal, width=10).grid(row=11,column=7,padx =5, pady =5)
        
        Entry(pos_maint_frame, textvariable=P_pos_maint_dech, width=10).grid(row=3,column=5,padx =5, pady =5)
        Entry(pos_maint_frame, textvariable=I_pos_maint_dech, width=10).grid(row=3,column=6,padx =5, pady =5)
        Entry(pos_maint_frame, textvariable=D_pos_maint_dech, width=10).grid(row=3,column=7,padx =5, pady =5)
        
        Entry(pree_maint_frame, textvariable=P_pree_maint_dech, width=10).grid(row=6,column=5,padx =5, pady =5)
        Entry(pree_maint_frame, textvariable=I_pree_maint_dech, width=10).grid(row=6,column=6,padx =5, pady =5)
        Entry(pree_maint_frame, textvariable=D_pree_maint_dech, width=10).grid(row=6,column=7,padx =5, pady =5)
        
        Entry(rup_maint_frame, textvariable=P_rup_maint_dech, width=10).grid(row=8,column=5,padx =5, pady =5)
        Entry(rup_maint_frame, textvariable=I_rup_maint_dech, width=10).grid(row=8,column=6,padx =5, pady =5)
        Entry(rup_maint_frame, textvariable=D_rup_maint_dech, width=10).grid(row=8,column=7,padx =5, pady =5)
        
        Entry(fat_maint_frame, textvariable=P_fat_maint_dech, width=10).grid(row=10,column=5,padx =5, pady =5)
        Entry(fat_maint_frame, textvariable=I_fat_maint_dech, width=10).grid(row=10,column=6,padx =5, pady =5)
        Entry(fat_maint_frame, textvariable=D_fat_maint_dech, width=10).grid(row=10,column=7,padx =5, pady =5)
        
        Entry(pal_maint_frame, textvariable=P_pal_maint_dech, width=10).grid(row=12,column=5,padx =5, pady =5)
        Entry(pal_maint_frame, textvariable=I_pal_maint_dech, width=10).grid(row=12,column=6,padx =5, pady =5)
        Entry(pal_maint_frame, textvariable=D_pal_maint_dech, width=10).grid(row=12,column=7,padx =5, pady =5)
        
        retour_btn=Button(fen_pid, text='Retour',command=fen_pid.destroy)
        suivant_btn=Button(fen_pid, text='Enregistrer',command=pid_suivant)
        reinit_btn=Button(fen_pid, text='Réinitialiser',command=reinit_val_fct)
        
        retour_btn.grid(row=13,column=1,padx =5, pady =5)
        suivant_btn.grid(row=13,column=3,padx =5, pady =5)
        reinit_btn.grid(row=13,column=2,padx =5, pady =5)
        
    def reinitialiser ():
        ###fonction de réinitialisation de la consigne et des valeurs utilisé lors de l'animation
        global timer 
        
        start_var.set(0)
        choix_enregistrer.set(0)
        timer=None
        difference2.set(0)
        mini.set(2000)
        maxi.set(-10000)
        maxi_charge.set(-10000)
        consigne_choix.set(0) 
        consigne_val.set(0) 
        temps_palier.set(0)
        compteur_palier.set(0)
        memoire_consigne.set(0)
        pente_val.set(0)
        limite_val.set(0)
        temps_bis.set(0)
        decharge.set(0)
        init.set(0)
        temps1.set(0)
        temps2.set(0)
        difference_palier.set(0)
        limite_basse.set(0)
        nb_cycles.set(0)
        compteur_cycles.set(0)
        rab.set(0)
        temps_voulu.set('00:00')
        temps_palier_final.set('00:00')
        pos_var.set(0)
        prec.set(0)
        sensi_charge_val=DoubleVar()
        sensi_charge_val.set(float(lecture_sensi_charge()))
        sensi_decharge_val=DoubleVar()
        sensi_decharge_val.set(float(lecture_sensi_decharge()))
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
        pid1.reset()
        pid2.reset()
        pid3.reset()
        pid4.reset()
        pid5.reset()
        pid6.reset()
        pid7.reset()
        pid8.reset()
        pid9.reset()
        pid10.reset()
        pid11.reset()
        pid12.reset()
        pid13.reset()
        pid14.reset()
        pid15.reset()
        pid16.reset()
        pid17.reset()
        pid18.reset()
        pid19.reset()
        pid20.reset()
        
        desactive_bouton(start_btn)
        active_bouton(stop_btn)
        desactive_bouton(pause_btn)
        
        menu1.entryconfigure(1, state=DISABLED)
        menu1.entryconfigure(2, state=DISABLED)
        menu1.entryconfigure(3, state=DISABLED)
        
        showinfo('Info','Consigne réinitialisée !')
        return 0
    
    def secondaire_fct():
        ###fenêtre d'affichage d'une fenêtre d'affichage de la consigne secondaire.
        def anim_second():
            data=recup_data()
            valeur_en_cours=etalonnage(data[6]*2)
            canvas_second.delete('valeur_charge_actuelle')
            canvas_second.create_text(500,500,text=round(valeur_en_cours,2),font=('Arial','200'),tags='valeur_charge_actuelle')
            canvas_second.after(500,anim_second)
            
        fen_secondaire=Toplevel(fenetre_graph_retd)
        
        canvas_second=Canvas(fen_secondaire,height=1000,width=1000,bg='#ffffff')
        canvas_second.grid()
        anim_second()
        
    def chemin_fct():
    ###fenêtre de choix du chemin des fonctions
        
        def chemin_suivant() :
            ###fonction d'écriture des sensibilité et de mise à jour des PID
            
            fichier=open('chemin_enre.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+chemin_enre.get()+'\n')
            fichier.close()
            fichier=open('chemin_manuel.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+chemin_aide.get()+'\n')
            fichier.close()
            fichier=open('nom_manuel.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+nom_manuel.get()+'\n')
            fichier.close()
            fen_chem.destroy()
            
            return 0

        fen_chem=Toplevel(fenetre_graph_retd)
        
        fen_chem.clipboard_append(' ')
        fen_chem.clipboard_get()  # récupère le contenu du presse-papier4
        
        chemin_enre=StringVar()
        chemin_aide=StringVar()
        nom_manuel=StringVar()
        chemin_enre.set(lecture_chemin('chemin_enre.txt')[:len(lecture_chemin('chemin_enre.txt'))-1])
        chemin_aide.set(lecture_chemin('chemin_manuel.txt')[:len(lecture_chemin('chemin_manuel.txt'))-1])
        nom_manuel.set(lecture_chemin('nom_manuel.txt')[:len(lecture_chemin('nom_manuel.txt'))-1])
        
        
        label_enre=Label(fen_chem, text="Choisissez le chemin des documents enregistrés")
        enre_entree = Entry(fen_chem, textvariable=chemin_enre, width=100)
        
        label_aide=Label(fen_chem, text="Choisissez le chemin du manuel d'aide")
        aide_entree = Entry(fen_chem, textvariable=chemin_aide, width=100)
        
        label_nom_manuel=Label(fen_chem, text="Choisissez le nom du manuel d'aide (ne pas oublier le .docx ou le .pdf)")
        manuel_entree = Entry(fen_chem, textvariable=nom_manuel, width=100)
      
        retour_btn=Button(fen_chem, text='Retour',command=fen_chem.destroy)
        suivant_btn=Button(fen_chem, text='Enregistrer',command=chemin_suivant)
        
        label_enre.grid(row=1,column=0,padx =10, pady =10)
        enre_entree.grid(row=1,column=1,padx =10, pady =10)
        label_aide.grid(row=2,column=0,padx =10, pady =10)
        aide_entree.grid(row=2,column=1,padx =10, pady =10)
        label_nom_manuel.grid(row=3,column=0,padx =10, pady =10)
        manuel_entree.grid(row=3,column=1,padx =10, pady =10)
        retour_btn.grid(row=4,column=0,padx =10, pady =10)
        suivant_btn.grid(row=4,column=1,padx =10, pady =10)
        
    def modif_mdp_fct():
        ###fenêtre de modification du mot de passe
        def modif_mdp_suite():
            fichier=open('mdp_liste.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+mdp_val.get()+'\n')
            fichier.close()
            fen_mdp.destroy()
            return 0
        
        fen_mdp=Toplevel(fenetre_graph_retd)
        
        fen_mdp.clipboard_append(' ')
        fen_mdp.clipboard_get()  # récupère le contenu du presse-papier4
        
        mdp_val=StringVar()
        mdp_val.set(lecture_chemin('mdp_liste.txt')[:len(lecture_chemin('mdp_liste.txt'))-1])
        
        label_mdp=Label(fen_mdp, text="Choisissez le nouveau mot de passe")
        mdp_entree = Entry(fen_mdp, textvariable=mdp_val, width=30)
      
        retour_btn=Button(fen_mdp, text='Retour',command=fen_mdp.destroy)
        suivant_btn=Button(fen_mdp, text='Enregistrer',command=modif_mdp_suite)
        
        label_mdp.grid(row=1,column=0,padx =10, pady =10)
        mdp_entree.grid(row=1,column=1,padx =10, pady =10)
        retour_btn.grid(row=4,column=0,padx =10, pady =10)
        suivant_btn.grid(row=4,column=1,padx =10, pady =10)
        
    def modif_etalonnage_fct():
        ###fenêtre de modification du mot de passe
        def modif_etalonnage_suite():
            fichier=open('etal_a.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+etal_a_val.get())
            fichier.close()
            fichier=open('etal_b.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+etal_b_val.get())
            fichier.close()
            fichier=open('etal_c.txt','a')
            fichier.write(str(datetime.datetime.now())[:11]+etal_c_val.get())
            fichier.close()
            fen_etal.destroy()
            return 0
        
        fen_etal=Toplevel(fenetre_graph_retd)
        
        fen_etal.clipboard_append(' ')
        fen_etal.clipboard_get()  # récupère le contenu du presse-papier4
        
        etal_a_val=StringVar()
        etal_a_val.set(lecture_chemin('etal_a.txt')[:len(lecture_chemin('etal_a.txt'))])
        etal_b_val=StringVar()
        etal_b_val.set(lecture_chemin('etal_b.txt')[:len(lecture_chemin('etal_b.txt'))])
        etal_c_val=StringVar()
        etal_c_val.set(lecture_chemin('etal_c.txt')[:len(lecture_chemin('etal_c.txt'))])
        
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
    
##################################################################################################################################
       
    global liste 
    
    entrees=entree_RetD()
    print(entrees)
    
    if lock==3:
        fct_depart()
        return 0
    
    for i in range(len(entrees)):
        if entrees[i]=='':
            print(i)
            return 0
        
    output(0,1)
    output(0,2)
    
    fenetre_graph_retd = tix.Tk(None,None,className='Fenetre graphique R&D')
    
    fenetre_graph_retd.clipboard_append(' ')
    fenetre_graph_retd.clipboard_get()  # récupère le contenu du presse-papier

        
    liste_memoire=[]
    liste=[]
    
    liste_charge=[]
    chemin_enre=StringVar()
    start_var=IntVar()
    utile=DoubleVar()
    utile.set(entrees[10])
    pourc_var=DoubleVar()
    episse=IntVar()
    episse.set(entrees[8])
    num_ref=DoubleVar()
    num_ref.set(entrees[6])
    choix_enregistrer=IntVar()
    choix_enregistrer.set(0)
    rupture=DoubleVar()
    rupture.set(float(entrees[5]))
    data=recup_data()
    compteur=IntVar()
    compteur_pointeur=IntVar()
    compteur_pointeur.set(1380/2)
    timer=None
    temps=IntVar()
    liste=[]
    difference=DoubleVar()
    difference2=DoubleVar()
    maxi=DoubleVar()
    mini=DoubleVar()
    mini.set(2000)
    maxi.set(-10000)
    maxi_charge=DoubleVar()
    maxi_charge.set(-10000)
    consigne_choix = IntVar() 
    consigne_val = DoubleVar() 
    temps_palier=DoubleVar()
    compteur_palier=IntVar()
    memoire_consigne=DoubleVar()
    pente_val=DoubleVar()
    limite_val=DoubleVar()
    roulette=IntVar()
    pas_telecommande=DoubleVar()
    pas_telecommande.set(1)
    active_telec=IntVar()
    societe=StringVar()
    adresse1=StringVar()
    adresse2=StringVar()
    adresse3=StringVar()
    contact1=StringVar()
    contact2=StringVar()
    contact3=StringVar()
    commande=StringVar()
    projet=StringVar()
    reference=StringVar()
    certif_val=IntVar()
    banc=StringVar()
    banc.set("Banc de traction C10TL27")
    nom_prenom=StringVar()
    nom_prenom.set(" ".join([entrees[1],entrees[2]]))
    materiel=StringVar()
    materiel.set(entrees[3])
    epreuve=StringVar()
    reference=StringVar()
    choix_asserv_val=IntVar()
    temps_restant_val=StringVar()
    temps_bis=IntVar()
    decharge=IntVar()
    init=IntVar()
    temps1=DoubleVar()
    temps2=DoubleVar()
    difference_palier=DoubleVar()
    longueur_banc=IntVar()
    normes=StringVar()
    validite=StringVar()
    limite_basse=DoubleVar()
    nb_cycles=IntVar()
    compteur_cycles=IntVar()
    rab=DoubleVar()
    temps_voulu = StringVar()
    temps_voulu.set('00:00')
    prec=IntVar()
    switch=StringVar()
    switch.set('off')
    sensi_charge_val=DoubleVar()
    sensi_charge_val.set(float(lecture_sensi_charge()))
    sensi_decharge_val=DoubleVar()
    sensi_decharge_val.set(float(lecture_sensi_decharge()))
    temps_palier_final=StringVar()
    temps_palier_final.set('00:00')
    pos_var=DoubleVar()
    
    P_char_pos=DoubleVar()
    I_char_pos=DoubleVar()
    D_char_pos=DoubleVar()
    P_char_pree=DoubleVar()
    I_char_pree=DoubleVar()
    D_char_pree=DoubleVar()
    P_char_rup=DoubleVar()
    I_char_rup=DoubleVar()
    D_char_rup=DoubleVar()
    P_char_fat=DoubleVar()
    I_char_fat=DoubleVar()
    D_char_fat=DoubleVar()
    P_char_pal=DoubleVar()
    I_char_pal=DoubleVar()
    D_char_pal=DoubleVar()
    P_pos_char_dech=DoubleVar()
    I_pos_char_dech=DoubleVar()
    D_pos_char_dech=DoubleVar()
    P_pree_char_dech=DoubleVar()
    I_pree_char_dech=DoubleVar()
    D_pree_char_dech=DoubleVar()
    P_rup_char_dech=DoubleVar()
    I_rup_char_dech=DoubleVar()
    D_rup_char_dech=DoubleVar()
    P_fat_char_dech=DoubleVar()
    I_fat_char_dech=DoubleVar()
    D_fat_char_dech=DoubleVar()
    P_pal_char_dech=DoubleVar()
    I_pal_char_dech=DoubleVar()
    D_pal_char_dech=DoubleVar()
    
    P_maint_pos=DoubleVar()
    I_maint_pos=DoubleVar()
    D_maint_pos=DoubleVar()
    P_maint_pree=DoubleVar()
    I_maint_pree=DoubleVar()
    D_maint_pree=DoubleVar()
    P_maint_rup=DoubleVar()
    I_maint_rup=DoubleVar()
    D_maint_rup=DoubleVar()
    P_maint_fat=DoubleVar()
    I_maint_fat=DoubleVar()
    D_maint_fat=DoubleVar()
    P_maint_pal=DoubleVar()
    I_maint_pal=DoubleVar()
    D_maint_pal=DoubleVar()
    P_pos_maint_dech=DoubleVar()
    I_pos_maint_dech=DoubleVar()
    D_pos_maint_dech=DoubleVar()
    P_pree_maint_dech=DoubleVar()
    I_pree_maint_dech=DoubleVar()
    D_pree_maint_dech=DoubleVar()
    P_rup_maint_dech=DoubleVar()
    I_rup_maint_dech=DoubleVar()
    D_rup_maint_dech=DoubleVar()
    P_fat_maint_dech=DoubleVar()
    I_fat_maint_dech=DoubleVar()
    D_fat_maint_dech=DoubleVar()
    P_pal_maint_dech=DoubleVar()
    I_pal_maint_dech=DoubleVar()
    D_pal_maint_dech=DoubleVar()
    
    chemin=''
    chemint=''
    chemin_final=chemin+chemint
    
    P_char_pos.set(lecture_coef(chemin_final+'Pos_char_P.txt'))
    I_char_pos.set(lecture_coef(chemin_final+'Pos_char_I.txt'))
    D_char_pos.set(lecture_coef(chemin_final+'Pos_char_D.txt'))
    P_char_pree.set(lecture_coef(chemin_final+'Pree_char_P.txt'))
    I_char_pree.set(lecture_coef(chemin_final+'Pree_char_I.txt'))
    D_char_pree.set(lecture_coef(chemin_final+'Pree_char_D.txt'))
    P_char_rup.set(lecture_coef(chemin_final+'Rup_char_P.txt'))
    I_char_rup.set(lecture_coef(chemin_final+'Rup_char_I.txt'))
    D_char_rup.set(lecture_coef(chemin_final+'Rup_char_D.txt'))
    P_char_fat.set(lecture_coef(chemin_final+'Fat_char_P.txt'))
    I_char_fat.set(lecture_coef(chemin_final+'Fat_char_I.txt'))
    D_char_fat.set(lecture_coef(chemin_final+'Fat_char_D.txt'))
    P_char_pal.set(lecture_coef(chemin_final+'Pal_char_P.txt'))
    I_char_pal.set(lecture_coef(chemin_final+'Pal_char_I.txt'))
    D_char_pal.set(lecture_coef(chemin_final+'Pal_char_D.txt'))
    P_pos_char_dech.set(lecture_coef(chemin_final+'Pos_P_char_dech.txt'))
    I_pos_char_dech.set(lecture_coef(chemin_final+'Pos_I_char_dech.txt'))
    D_pos_char_dech.set(lecture_coef(chemin_final+'Pos_D_char_dech.txt'))
    P_pree_char_dech.set(lecture_coef(chemin_final+'Pree_P_char_dech.txt'))
    I_pree_char_dech.set(lecture_coef(chemin_final+'Pree_I_char_dech.txt'))
    D_pree_char_dech.set(lecture_coef(chemin_final+'Pree_D_char_dech.txt'))
    P_rup_char_dech.set(lecture_coef(chemin_final+'Rup_P_char_dech.txt'))
    I_rup_char_dech.set(lecture_coef(chemin_final+'Rup_I_char_dech.txt'))
    D_rup_char_dech.set(lecture_coef(chemin_final+'Rup_D_char_dech.txt'))
    P_fat_char_dech.set(lecture_coef(chemin_final+'Fat_P_char_dech.txt'))
    I_fat_char_dech.set(lecture_coef(chemin_final+'Fat_I_char_dech.txt'))
    D_fat_char_dech.set(lecture_coef(chemin_final+'Fat_D_char_dech.txt'))
    P_pal_char_dech.set(lecture_coef(chemin_final+'Pal_P_char_dech.txt'))
    I_pal_char_dech.set(lecture_coef(chemin_final+'Pal_I_char_dech.txt'))
    D_pal_char_dech.set(lecture_coef(chemin_final+'Pal_D_char_dech.txt'))
    
    P_maint_pos.set(lecture_coef(chemin_final+'Pos_maint_P.txt'))
    I_maint_pos.set(lecture_coef(chemin_final+'Pos_maint_I.txt'))
    D_maint_pos.set(lecture_coef(chemin_final+'Pos_maint_D.txt'))
    P_maint_pree.set(lecture_coef(chemin_final+'Pree_maint_P.txt'))
    I_maint_pree.set(lecture_coef(chemin_final+'Pree_maint_I.txt'))
    D_maint_pree.set(lecture_coef(chemin_final+'Pree_maint_D.txt'))
    P_maint_rup.set(lecture_coef(chemin_final+'Rup_maint_P.txt'))
    I_maint_rup.set(lecture_coef(chemin_final+'Rup_maint_I.txt'))
    D_maint_rup.set(lecture_coef(chemin_final+'Rup_maint_D.txt'))
    P_maint_fat.set(lecture_coef(chemin_final+'Fat_maint_P.txt'))
    I_maint_fat.set(lecture_coef(chemin_final+'Fat_maint_I.txt'))
    D_maint_fat.set(lecture_coef(chemin_final+'Fat_maint_D.txt'))
    P_maint_pal.set(lecture_coef(chemin_final+'Pal_maint_P.txt'))
    I_maint_pal.set(lecture_coef(chemin_final+'Pal_maint_I.txt'))
    D_maint_pal.set(lecture_coef(chemin_final+'Pal_maint_D.txt'))
    P_pos_maint_dech.set(lecture_coef(chemin_final+'Pos_P_maint_dech.txt'))
    I_pos_maint_dech.set(lecture_coef(chemin_final+'Pos_I_maint_dech.txt'))
    D_pos_maint_dech.set(lecture_coef(chemin_final+'Pos_D_maint_dech.txt'))
    P_pree_maint_dech.set(lecture_coef(chemin_final+'Pree_P_maint_dech.txt'))
    I_pree_maint_dech.set(lecture_coef(chemin_final+'Pree_I_maint_dech.txt'))
    D_pree_maint_dech.set(lecture_coef(chemin_final+'Pree_D_maint_dech.txt'))
    P_rup_maint_dech.set(lecture_coef(chemin_final+'Rup_P_maint_dech.txt'))
    I_rup_maint_dech.set(lecture_coef(chemin_final+'Rup_I_maint_dech.txt'))
    D_rup_maint_dech.set(lecture_coef(chemin_final+'Rup_D_maint_dech.txt'))
    P_fat_maint_dech.set(lecture_coef(chemin_final+'Fat_P_maint_dech.txt'))
    I_fat_maint_dech.set(lecture_coef(chemin_final+'Fat_I_maint_dech.txt'))
    D_fat_maint_dech.set(lecture_coef(chemin_final+'Fat_D_maint_dech.txt'))
    P_pal_maint_dech.set(lecture_coef(chemin_final+'Pal_P_maint_dech.txt'))
    I_pal_maint_dech.set(lecture_coef(chemin_final+'Pal_I_maint_dech.txt'))
    D_pal_maint_dech.set(lecture_coef(chemin_final+'Pal_D_maint_dech.txt'))
    
    if entrees[4]=='20m':
        longueur_banc.set(20)
    if entrees[4]=='22m':
        longueur_banc.set(16.6)
    if entrees[4]=='24m':
        longueur_banc.set(14)
    if entrees[4]=='26m':
        longueur_banc.set(12)
    if entrees[4]=='9m':
        longueur_banc.set(10)
    
#######################################################################################en charge
##########################################PID position#########################
    
    pid1 = PID(P_char_pos.get(),I_char_pos.get(),D_char_pos.get() ,setpoint=0)
    pid1.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
    
    pid2 = PID(P_pos_char_dech.get(),I_pos_char_dech.get(),D_pos_char_dech.get(), setpoint=0)
    pid2.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
    
##########################################PID rupture#########################
    
    pid3 = PID(P_char_rup.get(),I_char_rup.get(),D_char_rup.get(), setpoint=0)
    pid3.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
    
    pid4 = PID(P_rup_char_dech.get(),I_rup_char_dech.get(),D_rup_char_dech.get(), setpoint=0)
    pid4.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
    
##########################################PID préétirage######################
    
    pid5 = PID(P_char_pree.get(),I_char_pree.get(),D_char_pree.get(), setpoint=0)
    pid5.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
    
    pid6 = PID(P_pree_char_dech.get(),I_pree_char_dech.get(),D_pree_char_dech.get(), setpoint=0)
    pid6.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
    
##########################################PID fatigue######################### 
    
    pid7 = PID(P_char_fat.get(),I_char_fat.get(),D_char_fat.get(), setpoint=0)
    pid7.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse

    pid8 = PID(P_fat_char_dech.get(),I_fat_char_dech.get(),D_fat_char_dech.get(), setpoint=0)
    pid8.output_limits = (-5, sensi_decharge_val.get())
    
##########################################PID palier######################### 
    
    pid9 = PID(P_char_pal.get(),I_char_pal.get(),D_char_pal.get(), setpoint=0)
    pid9.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse

    pid10 = PID(P_pal_char_dech.get(),I_pal_char_dech.get(),D_pal_char_dech.get(), setpoint=0)
    pid10.output_limits = (-5, sensi_decharge_val.get())
    
#######################################################################################en maintien
##########################################PID position#########################
    
    pid11 = PID(P_maint_pos.get(),I_maint_pos.get(),D_maint_pos.get() ,setpoint=0)
    pid11.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
    
    pid12 = PID(P_pos_maint_dech.get(),I_pos_maint_dech.get(),D_pos_maint_dech.get(), setpoint=0)
    pid12.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
    
##########################################PID rupture#########################
    
    pid13 = PID(P_maint_rup.get(),I_maint_rup.get(),D_maint_rup.get(), setpoint=0)
    pid13.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
    
    pid14 = PID(P_rup_maint_dech.get(),I_rup_maint_dech.get(),D_rup_maint_dech.get(), setpoint=0)
    pid14.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
    
##########################################PID préétirage######################
    
    pid15 = PID(P_maint_pree.get(),I_maint_pree.get(),D_maint_pree.get(), setpoint=0)
    pid15.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse
    
    pid16 = PID(P_pree_maint_dech.get(),I_pree_maint_dech.get(),D_pree_maint_dech.get(), setpoint=0)
    pid16.output_limits = (-5, sensi_decharge_val.get()) #brider la vitesse
    
##########################################PID fatigue######################### 
    
    pid17 = PID(P_maint_fat.get(),I_maint_fat.get(),D_maint_fat.get(), setpoint=0)
    pid17.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse

    pid18 = PID(P_fat_maint_dech.get(),I_fat_maint_dech.get(),D_fat_maint_dech.get(), setpoint=0)
    pid18.output_limits = (-5, sensi_decharge_val.get())
    
##########################################PID palier######################### 
    
    pid19 = PID(P_maint_pal.get(),I_maint_pal.get(),D_maint_pal.get(), setpoint=0)
    pid19.output_limits = (sensi_charge_val.get(), 5) #brider la vitesse

    pid20 = PID(P_pal_maint_dech.get(),I_pal_maint_dech.get(),D_pal_maint_dech.get(), setpoint=0)
    pid20.output_limits = (-5, sensi_decharge_val.get())
    
    
    nom=crea_nom(1)
    workbook = xlsxwriter.Workbook(nom)
    chartsheet = workbook.add_chartsheet()
    feuille = workbook.add_worksheet()
    date_format = workbook.add_format({'num_format': 'hh:mm:sssss'})

    nom_csv=crea_nom(2)
    fichier=open(nom_csv,'w')
    
    nom_csv2=crea_nom(3)
    fichier2=open(nom_csv2,'w')
    
    nom_csv3=crea_nom(4)
    fichier3=open(nom_csv3,'w')
    
    init_xlsx()
    init_csv(entrees[0],entrees[1],entrees[2],entrees[3],entrees[4])
    
    canvas=Canvas(fenetre_graph_retd,height=700,width=1600,bg='#ffffff')
    
    pointeur7=canvas.create_line(1430,600-(capteur_fct(data[7])*10),1430,600-(capteur_fct(data[7])*10),fill='red',tags="pointeur7")
    pointeur6=canvas.create_line(1430,600-(etalonnage(data[6])*10),1430,600-(etalonnage(data[6])*10),fill='green',tags="pointeur6")
    pointeur_consigne=canvas.create_line(1430,600,1430,600,fill='blue',tags="consigne")
    
    canvas.bind("<MouseWheel>", do_zoom)
    canvas.bind('<ButtonPress-1>', lambda event: canvas.scan_mark(event.x, event.y))
    canvas.bind("<B1-Motion>", lambda event: canvas.scan_dragto(event.x, event.y, gain=1))
    cadrillage()
    
    val_actuelle_label=LabelFrame( fenetre_graph_retd, text = 'Valeur position (mm)', fg='red')
    mini_label=LabelFrame( fenetre_graph_retd, text = 'Valeur minimale', fg='red')
    maxi_label=LabelFrame( fenetre_graph_retd, text = 'Valeur maximale', fg='red')
    val_actuelle_charge_label=LabelFrame( fenetre_graph_retd, text = 'Valeur charge (t)', fg='green')
    maxi_charge_label=LabelFrame( fenetre_graph_retd, text = 'Valeur maximale', fg='green')
    consigne_label=LabelFrame( fenetre_graph_retd, text = 'Consigne', fg='blue')
    temps_total_label=LabelFrame( fenetre_graph_retd, text = 'Temps total')
    temps_fin_label=LabelFrame( fenetre_graph_retd, text = 'Temps de fonctionnement (en min)')
    zone_com_label=LabelFrame( fenetre_graph_retd, text = 'Commentaires')
    temps_restant_label=LabelFrame( fenetre_graph_retd, text = 'Temps restant')
    telecommande=LabelFrame( fenetre_graph_retd, text = 'Commande charge')
    mode_manuel=LabelFrame(fenetre_graph_retd, text='Mode Manuel')
    pas_scale=Scale(telecommande,orient='horizontal',from_=0, to=5,resolution=0.1,variable=pas_telecommande,label='Vitesse')
    rappel_label=LabelFrame(fenetre_graph_retd, text='Consigne')
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
                         
    zone_temps_restant=Canvas(temps_restant_label,height=20,width=100,bg='#ffffff')
    zone_temps_consigne=Canvas(temps_total_label,height=20,width=100,bg='#ffffff') 
    zone_valeur=Canvas(val_actuelle_label,height=50,width=150,bg='#ffffff')
    zone_charge_valeur=Canvas(val_actuelle_charge_label,height=150,width=500,bg='#ffffff')
    zone_max=Canvas(maxi_label,height=20,width=100,bg='#ffffff')
    zone_min=Canvas(mini_label,height=20,width=100,bg='#ffffff')               
    zone_charge_max=Canvas(maxi_charge_label,height=20,width=100,bg='#ffffff')
    zone_consigne=Canvas(consigne_label,height=20,width=100,bg='#ffffff') 
                      
    com = StringVar() 
    com.set("None")
    zone_com=Entry( zone_com_label, textvariable= com, width=25)
    
    start_btn=Button(fenetre_graph_retd, text='Start', command=start_fct)
    pause_btn=Button(fenetre_graph_retd, text='Pause', command=do_pause,bg='red')
    stop_btn=Button(fenetre_graph_retd, text='Quitter et enregistrer', command=stop_fct)
    precedent2_btn=Button(fenetre_graph_retd, text='Précédent', command=precedent2_fct)
    mise_a_0_btn=Button(fenetre_graph_retd, text=' Mise à 0 ',command=mise_a_0_fct)
    mise_a_tension_btn=Button(fenetre_graph_retd, text=' Mise à tension ',command=mise_a_tension_fct)
    gauche_btn=Button(telecommande, text='Dech.',command=telec_gauche,repeatdelay=1,repeatinterval=1000000)
    droite_btn=Button(telecommande, text='Charge',command=telec_droite,repeatdelay=1,repeatinterval=1000000)
    off_button = Radiobutton(mode_manuel, text=" Off ", variable=switch,indicatoron=False,value="off",command=color_off)
    on_button = Radiobutton(mode_manuel, text=" On ", variable=switch,indicatoron=False, bg='gray',value="on",command=color_on)
    gauche_btn.bind("<ButtonRelease>", relache)
    droite_btn.bind("<ButtonRelease>", relache)
    consigne_btn=Button(fenetre_graph_retd, text=' ',bg='red',command=choix_asserv_fct)
    enregistrer_btn=Button(fenetre_graph_retd, text=' ', command=choix_enregistrer_fct)
    
    img1 = PhotoImage(file="icone_enregistrer.png") # make sure to add "/" not "\"
    enregistrer_btn.config(image=img1)
    img2 = PhotoImage(file="icone_engrenage.png") # make sure to add "/" not "\"
    consigne_btn.config(image=img2)
    img3 = PhotoImage(file="icone_retour.png") # make sure to add "/" not "\"
    mise_a_0_btn.config(image=img3)
    img4 = PhotoImage(file="icone_charge.png") # make sure to add "/" not "\"
    droite_btn.config(image=img4)
    img5 = PhotoImage(file="icone_decharge.png") # make sure to add "/" not "\"
    gauche_btn.config(image=img5)
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
    
    
    bal = tix.Balloon(fenetre_graph_retd)
    bal.bind_widget(start_btn, msg="Démarrer le test")
    bal.bind_widget(pause_btn, msg="Arrêter le test")
    bal.bind_widget(precedent2_btn, msg="Revenir au menu précédent")
    bal.bind_widget(mise_a_0_btn, msg="Renvoie le chariot à la position 0")
    bal.bind_widget(mise_a_tension_btn, msg="Avance le chariot jusqu'à détection de tension")
    bal.bind_widget(gauche_btn, msg="Relacher")
    bal.bind_widget(droite_btn, msg="Charger")
    bal.bind_widget(off_button, msg="Désactive le mode d'acquisition en manuel")
    bal.bind_widget(on_button, msg="Active l'acquisition en manuel")
    bal.bind_widget(stop_btn, msg="Termine le programme et enregistre les courbes")
    bal.bind_widget(consigne_btn, msg="Paramétrer la consigne")
    bal.bind_widget(enregistrer_btn, msg="Options d'enregistrements")
    
    bal.bind_widget(zone_temps_restant, msg="Temps restant avant la prochaine phase du programme en cours (en hh:mm:ss)")
    bal.bind_widget(zone_temps_consigne, msg="Temps écoulé depuis la dernière phase du programme en cours (en hh:mm:ss)")
    bal.bind_widget(zone_valeur, msg="Déplacement chariot actuel (mm)")
    bal.bind_widget(zone_charge_valeur, msg="Charge actuelle (tonnes)")
    bal.bind_widget(zone_charge_max, msg="Valeur de charge maximale atteinte (tonnes)")
    bal.bind_widget(zone_max, msg="Valeur de position maximale du chariot au lancement du programme (mm)")
    bal.bind_widget(zone_min, msg="Valeur de position minimale du chariot au lancement du programme (mm)")
    bal.bind_widget(zone_com, msg="Entrez ici un commentaire qui sera ajouté au document enregistré")
    bal.bind_widget(zone_consigne, msg="Affiche la consigne en cours")

    canvas.grid(row=4,column=1,columnspan=17)
    val_actuelle_label.grid(row=0,column=7,rowspan=2,padx =5, pady =5)
    val_actuelle_charge_label.grid(row=0,column=1,rowspan=2,padx =5, pady =5)
    zone_valeur.grid(row=0,column=7,rowspan=2,padx =5, pady =5)
    zone_charge_valeur.grid(row=0,column=1,rowspan=2,padx =5, pady =5)
    temps_total_label.grid(row=0,column=11,padx =5, pady =5)
    zone_temps_consigne.grid(row=0,column=11,padx =5, pady =5)
    temps_fin_label.grid(row=0,column=11,padx =5, pady =5)
    temps_restant_label.grid(row=1 ,column=11,padx =5, pady =5)
    zone_temps_restant.grid(row=1,column=11,padx =5, pady =5)
    
    telecommande.grid(row=0,column=16,rowspan=4,padx =5, pady =5)
    pas_scale.grid(row=0,column=16,columnspan=2,padx =5, pady =5)
    
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
    stop_btn.grid(row=2,column=18,padx =5, pady =5)
    consigne_btn.grid(row=1,column=14,padx =5, pady =5)
    enregistrer_btn.grid(row=1,column=15,padx =5, pady =5)
    gauche_btn.grid(row=1,column=16,padx =5, pady =5)
    droite_btn.grid(row=1,column=17,padx =5, pady =5)
    mise_a_0_btn.grid(row=0,column=17,padx =5, pady =5)
    mise_a_tension_btn.grid(row=1,column=17,padx =5, pady =5)
    mode_manuel.grid(row=0,column=18,padx =5, pady =5)
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
    
    desactive_bouton(start_btn)
    active_bouton(stop_btn)
    desactive_bouton(pause_btn)
    
    menubar = Menu(fenetre_graph_retd)

    menu1 = Menu(menubar, tearoff=0)
    
    menu1.add_command(label="Type d'asservissement",command=choix_asserv_fct)
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
    menu3.add_command(label="Ecran secondaire",command=secondaire_fct)
    menubar.add_cascade(label="Créer", menu=menu3)
    
    menu4 = Menu(menubar, tearoff=0)
    menu4.add_command(label="Aide",command=aide_fct)
    if lock==0 :
        menu4.add_command(label="Régler sensibilité PID",command=sensi_page)
        menu4.add_command(label="Régler coefficients PID",command=coef_pid_fct)
        menu4.add_command(label="Modifier les chemins",command=chemin_fct)
        menu4.add_command(label="Modifier le mot de passe",command=modif_mdp_fct)
        menu4.add_command(label="Modifier étalonnage du banc",command=modif_etalonnage_fct)
    menu4.add_separator()
    menu4.add_command(label="Menu précédent",command=precedent2_fct)
    menu4.add_command(label="Quitter",command=stop_fct)
    menubar.add_cascade(label="Autre", menu=menu4)
    
    fenetre_graph_retd.config(menu=menubar)
    
    lecture_a_vide()
    
    fenetre_graph_retd.mainloop()
    
    output(0,1)
    output(0,2)
    if prec.get()==0 :
        enregistrer_fct()
    print("nb de valeur acquises=", compteur_pointeur.get()-(1380/2))
    
fct_depart()






































