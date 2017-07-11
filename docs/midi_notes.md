trying to install rt-midi on windows
pip install python-rtmidi just werks (as long as a compiled binary exists for your version of python)

you may need to double check these
https://github.com/SpotlightKid/python-rtmidi/blob/master/INSTALL.rst#requirements

midi interface has a switch to config mode function that takes the midi config window as arg
so that it can update midi id stuff automagically with a callback after thing

midi config opens up a helper window for id-ing controls
when u enter midi config mode gui changes so that stuff that has a (potential) midi binding gets an overlay
on hover midi config tells u what cmd it is
on click midi config will let u set that cmd

will do this with a transluscent canvas overlay
generate tree of all objects using `widget.winfo_children()` and get their coords
or `widget.nametowidget()`
may need to give each of those children widgets names...
will have to have a big dictionary of widget names to commands because they all have different methods of activation
ie speed slider is different from a pad button
some thing have multiple commands like pad can de/activate
or clip collection clip can activate to diff layerz so these overlays need to be split up

savedata is `cmd_desc` as key contains `osc_addr`, controller names, array of midi keys, key type

/midi osc addr still exists but it simply goes to a wrapper fun of the midi interface which calls the appropriate callback fun

name_to_cmd [command_name] = {
    addr - cmd_osc
    desc - cmd_desc
    midi_keys [control] - { // control = input name, a nested dict so that multiple controllers can map to same cmd
        keys - [keys to bind]
        type - midi control type
        invert - bool flag
    }    
}