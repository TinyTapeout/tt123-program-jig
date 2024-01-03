'''
TT123 prognburn main and REPL utils
(C) 2023 Pat Deegan, https://psychogenic.com
'''

import os
from driver import Driver
import ttconfig as conf 
import time
import testseq as test



def burn():
    d = Driver.get()
    return d.writeToFlash(conf.FirmwareFile)

def verify():
    d = Driver.get()
    return d.verifyFlash(conf.FirmwareFile)
    
def awaitStart(blinkLED):
    d = Driver.get()
    d.awaitButtonPress()
    while not d.buttonPressed:
        blinkLED.blink() 
        time.sleep(0.8) 
        
    print("HO")
    
    
    
def flagFileDelete(filepath:str):
    print(f"Deleting startup flag file {filepath}")
    try:
        os.unlink(filepath)
    except OSError:
        print('Was not present')
        
def flagFileCreate(filepath:str):
    print(f"Touching startup flag file {filepath}")
    with open(filepath, 'w') as f:
        f.write('This file triggers behaviour on startup')
        f.close()

def flagFilePresent(filepath:str):
    try:
        f = open(filepath)
        f.close()
        return True
    except OSError:
        pass 
        
    return False
    
def doBurnFileDelete():
    flagFileDelete(conf.BurnOnStartupFile)
def doBurnFileCreate():
    flagFileCreate(conf.BurnOnStartupFile)
def doBurnFilePresent():
    return flagFilePresent(conf.BurnOnStartupFile)
        
def loopOnStartupDelete():
    flagFileDelete(conf.LoopOnStartupFile)
def loopOnStartupCreate():
    flagFileCreate(conf.LoopOnStartupFile)
def loopOnStartFilePresent():
    return flagFilePresent(conf.LoopOnStartupFile)
    
    
    
def boardInit():
    DoBurn = True
    
    d = Driver.get()
    d.clearFlash()
    d.pink.on()
    d.red.on()
    d.green.on()
    # a chance to abort
    time.sleep(1)
    d.pink.off()
    d.red.off()
    d.green.off()
    
    DoBurn = doBurnFilePresent()
    
    if d.button or not DoBurn:
        DoBurn = False
        d.green.flash(5) 
        awaitStart(d.green)
    else:
        awaitStart(d.pink) 
    
    if DoBurn:
        print("BURN")
        d.red.on()
        try:
            d.writeToFlash(conf.FirmwareFile)
        except OSError:
            print("Flash access FAILURE")
            for i in range(10):
                d.green.toggle()
                d.pink.toggle()
                time.sleep(0.25) 
                d.red.flash(3) 
                
            
            d.green.off()
            d.pink.off()
            d.red.on()
            return False
        print("DONE")
        time.sleep(0.5) 
        d.red.off()
    
    if not verify():
        for i in range(5):
            d.red.flash(5, 0.2) 
            time.sleep(1)
    else:
        d.green.flash(5)
        
        
def testInverter():
    d = Driver.get()
    inSeq = test.InverterSequence(d)
    print(f'Test: {inSeq.name}')
    
    d.red.blink()
    awaitStart(d.pink)
    if inSeq.run():
        print("Test success!")
        return True 
        
    return False
    

def testManual():
    d = Driver.get()
    inSeq = test.ManualClockSequence(d)
    print(f'Test: {inSeq.name}')
    
    d.red.blink()
    awaitStart(d.pink)
    if inSeq.run():
        print("Test success!")
        return True
    
    return False

def testHello():
    d = Driver.get()
    inSeq = test.HelloSequence(d)
    print(f'Test: {inSeq.name}')
    
    d.red.blink()
    awaitStart(d.pink)
    if inSeq.run():
        print("Test success!")
        return True 
    return False
        
        
def testAll():
    testInverter()
    testManual()
    testHello()
    
def flashEnd():
    d = Driver.get()
    dly = 0.08
    for n in range(4):
        for ld in d.pins.leds:
            ld.on()
            time.sleep(dly)
        time.sleep(dly) 
        for ld in d.pins.leds:
            ld.off()
            time.sleep(dly)
        time.sleep(dly) 
    
def boardLoop():
    boardInit()
    if conf.EnableTesting:
        testAll()
    flashEnd()
    
if loopOnStartFilePresent():
    while True:
        boardLoop()
        time.sleep(1)
        
    

    
    