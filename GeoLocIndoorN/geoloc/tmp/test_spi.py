# Simple SPI server for RPi and Decawave DW1000
# Copyright (c) Jeremy P Bentham 2019. See iosoft.blog for details

# To enable SPI1, add dtoverlay=spi1-3cs to /boot/config.txt
# Connector pin numbers:
#       SPI0            SPI1
# GND   25              34
# CS    24 (CE0 - BCM8) 36 (CE2)
# MOSI  19 (BCM10)      38
# MISO  21 (BCM9)       35
# CLK   23 (BCM11)      40
# IRQ   18 (BCM24)      32
# RESET 22 (BCM25)      37 (BCM26)
# NRST  16 (BCM23)      31 (BCM6)

import sys, socket, time, select, spidev, RPi.GPIO as GPIO
from ctypes import c_uint as U32, c_ulonglong as U64

VERSION = "0.13"

SPIF1       = 0,0   # First SPI interface
RST_PIN1    = 11
NRST_PIN1   = 16
IRQ_PIN1    = 13
CS_PIN1     = 36
SPIF2       = 1,2   # Second SPI interface
RST_PIN2    = 37
NRST_PIN2   = 31
IRQ_PIN2    = 32
CS_PIN2     = 36
SPI_SPEED   = 2000000

RESET_VAL   = 0xff  # Values for first network byte
ANS_VAL     = 0xaa
IRQ_VAL     = 0xfe

PORTNUM     = 1401  # Default port (for first SPI interface)
portnum     = PORTNUM
MAXDATA     = 2048

verbose     = False # Global flags
interrupt   = True
connection  = None
SEQLEN      = 2

# Handle pin-change event: set interrupt flag
def irq_handler(chan):
    global interrupt
    interrupt = True
    
# Return string with hex values of bytes    
def hexvals(data):
    return " ".join(["%02X" % b for b in bytearray(data)])

if __name__ == "__main__":
    # Handle command-line args
    print("SPI_SERVER v" + VERSION)
    for arg in sys.argv[1:]:
        if arg.lower() == "-v":
            verbose = True
        elif arg[0].isdigit():
            portnum = int(arg)
        else:
            print("Unrecognised argument '%s'" % arg)

    # Set up SPI interface; use 2nd if 2nd port number
    spif = SPIF1 if portnum==PORTNUM else SPIF2
    rst_pin = RST_PIN1 if portnum==PORTNUM else RST_PIN2
    nrst_pin = NRST_PIN1 if portnum==PORTNUM else NRST_PIN2
    irq_pin = IRQ_PIN1 if portnum==PORTNUM else IRQ_PIN2
    cs_pin = CS_PIN1 if portnum==PORTNUM else CS_PIN2
    spi = spidev.SpiDev()
    spi.open(*spif)
    spi.max_speed_hz = SPI_SPEED
    spi.mode = 0

    # Set up board I/O
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(rst_pin, GPIO.OUT)
    GPIO.setup(nrst_pin, GPIO.IN)
    GPIO.setup(irq_pin, GPIO.IN)
    GPIO.setup(cs_pin, GPIO.OUT)
    GPIO.output(cs_pin, 1)
    GPIO.add_event_detect(irq_pin, GPIO.RISING, callback=irq_handler)

    DEV_ID    = 0x0, 4, None,(("REV",U32, 4),("VER",U32, 4),("MODEL",U32, 8), ("RIDTAG",U32,16))

    #resp = bytearray(spi.xfer(DEV_ID))
    print(DEV_ID)
    resp = spi.xfer2(5*[0])
    print("Device ID: %s" % hexvals(resp))

    # Main loop
    toff = time.time()
    while True:
        resp = []
        # If interrupt has been received, send single-byte message
        interrupt=True
        if interrupt:
            tim = time.time() - toff
            print("%1.3f IRQ pin %u" % ((tim % 10.0), irq_pin))
#            sock.xmit_irq()
            interrupt = False
        # Check for incoming commands
        for data in sock.receive():
            # Single-byte command is a reset
            if len(data) == 1:
                if data[0] == RESET_VAL:
                    GPIO.output(rst_pin, 1)
                    GPIO.setup(nrst_pin, GPIO.OUT)
                    GPIO.output(nrst_pin, 0)
                    print("Reset pin %u" % rst_pin)
                    toff = time.time()
                    interrupt = False
                else:
                    GPIO.output(rst_pin, 0)
                    GPIO.setup(nrst_pin, GPIO.IN)
                resp = [data[0]]
            # Multi-byte command: send to SPI
            elif len(data) > 1:
                resp = spi.xfer(data)
                # Change 1st byte of read response to be 'AA'
                if data[0] & 0x80 == 0:
                    resp[0] = ANS_VAL
            if resp:
                sock.send(resp)
        if len(resp):
            sock.xmit(sock.txdata)
    GPIO.cleanup()
    sock.close()
# EOF
