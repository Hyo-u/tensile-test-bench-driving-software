# coding: utf-8

import threading
from screeninfo import get_monitors
from queue import Queue, Empty

from crappy.blocks.block import Block
from crappy._global import OptionalModule

try:
   from tkinter import Tk, Label
except (ModuleNotFoundError, ImportError):
   Tk = OptionalModule("tkinter")
   Label = OptionalModule("tkinter")


class Dashboard_window:
   """Dashboard class created, is launched in a new thread."""

   def __init__(self, labels: list, nb_digits: int, queue: Queue,
                      is_primary: bool) -> None:            # modified
      self.root = Tk()
      self.root.title('Valeurs')
    #   self.root.resizable(width=False, height=False)
      self.nb_digits = nb_digits
      self.labels = labels
      self.c1 = {}
      self.c2 = {}
      self.queue = queue
      self.is_primary = is_primary
      self.stop = False                               # modified
      row = 0
      
      # Putting the window on the right screen        # modified
      screens_list = get_monitors()
      screen_index = 0
      while screen_index < len(screens_list) and screens_list[screen_index].is_primary != is_primary :
         screen_index +=1      # Cherche l'écran principal.
      if screen_index < len(screens_list) :
         x, y = screens_list[screen_index].x, screens_list[screen_index].y
         self.root.geometry(f"+{x}+{y}")
      else :
         self.root.withdraw()
      
      # Creating the first and second column. Second column will be updated.
      font_size = 24 if self.is_primary else 48
      for label in self.labels:
         self.c1[label] = Label(self.root, text=label, borderwidth=15,
                                           font=("Courier bold", font_size))
         self.c1[label].grid(row=row, column=0)
         self.c2[label] = (Label(self.root, text='', borderwidth=15,
                                             font=("Courier bold", font_size)))
         self.c2[label].grid(row=row, column=1)
         row += 1
      # Updating the second column until told to stop
      while not self.stop:
         self.update()

   def update(self) -> None:
      """Method to update the output window."""

      try:
         values = self.queue.get(timeout=0.1)
      except Empty:
         # Re-looping if nothing to display
         return

      # Stopping and closing the window
      if values == 'stop':
         self.stop = True
         self.root.destroy()
         return
      # Updating the display
      for label in self.labels:
         try:
            if isinstance(values[label], str):
               self.c2[label].configure(text=values[label])
            else:
               self.c2[label].configure(text='%.{}f'.format(self.nb_digits) %
                                                            values[label])
         except KeyError:
            # If a wrong label is given it just won't be updated
            pass
      self.root.update()


class Dashboard(Block):
   """The Dashboard receives data from a :ref:`Link`, and prints it on a new
   popped window.

   It can only display data coming from one block.
   """

   def __init__(self,
                      labels: list,
                      nb_digits: int = 2,
                      is_primary: bool = True,                  # modified
                      verbose: bool = False,
                      freq: float = 30) -> None:
      """Sets the args and initializes parent class.

      Args:
         labels (:obj:`list`): Values to plot on the output window.
         nb_digits (:obj:`int`, optional): Number of decimals to show.
         verbose (:obj:`bool`, optional): Display loop frequency ?
         freq (:obj:`float`, optional): If set, the block will loop at this
            frequency.
      """

      super().__init__()
      self.verbose = verbose
      self.freq = freq
      self.labels = labels
      self.nb_digits = nb_digits
      self.is_primary = is_primary                        # modified
      # global queue

   def prepare(self) -> None:
      """Creates the window in a new thread."""

      self.queue = Queue()
      if len(self.inputs) == 0:
         raise IOError("No link pointing towards the Dashboard block !")
      elif len(self.inputs) > 1:
         raise IOError("Too many links pointing towards the Dashboard block !")
      self.dash_thread = threading.Thread(target=Dashboard_window,
                                                            args=(self.labels, self.nb_digits,
                                                                     self.queue, self.is_primary))                      # modified
      self.dash_thread.start()

   def loop(self) -> None:
      """Simply transmits the received data to the thread."""

      received_data = [link.recv_last() for link in self.inputs]
      if received_data[0] is not None:
         self.queue.put_nowait(received_data[0])

   def finish(self) -> None:
      """Closes the thread."""
      self.queue.put_nowait('stop')
      self.dash_thread.join(timeout=0.1)
