import sys, time, os, ast, re, statistics as st, pymysql, uuid, netifaces as ni, numpy as np
from ctypes import sizeof, LittleEndianStructure as Structure, Union
from ctypes import c_ubyte as U8, c_short as U16, c_ulonglong as U64
from dw1000_regs import Reg, DW1000, msdelay
from dw1000_spi import Spi
from sklearn import manifold

# Specify SPI interfaces:
#   "UDP", "<IP_ADDR>", <PORT_NUM>
SPIF1       = "UDP", "192.168.0.117", 1401
SPIF2       = "UDP", "192.168.0.211", 1401

ifaces=ni.interfaces()
ifc=[]
prio="";
lip="";
for i in ifaces:
    if (i=="eth0") or (i=="wlan0") or (i=="bat0"):
        ifc.append(i)
        try:
            if (i=="bat0"):
                prio=i
                lip=ni.ifaddresses(i)[ni.AF_INET][0]['addr']
            elif (i=="wlan0") and (prio!="bat0"):
                prio=i
                lip=ni.ifaddresses(i)[ni.AF_INET][0]['addr']
            elif (i=="eth0") and (prio!="bat0") and (prio!="wlan0"):
                prio=i
                lip=ni.ifaddresses(i)[ni.AF_INET][0]['addr']
        except:
            pass

lip=lip.split(".")
red=lip[0]+"."+lip[1]+"."+lip[2]+"."
print (red)
#red="192.168.0."

stream = os.popen('sudo nmap -T5 -sP '+red+'0/24 -oG - | awk \'/Up$/{print $2}\'')
ips = stream.read()
#print (ips)
nodos=[]

if __name__ == "__main__":
    for ip in ips.splitlines():
        try:
            print ("trying "+ip,end="")
            SPIX = "UDP", ip, 1401
            spix = Spi(SPIX, '1')
            dwx = DW1000(spix)
            if dwx.test_irq():
                nodos.append(ip)
                print (" Node Found")
            else:
                print (" ...")
        except:
                pass
    print(nodos)
    nn=len(nodos)
    nt=nn*(nn-1)
    na=1
    db = pymysql.connect("localhost","root","ge0","GeoLoc")
    cursor = db.cursor()
    session=uuid.uuid4()
    for ip1 in nodos:
        for ip2 in nodos:
            if (ip1!=ip2):
                centinela = False
                while centinela==False:
                    stream = os.popen('python3 dw1000_range.py '+ip1+' '+ip2)
                    tiempos = stream.read()
                    tiempos = re.sub('[^0-9,.\[\]]','',tiempos)
                    tiempos = re.sub(',{2,}',',',tiempos)
                    tiempos = ast.literal_eval(tiempos)
                    var=st.variance(tiempos)
                    if (var<2):
                        centinela = True
                        med=st.mean(tiempos)
                        print (str(na)+"/"+str(nt)+" -> ",end="")
                        print (ip1+" - "+ip2+" : ",end="")
                        print (med)
                        sql = "INSERT INTO measures(ip1, ip2, distance, session) \
                        VALUES ('{0}','{1}','{2}','{3}')".format(ip1,ip2,med,session)
                        try:
                           cursor.execute(sql)
                           db.commit()
                        except:
                           db.rollback()
                    na=na+1
    
    
    sql = "SELECT session FROM GeoLoc.measures ORDER BY id DESC LIMIT 0,1"
    cursor.execute(sql)
    results = cursor.fetchall()
    for row in results:
        session = row[0]
    list_ips=[]
    sql = "SELECT ip1 FROM GeoLoc.measures WHERE session='{0}' GROUP BY ip1 ORDER BY ip1 ASC;".format(session)
    cursor.execute(sql)
    results = cursor.fetchall()
    for row in results:
        list_ips.append(row[0])
    datos=[]
    for i in list_ips:
        for j in list_ips:
            if (i!=j):
                sql = "SELECT ip1,ip2,distance FROM GeoLoc.measures WHERE session='{0}' AND ((ip1='{1}' AND ip2='{2}') OR (ip2='{1}' AND ip1='{2}')) ORDER BY ip1 ASC".format(session,i,j)
                cursor.execute(sql)
                results = cursor.fetchall()
                d=0.0
                for row in results:
                   d=d+float(row[2])
                d=d/2
                datos.append([i,j,d])
    distan=[]
    d_act=[]
    count=0
    print (list_ips)
    for i in list_ips:
        d_act=[]
        for j in list_ips:
            if (i==j):
                d_act.append(0)
            else:
                for k in datos:
                    if (i==k[0] and j==k[1]):
                        d_act.append(k[2])
        distan.append(d_act)
    print (distan)

    distancias = np.array(distan)

    mds = manifold.MDS(n_components=2, max_iter=3000, eps=1e-9, random_state=0, dissimilarity="precomputed", n_jobs=1)
    pos = mds.fit(distancias).embedding_
    y=[]
    x=[]
    for i in pos:
        x.append(i[0])
        y.append(i[1])
    minx=min(x)
    miny=min(y)
    for i in pos:
        i[0]=i[0]-minx
        i[1]=i[1]-miny
    
    print(pos)
    

    j=0
    for i in pos:
        sql = "INSERT INTO coords(session, ip, coordx, coordy, date) VALUES ('{0}','{1}','{2}','{3}', NOW())".format(session,list_ips[j],i[0],i[1])
        try:
           cursor.execute(sql)
           db.commit()
        except:
           db.rollback()
        j=j+1
    db.close()
# EOF


