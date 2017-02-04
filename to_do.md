## isadoraBL

- clip initialization needs to be in folder order..
- so as part of dumbed down gui add instantiate from folder
- other changes to overall structure
	- random playback callback ?
	- gotta make sure update speed when flipping it lol

##### list of osc addresses

| addr | notes |
| ---- | ----- |
| /isadorabl | prefix to everything |
| /blend | external to sol actually |
| /layer1 | layer 1 |
| /layer2 | layer 2 |
| /clip | clip selection integer corresponding to clip no inside library, 0 none |
| /loop | 0 - off (don't do this), 1 - regular, 2 - palindrome |
| /loop/a | set start of loop (0-100) |
| /loop/b | set end of loop (0-100) |
| /seek | seek to time (0-100) |
| /speed | playback spped (-10 - 10), negative is reverse, 0 is pause |

and uhh it sends to /layer[1,2]/position