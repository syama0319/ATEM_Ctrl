import csv
import time
import mido
from mido import Message
from sqlalchemy import true

with open(f"./settings.csv", encoding="utf_8") as setting_file:
    setting_list = csv.reader(setting_file)
    setting_dict = {}
    for row in setting_list:
        setting_dict[row[0]] = row[1]

function_list = {}
button_call = {}
button_list = []
def set_list(num) -> None:
    with open(f"./{setting_dict['profile'+str(num)]}", encoding="utf_8") as list_file:
        f = csv.reader(list_file)
        header = next(f) #ヘッダー行を除く
        for row in f:
            #key: button, contents: function, value, color
            function_list[str(row[4])] = [str(row[1]), str(row[2]), str(row[3])]
            button_call[(str(row[1]), str(row[2]))] = [str(row[4]), str(row[3])]
            button_list.append(str(row[4]))

###########   MIDI padの設定   ###########
#MIDIのポート設定
try:
    print(f"[{time.ctime()}] Connecting MIDI pad...")
    outport = mido.open_output(setting_dict['MIDI input'])
    inport = mido.open_input(setting_dict['MIDI output'])
    print(f"[{time.ctime()}] MIDI pad connected!")
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
    temp_list = list(filter(None, button_list))
    for i in temp_list:
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
def transiton(num):
    print(f'[{time.ctime()}] transition {num}')
def profile(num):
    print(f'[{time.ctime()}] loading profile {num}')
    set_list(num)
    initialize()
function = {'pgm': pgm, 'pvw': pvw, 'transtyle': transtyle, 'transition': transiton, 'profile':profile}

set_list(1)
initialize()
while(true):
    msg = inport.receive().hex().split()
    if msg[2] == '00':
        continue
    if msg[1] in button_list:
        function.get(function_list[str(msg[1])][0])(function_list[str(msg[1])][1])