import tkinter as tk
from tkinter import ttk

import rtmidi

# to-do
# need toggle for config vs usage
# can use any number of midi controllers
# copy pasta all the stuff from midi basically lol
# no longer need to map stuff to osc
# handle errors? what happens on midi disconnect : ( ? nothing..

class MidiInterface:
    def __init__(self):
        self.input_ports = {}
        self.midi_inputs = {}
        self.refresh_input_ports()

    def refresh_input_ports(self):
        # get a list of all inputs
        for api in rtmidi.get_compiled_api():
            try:
                midi = rtmidi.MidiIn(api)
                ports = midi.get_ports()
            except:
                continue
            if ports:
                for num, name in enumerate(ports):
                    self.input_ports[name] = (api, num)
            del midi

    def open_midi_input(self, input_name):
        if input_name not in self.input_ports:
            return
        self.close_midi_input(input_name)
        try:
            port_nos = self.input_ports[input_name]

            new_input = rtmidi.MidiIn(port_nos[0])
            new_input.open_port(port_nos[1])
            new_input.set_callback(self.midi_callback_fun, data=input_name)
            new_input.set_error_callback(self.midi_error_fun)
            self.midi_inputs[input_name] = new_input
        except:
            self.close_midi_input(input_name)

    def close_midi_input(self, name):
        if name in self.midi_inputs:
            self.midi_inputs[name].close_port()
            self.midi_inputs[name].cancel_callback()
            self.midi_inputs[name].cancel_error_callback()
            del self.midi_inputs[name]

    def midi_callback_fun(self, midi_tuple, input_name):
        print(midi_tuple)

    def midi_error_fun(self, error, error_msg):
        pass


class MidiConfig:
    def __init__(self, root):
        self.root = root
        self.midi_int = MidiInterface()

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack()

        input_options = ['None'] + list(self.midi_int.input_ports.keys())

        self.midi_choice = tk.StringVar()

        self.choose_midi = ttk.Combobox(self.main_frame, values=input_options, textvariable=self.midi_choice, name='poop')
        self.choose_midi.config(state='readonly')
        self.choose_midi.set('None')

        self.midi_choice.trace("w", self.midi_choice_changed)

        self.choose_midi.pack()

    def midi_choice_changed(self, *args):
        new_choice = self.midi_choice.get()
        if new_choice != 'None':
            self.midi_int.open_midi_input(new_choice)



if __name__ == '__main__':

    rootwin = tk.Tk()
    rootwin.title('midi config')

    test_config = MidiConfig(rootwin)
    rootwin.mainloop()