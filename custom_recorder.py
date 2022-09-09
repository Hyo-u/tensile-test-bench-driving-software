
import crappy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.widgets
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import NoReturn, Optional, Tuple
# from matplotlib.widgets import Button


class CustomRecorder(crappy.blocks.Recorder):
   """FR : Version qui rajoute nos paramètres au début du fichier.

   EN : Version that adds our parameters at top of the file."""
   def __init__(self, filename, delay = 2, labels = 't(s)', parametres_a_inscrire = {}):
      """Sets the args and initializes the parent class.
      Args:
         filename (:obj:`str`): Path and name of the output file. If the folders
         do not exist, they will be created. If the file already exists, the
         actual file will be named with a trailing number to avoid overriding
         it.
         delay (:obj:`float`, optional): Delay between each write in seconds.
         labels (:obj:`list`, optional): What labels to save. Can be either a
         :obj:`str` to save all labels but this one first, or a :obj:`list` to
         save only these labels.
      """
      crappy.blocks.Recorder.__init__(self, 
                                      filename = filename, 
                                      delay = delay, 
                                      labels = labels)
      self.parametres_a_inscrire = parametres_a_inscrire 

   def begin(self):
      self.last_save = self.t0
      r = self.inputs[0].recv_delay(self.delay)  # To know the actual labels
      if self.labels:
         if not isinstance(self.labels, list):
            if self.labels in r.keys():
               # If one label is specified, place it first and
               # add the others alphabetically
               self.labels = [self.labels]
               for k in sorted(r.keys()):
                  if k not in self.labels:
                     self.labels.append(k)
            else:
               # If not a list but not in labels, forget it and take all the labels
               self.labels = list(sorted(r.keys()))
            # if it is a list, keep it untouched
      else:
         # If we did not give them (False, [] or None):
         self.labels = list(sorted(r.keys()))
      with open(self.filename, 'w') as f:
         for parametre in self.parametres_a_inscrire :      # modified
            f.write(parametre + "\n")                       # modified
         f.write(", ".join(self.labels) + "\n")
      self.save(r)
