#!/usr/bin/python3
import paho.mqtt.client as mqtt
import time
import configparser
import urllib.request
import json
import os
import argparse
import re
import getopt
os.chdir('/var/www/html/openWB')
config = configparser.ConfigParser()
config.read('/var/www/html/openWB/smarthome.ini')
loglevel=2


DeviceValues = { }
DeviceTempValues = { }
DeviceCounters = { }
for i in range(0, 11):
    DeviceTempValues.update({'oldw'+str(i) : '2'})
    DeviceTempValues.update({'oldwh'+str(i) : '2'})
    DeviceTempValues.update({'oldtemp'+str(i) : '2'})

global numberOfDevices
def logDebug(level, msg):
    if (int(level) >= int(loglevel)):
        file = open('/var/www/html/openWB/ramdisk/smarthome.log', 'a')
        if (int(level) == 1):
            file.write(time.ctime() + ': ' + str(msg)+ '\n')
        if (int(level) == 2):
            file.write(time.ctime() + ': ' + str('\x1b[6;30;42m' + msg + '\x1b[0m')+ '\n')
        file.close()
def simcount(watt2, pref, importfn, exportfn, nummer):
    # emulate import  export
    seconds2= time.time()
    watt1=0
    seconds1=0.0
    if os.path.isfile('/var/www/html/openWB/ramdisk/'+pref+'sec0'): 
        f = open('/var/www/html/openWB/ramdisk/'+pref+'sec0', 'r')
        seconds1=float(f.read())
        f.close()
        f = open('/var/www/html/openWB/ramdisk/'+pref+'wh0', 'r')
        watt1=int(f.read())
        f.close()
        f = open('/var/www/html/openWB/ramdisk/'+pref+'watt0pos', 'r')
        wattposh=int(f.read())
        f.close()
        f = open('/var/www/html/openWB/ramdisk/'+pref+'watt0neg', 'r')
        wattnegh=int(f.read())
        f.close()
        f = open('/var/www/html/openWB/ramdisk/'+pref+'sec0', 'w')
        value1 = "%22.6f" % seconds2
        f.write(str(value1))
        f.close()
        f = open('/var/www/html/openWB/ramdisk/'+pref+'wh0', 'w')
        f.write(str(watt2))
        f.close()
        seconds1=seconds1+1
        deltasec = seconds2- seconds1
        deltasectrun =int(deltasec* 1000) / 1000
        stepsize = int((watt2-watt1)/deltasec)
        while seconds1 <= seconds2:
            if watt1 < 0:
                wattnegh= wattnegh + watt1
            else:
                wattposh= wattposh + watt1
            watt1 = watt1 + stepsize
            if stepsize < 0:
                watt1 = max(watt1,watt2)
            else:
                watt1 = min(watt1,watt2)
            seconds1= seconds1 +1
        rest= deltasec - deltasectrun
        seconds1= seconds1  - 1 + rest
        if rest > 0:
            watt1 = int(watt1 * rest)
            if watt1 < 0:
                wattnegh= wattnegh + watt1
            else:
                wattposh= wattposh + watt1
        wattposkh=wattposh/3600
        wattnegkh=(wattnegh*-1)/3600
        f = open('/var/www/html/openWB/ramdisk/'+pref+'watt0pos', 'w')
        f.write(str(wattposh))
        f.close()
        DeviceValues.update( {str(nummer) + "wpos" : wattposh})
        f = open('/var/www/html/openWB/ramdisk/'+pref+'watt0neg', 'w')
        f.write(str(wattnegh))
        f.close()
        f = open('/var/www/html/openWB/ramdisk/'+ importfn,'w')
        #    f = open('/var/www/html/openWB/ramdisk/speicherikwh', 'w')
        DeviceValues.update( {str(nummer) + "wh" : round(wattposkh, 2)})
        f.write(str(round(wattposkh, 2)))
        f.close()
        f = open('/var/www/html/openWB/ramdisk/' +exportfn , 'w')
        #   f = open('/var/www/html/openWB/ramdisk/speicherekwh', 'w')
        f.write(str(wattnegkh))
        f.close()
    else: 
        f = open('/var/www/html/openWB/ramdisk/'+pref+'sec0', 'w')
        value1 = "%22.6f" % seconds2
        f.write(str(value1))
        f.close()
        f = open('/var/www/html/openWB/ramdisk/'+pref+'wh0', 'w')
        f.write(str(watt2))
        f.close()
      
def publishmqtt(case):
    parser = argparse.ArgumentParser(description='openWB MQTT Publisher')
    parser.add_argument('--qos', '-q', metavar='qos', type=int, help='The QOS setting', default=0)
    parser.add_argument('--retain', '-r', dest='retain', action='store_true', help='If true, retain this publish')
    parser.set_defaults(retain=False)
    args = parser.parse_args()
    client = mqtt.Client("openWB-SmartHome-bulkpublisher-" + str(os.getpid()))
    client.connect("localhost")
    for key in DeviceValues:
        if ( "temp" in key):
            nummer = str(list(filter(str.isdigit, key))[0])
            if ( DeviceValues[str(key)] != DeviceTempValues['oldtemp' + str(nummer)]):   
                sensor = str(list(filter(str.isdigit, key))[1])
                client.publish("openWB/SmartHome/Devices/"+str(nummer)+"/TemperatureSensor"+str(sensor), payload=DeviceValues[str(key)], qos=0, retain=True)
                DeviceTempValues.update({'oldtemp'+str(nummer) : DeviceValues[str(key)]})
        if ( "watt" in key):
            nummer = int(list(filter(str.isdigit, key))[0])
            if ( DeviceValues[str(key)] != DeviceTempValues['oldw' + str(nummer)]):
                client.publish("openWB/SmartHome/Devices/"+str(nummer)+"/Watt", payload=DeviceValues[str(key)], qos=0, retain=True)
                client.loop(timeout=2.0)
                DeviceTempValues.update({'oldw'+str(nummer) : DeviceValues[str(key)]})
        if ( "wh" in key):
            nummer = int(list(filter(str.isdigit, key))[0])
            if ( DeviceValues[str(key)] != DeviceTempValues['oldwh' + str(nummer)]):
                client.publish("openWB/SmartHome/Devices/"+str(nummer)+"/Wh", payload=DeviceValues[str(key)], qos=0, retain=True)
                client.loop(timeout=2.0)
                DeviceTempValues.update({'oldwh'+str(nummer) : DeviceValues[str(key)]})
        if ( "wpos" in key):
            nummer = int(list(filter(str.isdigit, key))[0])
            client.publish("openWB/SmartHome/Devices/"+str(nummer)+"/WHImported_temp", payload=DeviceValues[str(key)], qos=0, retain=True)
            client.loop(timeout=2.0)

# Lese aus der Ramdisk Regelrelevante Werte ein
def loadregelvars():
    global uberschuss
    global speicherleistung
    global speichersoc
    global speichervorhanden
    global loglevel
    global reread
    try:
        with open('ramdisk/wattbezug', 'r') as value:
            uberschuss = int(value.read()) * -1
        with open('ramdisk/speichervorhanden', 'r') as value:
            speichervorhanden = int(value.read())
        if ( speichervorhanden == 1):
            with open('ramdisk/speicherleistung', 'r') as value:
                speicherleistung = int(value.read())
            with open('ramdisk/speichersoc', 'r') as value:
                speichersoc = int(value.read())
        else:
            speicherleistung = 0
            speichersoc = 100
    except Exception as e:
        logDebug("2", "Fehler beim Auslesen der Ramdisk: " + str(e))
        uberschuss = 0
        speichervorhanden = 0
        speicherleistung = 0
        speichersoc = 0
    try:
        with open('ramdisk/smarthomehandlerloglevel', 'r') as value:
            loglevel = int(value.read())
    except:
            loglevel=2
            f = open('/var/www/html/openWB/ramdisk/smarthomehandlerloglevel', 'w')
            f.write(str(2))
            f.close()

    try:
        with open('ramdisk/rereadsmarthomedevices', 'r') as value:
            reread = int(value.read())
    except:
        reread = 1
        config.read('/var/www/html/openWB/smarthome.ini')
    if ( reread == 1):
        config.read('/var/www/html/openWB/smarthome.ini')
        f = open('/var/www/html/openWB/ramdisk/rereadsmarthomedevices', 'w')
        f.write(str(0))
        f.close()
        logDebug("2", "Config reRead")



    for i in range(1, 10):
        try:
            with open('ramdisk/smarthome_device_manual_' + str(i), 'r') as value:
                DeviceValues.update( {str(i) + "manual": int(value.read())}) 
        except:
            DeviceValues.update( {str(i) + "manual": 0})
    logDebug("1", "Uberschuss: " + str(uberschuss) + " Speicherleistung: " + str(speicherleistung) + " SpeicherSoC: " + str(speichersoc))
DeviceValues.update( {"1WHImported_tmp" : int(0)})
DeviceValues.update( {"2WHImported_tmp" : int(0)})
DeviceValues.update( {"3WHImported_tmp" : int(0)})
DeviceValues.update( {"4WHImported_tmp" : int(0)})
DeviceValues.update( {"5WHImported_tmp" : int(0)})
DeviceValues.update( {"6WHImported_tmp" : int(0)})
DeviceValues.update( {"7WHImported_tmp" : int(0)})
DeviceValues.update( {"8WHImported_tmp" : int(0)})
DeviceValues.update( {"9WHImported_tmp" : int(0)})
DeviceValues.update( {"10WHImported_tmp" : int(0)})

def on_connect(client, userdata, flags, rc):
    client.subscribe("openWB/SmartHome/#", 2)
def on_message(client, userdata, msg):
    if msg.topic == "openWB/SmartHome/Devices/1/WHImported_temp":
        DeviceValues.update( {"1WHImported_tmp": int(msg.payload)})
    if msg.topic == "openWB/SmartHome/Devices/2/WHImported_temp":
        DeviceValues.update( {"2WHImported_tmp": int(msg.payload)})
client = mqtt.Client("openWB-mqttsmarthome")

client.on_connect = on_connect
client.on_message = on_message
startTime = time.time()
waitTime = 3
client.connect("localhost")
while True:
    client.loop()
    client.subscribe("openWB/SmartHome/#", 2)
    elapsedTime = time.time() - startTime
    if elapsedTime > waitTime:
        client.disconnect()
        break
# Auslesen des Smarthome Devices (Watt und/oder Temperatur)
def getdevicevalues():
    DeviceList = [config.get('smarthomedevices', 'device_configured_1'), config.get('smarthomedevices', 'device_configured_2'), config.get('smarthomedevices', 'device_configured_3'), config.get('smarthomedevices', 'device_configured_4'), config.get('smarthomedevices', 'device_configured_5'), config.get('smarthomedevices', 'device_configured_6'), config.get('smarthomedevices', 'device_configured_7'), config.get('smarthomedevices', 'device_configured_8'), config.get('smarthomedevices', 'device_configured_9'), config.get('smarthomedevices', 'device_configured_10')] 
    numberOfDevices = 0
    for n in DeviceList:
        numberOfDevices += 1
        if ( n == "1" ):
            if ( config.get('smarthomedevices', 'device_type_'+str(numberOfDevices)) == "shelly"):
                try:
                    answer = json.loads(str(urllib.request.urlopen("http://"+config.get('smarthomedevices', 'device_ip_'+str(numberOfDevices))+"/status", timeout=3).read().decode("utf-8")))
                    watt = int(answer['meters'][0]['power'])
                    relais = int(answer['relays'][0]['ison'])
                    try:
                        anzahltemp = int(config.get('smarthomedevices', 'device_temperatur_configured_'+str(numberOfDevices)))
                        if ( anzahltemp > 0):
                            for i in range(anzahltemp):
                                temp = str(answer['ext_temperature'][str(i)]['tC'])
                                DeviceValues.update( {str(numberOfDevices) + "temp" + str(i) : temp })
                                f = open('/var/www/html/openWB/ramdisk/device' + str(numberOfDevices) + '_temp'+ str(i), 'w')
                                f.write(str(temp))
                                f.close()
                    except:
                        pass
                    DeviceValues.update( {str(numberOfDevices) + "watt" : watt})
                    f = open('/var/www/html/openWB/ramdisk/device' + str(numberOfDevices) + '_watt', 'w')
                    f.write(str(watt))
                    f.close()
                    try:
                        with open('/var/www/html/openWB/ramdisk/smarthome_device_' + str(numberOfDevices) + 'watt0pos', 'r') as value:
                            importtemp = int(value.read())
                        simcount(watt, "smarthome_device_"+ str(numberOfDevices), "device"+ str(numberOfDevices)+"_wh" ,"device"+ str(numberOfDevices)+"_whe", str(numberOfDevices))
                        importtemp1 = int(DeviceValues[str(numberOfDevices)+"wpos"])
                    except Exception as e: 
                        importtemp = int(DeviceValues[str(numberOfDevices)+"WHImported_tmp"])
                        f = open('/var/www/html/openWB/ramdisk/smarthome_device_' + str(numberOfDevices) + 'watt0pos', 'w')
                        f.write(str(importtemp))
                        f.close()
                        f = open('/var/www/html/openWB/ramdisk/smarthome_device_' + str(numberOfDevices) + 'watt0neg', 'w')
                        f.write(str("0"))
                        f.close()
                    #Einschaltzeit des Relais setzen
                    if str(numberOfDevices)+"relais" in DeviceValues:
                        if ( DeviceValues[str(numberOfDevices)+"relais"] == 0 ):
                            if ( relais == 1 ):
                                DeviceCounters.update( {str(numberOfDevices) + "eintime" : time.time()})
                        else:
                            if ( relais == 0 ):
                                del DeviceCounters[str(numberOfDevices) + "eintime"]
                    DeviceValues.update( {str(numberOfDevices) + "relais" : relais})
                    logDebug("1", "Device: " + str(numberOfDevices) + " " + str(config.get('smarthomedevices', 'device_name_'+str(numberOfDevices))) + " relais: " + str(relais)  + " aktuell: " + str(watt))
                except Exception as e:
                    DeviceValues.update( {str(numberOfDevices) : "error"})
                    logDebug("2", "Device Shelly " + str(numberOfDevices) + str(config.get('smarthomedevices', 'device_name_'+str(numberOfDevices))) + " Fehlermeldung: " + str(e)) 
            #für später...
            if ( config.get('smarthomedevices', 'device_type_'+str(numberOfDevices)) == "http"):
                watt = int(str(urllib.request.urlopen("http://"+config.get('smarthomedevices', 'device_ip_'+str(numberOfDevices)), timeout=3).read().decode("utf-8")))
                DeviceValues.update( {str(numberOfDevices) : watt})
    publishmqtt("1")
def turndevicerelais(nummer, zustand):
    if ( zustand == 1):
        try:
            urllib.request.urlopen("http://"+config.get('smarthomedevices', 'device_ip_'+str(nummer))+"/relay/0?turn=on", timeout=3)
            logDebug("1", "Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer))) + " angeschaltet")
            DeviceCounters.update( {str(nummer) + "eintime" : time.time()})
        except Exception as e:
            logDebug("2", "Fehler beim Einschalten von Device " + str(nummer) + " Fehlermeldung: " + str(e))
    if ( zustand == 0):
        try:
            urllib.request.urlopen("http://"+config.get('smarthomedevices', 'device_ip_'+str(nummer))+"/relay/0?turn=off", timeout=3)
            logDebug("1", "Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer))) + " ausgeschaltet")
        except Exception as e:
            logDebug("2", "Fehler beim Ausschalten von Device " + str(nummer) + " Fehlermeldung: " + str(e))
def conditions(nummer):
    einschwelle = int(config.get('smarthomedevices', 'device_einschaltschwelle_'+str(nummer)))
    ausschwelle = int(config.get('smarthomedevices', 'device_ausschaltschwelle_'+str(nummer)))
    einverz = int(config.get('smarthomedevices', 'device_einschaltverzoegerung_'+str(nummer))) * 60
    ausverz = int(config.get('smarthomedevices', 'device_ausschaltverzoegerung_'+str(nummer))) * 60
    mineinschaltdauer = int(config.get('smarthomedevices', 'device_mineinschaltdauer_'+str(nummer))) * 60
    if ( uberschuss > einschwelle):
        logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer)))+ " Überschuss größer Einschaltschwelle")
        if  str(nummer)+"einverz" in DeviceCounters:
            timesince = int(time.time()) - int(DeviceCounters[str(nummer)+"einverz"])
            if ( einverz < timesince ):
                if ( DeviceValues[str(nummer)+"relais"] == 0 ):
                    logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer)))  + " Einschaltverzögerung erreicht, schalte ein")
                    turndevicerelais(nummer, 1)
                else:
                    logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer)))+ " Einschaltverzögerung erreicht, bereits eingeschaltet")
            else:
                logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer))) + " Einschaltverzögerung noch nicht erreicht. " + str(einverz) + " ist größer als " + str(timesince))
        else:
            DeviceCounters.update( {str(nummer) + "einverz" : time.time()})
            logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer))) + " Einschaltverzögerung gestartet")
    else:
        if ( uberschuss < ausschwelle):
            logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer)))+ "Überschuss kleiner Ausschaltschwelle")
            if  str(nummer)+"ausverz" in DeviceCounters:
                timesince = int(time.time()) - int(DeviceCounters[str(nummer)+"ausverz"])
                if ( ausverz < timesince ):
                    if ( DeviceValues[str(nummer)+"relais"] == 1 ):
                        if  str(nummer)+"eintime" in DeviceCounters:
                            timestart = int(time.time()) - int(DeviceCounters[str(nummer)+"eintime"])
                            if ( mineinschaltdauer < timestart):
                                logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer)))  + " Ausschaltverzögerung & Mindesteinschaltdauer erreicht, schalte aus")
                                turndevicerelais(nummer, 0)
                            else:
                                logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer)))  + " Ausschaltverzögerung erreicht, Mindesteinschaltdauer noch nicht erreicht, " + str(mineinschaltdauer) + " ist größer als " + str(timestart))
                        else:
                            logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer)))+ " Mindesteinschaltdauer nicht bekannt, schalte aus")
                            turndevicerelais(nummer, 0)
                    else:
                        logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer)))+ " Ausschaltverzögerung erreicht, bereits ausgeschaltet")

                else:
                    logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer))) + " Ausschaltverzögerung noch nicht erreicht. " + str(ausverz) + " ist größer als " + str(timesince))
            else:
                DeviceCounters.update( {str(nummer) + "ausverz" : time.time()})
                logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer))) + " Ausschaltverzögerung gestartet")
        else:
            logDebug("1","Device: " + str(nummer) + " " + str(config.get('smarthomedevices', 'device_name_'+str(nummer))) + " Überschuss kleiner als Einschaltschwelle und größer als Ausschaltschwelle")

while True:
    config.read('/var/www/html/openWB/smarthome.ini')
    #try:
    loadregelvars()
    #print(str(config.get('smarthomedevices', 'device_name_1')))
    getdevicevalues()
    #print(str(DeviceValues["2w"]) + "Watt")
    #print(str(DeviceValues["2r"]) + "Relais")
    #turndevicerelais(2, 1)
    #contents = getshellyvalues(str(config.get('smarthomedevices', 'device_ip_1')))
    #json_data =json.loads(str(contents))
    #print(int(json_data['meters'][0]['power']))
    for i in range(1,11):
        try:
            configured = config.get('smarthomedevices', 'device_configured_' + str(i))
            if (configured == "1"):
                if ( DeviceValues[str(i)+"manual"] == 1 ):
                    logDebug("1","Device: " + str(i) + " " + str(config.get('smarthomedevices', 'device_name_'+str(i))) + " manueller Modus aktiviert, führe keine Regelung durch")
                else:
                    conditions(int(i))
        except Exception as e:
            logDebug("2", "Device: " + str(i) + " " + str(config.get('smarthomedevices', 'device_name_'+str(i))) + str(e))
    #conditions(2)
    #if "2eintime" in DeviceCounters:
    #    print(DeviceCounters["2eintime"])
    time.sleep(5)
    #except:
    #exit()