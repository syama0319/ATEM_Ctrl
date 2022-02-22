#-*- coding:utf-8 -*-
import threading
import time

def send00():
    while True:
        print("ようこそ")
        time.sleep(1)

def send01():
    while True:
        print("ジャパリパー")
        time.sleep(1.5)

if __name__ == "__main__":
    th00 = threading.Thread(target=send00, name="th00", args=())
    th01 = threading.Thread(target=send01, name="th01", args=())
    th00.start()
    th01.start()