`sol_resolume_template_windows.avc`

has everything setup for a 2 layer setup

make sure you have the spoutsender plugin installed

the key things to keep in mind

1. just 1 deck (switching decks is not instantaneous, you want to be able to trigger any clip)
2. have spoutsenders (or syphon on osx) on layers 1.. however many layers you want (2)
3. Composition Settings
	a. Beat Snap - None
	b. Clip Target - Active Layer (!!!)
	c. Clip Trigger Style - Normal
4. General Preferences
	a. OSC Preferences
		i. Input Port 7000 
		ii. Output Port matches what is in sol's network config for osc port (default: 7001)

`isadoraBL.izz`

has an initial template for a 2 layer setup using isadora