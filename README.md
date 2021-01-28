# DodeTime
## Tutorial on how to build a dodecahedron time tracker


This project will give you the basics to create your own dodecahedron time tracking device, the DodeTime, that will upload your tracked time using WiFi. The guide will provide a model that can be 3D-printed, the BOM for the things that you need to put inside and the code that will detect wich side you place the dodecahedron on. The DodeTime will also include a pomodor timer so that you remember to take needed breakes. 

This project should only take a few hours, printing the dodecahedron takes the longest (given that the code works). Otherwise there is minimal amount of soldering and configuration. 


### Objective

Knowing how you spend your time can be useful to help you make changes in your life and make educated decission when you whant to make these change. Even if there are many applications avilable for desktop and mobile, these can be easily forgotten and you maybe change task often and don't whant to pick up your phone everytime. I have tried to track some of my own time but often just left the timers running, so now i wanted to try and make a physical object that was fast and easy to manipulate. 
Therefore during the course [Introduction to Applied Internet of Things](https://lnu.se/kurs/tillampad-internet-of-things-introduktion/distans-sommar/) given by the Linnaeus University I decided to design, code and 3D-print my own version of a time tracker similar to the [TimeFlip](https://timeflip.io/) or the [Timeular](https://timeular.com/)

The plan is to create a physical object that can track your time. The time will be tracked on Ubidots so that you can get a clear overview of how you spend your time.

The DodeTime will also include a small buzzer that can be set as a pomodoro timer to help remind you to take breakes when you have been working on a project for to long.

### Material

Explain all material that is needed. All sensors, where you bought them and their specifications. Please also provide pictures of what you have bought and what you are using.


Example:
| Component                         | Function                      | Approx. Cost                                                       |
| --------------------------------- | ----------------------------- | ------------------------------------------------------------------ |
| Wemos D1 mini                     | Running code and sending data | 5 $ [[Buy it](https://www.aliexpress.com/item/32529101036.html)]   |
| D1 mini battery shield            | Charging a LiPo battery       | 1.5 $ [[Buy it](https://www.aliexpress.com/item/32804528128.html)] |
| 250 mAh LiPo battery              | POWER!                        | 4 $ [[Buy it](https://www.aliexpress.com/item/4000014689691.html)] |
| GY-521 / MPU-6050 - gyro./accel.  | Detect angle of DodeTime      | 1.5 $ [[Buy it](https://www.aliexpress.com/item/32641703712.html)] |
| RGB led                           | Show color of started project |  1 $ [[Buy it](https://www.aliexpress.com/item/32278313170.html)]   |
| Active buzzer                     | Make annoying sounds          | 1 $ [[Buy it](https://www.aliexpress.com/item/32663245562.html)]   |
| Magnetic USB                      | Charging the device           | 2 $ [[Buy it](https://www.aliexpress.com/item/32998516651.html)]   |
| 2 x M2.5 Insert threads and bolts | Fastening the MPU6050         | 1 $                                                                |
| 2 x M2 Insert threads and bolts   | Fastening the D1 mini         | 1 $                                                                |
| Magnets                           | Hold is all togheter          | 1 $ [[Buy it](https://www.aliexpress.com/item/32959402237.html)]   |
| 3D-printed dodecahedron           | The main physical thing       |                                                                    |



For this project I have chosen to work with the Wemos D1 mini device as seen in Fig. 1, it's a small device running MicroPython. It offers a few inputs and outputs that can be used for different purposes. I paired this with a battery sheild that will charge a LiPo battery. 


| ![D1!](https://www.wemos.cc/en/latest/_static/boards/d1_mini_v3.1.0_1_16x16.jpg =180x)| ![D1 Battery Shield](https://www.wemos.cc/en/latest/_images/battery_v1.3.0_1_16x16.jpg)|
| -------- | -------- |
| Fig.1. Wemos D1 mini without headers. www.wemos.cc     | Fig.2. Wemos D1 mini Battery Shield without headers. www.wemos.cc  |

### Computer setup

For the coding I used the [Atom](https://atom.io/) IDE, which is avialable for most operations systems. [Python](https://www.python.org/downloads/) should also be installed if you already don't have it.

Make sure to install drivers for the [CH340](https://www.wemos.cc/en/latest/ch340_driver.html) UBS2TTL chip if you use Windows or Mac OS.

#### REPL
To communicate with the board, this [guide](https://micropython-on-wemos-d1-mini.readthedocs.io/en/latest/setup.html) can help you with the setup.
I setup [Putty](https://www.putty.org/) following this short [guide](https://uplogix.com/docs/local-manager-user-guide/introduction/connecting-to-usb-console-windows-10), mailny change to "serial" and enter the correct COM-port and the buad rate (speed) 115200. 

#### WiFi
For the DodeTime to be able to send data it needs a WiFi connection, this can be done once and the D1 mini will remeber it. This is done via the REPL inteface, following the [guide](https://micropython-on-wemos-d1-mini.readthedocs.io/en/latest/basics.html#network) you can run the following to connect to an existing network, replacing "SSID" and "password".
```
import network
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect("SSID", "password")
```
####  File upload
There is also a guide for [file upload](https://micropython-on-wemos-d1-mini.readthedocs.io/en/latest/basics.html#uploading-files), you can use Ampy or WebREPL which both are described in th linked guide. For Ampy you need Python, with wich you can install Ampy. This can be installed with the following line in a terminal:
```
pip install adafruit-ampy
```
And then you can use it to copy files to your board:
```
ampy --port /dev/ttyUSB0 put yourfile.xxx
```
or if you use windows command line
```
ampy --port COM# put yourfile.xxx
```
I use windows and ran the following commands to upload my files:
```
ampy --port COM7 put main.py
ampy --port COM7 put config.json
ampy --port COM7 put lib\imu.py /lib/imu.py
ampy --port COM7 put lib\beep.py /lib/beep.py
ampy --port COM7 put lib\rgb_led.py /lib/rgb_led.py
ampy --port COM7 put lib\Kalman.py /lib/Kalman.py
ampy --port COM7 put lib\urequests_auth.py /lib/urequests_auth.py
```
#### MicroPython flashing
The Wemos D1 mini should come flashed with micropython firmware. If the firmware have been changed or you need the lastest firmware, you can flash MicroPython firmware by yourself, see guide at [wemos.cc](https://www.wemos.cc/en/latest/tutorials/d1/get_started_with_micropython_d1.html).



### Putting everything together
Here is how everything should be connected to work with the code, if different pins are used this can be changed in the code.
The battery is a placeholder, a 250 mAh battery was used in my case. But an estimation of the unit using about 100 mA wich means the battery will hold for 2.5 hours. A larger batter might fit or optimisation of the code might prolong the battery-life.
![Circuit](https://i.imgur.com/7vsXgaB.png)

Magnets and threads fitted to the 3D-print.
![3D-print](https://i.imgur.com/o8DonEt.jpg)


Magnet USB for charging.
![USB-Magnet](https://i.imgur.com/mVBOXZf.jpg)

Base with corresponding magnet for power.
![Base](https://i.imgur.com/UwSrxs0.jpg)

Cabel and magnets inserted into base.
![Base underside](https://i.imgur.com/Z0KwsMI.jpg)

Main components in the dodecaheadron.
![Components](https://i.imgur.com/0jUjMtI.jpg)

For connecting the magnet to the battery shield a micro-USB was sourced from a old battery pack. Due to poor planning a normal micro-USB did not fit so a non molded contact was used to since it was shorter.
![](https://i.imgur.com/E6BMqwN.jpg)


### Platform

At the moment [Ubidots](https://ubidots.com/) is used to gather the data, the only limit is the 10 sensors per device. Toggl time tracker was planned to be used but due to memory limititations of the esp8266 it was not possible to connect to their service.

Ubidots have several differnet protocals for recivning data, HTTP, MQTT, ect.
Ubidots also offer dashbords that can be configerd to show the recived data in multiple differnt ways.


### The code

Here is the main code, all libraries are avilable on [GitHub](https://github.com/YoruTen/DodeTime).


```python=
import imu
import beep
from network import WLAN
import urequests_auth as requests
import machine
import time
import json
import rgb_led

with open('config.json') as config_file: #Imports configs
    conf = json.load(config_file)
#defines variables
UBI_TOKEN = conf['UBI_TOKEN']
TOG_TOKEN = conf['TOG_TOKEN']
beep_pin = conf['BEEP_PIN']
sides= conf['SIDES']
device = conf['DEVICE']
DELAY = conf['DELAY']  # Delay in seconds
alarm = ("G4","A3",0,"G4","A3",0,"G4","A3",0,"G4","A7",0,)
TOGGL_API = "https://www.toggl.com/api/v8/"
tog_auth=(TOG_TOKEN,"api_token")

def angle(): #function for getting angle
     kAx,kAy = imu.read_angle()
     return (kAx,kAy)

def sound(note):
    buz=beep_pin
    beep.beep(buz, note)
    pass

# Builds the json to send the request # Based on https://help.ubidots.com/en/articles/961994-connect-any-pycom-board-to-ubidots-using-wi-fi-over-http
def build_json(value1, key_value):
    try:
        data = {key_value: {"value": value1}}
        return data
    except:
        prin("Could not build JSON")
        return None

# Sends the request. Please reference the REST API reference https://ubidots.com/docs/api/
def post_var(device, value1, key_value):
    try:
        url = "https://things.ubidots.com/"
        url = url + "api/v1.6/devices/" + device
        headers = {"X-Auth-Token": UBI_TOKEN, "Content-Type": "application/json"}
        data = build_json(key_value, value1)
        if data is not None:
            print(data)
            req = requests.post(url=url, headers=headers, json=data)
            req.close()
            pass
        else:
            print("Failed to send data")
            pass
    except:
        pass

#Tests if the angle  corresponds to defined intevals
def check_interval(kAx, kAy, PrevState):
    for key in sides:
        #Check in which interval the angle fits
        #Build interval
        T_kAx = (sides[key]["kAx"]-10,sides[key]["kAx"]+10)
        T_kAy = (sides[key]["kAy"]-10,sides[key]["kAy"]+10)
        # print(T_kAx, T_kAy)

        if (T_kAx[0] < kAx < T_kAx[1]) and (T_kAy[0] < kAy < T_kAy[1]):
            DodeState = key
            return DodeState

def main_prog():
    PrevState = "Side0"
    timer=time.time()
    while True:
        # try:
        kAx, kAy = angle()
        DodeState = check_interval(kAx, kAy, PrevState)
        if DodeState is None:
            print("Side not defined", kAx, kAy)
            pass
        elif DodeState == PrevState:
            #If the side has not changed
            print("State is the same: ", DodeState)
            dt=time.time()-timer
            pomtime = sides[DodeState]["Timer"]*60
            if type(pomtime) == str:
                 pass
            elif dt >= pomtime: #If the elapsed time is greater than the set time the alarm sounds
                beep.beep(beep_pin,alarm)
                g=1
                while g != 4:
                    rgb_led.setColor([255,0,0],1) #Flashes LED red
                    time.sleep(1)
                    g += 1
                pass
            pass
        elif DodeState != PrevState:
            print("State is not same, new side: ", DodeState)
            dt=time.time()-timer
            if DodeState == "Side0": #If the side is the charging side nothing is done
                pass
            else:#Sends the previous side and the elapsed time
                post_var(device ,dt, sides[PrevState]["Activity"]) 
                pass
            rgb_led.setColor(sides[DodeState]["Color"],DELAY) #Flashes LED for 10 s in project color
            PrevState = DodeState
            timer=time.time() #Sets new time to compare
            pass
        time.sleep(DELAY) #Waits for the time of DELAY before checking if the side has changed
    pass
main_prog() #Starts the main program

```



### Transmitting the data / connectivity

The data is sent everytime it detects that the DodeTime hase been placed on a new side, the orientation is checked every 5 seconds.
It send data over WiFi using HTTP requests.


### Presenting the data

The data sent to Ubidots contain the seconds and the task of the previous side. Data is saved everytime it's sent, with a limit of 4000 times per day.

![Pie Chart](https://i.imgur.com/Wfqjuhl.png)


### Finalizing the design

As it stands right now the project works ok, battery-life might be lacking, and the faces of the DodeTime needs to have symbols for recognising wich timer is activated. Some changes could be done to the 3D-print to fit the USB cable better, also the tolerans for the magnets needs to be increased so that they fit directly, I needed to carve out the holes. The buzzer and the LED are not in place yet, but this only need some soldering.


![Assembled](https://i.imgur.com/HJQsKcI.jpg)

