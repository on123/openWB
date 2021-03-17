#!/bin/bash
#TESLALOGGERBASEURL="192.168.178.137:5000"
#TESLALOGGERCARNR="1"

TESLALOGGERDEBUG="1"

OPENWBBASEDIR=$(cd `dirname $0`/../../ && pwd)
RAMDISKDIR="$OPENWBBASEDIR/ramdisk"
#MODULEDIR=$(cd `dirname $0` && pwd)
#CONFIGFILE="$OPENWBBASEDIR/openwb.conf"
LOGFILE="$RAMDISKDIR/soc-teslalogger.log"

#LOADCONFIG
#$OPENWBBASEDIR/loadconfig.sh

if [ -z ${teslaloggerbaseurl+x} ]; then echo "!!!! teslaloggerbaseurl is unset!" >> $LOGFILE; fi
if [ -z ${teslaloggercarnr+x} ]; then echo "!!!! teslaloggercarnr is unset!" >> $LOGFILE; fi

#Make Vars UPPERCASE
TESLALOGGERBASEURL=$teslaloggerbaseurl
TESLALOGGERCARNR=$teslaloggercarnr

#URL to get SOC from teslalogger
TESLALOGGERSOCURL="$TESLALOGGERBASEURL/get/$TESLALOGGERCARNR/battery_level?raw"
#URL to get car state from teslalogger (e.g. asleep)
TESLALOGGERCARSTATEURL="$TESLALOGGERBASEURL/get/$TESLALOGGERCARNR/state?raw"
#URL to get car charging state from tesalalogger (e.g. Stopped/Charging/Complete)
TESLALOGGERCHARGINGSTATEURL="$TESLALOGGERBASEURL/get/$TESLALOGGERCARNR/charging_state?raw"
#URL to wake_up car via teslalogger
TESLALOGGERWAKEUPURL="$TESLALOGGERBASEURL/command/$TESLALOGGERCARNR/wake_up"

if [[ $TESLALOGGERDEBUG == "2" ]] ; then
        date=$(date)
        echo "$date -> BASEURL is: $teslaloggerbaseurl" >> $LOGFILE
        echo "$date -> CAR IS: $teslaloggercarnr" >> $LOGFILE
fi

#GET SOC from Teslalogger
tlsoc=$(curl --connect-timeout 15 -s $TESLALOGGERSOCURL | cut -f1 -d".")

#wenn SOC nicht verfügbar (keine Antwort) ersetze leeren Wert durch eine 0
re='^[0-9]+$'
if [[ $tlsoc =~ $re ]] ; then
    #echo $tlsoc
    if [[ $TESLALOGGERDEBUG == "2" ]] ; then
        date=$(date)
        echo "$date -> SOC from teslalogger is: $tlsoc" >> $LOGFILE
        echo "$date -> IP is: $hsocip" >> $LOGFILE
    fi
    #zur weiteren verwendung im webinterface
    echo $tlsoc > "$RAMDISKDIR/soc"
fi


#wenn Ladestatus = 1 und auto schläft und auto noch nicht fertig mit laden -> Wecken

#/var/www/html/openWB/ramdisk/ladestatus

# START of WAKEUP Logic
mylademodus=$(<$RAMDISKDIR/lademodus)
myladestatus=$(<$RAMDISKDIR/ladestatus)
myllsoll=$(<$RAMDISKDIR/llsoll)

if [[ $TESLALOGGERDEBUG == "1" ]] ; then
    date=$(date)
    echo "$date -> Lademodus: $mylademodus Ladestatus: $myladestatus LL-Soll: $myllsoll SOC: $tlsoc" >> $LOGFILE
fi


if [[ $mylademodus == "2" ]] && [[ $myladestatus == "1" ]] ; then
    # Wake Car only in PV Mode
    carState=$(curl --connect-timeout 2 -s $TESLALOGGERCARSTATEURL)
    if [[ $TESLALOGGERDEBUG == "1" ]] ; then
        date=$(date)
        echo "$date -> carState: $carState" >> $LOGFILE
    fi

    if [[ $carState == "asleep" ]] ; then
        charging_state=$(curl --connect-timeout 2 -s $TESLALOGGERCHARGINGSTATEURL)
        if [[ $TESLALOGGERDEBUG == "1" ]] ; then
            date=$(date)
            echo "$date -> charging_state: $charging_state" >> $LOGFILE
        fi

        if [[ $charging_state != "Complete" ]] && [[ $charging_state != "Disconnected" ]] ; then
            date=$(date)
            echo "$date -> Fahrzeug schläft, Ladestatus ist $charging_state und Fahrzeug soll laden mit $myllsoll A. Fahrzeug wird daher jetzt geweckt!" >> $LOGFILE
            curl --silent --connect-timeout 2 curl $TESLALOGGERWAKEUPURL >> $LOGFILE
            echo -e "\n\r\n\r" >> $LOGFILE
        fi
    fi
fi
# END of WAKEUP Logic
