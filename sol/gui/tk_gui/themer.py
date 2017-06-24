# from tkinter import ttk

# themes = ttk.Style().theme_names()

#             # b = ttk.Button(lf, text=t, command=lambda t=t: 

# print(themes)

def hex_to_rgb(hex_val):
    hex_val = hex_val.lstrip('#')
    lv = len(hex_val)
    return tuple(int(hex_val[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def rgb_to_hex(rgb_val):
    return '#%02x%02x%02x' % rgb_val


from_to_hex = ('#aaa', '#333')

print([hex_to_rgb(from_to_hex[0]), hex_to_rgb(from_to_hex[1])])