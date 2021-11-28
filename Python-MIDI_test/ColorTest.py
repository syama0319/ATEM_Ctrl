import mido
import time
import argparse
from mido import Message

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', help='MIDI pad model (ex: X)')
args = parser.parse_args()

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

def Color():
    for i in range(1, 89):
        msg = Message('note_on', channel = 0, note = i + 10, velocity = i+38)
        outport.send(msg)
        print(f'[{time.ctime()}] {msg}')
        time.sleep(0.02)
    
initialize()
Color()

while True:
    try:
        msg = inport.receive().hex().split()
        print(msg)
        if msg[2] != '00':
            msg[2] = '15'
        outport.send(Message.from_hex(' '.join(msg)))
        if msg[0] == 'B0':
            outport.send(Message.from_hex('80 12 00'))
        if msg[1] == '0C':
            Color()
        if msg[1] == '0B':
            #Launchpad XのLive Mode化
            outport.send(Message.from_hex('F0 00 20 29 02 0C 0E 00 F7'))
            outport.send(Message.from_hex('F0 00 20 29 02 0C 0B 00 01 F7'))
            outport.close()
            print('end sequence is completed.')
            break
    except AttributeError:
        print('no function is assigned.')
        continue