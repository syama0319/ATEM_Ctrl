import time
import argparse
import mido
import PyATEMMax
import asyncio
from typing import Dict, Any
from mido import Message
from tabulate import WIDE_CHARS_MODE, tabulate

#引数の追加
#実行時に $ python3 なんたら.py -ip [ip address]とすることでscan()を実行しなくて済む
#ex.) $ python3 scan.py -ip 192.168.1
#-hオプションをつけるとhelpメッセージがでる
parser = argparse.ArgumentParser()
parser.add_argument('-i','--ip', help='IP address (ex: 192.168.10.240')
parser.add_argument('-m', '--model', help='MIDI pad model (ex: lpx)')
args = parser.parse_args()

#Switcherオブジェクトの生成
switcher = PyATEMMax.ATEMMax()

#LaunchpadとATEMのボタン対応
pvwin = ('33','34','35','36','37','29','2A','2B','2C','2D')
pgmin = ('51','52','53','54','55','47','48','49','4A','4B')
inputs = ('input1', 'input2', 'input3', 'input4', 'input5', 'input6', 'input7', 'input8', 'input9', 'input10')
cols = ('black', 'colorBars', 'color1', 'color2', 'mediaPlayer1', 'mediaPlayer2')
pvwcol = ('3B','31','2F','30','39','3A') #colは Black ColorBars Color mediaPlayer1 mediaPlayer2の順
pgmcol = ('59','4F','4D','4E','57','58')
ftb = '45'
cutme = '10'
autome = '12'
me = ('19','1A','1B','1C','1D')
mes = ('mix','dip','wipe','sting','dVE')
pvwtrans = '13'
mpties = ('15','0B') #mp1, mp2
mpairs = ('16', '0C')
mpautos = ('17', '0D')
keyers = ('keyer1','keyer2','keyer3','keyer4')
dsks = ('dsk1', 'dsk2')
mptie = [False, False]
mpair = [False, False]
mpauto = [False, False]

#MIDIのポート設定
# ports = mido.open_output('Launchpad X LPX MIDI In')
if args.model == 'lpx':
    outport = mido.open_output('Launchpad X LPX MIDI In')
    inport = mido.open_input('Launchpad X LPX MIDI Out')
else:
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

def defcal():
    for i in pvwin:
        outport.send(Message.from_hex('90 '+ i +' 15'))
    for i in pgmin:
        outport.send(Message.from_hex('90 '+ i +' 05'))
    for i in range(len(pgmcol)):
        outport.send(Message.from_hex('90 '+pvwcol[i]+' 18'))
        outport.send(Message.from_hex('90 '+pgmcol[i]+' 04'))
    for i in me:
        outport.send(Message.from_hex('90 '+ i +' 0C'))
    for i in mpties:
        outport.send(Message.from_hex('90 '+ i +' 0C'))
    for i in mpairs:
        outport.send(Message.from_hex('90 '+ i +' 05'))
    for i in mpautos:
        outport.send(Message.from_hex('90 '+ i +' 05'))
    outport.send(Message.from_hex('90 '+ftb+' 03'))
    outport.send(Message.from_hex('90 '+cutme+' 09'))
    outport.send(Message.from_hex('90 '+autome+' 09'))
    outport.send(Message.from_hex('90 '+pvwtrans+' 22'))

#ATEMの状態を取得
pgmcam_old = 'old'
pvwcam_old = 'old'
def syncStatus():
    pgmcam = str(switcher.programInput[0].videoSource)
    pvwcam = str(switcher.previewInput[0].videoSource)
    style = str(switcher.transition[0].style)
    
    for i in range(0,1):
        mptie[i] = switcher.downstreamKeyer[dsks[i]].tie
        mpair[i] = switcher.downstreamKeyer[dsks[i]].onAir
        mpauto[i] = switcher.downstreamKeyer[dsks[i]].isAutoTransitioning
    """print(type(switcher.downstreamKeyer[dsks[0]].tie))
    print(switcher.downstreamKeyer[dsks[0]].tie)
    print(type(switcher.downstreamKeyer[dsks[0]].onAir))
    print(switcher.downstreamKeyer[dsks[0]].tie)
    print(type(switcher.downstreamKeyer[dsks[0]].isAutoTransitioning))
    print(switcher.downstreamKeyer[dsks[0]].tie)"""

    #ボタンを光らせる
    #PGMボタン
    if pgmcam in inputs:
        num = inputs.index(pgmcam)
        outport.send(Message.from_hex(f'90 {pgmin[num]} 03'))

    if pgmcam in cols:
        num = cols.index(pgmcam)
        outport.send(Message.from_hex(f'90 {pgmcol[num]} 03'))
    
    if pvwcam in inputs:
        num = inputs.index(pvwcam)
        outport.send(Message.from_hex(f'90 {pvwin[num]} 03'))

    if pvwcam in cols:
        num = cols.index(pvwcam)
        outport.send(Message.from_hex(f'90 {pvwcol[num]} 03'))
    
    if style in mes:
        num = mes.index(style)
        outport.send(Message.from_hex(f'90 {me[num]} 03'))
    
    for i in range(0,1):
        if mptie[i] == True:
            outport.send(Message.from_hex(f'90 {mpties[i]} 03'))
        if mpair[i] == True:
            outport.send(Message.from_hex(f'90 {mpairs[i]} 03'))
        if mpauto[i] == True:
            outport.send(Message.from_hex(f'91 {mpautos[i]} 03'))    

    print(f"[{time.ctime()}] ATEM-MIDIpad synced")

###########   Eventのログを表示   ###########
#たぶん，非同期処理がなくともOK?
def onConnectAttempt(params: Dict[Any, Any]) -> None:
    """Called when a connection is attempted"""

    print(f"[{time.ctime()}] Trying to connect to switcher at {params['switcher'].ip}")

def onConnect(params: Dict[Any, Any]) -> None:
    """Called when the switcher is connected"""

    print(f"[{time.ctime()}] Connected to switcher {switcher.atemModel} at {params['switcher'].ip}")

def onDisconnect(params: Dict[Any, Any]) -> None:
    """Called when the switcher disconnects"""

    print(f"[{time.ctime()}] DISCONNECTED from switcher at {params['switcher'].ip}")

def onReceive(params: Dict[Any, Any]) -> None:
    """Called when data is received from the switcher"""
    defcal()
    syncStatus()
    print(f"[{time.ctime()}] Received [{params['cmd']}]: {params['cmdName']}")

def onWarning(params: Dict[Any, Any]) -> None:
    """Called when a warning message is received from the switcher"""

    print(f"[{time.ctime()}] Received warning message: {params['cmd']}")

switcher.registerEvent(switcher.atem.events.connectAttempt, onConnectAttempt)
switcher.registerEvent(switcher.atem.events.connect, onConnect)
switcher.registerEvent(switcher.atem.events.disconnect, onDisconnect)
switcher.registerEvent(switcher.atem.events.receive, onReceive)
switcher.registerEvent(switcher.atem.events.warning, onWarning)

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

#実行時にipを入れればatem_scan()はスキップされる
if args.ip is not None :
    switcher.connect(args.ip)
else:
    atem_scan()
    atem_connect(input('Input IP address'))

#MIDIパッド初期化
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
    #Novationのロゴを光らせる
    outport.send(Message.from_hex('90 63 03'))
    defcal()

#終了時にやること
def end_seq():
    print(f"[{time.ctime()}] Shutdown...")
    #ATEMとの接続解除
    switcher.disconnect()
    #Launchpad XのAftertouch有効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0B 00 01 F7'))
    #Launchpad XのLive Mode化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0E 00 F7'))
    outport.close()
    print(f"[{time.ctime()}] BYE!")
    quit()

initialize()

#MIDIパッドからの入力をATEMに反映
while True:
    msgh = inport.receive().hex().split()
    #ボタンを離したときは無視する
    if msgh[2] != '00':
        if msgh[1] in pgmin:
            num = pgmin.index(msgh[1]) +1
            switcher.setProgramInputVideoSource(0, num)
            print(f"[{time.ctime()}]  PGM Video source: {num}")
        elif msgh[1] in pvwin:
            num = pvwin.index(msgh[1]) +1
            switcher.setPreviewInputVideoSource(0, num)
            print(f"[{time.ctime()}]  PVW Video source: {num}")
        elif msgh[1] in pgmcol:
            num = pgmcol.index(msgh[1])
            switcher.setProgramInputVideoSource(0, cols[num])
            print(f"[{time.ctime()}]  PGM Video source: " + cols[num])
        elif msgh[1] in pvwcol:
            num = pvwcol.index(msgh[1])
            switcher.setPreviewInputVideoSource(0, cols[num])
            print(f"[{time.ctime()}]  PVW Video source: " + cols[num])
        elif msgh[1] in me:
            num = me.index(msgh[1])
            switcher.setTransitionStyle(0, mes[num])
        elif msgh[1] == ftb:
            if switcher.fadeToBlack[0].state.fullyBlack == False and switcher.fadeToBlack[0].state.inTransition:
                switcher.execFadeToBlackME(1)
                outport.send(Message.from_hex('91 '+ftb+' 05'))
        elif msgh[1] == autome:
            switcher.execAutoME(0)
        elif msgh[1] == cutme:
            switcher.execCutME(0)
        elif msgh[1] in mpties:
            num = mpties.index(msgh[1])
            mptie[num] != mptie[num]
            switcher.setDownstreamKeyerTie(dsks[num], mptie[num])
        elif msgh[1] in mpairs:
            num = mpairs.index(msgh[1])
            mpair[num] != mpair[num]
            switcher.setDownstreamKeyerTie(dsks[num], mpair[num])
        elif msgh[1] in mpautos:
            num = mpautos.index(msgh[1])
            mpautos[num] != mpauto[num]
            switcher.setDownstreamKeyerTie(dsks[num], mpauto[num])
        

