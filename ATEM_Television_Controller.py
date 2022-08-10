import time
import mido
import PyATEMMax
import csv
import sys
from typing import Dict, Any
from mido import Message
from tabulate import WIDE_CHARS_MODE, tabulate

with open(f"./Profiles/settings.csv", encoding="utf_8") as setting_file:
    setting_list = csv.reader(setting_file)
    setting_dict = {}
    for raw in setting_list:
        setting_dict[raw[0]] = raw[1]

function_list = {} #ボタンのIDから呼びだす
button_call = {} #関数からボタンの情報を呼び出す
button_list = [] #有効なボタンリスト
profile_num = 1
me_num = 0
sw_num = 0
pgmin = 'input1'
pvwin = 'input1'
old_pgmin = 'input1'
old_pvwin = 'input1'
old_transty = 'mix'

bool_pvw_trans = False
bool_auto_trans = False
bool_ftb = False
old_bool_auto_trans = False #boolで扱う変数のうち，点滅系だけはoldがいる
old_bool_ftb = False
#[ onair, next ]
key_usk = ('bkgd', 'keyer1') 
bool_usk = {'bkgd': [True, True], 'keyer1': [False, False]}
#[ tie, onair, auto ]
key_dsk = ('dsk1', 'dsk2')
bool_dsk = {'dsk1': [False, False, False], 'dsk2': [False, False, False]}

def set_list(num) -> None:
    profile_num = num
    global function_list
    global button_list
    with open(f"./Profiles/{setting_dict['profile'+str(num)]}", encoding="utf_8") as list_file:
        f = csv.reader(list_file)
        header = next(f) #ヘッダー行を除く
        for raw in f:
            #key: button, contents: function, value, color
            function_list[str(raw[4])] = [str(raw[1]), str(raw[2]), str(raw[3])]
            #key: function, value  contents: button, color
            button_call[(str(raw[1]), str(raw[2]))] = [str(raw[4]), str(raw[3])]
            if str(raw[4]) != '':
                button_list.append(str(raw[4]))

def bool2color(tf, fn, val):
    if tf == True:
        return '03'
    else:
        return button_call[(fn, val)][1]

###########   MIDI padの設定   ###########
try: #settings.csvにあるMIDIパッドに接続を試みる
    print(f"[{time.ctime()}] Connecting MIDI pad")
    outport = mido.open_output(setting_dict['MIDI input'])
    inport = mido.open_input(setting_dict['MIDI output'])
    print(f"[{time.ctime()}] MIDI pad connected")
except: #だめだったら探して接続
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

###########   ATEMへ接続   ###########
ips = []
switcher = PyATEMMax.ATEMMax()
switcher1 = PyATEMMax.ATEMMax()
switcher2 = PyATEMMax.ATEMMax()
switcher3 = PyATEMMax.ATEMMax()
switchers = (switcher, switcher1, switcher2, switcher3)

#LAN内のATEMスキャン
def atem_scan():
    print(f"[{time.ctime()}] Scan network for ATEM switchers")
    count = 0
    global ips
    iprange = input("Input Subnet(/24) (ex: 192.168.10) : ")
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
    switcher.connect(str(setting_dict['ip address 1']))
except:
    atem_scan()
    atem_connect(input('Input IP address'))

def sync_status():
    global pgmin
    global pvwin
    global old_pgmin
    global old_pvwin
    global old_transty
    global bool_pvw_trans
    global bool_auto_trans
    global bool_ftb
    global old_bool_auto_trans
    global old_bool_ftb
    global bool_pvw_trans
    global key_usk
    global key_dsk
    global bool_usk
    global bool_dsk

    pgmin = str(switcher.programInput[me_num].videoSource)
    pvwin = str(switcher.previewInput[me_num].videoSource)
    transty = str(switcher.transition[me_num].style)
    bool_auto_trans = switcher.transition[me_num].inTransition
    if switcher.fadeToBlack[me_num].state.fullyBlack == True or switcher.fadeToBlack[me_num].state.inTransition == True:
        bool_ftb = True
    bool_pvw_trans = switcher.transition[me_num].preview.enabled
    for i in key_dsk:
        bool_dsk[i][0] = switcher.downstreamKeyer[i].tie
        bool_dsk[i][1] = switcher.downstreamKeyer[i].onAir
        bool_dsk[i][2] = switcher.downstreamKeyer[i].isAutoTransitioning
    for i in key_usk:
        if i != 'bkgd':
            bool_usk[i][0] = switcher.keyer[me_num][i].onAir.enabled
    bool_usk['bkgd'][1] = switcher.transition[me_num].nextTransition.background
    bool_usk['keyer1'][1] = switcher.transition[me_num].nextTransition.key1

    outport.send(Message.from_hex('90 '+button_call[('pgm', old_pgmin)][0]+' '+button_call[('pgm', old_pgmin)][1]))
    outport.send(Message.from_hex('90 '+button_call[('pgm', pgmin)][0]+' 03'))
    outport.send(Message.from_hex('90 '+button_call[('pvw', old_pvwin)][0]+' '+button_call[('pvw', old_pvwin)][1]))
    outport.send(Message.from_hex('90 '+button_call[('pvw', pvwin)][0]+' 03'))
    outport.send(Message.from_hex('90 '+button_call[('transtyle', old_transty)][0]+' '+button_call[('transtyle', old_transty)][1]))
    outport.send(Message.from_hex('90 '+button_call[('transtyle', transty)][0]+' 03'))
    if bool_auto_trans == True:
        outport.send(Message.from_hex('91 '+ button_call[('autome', 'auto')][0]+' 05'))
    elif bool_auto_trans == False:
        outport.send(Message.from_hex('90 '+ button_call[('autome', 'auto')][0]+' '+button_call[('autome', 'auto')][1]))
        
    
    outport.send(Message.from_hex('90 '+button_call[('pvw_transition', 'mode')][0] +' '+bool2color(bool_pvw_trans, 'pvw_transition', 'mode')))
    
    old_pgmin = pgmin
    old_pvwin = pvwin
    old_transty = transty

    print(f"[{time.ctime()}] MIDI pad is syncd!")

###########   Eventのログを表示   ###########
def onConnectAttempt(params: Dict[Any, Any]) -> None:
    """Called when a connection is attempted"""
    outport.send(Message.from_hex('92 63 0D'))
    print(f"[{time.ctime()}] Trying to connect to switcher at {params['switcher'].ip}")

def onConnect(params: Dict[Any, Any]) -> None:
    """Called when the switcher is connected"""
    outport.send(Message.from_hex('90 63 03'))
    print(f"[{time.ctime()}] Connected to switcher {switcher.atemModel} at {params['switcher'].ip}")

def onDisconnect(params: Dict[Any, Any]) -> None:
    """Called when the switcher disconnects"""
    outport.send(Message.from_hex('91 63 05'))
    print(f"[{time.ctime()}] DISCONNECTED from switcher at {params['switcher'].ip}")

def onReceive(params: Dict[Any, Any]) -> None:
    """Called when data is received from the switcher"""
    print(f"[{time.ctime()}] Received [{params['cmd']}]: {params['cmdName']}")
    sync_status()

def onWarning(params: Dict[Any, Any]) -> None:
    """Called when a warning message is received from the switcher"""
    outport.send(Message.from_hex('90 63 0D'))
    print(f"[{time.ctime()}] Received warning message: {params['cmd']}")

switcher.registerEvent(switcher.atem.events.connectAttempt, onConnectAttempt)
switcher.registerEvent(switcher.atem.events.connect, onConnect)
switcher.registerEvent(switcher.atem.events.disconnect, onDisconnect)
switcher.registerEvent(switcher.atem.events.receive, onReceive)
switcher.registerEvent(switcher.atem.events.warning, onWarning)
print("Event Logs have been resisted!")


#ボタンを押すと呼び出される関数
def pgm(num) -> None:
    print(f'[{time.ctime()}] set PGM: {num}')
    switcher.setProgramInputVideoSource(me_num, num)

def pvw(num) -> None:
    print(f'[{time.ctime()}] set PVW: {num}')
    switcher.setPreviewInputVideoSource(me_num, num)
def transtyle(num) -> None:
    print(f'[{time.ctime()}] set transition-style: {num}')
    switcher.setTransitionStyle(me_num, num)
def autome(num) -> None:
    print(f'[{time.ctime()}] exec transition: {num}')
    switcher.execAutoME(me_num)
def cutme(num) -> None:
    print(f'[{time.ctime()}] exec transition: {num}')
    switcher.execCutME(me_num)
def usk_onair(num) -> None:
    print(f'[{time.ctime()}] set usk_onair: {num}')
    bool_usk[num][0] = not bool_usk[num][0]
    switcher.setKeyerOnAirEnabled(me_num, num, bool_usk[num][0])
def usk_next(num) -> None:
    print(f'[{time.ctime()}] set usk_next: {num}')
    global key_usk
    temp = key_usk.index(num)
    bool_usk[num][1] = not bool_usk[num][1]
    #switcher.setKeyerFlyEnabled(me_num, num, bool_usk[num][1])
    switcher.setTransitionNextTransition(me_num, temp)
def dsk_tie(num) -> None:
    print(f'[{time.ctime()}] set dsk_tie: {num}')
    global bool_dsk
    bool_dsk[num][0] = not bool_dsk[num][0]
    switcher.setDownstreamKeyerTie(num, bool_dsk[num][0])
def dsk_onair(num) -> None:
    print(f'[{time.ctime()}] set dsk_onair: {num}')
    global bool_dsk
    bool_dsk[num][1] = not bool_dsk[num][1]
    switcher.setDownstreamKeyerOnAir(num, bool_dsk[num][1])
def dsk_auto(num)-> None:
    print(f'[{time.ctime()}] exec dsk_auto: {num}')
    switcher.execDownstreamKeyerAutoKeyer(num)
def pvw_trans(num) -> None:
    print(f'[{time.ctime()}] set pvw_transition {num}')
    global bool_pvw_trans
    bool_pvw_trans = not bool_pvw_trans
    switcher.setTransitionPreviewEnabled(me_num, bool_pvw_trans)
def ftb(num) -> None:
    print(f'[{time.ctime()}] exec fade_to_black {num}')
    switcher.execFadeToBlackME(me_num)
def profile(num) -> None:
    print(f'[{time.ctime()}] loading profile {num}')
    set_list(num)
    initialize()
def end(num) -> None:
    print(f"[{time.ctime()}] exec Shutdown-Sequence")
    #ATEMとの接続解除
    switcher.disconnect()
    #Launchpad XのAftertouch有効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0B 00 01 F7'))
    #Launchpad XのVelocity有効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 04 01 F7'))
    #Launchpad XのFader velocity toggle 有効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0D 01 F7'))
    #Launchpad XのLive Mode化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0E 00 F7'))
    outport.close()
    print(f"[{time.ctime()}] {num}")
    sys.exit()
function = {'pgm': pgm, 'pvw': pvw, 'transtyle': transtyle, 'autome': autome, 'cutme': cutme, 'profile':profile, 'usk_onair': usk_onair, 'usk_next': usk_next, 'dsk_tie': dsk_tie, 'dsk_onair': dsk_onair, 'dsk_auto': dsk_auto, 'pvw_transition': pvw_trans, 'fade_to_black': ftb}

set_list(1)
# 1秒 止める
time.sleep(1.0)
initialize()
# 1秒 止める
time.sleep(1.0)
sync_status()
# 1秒 止める
time.sleep(1.0)
while True:
    msg = inport.receive().hex().split()
    if msg[2] == '00':
        continue
    elif msg[1] in button_list:
        function.get(function_list[str(msg[1])][0])(function_list[str(msg[1])][1])