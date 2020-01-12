import sys
import base64
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QIcon, QPixmap

#modules for data gathering and processing
import os
import sys
import git
import requests
import json
import yaml
import xml.etree.ElementTree as ET
from os.path import expanduser
from git import Repo

#orbit prediction modules
from numpy import diff
from skyfield import api
from pytz import timezone
import matplotlib.pyplot as plt
tzone = timezone('America/Vancouver')

qtCreatorFile = "schedule.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)



class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    upcoming_passes = []

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        QtWidgets.QTabWidget.__init__(self)
        Ui_MainWindow.__init__(self)
        

        self.setupUi(self)
        pixmap = QPixmap("earth.jpg")
        pixmap = pixmap.scaled(650, 400, QtCore.Qt.KeepAspectRatio, QtCore.Qt.FastTransformation)
        self.label = QLabel(self)
        self.label.setPixmap(pixmap)
        # Dimensions are probably not correct 
        self.label.setGeometry(20, 40, 650, 400)

        self.scheduleSearch.clicked.connect(self.getParams)
        #self.scheduleSearch.clicked.connect(self.getAvailableSats)


    def getAvailableSats(self):
        date = self.scheduleDateEdit.date().toPyDate()
        # Call Andrew's script
        # Call populateTable when adding script to retrieve data

    def populateTable(self, data):
        print("calling populateTable")
        self.availableSats.clearContents()
        self.availableSats.setRowCount(len(data))
        for row in range(0, len(data)):
            for column in range(0, len(data[row])):
                self.availableSats.setItem(row, column, QtWidgets.QTableWidgetItem(data[row][column]))

    def setup(self):
        #Create directory to host system documents
        home = expanduser("~")
        earth_station_path = home + '/earthstation/'
        gr_sat_dir = earth_station_path + 'gr-satellites/' 
        if not os.path.exists(earth_station_path):
            os.mkdir(earth_station_path)

        gr_sat_list = []
       
        print("Updating list of compatible satellites from remote gr-satellites repository")
        if not os.path.exists(gr_sat_dir):
            Repo.clone_from('https://github.com/daniestevez/gr-satellites', gr_sat_dir)
        else:
            git.cmd.Git(gr_sat_dir).pull()
        
        sat_data = {}

        for root, directory, files in os.walk(gr_sat_dir + 'apps/'):
            for f in files:
                if '.grc' in f:
                    sat_name = os.path.splitext(f)[0]
                    gr_sat_list.append(sat_name)
                    fname = os.path.join(root, f)

                    with open(fname) as f:
                        first_line = f.readline()
                        if 'xml' in first_line:
                            xml_tree = ET.parse(fname)
                            norad_id_flag = False

                            # Save list of norad ids from gr-satellites
                            for elem in xml_tree.iter():
                                if norad_id_flag and elem.text.isdigit() and elem.text != '0':
                                    norad_id = int(elem.text)
                                    sat_data[norad_id] = {}
                                    sat_data[norad_id]['sat_name'] = sat_name
                                    norad_id_flag = False
                                if elem.tag == 'key' and elem.text == 'noradID':
                                    norad_id_flag = True
                        else:
                            with open(fname, 'r') as stream:
                                try:
                                    data = yaml.safe_load(stream)['blocks']
                                except yaml.YAMLError as exc:
                                    print(exc)

                            for i in data:
                                if 'noradID' in i['parameters']:
                                    norad_id = i['parameters']['noradID']
                                    if norad_id.isdigit():
                                        norad_id = int(norad_id)
                                        if norad_id != 0:
                                            sat_data[norad_id] = {}
                                            sat_data[norad_id]['sat_name'] = sat_name
        
        #TODO: add local caching so we don't have to call get every time we execute script
        #Get satellite info from SatNOGS DB
        satnogs_url = 'http://db.satnogs.org/'
       
        #Note becareful not to spam these requests to prevent IP from getting blocked
        #satnogs_sats_json = requests.get(satnogs_url + 'api/satellites/?format=json')
        #if satnogs_sats_json.status_code != 200:
        #    print('Failed to retrieve satellite data from SatNOGS DB')
        #    sys.exit()
       
        #satnogs_transmitters_json = requests.get(satnogs_url + 'api/transmitters/?format=json')
        #if satnogs_transmitters_json.status_code != 200:
        #    print('Failed to retrieve transmitter data from SatNOGS DB')
        #    sys.exit()

        with open('/home/andrew/Documents/classes/capstone/sandbox/satnogs_transmitters.json') as f:
            data = json.load(f)
        for transmitter in data:
            norad_id = transmitter['norad_cat_id']
            trans_name = transmitter['description']
            if norad_id in sat_data:
                sat_data[norad_id][trans_name] = {}
                sat_data[norad_id][trans_name]['downlink_low'] = transmitter['downlink_low']
            
        #JSON object containing satellite data (norad ID is key, name and downlink freqs are other fields)        
        #json_sat_data = json.dumps(sat_data, indent=4, sort_keys=True)

        sats = api.load.tle('https://celestrak.com/NORAD/elements/amateur.txt')
        #This object can be dereferenced by sat name or norad ID
        #beesat = sats['NUSAT-1']
        #beesat = sats[41557]

        self.sat_list = []
        
        for i in sat_data:
            # Might not have TLE data for all satellites supported TODO: Fix this
            if i in sats:
                self.sat_list.append(sats[i])


    def getParams(self):
        # INPUT STARTS HERE

        #lat = input('Please enter the latitude of your ground station (e.g. 12.3456 N): ')
        #if not lat:
        lat = '49.2606 N'

        #lng = input('Please enter the longitude of your ground station (e.g. -78.9012 E): ')
        #if not lng:
        lng = '-123.2460 E'

        #TODO: Convert this input (provided in PST) to UTC before passing to the ts.utc function below
        dateStart = self.scheduleDateEditStart.dateTime().toPyDateTime()
        dateEnd = self.scheduleDateEditEnd.dateTime().toPyDateTime()
        #mins = (dateEnd-dateStart).total_seconds()/60
        
        year = int(dateStart.year)
        month = int(dateStart.month)
        day = int(dateStart.day)
        hour = int(dateStart.hour)
        minutes = range(int((dateEnd-dateStart).total_seconds()/60))

        #minutes = range(60 * 12) #12 hours
        ts = api.load.timescale()
        #t = ts.utc(2019, 11, 19, 23, minutes)
        t = ts.utc(year, month, day, hour, minutes)

        #station_location = api.Topos('49.2606 N', '-123.2460 E')
        station_location = api.Topos(lat, lng)

        orbits = {}
        loc_data = {}

        #Calulate locations of satellites relative to the ground station
        for sat in self.sat_list:
            orbits[sat] = (sat - station_location).at(t)

        for o in orbits:
            loc_data[o] = orbits[o].altaz()

        above_horizons = {}
        for data in loc_data:
            alt = loc_data[data][0]
            above_horizons[data] = alt.degrees > 0 #appending altitude arrays

        pass_boundaries = {}
        for data in above_horizons:
            pass_boundaries[data] = diff(above_horizons[data]).nonzero()

        passes = {}
        for b in pass_boundaries:
            if len(pass_boundaries[b][0]) == 2:
                passes[b] = pass_boundaries[b][0].reshape(1, 2)
            # TODO: handle cases where len > 2 and count is uneven
            if len(pass_boundaries[b][0]) > 2 and len(pass_boundaries[b][0]) % 2 == 0:
                passes[b] = pass_boundaries[b][0].reshape(len(pass_boundaries[b][0]) // 2, 2)

       
        name_to_pass_map = {}
        self.upcoming_passes = []
        for p in passes:
            name_to_pass_map[p.name] = p
            if len(passes[p]) > 1:
                for i in range(0, len(passes[p])):
                    entry = [] 
                    entry.append(p.name)
                    entry.append('temp_status')
                    entry.append('temp_mode')
                    entry.append('temp_uplink')
                    entry.append('temp_downlink')
                    entry.append(t[passes[p][i][0]].astimezone(tzone).strftime('%Y/%m/%d %H:%M:%S') + ' PST')
                    entry.append(t[passes[p][i][1]].astimezone(tzone).strftime('%Y/%m/%d %H:%M:%S') + ' PST')
                    self.upcoming_passes.append(entry)
            else:
                entry = []
                entry.append(p.name)
                entry.append('temp_status')
                entry.append('temp_mode')
                entry.append('temp_uplink')
                entry.append('temp_downlink')
                entry.append(t[passes[p][0][0]].astimezone(tzone).strftime('%Y/%m/%d %H:%M:%S') + ' PST')
                entry.append(t[passes[p][0][1]].astimezone(tzone).strftime('%Y/%m/%d %H:%M:%S') + ' PST')
                self.upcoming_passes.append(entry)


        self.populateTable(self.upcoming_passes)
      #  for p in passes:
      #      print('------------ ' + p.name + ' ------------')
      #      if len(passes[p]) > 1:
      #          for i in range(0, len(passes[p])):
      #              print(str(i) + ')\tRises:\t', t[passes[p][i][0]].astimezone(tzone).strftime('%Y/%m/%d %H:%M:%S'), 'PST')
      #              print('\tSets:\t', t[passes[p][i][1]].astimezone(tzone).strftime('%Y/%m/%d %H:%M:%S'), 'PST')
      #              print('\n')
      #      else:
      #          print('0)\tRises:\t', t[passes[p][0][0]].astimezone(tzone).strftime('%Y/%m/%d %H:%M:%S'), 'PST')
      #          print('\tsets:\t', t[passes[p][0][1]].astimezone(tzone).strftime('%Y/%m/%d %H:%M:%S'), 'PST')
      #          print('\n')

      #  if not passes:
      #      print('No satellite passes overhead during that time')
      #      sys.exit()

      #  sched_sat = input('Enter the name of the satellite you would like to schedule for autonomous communication: ')
      #  pass_num = int(input('Enter the pass number you would like to schedule: '))

      #  if not sched_sat and not pass_num:
      #      print('No passes scheduled')
      #      sys.exit()

      #  pass_sched = passes[name_to_pass_map[sched_sat]]

      #  print('\nData will automatically be collected from', sched_sat, 'during the pass from:')
      #  print(t[pass_sched[pass_num][0]].astimezone(tzone).strftime('%Y/%m/%d %H:%M:%S'), 'PST to', t[pass_sched[pass_num][1]].astimezone(tzone).strftime('%Y/%m/%d %H:%M:%S'), 'PST')
      #  print('\n')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.setup()
    window.show()
    sys.exit(app.exec_())
