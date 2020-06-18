import sys, time, os
from ctypes import sizeof, LittleEndianStructure as Structure, Union
from ctypes import c_ubyte as U8, c_short as U16, c_ulonglong as U64
from dw1000_regs import Reg, DW1000, msdelay
from dw1000_spi import Spi

# Specify SPI interfaces:
#   "UDP", "<IP_ADDR>", <PORT_NUM>
SPIF1       = "UDP", "192.168.0.117", 1401
SPIF2       = "UDP", "192.168.0.211", 1401

red="192.168.1."

stream = os.popen('sudo nmap -T5 -sP '+red+'0/24 -oG - | awk \'/Up$/{print $2}\'')
ips = stream.read()
print (ips)
nodos=[]

if __name__ == "__main__":
    for ip in ips.splitlines():
        try:
            print ("trying "+ip)
            SPIX = "UDP", ip, 1401
            spix = Spi(SPIX, '1')
            dwx = DW1000(spix)
            if dwx.test_irq():
                nodos.append(ip)
        except:
                pass
    print(nodos)

# EOF


