'''
TT123 prognburn Driver implementation
(C) 2023 Pat Deegan, https://psychogenic.com
'''
from machine import Pin, SPI
import lib.winbond as wb
import ttconfig as conf 
import time

class LED:
    def __init__(self, p:Pin):
        self.pin = p
        self.pin.init(Pin.OUT)
        self.off()
    
    def set(self, to:bool):
        if to:
            self.pin(1)
        else:
            self.pin(0)
    def off(self):
        self.set(False)
    
    def on(self):
        self.set(True)
        
    def toggle(self):
        self.pin.toggle()
        
    def flash(self, num:int=2, dly:float=0.1):
        for i in range(num):
            self.on()
            time.sleep(dly) 
            self.off()
            time.sleep(dly)
            
    def blink(self):
        self.flash(1, 0.06)
            
    
                  
class PlatformPins:
    def __init__(self):
        self.cs = Pin(1)
        self.sck = Pin(2)
        self.mosi = Pin(3)
        self.miso = Pin(4)
        self.outputs = [
            Pin(9),
            Pin(8),
            Pin(7),
            Pin(6),
            Pin(22),
            Pin(26),
            Pin(27),
            Pin(28),
        ]
        self.inputs = [
            Pin(14),
            Pin(15),
            Pin(16),
            Pin(17),
            Pin(18),
            Pin(19),
            Pin(20),
            Pin(21),
        ]
        self.leds = [
        ]
        
        
        self.button = self.inputs[0]
        
        
    def readOut(self):
        v = 0
        for i in range(len(self.outputs)):
            if self.outputs[i]():
                v |= (1 << i)
        
        return v
        
      
    def begin(self):
        pu = None # Pin.PULL_DOWN
        for p in self.inputs:
            p.init(Pin.IN, pull=pu)
        
        for p in self.outputs:
            p.init(Pin.IN, pull=pu)
            
        
        self.leds = [
            LED(self.inputs[5]),
            LED(self.inputs[6]),
            LED(self.inputs[7]),
        ]
        
    def outputIRQs(self, cb):
        for p in self.outputs:
            p.irq(cb)
    
            
        

_driverSingleton = None
class Driver:
    def __init__(self, baudrate:int=conf.FlashBaudrate):
        self.pins = PlatformPins()
        self._baudrate = baudrate
        self._spi = None 
        self._flash = None 
        self.passthrough_enable = conf.UsingHKSPI
        self.pins.begin()
        self._buttonpressed = False
        self._outputIRQsOn = False
        self._outputChangeRegistered = False
        self._outputSettleTimeSecs = 0.005
    
    @classmethod
    def get(cls):
        global _driverSingleton
        if _driverSingleton is None:
            _driverSingleton = Driver()
        return _driverSingleton
    
    
    @property 
    def passthrough_enable(self):
        return wb.W25QFlash.USING_HKSPI
        
    @passthrough_enable.setter 
    def passthrough_enable(self, setTo:bool):
        wb.W25QFlash.USING_HKSPI = setTo
        
    
    @property 
    def red(self) -> LED:
        return self.pins.leds[0]
    
    @property 
    def pink(self) -> LED:
        return self.pins.leds[1]
        
    @property 
    def green(self) -> LED:
        return self.pins.leds[2]
        
    @property 
    def outputs(self):
        return self.pins.readOut()
        
    def _outputChanged(self, pin):
        self._outputChangeRegistered = True
        
    def awaitOutputChange(self, timeoutSecs:int=10, settleTimeSecs:float=None):
        if not self._outputIRQsOn:
            self.pins.outputIRQs(self._outputChanged)
        
        if settleTimeSecs is None:
            settleTimeSecs = self._outputSettleTimeSecs
        self._outputChangeRegistered = False
        tNow = time.ticks_ms()
        tMax = tNow + (timeoutSecs * 1000)
        while tNow < tMax:
            if not self._outputChangeRegistered:
                time.sleep(0.005)
                tNow  = time.ticks_ms()
            else:
                # a change was registered
                time.sleep(settleTimeSecs)
                return self.outputs 
        
        return None 
        
    @property 
    def spi(self):
        if self._spi is None:
            self._spi = SPI(0,
                  baudrate=self._baudrate,
                  polarity=1,
                  phase=1,
                  bits=8,
                  # firstbit=machine.SPI.MSB,
                  sck=self.pins.sck,
                  mosi=self.pins.mosi,
                  miso=self.pins.miso)
        return self._spi
        
    @property 
    def flash(self) -> wb.W25QFlash:
        if self._flash is None:
            self._flash = wb.W25QFlash(spi=self.spi, 
                cs=self.pins.cs, baud=self._baudrate, 
                software_reset=True)
        return self._flash
        
    def clearFlash(self):
        self._flash = None
        
    @property 
    def button(self):
        return self.pins.button()
        
    def _buttonPressCb(self, pin):
        self._buttonpressed = True 
        pin.irq(handler=None)
        
    def awaitButtonPress(self):
        self.clearButtonPress()
        self.pins.button.irq(self._buttonPressCb, trigger=Pin.IRQ_RISING)
        
    @property 
    def buttonPressed(self):
        return self._buttonpressed
        
    def clearButtonPress(self):
        self._buttonpressed = False
        
        
        
    def readFlashTo(self, outfile:str, start_block=0, size=2400):
        block_size = wb.W25QFlash.BLOCK_SIZE
        if size % block_size:
            cnt = (size // block_size) + 1
            size = cnt * block_size 
            
        num_blocks = size // block_size
        
        blocks_written = 0
        with open(outfile, 'wb') as f:
            for i in range(num_blocks):
                print('-', end='')
                buf = bytearray(block_size)
                self.flash.readblocks(i + start_block, buf)
                f.write(buf)
                print('.', end='')
                blocks_written += 1
                
            print(f'\ndone: {i} blocks written to {outfile}')
            f.close()
            
        return blocks_written
        
    def writeToFlash(self, infilepath:str, start_sector=0):
        sector_size = wb.W25QFlash.SECTOR_SIZE
        sector_count = 0
        all_read = False
        with open(infilepath, 'rb') as f:
            print('-', end='')
            buf = f.read(sector_size)
            if all_read or buf is None or not len(buf):
                f.close()
                print(f'\ndone: {sector_count} sectors written')
                return 
            buflen = len(buf)
            if buflen < sector_size:
                all_read = True 
                buf = buf + bytearray(sector_size - len(buf))
            
                
            self.flash.writesector(start_sector + sector_count, buf)
            sector_count += 1
            
        return sector_count
        
    def verifyFlash(self, firmwarefilepath:str, start_block:int=0):
        
        block_size = wb.W25QFlash.BLOCK_SIZE
        block_count = 0
        all_done = False
        with open(firmwarefilepath, 'rb') as vfile:
            origbuf = vfile.read(block_size)
            flashbuf = bytearray(block_size)
            
            if all_done or not origbuf or not len(origbuf):
                return True
            
            self.flash.readblocks(block_count + start_block, flashbuf)
            
            readlen = len(origbuf)
            if readlen < block_size:
                # only got a partial block, last read
                flashbuf = flashbuf[:readlen]
                all_done = True
                
            if flashbuf != origbuf:
                print(f'Mismatch in buf at block count {block_count}')
                return False
            
            block_count += 1
        
        return True
    
            
            