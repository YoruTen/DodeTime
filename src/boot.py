"""
import webrepl
import network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print('connecting to network...')
    wlan.connect('Nudadalen', 'Kaspar2020')
    while not wlan.isconnected():
        pass
print('network config:', wlan.ifconfig())
webrepl.start()
"""