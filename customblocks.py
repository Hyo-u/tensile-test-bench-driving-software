
import crappy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.widgets
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import NoReturn, Optional, Tuple
# from matplotlib.widgets import Button


class YBlock(crappy.blocks.Block):

   def __init__(self, cmd_labels = None, out_labels = None, freq = 50):
      super().__init__()
      self.cmd_labels = cmd_labels if cmd_labels is not None else out_labels
      self.out_labels = out_labels
      self.freq = freq
   
   def prepare(self):
      self.output = {}

   def loop(self):
      for link in self.inputs:
         recv_dict = link.recv_last()
         if recv_dict is not None:
            for label in recv_dict:
               self.output[label] = recv_dict[label]
      
      # if self.output == {} :
      #    self.output["sortie_charge_transformee"] = 0.0
      #    self.output["consigne"] = 0.0
      #    self.output["t(s)"] = 0.0
      self.send(self.output)
