'''
TT123 prognburn test sequence
(C) 2023 Pat Deegan, https://psychogenic.com
'''
from driver import Driver
import time
class Sequence:
    
    def __init__(self, name:str, d:Driver, expectedList:list):
        self.driver = d
        self.name = name
        self.step = 0
        self.expected = expectedList
    
    def showSuccess(self):
        self.driver.green.blink()
        
    def completeSuccess(self):
        self.driver.green.flash(10, 0.05)
        
    def run(self):
        self.step = 0
        if self.driver.outputs != self.expected[0]:
            print('Starting in a bad place')
            self.driver.red.flash(3)
        else:
            print('1st good')
            self.showSuccess()
            self.step += 1
        
        while self.step < len(self.expected):
            print(f'Step {self.step+1}')
            val = self.driver.awaitOutputChange()
            if val is None:
                print('Timeout')
                self.driver.red.flash()
                continue
            
            if val == self.expected[self.step]:
                #print("good")
                self.showSuccess()
                self.step += 1
            else:
                print(f'Failed test {self.name} on step {self.step + 1}: {val} != {self.expected[self.step]}')
                self.driver.awaitButtonPress()
                while not self.driver.buttonPressed:
                    self.driver.red.flash(3)
                    time.sleep(0.5)
                    
                print("Button press: BACK!")
                        
        self.completeSuccess()
        return True
        
        
class InverterSequence(Sequence):
    def __init__(self, d:Driver):
        super().__init__('Inverter', d, 
            [
            0,
            128,
            192,
            224,
            240,
            248,
            252,
            254,
            255,
            254,
            255,
            253,
            255
        ])
                    
class ManualClockSequence(Sequence):
    
    def __init__(self, d:Driver):
        super().__init__('ManualClock', d, 
            [
            0,
            1
            ])
            
class HelloSequence(Sequence):
    
        
    def __init__(self, d:Driver):
        super().__init__('Hello', d, 
        [
            116, # -- first of sequence
            128,
            121,
            128,
            56,
            128,
            56,
            128,
            63,
            128,
            0,
            128,
            0,
            128
        ])
        self.sequenceStart = self.expected[0]
        
    def showSuccess(self):
        print('!', end='')
        return # print("good")
        
    def run(self):
        attempts = 0
        val = 0
        print(f'Waiting for first value {self.sequenceStart}')
        while attempts < 30 and val != self.sequenceStart:
            val = self.driver.awaitOutputChange()
            if val is not None and val != self.sequenceStart:
                attempts += 1
                self.driver.red.toggle()
            elif val == self.sequenceStart:
                self.driver.red.off()
                self.driver.pink.off()
            else:
                self.driver.pink.toggle()
                
        
        if val != self.sequenceStart:
            self.driver.red.flash(10) 
            print("Never saw start")
            return False
        
        return super().run()
        
        




