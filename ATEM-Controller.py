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
parser.add_argument('-m', '--model', help='MIDI pad model (ex: LPX)')
args = parser.parse_args()

#Switcherオブジェクトの生成
switcher = PyATEMMax.ATEMMax()

#LaunchpadとATEMのボタン対応
pvwin = ('51','52','53','54','55','56','57','58','47','48')
pgmin = ('3D','3E','3F','40','41','42','43','44','33','34')
#colは Black ColorBars Colorの順
pvwcol = ('35','36','37')
pgmcol = ('49','4A','4B')
pvwmp = ('39','3A')
pgmmp = ('4D','4E')
ftb = '4F'
cutme = '0C'
autome = '0E'
me = ('22','23','24','25','26')
pvwtrans = '0E'

#MIDIのポート設定
# ports = mido.open_output('Launchpad X LPX MIDI In')
if args.model == 'lpx':
    outport = mido.open_output(f'Launchpad X LPX MIDI In')
    inport = mido.open_input(f'Launchpad X LPX MIDI Out')
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

#ATEMの状態を取得
def syncStates():
    pgmcam = switcher.programInput[0].videoSource
    pvwcam = switcher.previewInput[0].videoSource
    #ボタンを光らせる
    #PGMボタン
    outport.send(Message.from_hex(f'90 {pgmin[pgmcam -1]} 05'))
    #PRVボタン
    outport.send(Message.from_hex(f'90 {pvwin[pvwcam -1]} 15'))

#Eventのログを表示
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

    print(f"[{time.ctime()}] Received [{params['cmd']}]: {params['cmdName']}")
    syncStates()


def onWarning(params: Dict[Any, Any]) -> None:
    """Called when a warning message is received from the switcher"""

    print(f"[{time.ctime()}] Received warning message: {params['cmd']}")

switcher.registerEvent(switcher.atem.events.connectAttempt, onConnectAttempt)
switcher.registerEvent(switcher.atem.events.connect, onConnect)
switcher.registerEvent(switcher.atem.events.disconnect, onDisconnect)
switcher.registerEvent(switcher.atem.events.receive, onReceive)
switcher.registerEvent(switcher.atem.events.warning, onWarning)

#ATEMへ接続
ips = 0
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

#MIDIパッド初期化
def initialize():
    print(f"[{time.ctime()}] Initializing MIDI pad...")
    #Launchpad XのProgrammer Mode化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0E 01 F7'))
    #Launchpad XのAftertouch無効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0B 02 01 F7'))
    #Launchpad XのLED有効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0A 01 01 F7'))
    #とりま全キーを真っ暗に
    for i in range(1, 99):
        outport.send(Message('note_on', channel = 0, note = i, velocity = 0))
    #Novationのロゴを光らせる
    outport.send(Message.from_hex('90 63 03'))
    for i in range(len(pgmin)):
        outport.send(Message.from_hex('90 '+pvwin[i]+' 03'))
        outport.send(Message.from_hex('90 '+pgmin[i]+' 03'))
    for i in range(len(pgmcol)):
        outport.send(Message.from_hex('90 '+pvwcol[i]+' 03'))
        outport.send(Message.from_hex('90 '+pgmcol[i]+' 03'))
    for i in range(len(pvwmp)):
        outport.send(Message.from_hex('90 '+pvwmp[i]+' 03'))
        outport.send(Message.from_hex('90 '+pgmin[i]+' 03'))
    outport.send(Message.from_hex('F0 00 20 29 02 0C 03 00 '+ftb+' 04 00 '+cutme+' 03 00 '+autome+' 03 00 '+pvwtrans+' 24'))

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

#実行時にipを入れればScan()はスキップされる
if args.ip is not None :
    switcher.connect(args.ip)
else:
    atem_scan()
    atem_connect(input('Input IP address'))
initialize()


#MIDIパッドからの入力をATEMに反映
while True:
    msgh = inport.receive.hex().split()
    if msgh[1] in pgmin:
        num = pgmin.index(msgh) +1
        switcher.setProgramInputVideoSource(0, num)
        print(f"[{time.ctime()}]  PGM Video source: {num}")
    if msgh[1] in pvwin:
        num = pvwin.index(msgh) +1
        switcher.setProgramInputVideoSource(0, num)
        print(f"[{time.ctime()}]  PVW Video source: {num}")
