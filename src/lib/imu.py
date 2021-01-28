import time
import math
from Kalman import KalmanAngle
from machine import I2C
from math import atan, pi, pow, sqrt

MPU6050_ADDRESS_AD0_LOW = 0x68  # address pin low (GND)
MPU6050_ADDRESS_AD0_HIGH = 0x69  # address pin high (VCC)
MPU6050_DEFAULT_ADDRESS = MPU6050_ADDRESS_AD0_LOW

kalmanX = KalmanAngle()
kalmanY = KalmanAngle()

radToDeg = 57.2957786
kalAngleX = 0
kalAngleY = 0
#some MPU6050 Registers and their Address
PWR_MGMT_1 = 0x6B
PWR_MGMT_2 = 0x6C
SMPLRT_DIV = 0x19
CONFIG = 0x1A
GYRO_CONFIG = 0x1B
MOT_THR = 0x1F
MOT_DUR = 0x20
ZRMOT_THR = 0x21
ZRMOT_DUR = 0x22
MOT_DETECT_CTRL = 0x69
INT_PIN_CFG = 0x37
INT_ENABLE = 0x38
INT_STATUS = 0x3A
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H = 0x43
GYRO_YOUT_H = 0x45
GYRO_ZOUT_H = 0x47
ACCEL_CONFIG = 0x1c

# PWR_MGMT_1
PWR1_DEVICE_RESET_BIT = 7
PWR1_SLEEP_BIT        = 6
PWR1_CYCLE_BIT        = 5
PWR1_TEMP_DIS_BIT     = 3

# PWR_MGMT_2
PWR2_LP_WAKE_CTRL_BIT    = 7
PWR2_LP_WAKE_CTRL_LENGTH = 2
PWR2_STBY_XA_BIT         = 5
PWR2_STBY_YA_BIT         = 4
PWR2_STBY_ZA_BIT         = 3
PWR2_STBY_XG_BIT         = 2
PWR2_STBY_YG_BIT         = 1
PWR2_STBY_ZG_BIT         = 0

# INT_ENABLE
MOT_EN_BIT = 6
ZMOT_EN_BIT = 5

# INT_PIN_CFG
INT_LEVEL_BIT = 7
INT_OPEN_BIT = 6
LATCH_INT_EN_BIT = 5
INT_RD_CLEAR_BIT = 4

# INT_STATUS
MOT_INT_BIT = 6
ZMOT_INT_BIT = 5

# ACCEL_CONFIG
ACCEL_HPF_BIT = 2 # Starting bit
ACCEL_HPF_LENGTH = 3

# CONFIG
DLPF_CFG_BIT = 2 # Starting bit
DLPF_CFG_LENGTH = 3

class MPUException(OSError):
    """MPUExeption."""
    pass

class MPU6050():
    #Read the gyro and acceleromater values from MPU6050
    def __init__(self, i2c=None, address=MPU6050_DEFAULT_ADDRESS):
        """Init MPU6050 instance."""
        if isinstance(i2c, I2C):
            self.i2c = i2c

        self.address = address
        self.buf = bytearray(1)
        self.reset_flag = False

        #Write to power management register
        self.i2c.writeto_mem(self.address, PWR_MGMT_1, b'\x00')


        #write to sample rate register
        self.i2c.writeto_mem(self.address, SMPLRT_DIV, b'\x07')

        #Write to Configuration register
        #Setting DLPF (last three bit of 0X1A to 6 i.e '110' It removes the noise due to vibration.) https://ulrichbuschbaum.wordpress.com/2015/01/18/using-the-mpu6050s-dlpf/
        self.i2c.writeto_mem(self.address, CONFIG, b'\x00')
        #self.writeto_mem(self.address, CONFIG, int('0000110',2))

        #Write to Gyro configuration register
        self.i2c.writeto_mem(self.address, GYRO_CONFIG, b'\x23')

    def read_raw_data(self, addr):
        #Accelero and Gyro value are 16-bit
        high = self.i2c.readfrom_mem(self.address, addr, 1)
        low = self.i2c.readfrom_mem(self.address, addr+1, 1)
        #concatenate higher and lower value
        val = high[0] << 8 | low[0]

        #we're expecting a 16 bit signed int (between -32768 to 32768).
        #This step ensures 16 bit unsigned int raw readings are resolved.
        if val > 32768:
            val = val - 65536
        return val

    def read_angle(self):
        time.sleep(1)
        #Read Accelerometer raw value
        accX, accY, accZ, gyroX, gyroY, gyroZ = self.read_values_helper()

        roll = math.atan2(accY, accZ) * radToDeg
        pitch = math.atan2(-accX, accZ) * radToDeg

        #print(roll)
        kalmanX.setAngle(roll)
        kalmanY.setAngle(pitch)
        gyroXAngle = roll
        gyroYAngle = pitch
        compAngleX = roll
        compAngleY = pitch

        timer = time.time()
        flag = 0
        while True:
            if flag > 100: #Problem with the connection
                print("There is a problem with the connection")
                flag = 0
                continue
            try:
                accX, accY, accZ, gyroX, gyroY, gyroZ = self.read_values_helper()

                dt = time.time() - timer
                timer = time.time()
                roll = math.atan2(accY, accZ) * radToDeg
                pitch = math.atan2(-accX, accZ) * radToDeg

                gyroXRate = gyroX/131
                gyroYRate = gyroY/131
                gyroZRate = gyroZ/131

                kalAngleX = kalmanX.getAngle(roll, gyroXRate, dt)
                kalAngleY = kalmanY.getAngle(pitch, gyroYRate, dt)

                #angle = (rate of change of angle) * change in time
                gyroXAngle = gyroXRate * dt
                gyroYAngle = gyroYAngle * dt

                #compAngle = constant * (old_compAngle + angle_obtained_from_gyro) + constant * angle_obtained from accelerometer
                compAngleX = 0.93 * (compAngleX + gyroXRate * dt) + 0.07 * roll
                compAngleY = 0.93 * (compAngleY + gyroYRate * dt) + 0.07 * pitch

                if ((gyroXAngle < -180) or (gyroXAngle > 180)):
                    gyroXAngle = kalAngleX
                if ((gyroYAngle < -180) or (gyroYAngle > 180)):
                    gyroYAngle = kalAngleY

                #print("Angle X: " + str(int(kalAngleX))+"   " +"Angle Y: " + str(int(kalAngleY)))
                #print(str(roll)+"  "+str(gyroXAngle)+"  "+str(compAngleX)+"  "+str(kalAngleX)+"  "+str(pitch)+"  "+str(gyroYAngle)+"  "+str(compAngleY)+"  "+str(kalAngleY))
                time.sleep(0.005)
                return (kalAngleX, kalAngleY)
            except:
                flag += 1

    def read_values_helper(self):
        #Read Accelerometer raw value
        accX = self.read_raw_data(ACCEL_XOUT_H)
        accY = self.read_raw_data(ACCEL_YOUT_H)
        accZ = self.read_raw_data(ACCEL_ZOUT_H)
        #Read Gyroscope raw value
        gyroX = self.read_raw_data(GYRO_XOUT_H)
        gyroY = self.read_raw_data(GYRO_YOUT_H)
        gyroZ = self.read_raw_data(GYRO_ZOUT_H)
        return (accX, accY, accZ, gyroX, gyroY, gyroZ)

    def read_bit(self, register, bit_num):
        """Read a single bit from an 8-bit device register."""
        self.i2c.readfrom_mem_into(self.address, register, self.buf)
        b = self.buf[0]
        b & (1 << bit_num)
        b >>= bit_num
        return b

    def write_bit(self, register, bit_num, data):
        """Write a single bit in an 8-bit device register."""
        self.buf = self.read_byte(register)
        b = self.buf[0]
        b = (b | (1 << bit_num)) if (data != 0) else (b & ~(1 << bit_num))
        return self.write_byte(register, b)

    def read_bits(self, register, bit_start, length):
        """Read multiple bits from an 8-bit device register."""
        self.i2c.readfrom_mem_into(self.address, register, self.buf)
        mask = ((1 << length) - 1) << (bit_start - length + 1)
        b = self.buf[0]
        b &= mask
        b >>= (bit_start - length + 1)
        return b

    def write_bits(self, register, bit_start, length, data):
        """Write multiples bits in an 8-bit device register."""
        self.buf = self.read_byte(register)
        b = self.buf[0]
        mask = ((1 << length) - 1) << (bit_start - length + 1)
        data <<= (bit_start - length + 1)
        data &= mask
        b &= ~(mask)
        b |= data
        return self.write_byte(register, b)

    def read_byte(self, register):
        """Read single byte from an 8-bit device register."""
        self.i2c.readfrom_mem_into(self.address, register, self.buf)
        return self.buf

    def write_byte(self, register, data):
        """Write a single byte in an 8-bit device register."""
        data = bytearray([data])
        self.i2c.writeto_mem(self.address, register, data)
        if (data == self.read_byte(register)) or (self.reset_flag):
            self.reset_flag = False
            return True
        raise MPUException()

    def read_bytes(self, register, length):
        """Read single byte from an 8-bit device register."""
        return self.i2c.readfrom_mem(self.address, register, length)

    def interrupt_init(self):
        "Make sure accel is running"
        self.set_cycle_enabled(0)
        self.set_sleep_enabled(0)
        self.set_axis_standby_enabled(PWR2_STBY_XA_BIT, 0)
        self.set_axis_standby_enabled(PWR2_STBY_YA_BIT, 0)
        self.set_axis_standby_enabled(PWR2_STBY_ZA_BIT, 0)
        "Set accel HPF to reset settings"
        self.set_acceleration_highpassfilter(0)
        "Set Accel LPF setting to 256Hz bandwidth"
        self.set_acceleration_lowpassfilter(0)
        "Set interrupt style"
        self.set_interrupt_mode(0)
        self.set_interrupt_drive(0)
        self.set_interrupt_latch(1)
        self.set_interrupt_clear(0)
        "Set Motion interrupt to enable"
        self.set_motion_detection_interrupt_enabled(1)
        "Set motion duration"
        self.set_motion_detection_duration(1)
        "Set motion threshold"
        self.set_motion_detection_threshold(100)

        """Delay"""
        time.sleep_ms(1)
        "Set accel HPF to HOLD"
        self.set_acceleration_highpassfilter(7)
        "Set frequency of wakeup"
        #self.i2c.writeto_mem(self.address, PWR_MGMT_2, bytearray([1000111]))
        """
        self.set_low_power_wake_control(1)
        self.set_accel_x_standby_enabled(1)
        self.set_accel_y_standby_enabled(1)
        self.set_accel_z_standby_enabled(1)
        """
        "Enable cycle mode"
        #self.set_cycle_enabled(1)
        #self.set_sleep_enabled(0)
        #self.set_temperature_sensor_disabled(1)

        """
        self.set_zero_motion_detection_interrupt_enabled(1)
        self.set_zero_motion_detection_threshold(10)
        self.set_zero_motion_detection_duration(20)
        """

    def set_motion_detection_interrupt_enabled(self, enabled):
        """
        Set Data Ready interrupt enabled.

        0 | Disabled
        1 | Enabled
        """
        return self.write_bit(INT_ENABLE, MOT_EN_BIT, enabled)

    # INT_PIN_CFG
    def set_interrupt_mode(self, mode):
        """
        Set interrupt logic level.

        0 | HIGH
        1 | LOW
        """
        return self.write_bit(INT_PIN_CFG, INT_LEVEL_BIT, mode)

    def set_interrupt_drive(self, drive):
        """
        Set interrup drive level.

        0 | PUSH-PULL
        1 | OPEN DRAIN
        """
        return self.write_bit(INT_PIN_CFG, INT_OPEN_BIT, drive)

    def set_interrupt_latch(self, enable):
        """
        Configures interrupt latch mode. When this bit is equal to 0, 
        the INT pin emits a 50us long pulse. When this bit is equal to 1, 
        the INT pin is held high until the interrupt is cleared.

        0 | 50us long pulse
        1 | high until cleared
        """
        return self.write_bit(INT_PIN_CFG, LATCH_INT_EN_BIT, enable)

    def set_interrupt_clear(self, enable):
        """
        Configures interrupt read clear mode. 
        When this bit is equal to 0, interrupt status bits are 
        cleared only by reading INT_STATUS (Register 58). 
        When this bit is equal to 1, interrupt status bits are 
        cleared on any read operation.

        0 | INT_STATUS
        1 | read operation
        """
        return self.write_bit(INT_PIN_CFG, INT_RD_CLEAR_BIT, enable)

    def set_motion_detection_threshold(self, level):
        """
        8-bit unsigned value. Specifies the Motion detection threshold

        0-255 | level

        """
        return self.write_byte(MOT_THR, level)

    def set_motion_detection_duration(self, level):
        """
        8-bit unsigned value. Specifies the Motion detection duration

        0-1 | level

        """
        return self.write_byte(MOT_DUR, level)

    def set_acceleration_highpassfilter(self, value):
        """
        3-bit unsigned value.
        Selects the Digital High Pass Filter configuration

        0 = Reset
        1 = On @ 5 Hz
        2 = On @ 2.5 Hz
        3 = On @ 1.25 Hz
        4 = On @ 0.63 Hz
        7 = Hold

        """
        return self.write_bits(ACCEL_CONFIG, ACCEL_HPF_BIT, ACCEL_HPF_LENGTH, value)

    def set_acceleration_lowpassfilter(self, value):
        """
        3-bit unsigned value.
        Selects the Digital Low Pass Filter configuration
        
        0 = 260 Hz, 0 ms / 256 Hz, 0.98 ms, 8 kHz
        1 = 184 Hz, 2.0 ms / 188 Hz, 1.9 ms, 1 kHz
        2 = 94 Hz, 3.0 ms / 98 Hz, 2.8 1 ms, kHz
        3 = 44 Hz, 4.9 ms / 42 Hz, 4.8 1 ms, kHz
        4 = 21 Hz, 8.5 ms / 20 Hz, 8.3 1 ms, kHz
        5 = 10 Hz, 13.8 ms / 10 Hz, 13.4 ms, 1 kHz
        6 = 5 Hz, 19.0 ms / 5 Hz, 18.6 1 ms, kHz
        7 = RESERVED / RESERVED, 8 kHz
        """
        return self.write_bits(CONFIG, DLPF_CFG_BIT, DLPF_CFG_LENGTH, value)

    # PWR_MGMT_2
    def set_low_power_wake_control(self, frec):
        """
        Set frequency of wake-ups during Accel Only Low Power Mode.

        0 | 1.25 Hz
        1 | 5    Hz
        2 | 20   Hz
        3 | 40   Hz
        """
        return self.write_bits(PWR_MGMT_2,
                               PWR2_LP_WAKE_CTRL_BIT,
                               PWR2_LP_WAKE_CTRL_LENGTH,
                               frec)

    def set_axis_standby_enabled(self, axis_bit, enabled):
        """
        Set axis accelerometer standby mode.

        0 | Disabled
        1 | Enabled
        """
        return self.write_bit(PWR_MGMT_2,
                              axis_bit,
                              enabled)

    # PWR_MGMT_1
    def device_reset(self):
        """
        Reset all internal registers to their default values.

        The bit automatically clears to 0 once the reset is done.

        Note:
        When using SPI interface, user should use DEVICE_RESET (register 107)
        as well as SIGNAL_PATH_RESET (register 104) to ensure the reset is
        performed properly.
        The sequence used should be:
          1. Set DEVICE_RESET = 1 (PWR_MGMT_1)
          2. Wait 100ms
          3. Set GYRO_RESET = ACCEL_RESET = TEMP_RESET = 1 (SIGNAL_PATH_RESET)
          4. Wait 100ms
        """
        self.reset_flag = True
        return self.write_bit(PWR_MGMT_1,
                              PWR1_DEVICE_RESET_BIT,
                              True)

    def set_sleep_enabled(self, enabled):
        """
        Set sleep mode status.

        0 | Disabled
        1 | Enabled
        """
        return self.write_bit(PWR_MGMT_1,
                              PWR1_SLEEP_BIT,
                              enabled)

    def set_cycle_enabled(self, enabled):
        """
        Set cycle eneabled.
        
        0 | Disabled
        1 | Enabled
        """
        return self.write_bit(PWR_MGMT_1,
                              PWR1_CYCLE_BIT,
                              enabled)

    def set_temperature_sensor_disabled(self, disabled):
        """
        Set temperature sensor disabled.

        0 | Enabled
        1 | Disabled
        """
        return self.write_bit(PWR_MGMT_1,
                              PWR1_TEMP_DIS_BIT,
                              disabled)

    def get_motion_interrupt(self):
        """
        Get I2C Master interrupt status.

        This bit automatically sets to 1 when an I2C Master interrupt has been
        enerated.For a list of I2C Master interrupts, please refer to
        Register 54.
        The bit clears to 0 after the register has been read.
        """
        return self.read_bit(INT_STATUS,
                             MOT_INT_BIT)