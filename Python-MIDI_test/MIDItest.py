import mido 
import sys
import time
import argparse
import asyncio
from mido import Message

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', help='MIDI pad model (ex: X)')
args = parser.parse_args()

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


if args.model is not None:
    outport = mido.open_output(f'Launchpad {args.model} LPX MIDI In')
    inport = mido.open_input(f'Launchpad {args.model} LPX MIDI Out')
else:
    print(f"[{time.ctime()}] Scanning MIDI devices.")
    #port名取得
    ports_o = mido.get_output_names()
    print(f"[{time.ctime()}] FINISHED: {len(ports_o)} MIDI Input devices found.")
    print(f"[{time.ctime()}] {ports_o}")
    ports_i = mido.get_input_names()
    print(f"[{time.ctime()}] FINISHED: {len(ports_i)} MIDI Input devices found.")
    print(f"[{time.ctime()}] {ports_i}")
    port_on = int(input('Which MIDI Output device? [int] : '))
    port_in = int(input('Which MIDI Input device? [int] : '))
    #ports = mido.open_output('Launchpad X LPX MIDI In')
    outport = mido.open_output(ports_o[port_on])
    inport = mido.open_input(ports_i[port_in])

#msg = Message('note_on',channel = 1, note=144, velocity=5, time=480)
#SysExで送りたいときは('sysex', data=(0~127, 0~127, ....))
#16進数にしたいときは msg = Message.from_hex("09 05 ...")

#初期化
def initialize():
    """
    for i in range(1, 99):
        outport.send(Message('note_on', channel = 0, note = i, velocity = 0))
    #Launchpad XのProgrammer Mode化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0E 01 F7'))
    #Launchpad XのAftertouch無効化
    outport.send(Message.from_hex('F0 00 20 29 02 0C 0B 02 01 F7'))

    outport.send(Message.from_hex('90 63 03'))
    """
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
    
initialize()

#with mido.open_output(ports_o[port_on]) as outport:
#    outport.send(msg)
#    outport.send(Message.from_hex("90 40 15"))
#with mido.open_input(ports_i[port_in]) as inport:
#    msg = inport.receive()
#    #outport.send(msg)
#    print(msg)
def Color():
    for i in range(1, 89):
        msg = Message('note_on', channel = 0, note = i + 10, velocity = i)
        outport.send(msg)
        print(f'[{time.ctime()}] {msg}')
        time.sleep(0.02)

async def logo():
    i = 0
    while True:
        print(f'[{time.ctime()}] Waiting..')
        await asyncio.sleep(0.5)
        outport.send(Message('note_on', channel = 2, note = 99, velocity = i))
        i += 1
        if i >= 128:
            i = 0
        #await asyncio.sleep(0.1)

async def main():
    while True:
        try:
            msg = inport.receive().hex().split()
            print(msg)
            if(msg[2] != '00'):
                msg[2] = '15'
            outport.send(Message.from_hex(' '.join(msg)))
            if(msg[0] == 'B0'):
                outport.send(Message.from_hex('80 12 00'))
            if(msg[1] == '0B'):
                #Launchpad XのLive Mode化
                outport.send(Message.from_hex('F0 00 20 29 02 0C 0E 00 F7'))
                outport.send(Message.from_hex('F0 00 20 29 02 0C 0B 00 01 F7'))
                outport.close()
                print('end sequence is completed.')
                break
        except AttributeError:
            print('no function is assigned.')
            continue
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                logo(),
                main()
            )
        )
    finally:
        loop.close()


