import crappy


if __name__ == '__main__':


   gen = crappy.blocks.Generator(path=[{'type': 'constant',
                               'value': 0,
                               'condition': "delay=0.01"}],
                          cmd_label='commande_en_charge',
                          spam=True)


   carte_NI = crappy.blocks.IOBlock(name="Nidaqmx",
                                    labels=["t(s)", "sortie_charge", 
                                             "sortie_deplacement"],
                                    cmd_labels=["commande_en_charge", "commande_en_charge"],
                                    initial_cmd=[0.0, 0.0],
                                    exit_values=[0.0, 0.0],
                                    channels=[{'name': 'Dev2/ao0'},
                                    {'name': 'Dev2/ao1'},
                                    {'name': 'Dev2/ai6'},
                                    {'name': 'Dev2/ai7'}])

   crappy.link(gen, carte_NI)
   crappy.start()