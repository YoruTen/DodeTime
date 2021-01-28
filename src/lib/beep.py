#Based on http://wiki.micropython.org/Play-Tone and https://forum.pycom.io/topic/802/example-pwm-mariobros
import time
from machine import Pin, PWM

# define frequency for each tone
tones = {"CS7":2217, "G7":3136, "A7":3520}

def beep(buz, note):
    try:
    # set up pin PWM timer for output to buzzer or speaker
        PWMbuz = PWM(Pin(buz))
        for i in note:
            if i == 0:
                PWMbuz.duty(0)
            else:
                tone = tones.get(i, "1000")
                PWMbuz.freq(tone)  # change frequency for change tone
                PWMbuz.duty(200)
            time.sleep(0.150)
        PWMbuz.deinit()
    except:
        PWMbuz.deinit()
