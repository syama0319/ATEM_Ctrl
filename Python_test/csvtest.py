import csv
from inspect import currentframe
import time
import mido
import sys
from mido import Message
from sqlalchemy import true

with open(f"./settings.csv", encoding="utf_8") as setting_file:
    setting_list = csv.reader(setting_file)
    setting_dict = {}
    for raw in setting_list:
        setting_dict[raw[0]] = raw[1]

function_list = {}
button_call = {}
button_list = []
profile_num = 1
def set_list(num) -> None:
    profile_num = num
    with open(f"./{setting_dict['profile'+str(num)]}", encoding="utf_8") as list_file:
        f = csv.reader(list_file)
        header = next(f) #ヘッダー行を除く
        for raw in f:
            #key: button, contents: function, value, color
            function_list[str(raw[4])] = [str(raw[1]), str(raw[2]), str(raw[3])]
            button_call[(str(raw[1]), str(raw[2]))] = [str(raw[4]), str(raw[3])]
            if str(raw[4]) != '':
                button_list.append(str(raw[4]))

###########   MIDI padの設定   ###########
try:
    print(f"[{time.ctime()}] Connecting MIDI pad")
    outport = mido.open_output(setting_dict['MIDI input'])
    inport = mido.open_input(setting_dict['MIDI output'])
    print(f"[{time.ctime()}] MIDI pad connected")
except:
    print(f"[{time.ctime()}] Scanning MIDI devices.")
    ports_o = mido.get_output_names()
    print(f"[{time.ctime()}] FINISHED: {len(ports_o)} MIDI Input devices found.")
    print(f"[{time.ctime()}] {ports_o}")
    ports_i = mido.get_input_names()
    print(f"[{time.ctime()}] FINISHED: {len(ports_i)} MIDI Input devices found.")
    print(f"[{time.ctime()}] {ports_i}")
    port_on = int(input('Which MIDI Output device? [int] : '))
    port_in = int(input('Which MIDI Input device? [int] : '))
    outport = mido.open_output(ports_o[port_on])
    inport = mido.open_input(ports_i[port_in])
    print(f"[{time.ctime()}] MIDI pad connected!")

#MIDIPadのデフォの色
def default_color() -> None:
    for i in button_list:
        outport.send(Message.from_hex(f'90 {i} {function_list[i][2]}'))

def initialize() -> None:
    print(f"[{time.ctime()}] Initializing MIDI pad...")
    #Launchpad XのProgrammer Mode化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0E 01 F7'))
    #Launchpad XのVelocity無効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 04 03 7F F7'))
    #Launchpad XのAftertouch無効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0B 02 01 F7'))
    #Launchpad XのLED有効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0A 01 01 F7'))
    #とりま全キーを真っ暗に
    for i in range(1, 99):
        outport.send(Message('note_on', channel = 0, note = i, velocity = 0))
    default_color()

#ボタンを押すと呼び出される関数
def pgm(num):
    print(f'[{time.ctime()}] pgm {num}')
def pvw(num):
    print(f'[{time.ctime()}] pvw {num}')
def transtyle(num):
    print(f'[{time.ctime()}] transition style {num}')
def autome(num):
    print(f'[{time.ctime()}] transition {num}')
def cutme(num):
    print(f'[{time.ctime()}] transition {num}')
def profile(num):
    print(f'[{time.ctime()}] loading profile {num}')
    set_list(num)
    initialize()
def end(num) -> None:
    print(f"[{time.ctime()}] exec Shutdown-Sequence")
    #Launchpad XのAftertouch有効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0B 00 01 F7'))
    #Launchpad XのVelocity有効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 04 01 F7'))
    #Launchpad XのFader velocity toggle有効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0D 01 F7'))
    #Launchpad XのLive Mode化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0E 00 F7'))
    outport.close()
    print(f"[{time.ctime()}] {num}")
    sys.exit()
function = {'pgm': pgm, 'pvw': pvw, 'transtyle': transtyle, 'autome': autome, 'cutme': cutme, 'profile':profile, 'end': end}

set_list(1)
initialize()
while(true):
    msg = inport.receive().hex().split()
    if msg[2] == '00':
        continue
    if msg[1] in button_list:
        function.get(function_list[str(msg[1])][0])(function_list[str(msg[1])][1])