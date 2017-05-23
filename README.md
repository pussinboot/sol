
~~~

                 d8b    
                 88P    　　　∩
                d88     　　 | | /二つ 
 .d888b, d8888b 888     　　（,ﾟДﾟ)      　　　　♪        
 ?8b,   d8P' ?88?88     　　 |ｖｖ       　　♪　　　 /    
   `?8b 88b  d88 88b    　　C|　|       　　＿＿＿/　♪  
`?888P' `?8888P'  88b   　　 し^Ｊ       　［●|圖|●］　　♪ 
          
~~~

sol is an interactive database of clips

it lets you organize and search for clips plus keep associated parameters, cue points, loop points, thumbnails and tags

it controls playback and adds some missing features to re*sol*ume

MIT licensed

## general overview

~~~
            database
              ^ |
              | v
 inputs ->  control -> gui
            (magi)  <- 
              | ^   
              v |
            model 
~~~

- control aka MAGI
	- **the brains**
	- gets input from
		- inputs - midi or osc
		- its own state (for example, when to loop)
		- the gui

- database
	- **the data**
	- abstractions of clips
	- collections to store clips
	- methods to update or query database
	- save/load 

- gui
	- what's happening right now
	- what can be changed
	- multiple views
		1. performance
		2. library organization
		3. clip collection organization
- models
	- provide compatible api(s)
	- translates info coming in so that it can go out

## setup instructions

you will need `ffmpeg` and its associated `ffprobe`

either `pip install sol_vj` or clone this repo then `python setup.py install`

to use with resolume, see `/docs/templates` for a base composition