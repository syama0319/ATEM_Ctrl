import time
import argparse
import mido
import PyATEMMax
import csv
from typing import Dict, Any
from mido import Message
from tabulate import WIDE_CHARS_MODE, tabulate

#Switcherオブジェクトの生成
switcher = PyATEMMax.ATEMMax()

#CSVから設定やらのリスト読み込み
setting_file = open(f"./settings.csv", encoding="utf_8")
setting_list = csv.reader(setting_file)
setting_dict = {}
for row in setting_list:
    setting_dict[row[0]] = row[1]
f = csv.reader(open(f"./{setting_dict['button file']}", encoding="utf_8"))

#ボタンやらの変数，定数リスト
me = 0
header = next(f)
buttonlist = [str(row[3]) for row in f]
pgmin = tuple(buttonlist[0:10])
pgmcol = tuple(buttonlist[10:16])
pvwin = tuple(buttonlist[16:26])
pvwcol = tuple(buttonlist[26:32])
uskonair = tuple(buttonlist[32:36])
usknext = tuple(buttonlist[36:40])
dsktie = tuple(buttonlist[40:42])
dskonair = tuple(buttonlist[42:44])
dskauto = tuple(buttonlist[44:46])
transitionstyle = tuple(buttonlist[46:51])
cutme = buttonlist[51]
autome = buttonlist[52]
pvwtrans = buttonlist[53]
ftb = buttonlist[54]

###########   ATEMへ接続   ###########
ips = []
#LAN内のATEMスキャン
def atem_scan():
    print(f"[{time.ctime()}] Scan network for ATEM switchers")
    count = 0
    iprange = input("Input IP address range (ex: 192.168.10) : ")
    print(f"[{time.ctime()}] Scanning network range {iprange}.* for ATEM switchers")
    for i in range(1,255):
        ip = f"{iprange}.{i}"
        switcher.ping(ip)
        if switcher.waitForConnection():
            count += 1
            ips[count-1][0] = switcher.atemModel
            ips[count-1][1] = ip
        switcher.disconnect()
    print(f"[{time.ctime()}] FINISHED: {count} ATEM switchers found.")
    print(tabulate(ips, headers=["ATEM", "IP address"]))

#どれにつなぐかの設定
def atem_connect(inip):
    while True:
        switcher.connect(inip)
        if switcher.connected:
            break
        else:
            print(f"[{time.ctime()}] Faild. try again.")
            if(input(f"[{time.ctime()}] Scan network? [y/n]")== "y"):
                atem_scan()
            continue

#settingsにipを入れればatem_scan()はスキップされる
try:
    print(f"[{time.ctime()}] Connecting ATEM...")
    switcher.connect(setting_dict['ip address'])
except:
    atem_scan()
    atem_connect(input('Input IP address'))

###########   MIDI padの設定   ###########
#MIDIのポート設定
# ports = mido.open_output('Launchpad X LPX MIDI In')
try:
    outport = mido.open_output(setting_dict['MIDI input'])
    inport = mido.open_input(setting_dict['MIDI output'])
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

#MIDIPadのデフォの色
def defclr():
    for i in pvwin:
        outport.send(Message.from_hex('90 '+ i +' 15'))
    for i in pgmin:
        outport.send(Message.from_hex('90 '+ i +' 05'))
    for i in range(len(pgmcol)):
        outport.send(Message.from_hex('90 '+pvwcol[i]+' 18'))
        outport.send(Message.from_hex('90 '+pgmcol[i]+' 04'))
    for i in transitionstyle:
        outport.send(Message.from_hex('90 '+ i +' 0C'))
    for i in dsktie:
        outport.send(Message.from_hex('90 '+ i +' 0C'))
    for i in dskonair:
        outport.send(Message.from_hex('90 '+ i +' 05'))
    for i in dskauto:
        outport.send(Message.from_hex('90 '+ i +' 05'))
    outport.send(Message.from_hex('90 '+ftb+' 03'))
    outport.send(Message.from_hex('90 '+cutme+' 09'))
    outport.send(Message.from_hex('90 '+autome+' 09'))
    outport.send(Message.from_hex('90 '+pvwtrans+' 22'))

def initialize():
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
    defclr()