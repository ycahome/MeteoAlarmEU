"""
MeteoAlarmEU RSS Reader Plugin

Author: Ycahome, 2017

Version:    1.0.0: Initial Version
            1.0.1: Minor bug fixes
            1.0.2: Bug Correction
            1.0.3: Bug Correction with rss parsing

"""
"""


<plugin key="MeteoAlarmEU" name="Meteo Alarm EU RSS Reader" author="ycahome" version="1.0.3" wikilink="" externallink="http://www.domoticz.com/forum/viewtopic.php?f=65&t=19519">
    <params>
        <param field="Mode1" label="RSSFeed" width="400px" required="true" default="http://www.meteoalarm.eu/documents/rss/gr/GR011.rss"/>
        <param field="Mode3" label="Update every x minutes" width="200px" required="true" default="300"/>
        <param field="Mode4" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="False" />
            </options>
        </param>
    </params>
</plugin>
"""




import Domoticz
import json
import urllib.request
import urllib.error

from os import path
import sys
sys.path
sys.path.append('/usr/lib/python3/dist-packages')

import feedparser

from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
#from unidecode import unidecode


class BasePlugin:

    def __init__(self):
        self.debug = False
        self.error = False
        self.nextpoll = datetime.now()

        return

    def onStart(self):
        if Parameters["Mode4"] == 'Debug':
            self.debug = True
            Domoticz.Debugging(1)
            DumpConfigToLog()
        else:
            Domoticz.Debugging(0)

        Domoticz.Debug("onStart called")

        # check polling interval parameter
        try:
            temp = int(Parameters["Mode3"])
        except:
            Domoticz.Error("Invalid polling interval parameter")
        else:
            if temp < 5:
                temp = 5  # minimum polling interval
                Domoticz.Error("Specified polling interval too short: changed to 5 minutes")
            elif temp > 1440:
                temp = 1440  # maximum polling interval is 1 day
                Domoticz.Error("Specified polling interval too long: changed to 1440 minutes (1 day)")
            self.pollinterval = temp * 60
        Domoticz.Log("Using polling interval of {} seconds".format(str(self.pollinterval)))


        if Parameters["Mode4"] == 'Debug':
            self.debug = True
            Domoticz.Debugging(1)
            DumpConfigToLog()
        else:
            Domoticz.Debugging(0)


        # create the mandatory child devices if not yet exist
        if 1 not in Devices:
            Domoticz.Device(Name="Today", Unit=1, TypeName="Alert",Used=1).Create()
            Domoticz.Device(Name="Tomorrow", Unit=2, TypeName="Alert",Used=1).Create()
            Domoticz.Log("Devices created.")
        Devices[1].Update(0,"No Data")
        Devices[2].Update(0,"No Data")



    def onStop(self):
        Domoticz.Debug("onStop called")
        Domoticz.Debugging(0)


    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug(
            "onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onHeartbeat(self):
        now = datetime.now()
        rss=""
        feed=""
        FeedValueFTd=""
        FeedValueFTm=""

        if now >= self.nextpoll:
          self.nextpoll = now + timedelta(seconds=self.pollinterval)
          rss=Parameters["Mode1"]
          feed = feedparser.parse(rss)
          for key in feed["entries"]: 
            FeedValue = str(key["description"])
            FeedValue = '<tr>TODAY ' + FeedValue.split('Today')[1]

            FeedValueFTd = FeedValue.split('Tomorrow')[0]
            FeedValueFTm = FeedValue.split('Tomorrow')[1]
            Domoticz.Log("Gathering Data for:"+str(key["title"]))

            if not (FeedValueFTd.strip().find('wflag-l1')==-1):
              Domoticz.Debug("Alarm(s) for Today: No special awareness required.")
              #Domoticz.Log("Data Of Warning:"+str(FeedValueFTd.strip()))
              Domoticz.Debug("Type Of Warning:"+str(FeedValueFTd.find('wflag-l1-t5.jpg')))
              Domoticz.Debug("Data:"+str(FeedValueFTd).replace('<','-'))
              ValueToUpdate="No special awareness required"
              #Devices[1].Update(1,ValueToUpdate, Image=Images[icon].ID)

              Domoticz.Debug("Current Awareness Status:" +  Devices[1].sValue + " with Level " + str(Devices[1].nValue))
              if (ValueToUpdate != Devices[1].sValue):
                Domoticz.Log("Awareness for Today Updated to:" + ValueToUpdate)
                Devices[1].Update(1,ValueToUpdate)
              else:
                Domoticz.Log("Awareness Remains Unchanged for Today.")
            else:
              Domoticz.Debug("------FEEDPARSER OUTPUT for TODAY:------------------")
              #Domoticz.Log("Type Of Warning:"+str(FeedValueFTd.find('wflag-l1-t5.jpg')))
              #Domoticz.Log("Data:"+str(FeedValueFTd).replace('<br>','').replace('</br>','').replace('<td>','').replace('</td>','').replace('<tr>','').replace('</tr>','').replace('<b>','').replace('</b>','').replace('<i>','').replace('</i>','').replace('<',''))
              FeedValueFTdPeriod = FeedValueFTd.split('<td>')[0]
              FeedValueFTdPeriod = FeedValueFTdPeriod.split('alt="')[1]
              FeedValueFTdPeriod = FeedValueFTdPeriod.split(':')

              Domoticz.Debug("Icon:"+FeedValueFTd.split('<td>')[0].replace('<','-'))
              AWTPossitions = FeedValueFTd.replace('<','-').split('awt:')
              #if AWTPossitions[2]: Domoticz.Log("AWT Possitions 2:"+AWTPossitions[2])
              WarningText = ""
              for AWTPos in range(1,len(AWTPossitions)):
                AWTvalue = ""
                LEVELvalue = ""
                AWTvalue = AWTPossitions[AWTPos].split('level')[0].strip()
                Domoticz.Debug("AWT Possitions Value "+str(AWTPos)+":"+AWTvalue)
                #LEVELvalue = AWTPossitions[AWTPos].split('level:')[1].split('border')[0].replace('"','').strip()
                LEVELvalue = AWTPossitions[AWTPos].split('level:')[1].split('"')[0]
                Domoticz.Debug("Level Possitions Value "+str(AWTPos)+":"+LEVELvalue)
                AWTtext =  AWTvalue
                if (AWTvalue == "1") : AWTtext = "Wind"
                if (AWTvalue == "2") : AWTtext = "Snow/Ice"
                if (AWTvalue == "3") : AWTtext = "ThunderStorm"
                if (AWTvalue == "4") : AWTtext = "Fog"
                if (AWTvalue == "5") : AWTtext = "High Temp"
                if (AWTvalue == "6") : AWTtext = "Low Temp"
                if (AWTvalue == "7") : AWTtext = "Coastal Event"
                if (AWTvalue == "8") : AWTtext = "Forestfire"
                if (AWTvalue == "9") : AWTtext = "Avalanches"
                if (AWTvalue == "10") : AWTtext = "Rain"
                if (AWTvalue == "11") : AWTtext = "Flood"
                if (AWTvalue == "12") : AWTtext = "Rain-Flood"
                if (AWTPos > 1): WarningText = WarningText + ", "
                WarningText = WarningText + AWTtext+"("+LEVELvalue+")"
                Domoticz.Debug("Alarm(s) for today:"+ str(WarningText))
              Domoticz.Debug("AWT:"+FeedValueFTdPeriod[1].split(' ')[0].replace('<','-').replace('>','-'))
              Domoticz.Debug("Level:"+FeedValueFTdPeriod[2].split('"')[0].strip().replace('<','-'))
              Domoticz.Debug("Period:"+FeedValueFTd.split('<td>')[1].strip().replace('<br>','').replace('</br>','').replace('<td>','').replace('</td>','').replace('<','-'))
              #Domoticz.Log("MessageLocal:"+FeedValueFTd.split('<td>')[2].split('.')[0].strip())
              #Domoticz.Log("MessageEn:"+FeedValueFTd.split('<td>')[2].split('.')[1].strip().replace('<','-'))
              #Domoticz.Log("MessageEn:"+FeedValueFTd.split('<td>')[2].split('.')[1].split('english:')[1].strip())
              #ValueToUpdate=FeedValueFTd.split('<td>')[2].split('.')[1].split('english:')[1].strip()
              if (LEVELvalue=="5"): LEVELvalue="1"

              Domoticz.Debug("Current Awareness Status:" +  Devices[1].sValue + " with Level " + str(Devices[1].nValue))
              if (WarningText != Devices[1].sValue) or (int(LEVELvalue) != Devices[1].nValue):
                Domoticz.Log("Awareness for Today Updated to:" + WarningText)
                Devices[1].Update(int(LEVELvalue),WarningText)
              else:
                Domoticz.Log("Awareness Remains Unchanged for Today.")

            if not (FeedValueFTm.strip().find('wflag-l1')==-1):
              Domoticz.Debug("Alarm(s) for Tomorrow: No special awareness required")
              #Domoticz.Log("Data Of Warning:"+str(FeedValueFTm.strip()))
              Domoticz.Debug("Type Of Warning:"+str(FeedValueFTm.find('wflag-l1-t5.jpg')))
              ValueToUpdate="No special awareness required"
              Domoticz.Debug("Current Awareness Status:" +  Devices[2].sValue + " with Level " + str(Devices[2].nValue))
              if (ValueToUpdate != Devices[2].sValue):
                Domoticz.Log("Awareness for Tomorrow Updated to:" + ValueToUpdate)
                Devices[2].Update(1,ValueToUpdate)
              else:
                Domoticz.Log("Awareness Remains Unchanged for Tomorrow.")
            else:
              #FeedValueFTm = FeedValueFTd.split('<tr>')
              Domoticz.Debug("------FEEDPARSER OUTPUT for TOMORROW:------------------")
              #Domoticz.Log("Type Of Warning:"+str(FeedValueFTm.find('awt:5')))
              FeedValueFTmPeriod = FeedValueFTm.split('<td>')[0]
              FeedValueFTmPeriod = FeedValueFTmPeriod.split('alt="')[1]
              FeedValueFTmPeriod = FeedValueFTmPeriod.split(':')

              Domoticz.Debug("Icon:"+FeedValueFTm.split('<td>')[0].replace('<','-'))
              AWTPossitions = FeedValueFTm.replace('<','-').split('awt:')
              #if AWTPossitions[2]: Domoticz.Log("AWT Possitions 2:"+AWTPossitions[2])
              WarningText = ""
              HLEVELvalue = 1
              for AWTPos in range(1,len(AWTPossitions)):
                AWTvalue = ""
                LEVELvalue = ""
                AWTvalue = AWTPossitions[AWTPos].split('level')[0].strip()
                Domoticz.Debug("AWT Possitions Value "+str(AWTPos)+":"+AWTvalue)
                #LEVELvalue = AWTPossitions[AWTPos].split('level:')[1].split('border')[0].replace('"','').strip()
                LEVELvalue = AWTPossitions[AWTPos].split('level:')[1].split('"')[0]
                Domoticz.Debug("Level Possitions Value "+str(AWTPos)+":"+LEVELvalue)
                AWTtext =  AWTvalue
                if (AWTvalue == "1") : AWTtext = "Wind"
                if (AWTvalue == "2") : AWTtext = "Snow/Ice"
                if (AWTvalue == "3") : AWTtext = "ThunderStorm"
                if (AWTvalue == "4") : AWTtext = "Fog"
                if (AWTvalue == "5") : AWTtext = "High Temp"
                if (AWTvalue == "6") : AWTtext = "Low Temp"
                if (AWTvalue == "7") : AWTtext = "Coastal Event"
                if (AWTvalue == "8") : AWTtext = "Forestfire"
                if (AWTvalue == "9") : AWTtext = "Avalanches"
                if (AWTvalue == "10") : AWTtext = "Rain"
                if (AWTvalue == "11") : AWTtext = "Flood"
                if (AWTvalue == "12") : AWTtext = "Rain-Flood"
                WarningText = WarningText + AWTtext+"("+LEVELvalue+")"
                if (AWTPos > 1): WarningText = WarningText + ", "
                Domoticz.Debug("Alarm(s) for Tomorrow:"+ str(WarningText))
                if (int(LEVELvalue) > HLEVELvalue): HLEVELvalue = int(LEVELvalue)

              Domoticz.Debug("Icon:"+FeedValueFTm.split('<td>')[0].replace('<','-'))
              Domoticz.Debug("AWT:"+FeedValueFTmPeriod[1].split(' ')[0].strip().replace('<','-'))
              Domoticz.Debug("Level:"+FeedValueFTmPeriod[2].split('"')[0].strip().replace('<','-'))
              #Domoticz.Log("Period:"+FeedValueFTm.split('<td>')[1].strip().replace('<','-'))
              #Domoticz.Log("MessageLocal:"+FeedValueFTm.split('<td>')[2].split('.')[0].strip().replace('<','-'))
              #Domoticz.Log("MessageEn:"+FeedValueFTm.split('<td>')[2].split('.')[1].split('english:')[1].strip().replace('<','-'))
              #Domoticz.Log(FeedValueFTm)
              #ValueToUpdate=FeedValueFTm.split('<td>')[2].split('.')[1].split('english:')[1].strip().replace('<','-')
              if (HLEVELvalue==5): HLEVELvalue=0

              Domoticz.Debug("Current Awareness Status:" +  Devices[2].sValue + " with Level " + str(Devices[2].nValue))
              if (WarningText != Devices[2].sValue) or (int(HLEVELvalue) != Devices[2].nValue):
                Domoticz.Log("Awareness for Tomorrow Updated to:" + WarningText)
                Devices[2].Update(HLEVELvalue,WarningText)
              else:
                Domoticz.Log("Awareness Remains Unchanged for Tomorrow.")

              Domoticz.Debug("----------------------------------------------------")



global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

#############################################################################
#                   Device specific functions                     #
#############################################################################


# Generic helper functions


def DumpConfigToLog():
    for x in Parameters:
      if Parameters[x] != "":
          Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
      Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
      Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
      Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
      Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
      Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
      Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

#
# Parse an int and return None if no int is given
#

def parseIntValue(s):

        try:
            return int(s)
        except:
            return None

#
# Parse a float and return None if no float is given
#

def parseFloatValue(s):

        try:
            return float(s)
        except:
            return None

