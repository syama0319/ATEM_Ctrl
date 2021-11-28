import mido 
import sys
import time
import argparse
import asyncio
from mido import Message

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', help='MIDI pad model (ex: X)')
args = parser.parse_args()

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
mp1 = ('15', '16', '17') #mpはTIE, ON AIR, AUTOの順
mp2 = ('0B', '0C', '0D')


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
    for i in pvwin:
        outport.send(Message.from_hex('90 '+ i +' 15'))
    for i in pgmin:
        outport.send(Message.from_hex('90 '+ i +' 05'))
    for i in range(len(pgmcol)):
        outport.send(Message.from_hex('90 '+pvwcol[i]+' 18'))
        outport.send(Message.from_hex('90 '+pgmcol[i]+' 04'))
    for i in me:
        outport.send(Message.from_hex('90 '+ i +' 0C'))
    outport.send(Message.from_hex('91 '+ftb+' 05'))
    outport.send(Message.from_hex('90 '+cutme+' 09'))
    outport.send(Message.from_hex('90 '+autome+' 09'))
    outport.send(Message.from_hex('90 '+pvwtrans+' 22'))
    outport.send(Message.from_hex('90 '+mp1[0]+' 0C'))
    outport.send(Message.from_hex('90 '+mp1[1]+' 05'))
    outport.send(Message.from_hex('90 '+mp1[2]+' 05'))
    outport.send(Message.from_hex('90 '+mp2[0]+' 0C'))
    outport.send(Message.from_hex('90 '+mp2[1]+' 05'))
    outport.send(Message.from_hex('90 '+mp2[2]+' 05'))
    
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


