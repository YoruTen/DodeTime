import json
import time

import beep
import neopixel
import urequests as requests

from imu import MPU6050
from machine import Pin, I2C


p1 = Pin(14, Pin.IN)

with open('config.json') as config_file:
    conf = json.load(config_file)

INT_URL = conf['INT_URL']

beep_pin = conf['BEEP_PIN']
sides = conf['SIDES']

neo_pin = conf['NEO_PIN']
neo_num = conf['NEO_NUM']

S_Data = conf['I2CSDA']
S_Clock = conf['I2CSCL']

i2c = I2C(sda=Pin(S_Data), scl=Pin(S_Clock))
imu = MPU6050(i2c)

neo = neopixel.NeoPixel(Pin(neo_pin), neo_num)


DELAY = 5  # Delay in seconds
alarm = ("G7", "CS7", 0, "G7", "CS7", 0, "G7", "CS7", 0, "G7", "A7", 0)

def angle():
    kAx, kAy = imu.read_angle()
    return (kAx, kAy)

def sound(note):
    buz = beep_pin
    beep.beep(buz, note)


def toggl(TOG_PID):
    try:
        json_data = {"pid":{"value1":TOG_PID}}
        req = requests.post(url=INT_URL, json=json_data)
        req.close()
    except (RuntimeError, TypeError, NameError):
        print("Failed to send data")


def check_interval(kAx, kAy):
    for key in sides:
        #Check in which interval the angle fits
        #Build interval
        T_kAx = (sides[key]["kAx"]-10, sides[key]["kAx"]+10)
        T_kAy = (sides[key]["kAy"]-10, sides[key]["kAy"]+10)
        # print(T_kAx, T_kAy)

        if (T_kAx[0] < kAx < T_kAx[1]) and (T_kAy[0] < kAy < T_kAy[1]):
            DodeState = key
            return DodeState

def main_prog():
    PrevState = "Side0"
    timer = time.time()
    while True:
        try:
            kAx, kAy = angle()
            DodeState = check_interval(kAx, kAy)
            if DodeState is None:
                print("Side not defined", kAx, kAy)
            elif DodeState == PrevState:
                #If the side has not changed
                print("State is the same: ", DodeState)
                dt = time.time()-timer
                pomtime = sides[DodeState]["Timer"]#*60
                print(dt)
                print(pomtime)
                if isinstance(pomtime, str):
                    pass
                elif dt >= pomtime:
                    beep.beep(beep_pin, alarm)
                    g = 1
                    while g != 4:
                        set_color([255, 0, 0])
                        time.sleep(1)
                        g += 1
            elif DodeState != PrevState: # If the side has changed
                print("State is not same, new side: ", DodeState)
                dt = time.time()-timer
                if DodeState == "Side0": # If charging, stop toggl
                    toggl("stop")
                    clear()
                else: # If it's other side then 0, start timer
                    toggl(sides[DodeState]["TOG_ID"])
                    # Set color
                    set_color(sides[DodeState]["Color"])
                # Save new state to previous
                PrevState = DodeState
                timer = time.time()
            time.sleep(DELAY)
        except KeyboardInterrupt:
            break

def clear():
    for i in range(neo_num):
        neo[i] = (0, 0, 0)
        neo.write()

def set_color(color):
    for i in range(neo_num):
        neo[i] = (color[0], color[1], color[2])
        neo.write()

"""
def callback_fall(p):
    print('pin fall change', p)
"""
def callback_rise(p):
    print('pin rise change', p)

p1.irq(trigger=Pin.IRQ_RISING, handler=callback_rise)
#p1.irq(trigger=Pin.IRQ_FALLING, handler=callback_fall)

# Run main program
# main_prog()
# _thread.start_new_thread(main_prog())
