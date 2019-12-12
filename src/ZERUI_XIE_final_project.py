#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
from bs4 import BeautifulSoup
import json
import sqlite3
import matplotlib.pyplot as plt
import argparse
import time
import os


######################################### Data Getting and Management Part ##############################################


# In[2]:


class travel():

    def __init__(self):
        self.conn = sqlite3.connect(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "\data\weather.db")
        self.c = self.conn.cursor()
        self.travel_data = {}

    def create_data_base(self):
        # create database

        # creat table TRAVEL
        self.c.execute("""DROP TABLE IF EXISTS TRAVEL""")
        self.c.execute("""CREATE TABLE TRAVEL ( 
                         ID INTEGER PRIMARY KEY NOT NULL,
                         PLACE TEXT NOT NULL,
                         AREA TEXT,
                         STATE TEXT NOT NULL
                                        )""")
        self.c.execute("""SELECT * FROM TRAVEL""")
        print(self.c.fetchall())

    def page_get(self, url):
        # check status of url/api
        try:
            p = requests.get(url)
            p.raise_for_status()
        except requests.exceptions.ConnectionError:
            print("Connection Error")
            return None
        except requests.exceptions.HTTPError:
            print("HTTP Error")
            return None
        else:
            return p

    def travel(self):
        # get the data from a "scrape-able" url
        # store data into tabel TRAVEL (ID,PLACE,AREA(opt),STATE)
        # also store the data into a dictionary

        # preparation for data scraping
        r = self.page_get("https://www.cntraveler.com/galleries/2016-07-04/the-50-most-beautiful-places-in-america")
        soup = BeautifulSoup(r.content, 'lxml')
        body = soup.find('body')
        titles = body.find_all('h2', {'class': "hed"})

        self.create_data_base()

        p_id = 0  # id for each place
        for title in titles:
            # loop all the data and put them into data sets
            self.c.execute(f""" SELECT * FROM TRAVEL WHERE ID = {p_id} """)
            entry = self.c.fetchone()
            if entry is None:
                # check the data is exist or not
                if title.text.count(',') == 1:
                    # dealing with the data saparately
                    place, state = title.text.split(',')  # spilt the str
                    self.travel_data[p_id] = [place, state]  # input value

                    self.c.execute("""INSERT INTO TRAVEL (ID,PLACE,STATE) VALUES (?,?,?) """,
                                   (p_id, place, state))  # insert to table
                    p_id += 1


                else:

                    place, area, state = title.text.split(',')
                    self.travel_data[p_id] = [place, area, state]
                    self.c.execute("""INSERT INTO TRAVEL (ID,PLACE,AREA,STATE) VALUES (?,?,?,?) """,
                                   (p_id, place, area, state))
                    p_id += 1

        self.conn.commit()


# In[18]:


class location():

    def __init__(self):
        self.conn = sqlite3.connect(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "\data\weather.db")
        self.c = self.conn.cursor()

    def create_data_base(self):
        # create database

        # LOCATION
        self.c.execute("""DROP TABLE IF EXISTS LOCATION""")
        self.c.execute("""CREATE TABLE LOCATION ( 
                         ID INTEGER PRIMARY KEY NOT NULL,
                         LATI FLOAT NOT NULL,
                         LONGI FLOAT NOT NULL,
                         TYPE TEXT NOT NULL
                                        )""")
        self.c.execute("""SELECT * FROM LOCATION""")
        print(self.c.fetchall())

    def page_get(self, url):
        # check status of url/api
        try:
            p = requests.get(url)
            p.raise_for_status()
        except requests.exceptions.ConnectionError:
            print("Connection Error")
            return None
        except requests.exceptions.HTTPError:
            print("HTTP Error")
            return None
        else:
            return p

    def fifty_beauty(self):
        # store the 50 beautiful places
        self.create_data_base()
        t = self.c.execute("""SELECT * FROM TRAVEL""")
        l = t.fetchall()
        for i in range(len(l)):
            self.store_ll(l[i][0], l[i][1])

    def store_ll(self, p_id, adress):
        # store data into table LOCATION (ID,LATI,LONGI,TYPE)

        r = self.page_get(
            f"https://maps.googleapis.com/maps/api/geocode/json?address={adress}&key=AIzaSyCWKDb0ErBe1mfkYv7EyKxsK0Y1nMkSPjY")

        if r == None:
            print("Adress can't be located")
            return None

        lat = json.loads(r.content)['results'][0]['geometry']['location']['lat']
        log = json.loads(r.content)['results'][0]['geometry']['location']['lng']
        types = json.loads(r.content)['results'][0]['types']

        self.c.execute(f""" SELECT * FROM LOCATION WHERE LATI = {lat} AND LONGI = {log} """)
        entry = self.c.fetchone()

        if entry is None:
            # check the data is exist or not
            if 'natural_feature' in types:
                self.c.execute("""INSERT INTO LOCATION (ID,LATI,LONGI,TYPE) VALUES (?,?,?,?) """,
                               (p_id, lat, log, 'natural_feature'))  # insert to table
            elif 'park' in types:
                self.c.execute("""INSERT INTO LOCATION (ID,LATI,LONGI,TYPE) VALUES (?,?,?,?) """,
                               (p_id, lat, log, 'park'))
            else:
                self.c.execute("""INSERT INTO LOCATION (ID,LATI,LONGI,TYPE) VALUES (?,?,?,?) """,
                               (p_id, lat, log, 'establishment'))

        self.conn.commit()


# In[2]:


class near_city():

    def __init__(self):
        self.conn = sqlite3.connect(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "\data\weather.db")
        self.c = self.conn.cursor()

    def create_data_base(self):
        # create database

        # CITY
        self.c.execute("""DROP TABLE IF EXISTS CITY""")
        self.c.execute("""CREATE TABLE CITY ( 
                                 CITY_NAME TEXT NOT NULL,
                                 DISTANCE INTEGER,
                                 TYPE TEXT,
                                 LATT_LONG TEXT,
                                 WOEID INTEGER PRIMARY KEY NOT NULL
                                                )""")
        self.c.execute("""SELECT * FROM CITY""")
        print(self.c.fetchall())

        # CITY_PLACES
        self.c.execute("""DROP TABLE IF EXISTS CITY_PLACES""")
        self.c.execute("""CREATE TABLE CITY_PLACES ( 
                                 WOEID INTEGER NOT NULL,
                                 ID INTEGER NOT NULL
                                                )""")
        self.c.execute("""SELECT * FROM CITY_PLACES""")

    def page_get(self, url):
        # check status of url/api
        try:
            p = requests.get(url)
            p.raise_for_status()
        except requests.exceptions.ConnectionError:
            print("Connection Error")
            return None
        except requests.exceptions.HTTPError:
            print("HTTP Error")
            return None
        else:
            return p

    def fifty_beauty(self):
        # store the 50 beautiful places
        self.create_data_base()
        t = self.c.execute("""SELECT * FROM LOCATION""")
        l = t.fetchall()
        for i in range(len(l)):
            p_id = l[i][0]
            lat = l[i][1]
            long = l[i][2]
            self.store_c(p_id, lat, long)

    def store_c(self, p_id, lat, long):
        # try get the top 3 nearest cities' data
        # store in dic "near_cities"
        # store data into table CITY (ID,CITY_NAME,DISTANCE, TYPE, LATT_LONG, WOEID)

        r = self.page_get(
            f"https://www.metaweather.com/api/location/search/?lattlong= {lat},{long}")

        if r == None:
            print("Lattitude/Longitude can't be located")
            return None

        j = json.loads(r.content)

        self.c.execute(""" SELECT * FROM CITY WHERE WOEID = {} """.format(j[0]['woeid']))
        entry = self.c.fetchone()
        if entry is None:
            self.c.execute(
                """INSERT INTO CITY (CITY_NAME,DISTANCE, TYPE, LATT_LONG, WOEID) VALUES (?,?,?,?,?) """,
                (j[0]['title'], j[0]['distance'], j[0]['location_type'], j[0]['latt_long'],
                 j[0]['woeid']))  # insert to table

        self.c.execute(""" SELECT * FROM CITY_PLACES WHERE WOEID = {} AND ID = {}""".format(j[0]['woeid'], p_id))
        entry = self.c.fetchone()
        if entry is None:
            self.c.execute(
                """INSERT INTO CITY_PLACES (WOEID, ID) VALUES (?,?) """, (j[0]['woeid'], p_id))  # insert to table

        for n in range(1, 3):
            # pick the 2nd and 3rd closest cities and the distance need to <= 100KM
            if j[n]['distance'] <= 100000:

                self.c.execute(""" SELECT * FROM CITY WHERE WOEID = {} """.format(j[n]['woeid']))
                entry = self.c.fetchone()
                if entry is None:
                    # if not exist

                    self.c.execute(
                        """INSERT INTO CITY (CITY_NAME,DISTANCE, TYPE, LATT_LONG, WOEID) VALUES (?,?,?,?,?) """,
                        (j[n]['title'], j[n]['distance'], j[n]['location_type'], j[n]['latt_long'],
                         j[n]['woeid']))  # insert to table

                self.c.execute(
                    """ SELECT * FROM CITY_PLACES WHERE WOEID = {} AND ID = {}""".format(j[n]['woeid'], p_id))
                entry = self.c.fetchone()
                if entry is None:
                    self.c.execute("""INSERT INTO CITY_PLACES (WOEID, ID) VALUES (?,?) """,
                                   (j[n]['woeid'], p_id))  # insert to table

        self.conn.commit()

    # In[9]:


class weather_of_cities():

    def __init__(self):
        self.conn = sqlite3.connect(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "\data\weather.db")
        self.c = self.conn.cursor()

    def create_data_base(self):
        # create database

        # CITY_WEATHER(days)
        for i in range(6):
            self.c.execute(f"""DROP TABLE IF EXISTS CITIES_WEATHER{i}""")
            self.c.execute(f"""CREATE TABLE CITIES_WEATHER{i} ( 
                                     WOEID INTEGER NOT NULL,
                                     LOCAL_TIME TEXT,
                                     WEATHER TEXT,
                                     MIN_TEMP REAL,
                                     MAX_TEMP REAL,
                                     AVG_TEMP REAL,
                                     WIND_SPEED REAL,
                                     WIND_DIRECTION TEXT,
                                     HUMIDITY REAL,
                                     AIR_PRESSURE REAL,
                                     VISIBILITY REAL,
                                     PRED_PROB INTEGER
                                                    )""")
            self.c.execute(f"""SELECT * FROM CITIES_WEATHER{i}""")
            print(self.c.fetchall())

        # CITIES_LOCAL_TMIE
        self.c.execute("""DROP TABLE IF EXISTS CITIES_LOCAL_TMIE""")
        self.c.execute("""CREATE TABLE CITIES_LOCAL_TMIE ( 
                                     WOEID INTEGER PRIMARY KEY NOT NULL,
                                     DAY0 TEXT,
                                     DAY1 TEXT,
                                     DAY2 TEXT,
                                     DAY3 TEXT,
                                     DAY4 TEXT,
                                     DAY5 TEXT
                                                    )""")
        self.c.execute("""SELECT * FROM CITIES_LOCAL_TMIE""")
        print(self.c.fetchall())

        # CITIES_WEATHER
        self.c.execute(f"""DROP TABLE IF EXISTS CITIES_WEATHER""")
        self.c.execute(f"""CREATE TABLE CITIES_WEATHER ( 
                                     WOEID INTEGER PRIMARY KEY NOT NULL,
                                     DAY0 TEXT,
                                     DAY1 TEXT,
                                     DAY2 TEXT,
                                     DAY3 TEXT,
                                     DAY4 TEXT,
                                     DAY5 TEXT
                                                    )""")
        self.c.execute("""SELECT * FROM CITIES_WEATHER""")
        print(self.c.fetchall())

        # CITIES_TEMP
        self.c.execute(f"""DROP TABLE IF EXISTS CITIES_TEMP""")
        self.c.execute(f"""CREATE TABLE CITIES_TEMP ( 
                                     WOEID INTEGER PRIMARY KEY NOT NULL,
                                     DAY0_MIN_TEMP REAL,
                                     DAY0_MAX_TEMP REAL,
                                     DAY0_AVG_TEMP REAL,
                                     DAY1_MIN_TEMP REAL,
                                     DAY1_MAX_TEMP REAL,
                                     DAY1_AVG_TEMP REAL,
                                     DAY2_MIN_TEMP REAL,
                                     DAY2_MAX_TEMP REAL,
                                     DAY2_AVG_TEMP REAL,
                                     DAY3_MIN_TEMP REAL,
                                     DAY3_MAX_TEMP REAL,
                                     DAY3_AVG_TEMP REAL,
                                     DAY4_MIN_TEMP REAL,
                                     DAY4_MAX_TEMP REAL,
                                     DAY4_AVG_TEMP REAL,
                                     DAY5_MIN_TEMP REAL,
                                     DAY5_MAX_TEMP REAL,
                                     DAY5_AVG_TEMP REAL
                                                    )""")
        self.c.execute("""SELECT * FROM CITIES_TEMP""")
        print(self.c.fetchall())

        # CITIES_WIND
        self.c.execute(f"""DROP TABLE IF EXISTS CITIES_WIND""")
        self.c.execute(f"""CREATE TABLE CITIES_WIND ( 
                                     WOEID INTEGER PRIMARY KEY NOT NULL,
                                     DAY0_WIND_SPEED REAL,
                                     DAY0_WIND_DIRECTION TEXT,
                                     DAY1_WIND_SPEED REAL,
                                     DAY1_WIND_DIRECTION TEXT,
                                     DAY2_WIND_SPEED REAL,
                                     DAY2_WIND_DIRECTION TEXT,
                                     DAY3_WIND_SPEED REAL,
                                     DAY3_WIND_DIRECTION TEXT,
                                     DAY4_WIND_SPEED REAL,
                                     DAY4_WIND_DIRECTION TEXT,
                                     DAY5_WIND_SPEED REAL,
                                     DAY5_WIND_DIRECTION TEXT
                                     
                                                    )""")
        self.c.execute("""SELECT * FROM CITIES_WIND""")
        print(self.c.fetchall())

        # CITIES_HUMIDITY
        self.c.execute(f"""DROP TABLE IF EXISTS CITIES_HUMIDITY""")
        self.c.execute(f"""CREATE TABLE CITIES_HUMIDITY ( 
                                     WOEID INTEGER PRIMARY KEY NOT NULL,
                                     DAY0 REAL,
                                     DAY1 REAL,
                                     DAY2 REAL,
                                     DAY3 REAL,
                                     DAY4 REAL,
                                     DAY5 REAL
                        )""")
        self.c.execute("""SELECT * FROM CITIES_HUMIDITY""")
        print(self.c.fetchall())

        # CITIES_AIR_PRESSURE
        self.c.execute(f"""DROP TABLE IF EXISTS CITIES_AIR_PRESSURE""")
        self.c.execute(f"""CREATE TABLE CITIES_AIR_PRESSURE ( 
                                     WOEID INTEGER PRIMARY KEY NOT NULL,
                                     DAY0 REAL,
                                     DAY1 REAL,
                                     DAY2 REAL,
                                     DAY3 REAL,
                                     DAY4 REAL,
                                     DAY5 REAL
                        )""")
        self.c.execute("""SELECT * FROM CITIES_AIR_PRESSURE""")
        print(self.c.fetchall())

        # CITIES_VISIBILITY
        self.c.execute(f"""DROP TABLE IF EXISTS CITIES_VISIBILITY""")
        self.c.execute(f"""CREATE TABLE CITIES_VISIBILITY ( 
                                     WOEID INTEGER PRIMARY KEY NOT NULL,
                                     DAY0 REAL,
                                     DAY1 REAL,
                                     DAY2 REAL,
                                     DAY3 REAL,
                                     DAY4 REAL,
                                     DAY5 REAL
                        )""")
        self.c.execute("""SELECT * FROM CITIES_VISIBILITY""")
        print(self.c.fetchall())

    def page_get(self, url):
        # check status of url/api
        try:
            p = requests.get(url)
            p.raise_for_status()
        except requests.exceptions.ConnectionError:
            print("Connection Error")
            return None
        except requests.exceptions.HTTPError:
            print("HTTP Error")
            return None
        else:
            return p

    def fifty_beauty(self):
        # store weather data of the cities nearing the 50 beautiful places

        self.create_data_base()  # create database
        t = self.c.execute("""SELECT WOEID FROM CITY""")
        l = t.fetchall()
        for i in range(len(l)):
            self.store_cw(l[i][0])

    def store_cw(self, woeid):

        r = self.page_get(f"https://www.metaweather.com/api/location/{woeid}/")

        if r == None:
            print("Woeid not found")
            return None

        j = json.loads(r.content)['consolidated_weather']
        for i in range(len(j)):
            # get the weather from diifferent days
            self.c.execute(f""" SELECT * FROM CITIES_WEATHER{i} WHERE WOEID = {woeid} """)  # check by woeid
            entry = self.c.fetchone()
            if entry is None:
                # insert data

                self.c.execute(f"""
                               INSERT INTO CITIES_WEATHER{i} (WOEID, LOCAL_TIME, WEATHER, MIN_TEMP, MAX_TEMP,
                               AVG_TEMP, WIND_SPEED, WIND_DIRECTION, HUMIDITY, AIR_PRESSURE, VISIBILITY, PRED_PROB)
                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """, (woeid, j[i]['applicable_date'], j[i]['weather_state_name'], j[i]['min_temp'], j[i]['max_temp'], \
                      j[i]['the_temp'], j[i]['wind_speed'], j[i]['wind_direction_compass'], (j[i]['humidity']) / 100, \
                      j[i]['air_pressure'], j[i]['visibility'], j[i]['predictability']))

        # CITIES_LOCAL_TMIE
        self.c.execute(f""" SELECT * FROM CITIES_LOCAL_TMIE WHERE WOEID = {woeid} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute(f"""
                               INSERT INTO CITIES_LOCAL_TMIE (WOEID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5)
                               VALUES(?,?,?,?,?,?,?)
                    """, (woeid, j[0]['applicable_date'], \
                          j[1]['applicable_date'], \
                          j[2]['applicable_date'], \
                          j[3]['applicable_date'], \
                          j[4]['applicable_date'], \
                          j[5]['applicable_date']))

        # CITIES_WEATHER
        self.c.execute(f""" SELECT * FROM CITIES_WEATHER WHERE WOEID = {woeid} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute(f"""
                               INSERT INTO CITIES_WEATHER (WOEID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5)
                               VALUES(?,?,?,?,?,?,?)
                    """, (woeid, j[0]['weather_state_name'], \
                          j[1]['weather_state_name'], \
                          j[2]['weather_state_name'], \
                          j[3]['weather_state_name'], \
                          j[4]['weather_state_name'], \
                          j[5]['weather_state_name']))
        # CITIES_TEMP
        self.c.execute(f""" SELECT * FROM CITIES_TEMP WHERE WOEID = {woeid} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute(f"""
                               INSERT INTO CITIES_TEMP (WOEID, 
                               DAY0_MIN_TEMP, DAY0_MAX_TEMP, DAY0_AVG_TEMP,
                               DAY1_MIN_TEMP, DAY1_MAX_TEMP, DAY1_AVG_TEMP, 
                               DAY2_MIN_TEMP, DAY2_MAX_TEMP, DAY2_AVG_TEMP,
                               DAY3_MIN_TEMP, DAY3_MAX_TEMP, DAY3_AVG_TEMP, 
                               DAY4_MIN_TEMP, DAY4_MAX_TEMP, DAY4_AVG_TEMP,
                               DAY5_MIN_TEMP, DAY5_MAX_TEMP, DAY5_AVG_TEMP) 
                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (woeid, j[0]['min_temp'], j[0]['max_temp'], j[0]['the_temp'], \
                          j[1]['min_temp'], j[1]['max_temp'], j[1]['the_temp'], \
                          j[2]['min_temp'], j[2]['max_temp'], j[2]['the_temp'], \
                          j[3]['min_temp'], j[3]['max_temp'], j[3]['the_temp'], \
                          j[4]['min_temp'], j[4]['max_temp'], j[4]['the_temp'], \
                          j[5]['min_temp'], j[5]['max_temp'], j[5]['the_temp']))

        # CITIES_WIND
        self.c.execute(f""" SELECT * FROM CITIES_WIND WHERE WOEID = {woeid} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute(f"""
                               INSERT INTO CITIES_WIND (WOEID,
                               DAY0_WIND_SPEED, DAY0_WIND_DIRECTION,
                               DAY1_WIND_SPEED, DAY1_WIND_DIRECTION,
                               DAY2_WIND_SPEED, DAY2_WIND_DIRECTION,
                               DAY3_WIND_SPEED, DAY3_WIND_DIRECTION,
                               DAY4_WIND_SPEED, DAY4_WIND_DIRECTION,
                               DAY5_WIND_SPEED, DAY5_WIND_DIRECTION)
                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (woeid, j[0]['wind_speed'], j[0]['wind_direction_compass'], \
                          j[1]['wind_speed'], j[1]['wind_direction_compass'], \
                          j[2]['wind_speed'], j[2]['wind_direction_compass'], \
                          j[3]['wind_speed'], j[3]['wind_direction_compass'], \
                          j[4]['wind_speed'], j[4]['wind_direction_compass'], \
                          j[5]['wind_speed'], j[5]['wind_direction_compass']))

        # CITIES_HUMIDITY
        self.c.execute(f""" SELECT * FROM CITIES_HUMIDITY WHERE WOEID = {woeid} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute(f"""
                               INSERT INTO CITIES_HUMIDITY (WOEID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5)
                               VALUES(?,?,?,?,?,?,?)
                    """, (woeid, j[0]['humidity'] / 100, \
                          j[1]['humidity'] / 100, \
                          j[2]['humidity'] / 100, \
                          j[3]['humidity'] / 100, \
                          j[4]['humidity'] / 100, \
                          j[5]['humidity'] / 100))

        # CITIES_AIR_PRESSURE
        self.c.execute(f""" SELECT * FROM CITIES_AIR_PRESSURE WHERE WOEID = {woeid} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute(f"""
                               INSERT INTO CITIES_AIR_PRESSURE (WOEID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5)
                               VALUES(?,?,?,?,?,?,?)
                    """, (woeid, j[0]['air_pressure'], \
                          j[1]['air_pressure'], \
                          j[2]['air_pressure'], \
                          j[3]['air_pressure'], \
                          j[4]['air_pressure'], \
                          j[5]['air_pressure']))

        # CITIES_VISIBILITY
        self.c.execute(f""" SELECT * FROM CITIES_VISIBILITY WHERE WOEID = {woeid} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute(f"""
                               INSERT INTO CITIES_VISIBILITY (WOEID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5)
                               VALUES(?,?,?,?,?,?,?)
                    """, (woeid, j[0]['visibility'], \
                          j[1]['visibility'], \
                          j[2]['visibility'], \
                          j[3]['visibility'], \
                          j[4]['visibility'], \
                          j[5]['visibility']))

        self.conn.commit()


# In[13]:


class weather_of_places():

    def __init__(self):
        self.conn = sqlite3.connect(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "\data\weather.db")
        self.c = self.conn.cursor()

    def create_data_base(self):
        # create database

        # SUMMARY
        self.c.execute(f"""DROP TABLE IF EXISTS WEATHER_SUMMARY""")
        self.c.execute(f"""CREATE TABLE WEATHER_SUMMARY ( 
                                     ID PRIMARY KEY NOT NULL,
                                     SUMMARY TEXT
                                                    )""")
        self.c.execute(f"""SELECT * FROM WEATHER_SUMMARY""")

        # PLACES_WEATHER(days)
        for i in range(8):
            self.c.execute(f"""DROP TABLE IF EXISTS PLACES_WEATHER{i}""")
            self.c.execute(f"""CREATE TABLE PLACES_WEATHER{i} ( 
                                     ID PRIMARY KEY NOT NULL,
                                     LOCAL_TIME TEXT,
                                     SUMMARY TEXT,
                                     WEATHER TEXT,
                                     MIN_TEMP REAL,
                                     MIN_TIME REAL,
                                     MAX_TEMP REAL,
                                     MAX_TIME REAL,
                                     WIND_SPEED REAL,
                                     WINDBEARING REAL,
                                     HUMIDITY REAL,
                                     CLOUD_COVER REAL,
                                     AIR_PRESSURE REAL,
                                     VISIBILITY REAL
                                                    )""")
            self.c.execute(f"""SELECT * FROM PLACES_WEATHER{i}""")
            print(self.c.fetchall())

        # PLACES_TIME

        self.c.execute("""DROP TABLE IF EXISTS PLACES_TIME""")
        self.c.execute("""CREATE TABLE PLACES_TIME ( 
                                     ID PRIMARY KEY NOT NULL,
                                     DAY0 TEXT,
                                     DAY1 TEXT,
                                     DAY2 TEXT,
                                     DAY3 TEXT,
                                     DAY4 TEXT,
                                     DAY5 TEXT,
                                     DAY6 TEXT,
                                     DAY7 TEXT
                                             )""")
        self.c.execute("""SELECT * FROM PLACES_TIME""")
        print(self.c.fetchall())

        # PLACES_SUMMARY

        self.c.execute("""DROP TABLE IF EXISTS PLACES_SUMMARY""")
        self.c.execute("""CREATE TABLE PLACES_SUMMARY ( 
                                     ID PRIMARY KEY NOT NULL,
                                     DAY0 TEXT,
                                     DAY1 TEXT,
                                     DAY2 TEXT,
                                     DAY3 TEXT,
                                     DAY4 TEXT,
                                     DAY5 TEXT,
                                     DAY6 TEXT,
                                     DAY7 TEXT
                                    )""")
        self.c.execute("""SELECT * FROM PLACES_SUMMARY""")
        print(self.c.fetchall())

        # PLACES_WEATHER

        self.c.execute("""DROP TABLE IF EXISTS PLACES_WEATHER""")
        self.c.execute("""CREATE TABLE PLACES_WEATHER ( 
                                     ID PRIMARY KEY NOT NULL,
                                     DAY0 TEXT,
                                     DAY1 TEXT,
                                     DAY2 TEXT,
                                     DAY3 TEXT,
                                     DAY4 TEXT,
                                     DAY5 TEXT,
                                     DAY6 TEXT,
                                     DAY7 TEXT
                                    )""")
        self.c.execute("""SELECT * FROM PLACES_WEATHER""")
        print(self.c.fetchall())

        # PLACES_TEMP

        self.c.execute("""DROP TABLE IF EXISTS PLACES_TEMP""")
        self.c.execute("""CREATE TABLE PLACES_TEMP ( 
                                     ID PRIMARY KEY NOT NULL,
                                     DAY0_MIN_TEMP REAL,
                                     DAY0_MAX_TEMP REAL,
                                     DAY1_MIN_TEMP REAL,
                                     DAY1_MAX_TEMP REAL,
                                     DAY2_MIN_TEMP REAL,
                                     DAY2_MAX_TEMP REAL,
                                     DAY3_MIN_TEMP REAL,
                                     DAY3_MAX_TEMP REAL,
                                     DAY4_MIN_TEMP REAL,
                                     DAY4_MAX_TEMP REAL,
                                     DAY5_MIN_TEMP REAL,
                                     DAY5_MAX_TEMP REAL,
                                     DAY6_MIN_TEMP REAL,
                                     DAY6_MAX_TEMP REAL,
                                     DAY7_MIN_TEMP REAL,
                                     DAY7_MAX_TEMP REAL
                                    )""")
        self.c.execute("""SELECT * FROM PLACES_TEMP""")
        print(self.c.fetchall())

        # PLACES_WIND

        self.c.execute("""DROP TABLE IF EXISTS PLACES_WIND""")
        self.c.execute("""CREATE TABLE PLACES_WIND ( 
                                     ID PRIMARY KEY NOT NULL,
                                     DAY0_WIND_SPEED REAL,
                                     DAY0_WINDBEARING REAL,
                                     DAY1_WIND_SPEED REAL,
                                     DAY1_WINDBEARING REAL,
                                     DAY2_WIND_SPEED REAL,
                                     DAY2_WINDBEARING REAL,
                                     DAY3_WIND_SPEED REAL,
                                     DAY3_WINDBEARING REAL,
                                     DAY4_WIND_SPEED REAL,
                                     DAY4_WINDBEARING REAL,
                                     DAY5_WIND_SPEED REAL,
                                     DAY5_WINDBEARING REAL,
                                     DAY6_WIND_SPEED REAL,
                                     DAY6_WINDBEARING REAL,
                                     DAY7_WIND_SPEED REAL,
                                     DAY7_WINDBEARING REAL
                                    )""")
        self.c.execute("""SELECT * FROM PLACES_WIND""")
        print(self.c.fetchall())

        # PLACES_HUMIDITY     

        self.c.execute("""DROP TABLE IF EXISTS PLACES_HUMIDITY""")
        self.c.execute("""CREATE TABLE PLACES_HUMIDITY ( 
                                     ID PRIMARY KEY NOT NULL,
                                     DAY0 REAL,
                                     DAY1 REAL,
                                     DAY2 REAL,
                                     DAY3 REAL,
                                     DAY4 REAL,
                                     DAY5 REAL,
                                     DAY6 REAL,
                                     DAY7 REAL
                                             )""")
        self.c.execute("""SELECT * FROM PLACES_HUMIDITY""")
        print(self.c.fetchall())

        # PLACES_CLOUD_COVER

        self.c.execute("""DROP TABLE IF EXISTS PLACES_CLOUD_COVER""")
        self.c.execute("""CREATE TABLE PLACES_CLOUD_COVER ( 
                                     ID PRIMARY KEY NOT NULL,
                                     DAY0 REAL,
                                     DAY1 REAL,
                                     DAY2 REAL,
                                     DAY3 REAL,
                                     DAY4 REAL,
                                     DAY5 REAL,
                                     DAY6 REAL,
                                     DAY7 REAL
                                             )""")
        self.c.execute("""SELECT * FROM PLACES_CLOUD_COVER""")
        print(self.c.fetchall())

        # PLACES_AIR_PRESSURE

        self.c.execute("""DROP TABLE IF EXISTS PLACES_AIR_PRESSURE""")
        self.c.execute("""CREATE TABLE PLACES_AIR_PRESSURE ( 
                                     ID PRIMARY KEY NOT NULL,
                                     DAY0 REAL,
                                     DAY1 REAL,
                                     DAY2 REAL,
                                     DAY3 REAL,
                                     DAY4 REAL,
                                     DAY5 REAL,
                                     DAY6 REAL,
                                     DAY7 REAL
                                             )""")
        self.c.execute("""SELECT * FROM PLACES_AIR_PRESSURE""")
        print(self.c.fetchall())

        # PLACES_VISIBILITY

        self.c.execute("""DROP TABLE IF EXISTS PLACES_VISIBILITY""")
        self.c.execute("""CREATE TABLE PLACES_VISIBILITY ( 
                                     ID PRIMARY KEY NOT NULL,
                                     DAY0 REAL,
                                     DAY1 REAL,
                                     DAY2 REAL,
                                     DAY3 REAL,
                                     DAY4 REAL,
                                     DAY5 REAL,
                                     DAY6 REAL,
                                     DAY7 REAL
                                             )""")
        self.c.execute("""SELECT * FROM PLACES_VISIBILITY""")
        print(self.c.fetchall())

    def page_get(self, url):
        # check status of url/api
        try:
            p = requests.get(url)
            p.raise_for_status()
        except requests.exceptions.ConnectionError:
            print("Connection Error")
            return None
        except requests.exceptions.HTTPError:
            print("HTTP Error")
            return None
        else:
            return p

    def fifty_beauty(self):
        # store weather data of the cities nearing the 50 beautiful places

        self.create_data_base()  # create database
        t = self.c.execute("""SELECT * FROM LOCATION""")
        l = t.fetchall()
        for i in range(len(l)):
            self.store_pw(l[i][0], l[i][1], l[i][2])

    def store_pw(self, p_id, lat, log):
        # store data into table CITY (ID,CITY_NAME,DISTANCE, TYPE, LATT_LONG, WOEID)

        r = self.page_get(f"https://api.darksky.net/forecast/4f4112fdafe3f4e75efcdf4180235068/{lat},{log}")
        if r == None:
            return None
        j = json.loads(r.content)['daily']['data']

        self.c.execute(f""" SELECT * FROM WEATHER_SUMMARY WHERE ID = {p_id} """)  # check by ID
        entry = self.c.fetchone()
        if entry is None:
            self.c.execute(""" INSERT INTO WEATHER_SUMMARY (ID, SUMMARY) VALUES(?,?)""",
                           (p_id, json.loads(r.content)['daily']['summary']))

        for i in range(len(j)):
            # get the weather from diifferent days
            self.c.execute(f""" SELECT * FROM PLACES_WEATHER{i} WHERE ID = {p_id} """)  # check by woeid
            entry = self.c.fetchone()
            if entry is None:
                # insert data

                self.c.execute(f"""
                               INSERT INTO PLACES_WEATHER{i} (ID, LOCAL_TIME, SUMMARY, WEATHER, MIN_TEMP, MIN_TIME, MAX_TEMP,
                               MAX_TIME, WIND_SPEED, WINDBEARING, HUMIDITY, CLOUD_COVER, AIR_PRESSURE, VISIBILITY)
                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (p_id, j[i]['time'], j[i]['summary'], j[i]['icon'], j[i]['temperatureLow'],
                      j[i]['apparentTemperatureLowTime'], \
                      j[i]['temperatureHigh'], j[i]['apparentTemperatureHighTime'], j[i]['windSpeed'],
                      j[i]['windBearing'], \
                      j[i]['humidity'], j[i]['cloudCover'], j[i]['pressure'], j[i]['visibility']))

        # PLACES_TIME

        self.c.execute(f""" SELECT * FROM PLACES_TIME WHERE ID = {p_id} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute("""
                               INSERT INTO PLACES_TIME (ID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5, DAY6, DAY7)
                               VALUES(?,?,?,?,?,?,?,?,?)
                """, (p_id, j[0]['time'], \
                      j[1]['time'], \
                      j[2]['time'], \
                      j[3]['time'], \
                      j[4]['time'], \
                      j[5]['time'], \
                      j[6]['time'], \
                      j[7]['time']))

        # PLACES_SUMMARY

        self.c.execute(f""" SELECT * FROM PLACES_SUMMARY WHERE ID = {p_id} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute("""
                               INSERT INTO PLACES_SUMMARY (ID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5, DAY6, DAY7)
                               VALUES(?,?,?,?,?,?,?,?,?)
                """, (p_id, j[0]['summary'], \
                      j[1]['summary'], \
                      j[2]['summary'], \
                      j[3]['summary'], \
                      j[4]['summary'], \
                      j[5]['summary'], \
                      j[6]['summary'], \
                      j[7]['summary']))

        # PLACES_WEATHER

        self.c.execute(f""" SELECT * FROM PLACES_WEATHER WHERE ID = {p_id} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute("""
                               INSERT INTO PLACES_WEATHER (ID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5, DAY6, DAY7)
                               VALUES(?,?,?,?,?,?,?,?,?)
                """, (p_id, j[0]['icon'], \
                      j[1]['icon'], \
                      j[2]['icon'], \
                      j[3]['icon'], \
                      j[4]['icon'], \
                      j[5]['icon'], \
                      j[6]['icon'], \
                      j[7]['icon']))

        # PLACES_TEMP

        self.c.execute(f""" SELECT * FROM PLACES_TEMP WHERE ID = {p_id} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute("""
                               INSERT INTO PLACES_TEMP (ID, 
                               DAY0_MIN_TEMP, DAY0_MAX_TEMP,
                               DAY1_MIN_TEMP, DAY1_MAX_TEMP,
                               DAY2_MIN_TEMP, DAY2_MAX_TEMP,
                               DAY3_MIN_TEMP, DAY3_MAX_TEMP,
                               DAY4_MIN_TEMP, DAY4_MAX_TEMP,
                               DAY5_MIN_TEMP, DAY5_MAX_TEMP,
                               DAY6_MIN_TEMP, DAY6_MAX_TEMP,
                               DAY7_MIN_TEMP, DAY7_MAX_TEMP  
                               )
                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (p_id, j[0]['temperatureLow'], j[0]['temperatureHigh'], \
                      j[1]['temperatureLow'], j[1]['temperatureHigh'], \
                      j[2]['temperatureLow'], j[2]['temperatureHigh'], \
                      j[3]['temperatureLow'], j[3]['temperatureHigh'], \
                      j[4]['temperatureLow'], j[4]['temperatureHigh'], \
                      j[5]['temperatureLow'], j[5]['temperatureHigh'], \
                      j[6]['temperatureLow'], j[6]['temperatureHigh'], \
                      j[7]['temperatureLow'], j[7]['temperatureHigh']))
        # PLACES_WIND

        self.c.execute(f""" SELECT * FROM PLACES_WIND WHERE ID = {p_id} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute("""
                               INSERT INTO PLACES_WIND (ID, 
                               DAY0_WIND_SPEED, DAY0_WINDBEARING,
                               DAY1_WIND_SPEED, DAY1_WINDBEARING,
                               DAY2_WIND_SPEED, DAY2_WINDBEARING,
                               DAY3_WIND_SPEED, DAY3_WINDBEARING,
                               DAY4_WIND_SPEED, DAY4_WINDBEARING,
                               DAY5_WIND_SPEED, DAY5_WINDBEARING,
                               DAY6_WIND_SPEED, DAY6_WINDBEARING,
                               DAY7_WIND_SPEED, DAY7_WINDBEARING
                               )
                               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (p_id, j[0]['windSpeed'], j[0]['windBearing'], \
                      j[1]['windSpeed'], j[1]['windBearing'], \
                      j[2]['windSpeed'], j[2]['windBearing'], \
                      j[3]['windSpeed'], j[3]['windBearing'], \
                      j[4]['windSpeed'], j[4]['windBearing'], \
                      j[5]['windSpeed'], j[5]['windBearing'], \
                      j[6]['windSpeed'], j[6]['windBearing'], \
                      j[7]['windSpeed'], j[7]['windBearing']))

        # PLACES_HUMIDITY

        self.c.execute(f""" SELECT * FROM PLACES_HUMIDITY WHERE ID = {p_id} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute("""
                               INSERT INTO PLACES_HUMIDITY (ID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5, DAY6, DAY7)
                               VALUES(?,?,?,?,?,?,?,?,?)
                """, (p_id, j[0]['humidity'], \
                      j[1]['humidity'], \
                      j[2]['humidity'], \
                      j[3]['humidity'], \
                      j[4]['humidity'], \
                      j[5]['humidity'], \
                      j[6]['humidity'], \
                      j[7]['humidity']))

        # PLACES_CLOUD_COVER

        self.c.execute(f""" SELECT * FROM PLACES_CLOUD_COVER WHERE ID = {p_id} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute("""
                               INSERT INTO PLACES_CLOUD_COVER (ID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5, DAY6, DAY7)
                               VALUES(?,?,?,?,?,?,?,?,?)
                """, (p_id, j[0]['cloudCover'], \
                      j[1]['cloudCover'], \
                      j[2]['cloudCover'], \
                      j[3]['cloudCover'], \
                      j[4]['cloudCover'], \
                      j[5]['cloudCover'], \
                      j[6]['cloudCover'], \
                      j[7]['cloudCover']))

        # PLACES_AIR_PRESSURE

        self.c.execute(f""" SELECT * FROM PLACES_AIR_PRESSURE WHERE ID = {p_id} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute("""
                               INSERT INTO PLACES_AIR_PRESSURE (ID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5, DAY6, DAY7)
                               VALUES(?,?,?,?,?,?,?,?,?)
                """, (p_id, j[0]['pressure'], \
                      j[1]['pressure'], \
                      j[2]['pressure'], \
                      j[3]['pressure'], \
                      j[4]['pressure'], \
                      j[5]['pressure'], \
                      j[6]['pressure'], \
                      j[7]['pressure']))

        # PLACES_VISIBILITY

        self.c.execute(f""" SELECT * FROM PLACES_VISIBILITY WHERE ID = {p_id} """)  # check by woeid
        entry = self.c.fetchone()
        if entry is None:
            # insert data

            self.c.execute("""
                               INSERT INTO PLACES_VISIBILITY (ID, DAY0, DAY1, DAY2, DAY3, DAY4, DAY5, DAY6, DAY7)
                               VALUES(?,?,?,?,?,?,?,?,?)
                """, (p_id, j[0]['visibility'], \
                      j[1]['visibility'], \
                      j[2]['visibility'], \
                      j[3]['visibility'], \
                      j[4]['visibility'], \
                      j[5]['visibility'], \
                      j[6]['visibility'], \
                      j[7]['visibility']))

        self.conn.commit()


# In[ ]:


# In[ ]:


######################################### Interface and Interaction Part ###################################################


# In[ ]:


# In[3]:


class data_shows():

    def __init__(self):
        # self.up = user_part()
        self.conn = sqlite3.connect(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "\data\weather.db")
        self.c = self.conn.cursor()

    def shows_all(self, p_id):
        # show all the data of place
        print("""\n\n######################### ALL WEATHER DETAIL ###########################""")
        for i in range(8):
            t = self.c.execute(f"""SELECT * FROM PLACES_WEATHER{i} WHERE ID = {p_id} """)
            all_data = t.fetchall()[0]
            print(f"\n\n\nDay {i}", "\nLOCAL TIME:", all_data[1], "\nSUMMARY:", all_data[2], "\nWEATHER:", all_data[3],
                  "\nMIN_TEMP:", all_data[4], "\nMIN_TEMP_TIME:", all_data[5], "\nMAX_TEMP:", all_data[6],
                  "\nMAX_TEMP_TIME:", all_data[7], "\nWIND_SPEED:", all_data[8], "\nWINDBEARING:", all_data[9],
                  "\nHUMIDITY:", all_data[10], "\nCLOUD_COVER:", all_data[11], "\nAIR_PRESSURE:", all_data[12],
                  "\nVISIBILITY:", all_data[13])

    def shows_weather(self, p_id):

        print("""\n\n######################### WEATHER ###########################""")
        # showing the summary of 7 days weather
        t = self.c.execute(f"""SELECT * FROM WEATHER_SUMMARY WHERE ID = {p_id} """)
        summary_for_week = t.fetchall()[0][1]
        print("\n\nFor the future 7 days: ", summary_for_week)

        # weather and weather summary for each day
        t = self.c.execute(f"""SELECT * FROM PLACES_SUMMARY WHERE ID = {p_id} """)
        day_summary = t.fetchall()[0]
        t1 = self.c.execute(f"""SELECT * FROM PLACES_WEATHER WHERE ID = {p_id} """)
        day_weather = t1.fetchall()[0]

        for i in range(1, len(day_weather)):
            print(f"\n\nDAY {i - 1}\n    weather summary: ", day_summary[i], f"\n    weather: ", day_weather[i])

    def shows_temp(self, p_id):
        # max and min temp for each day
        print("""\n\n######################### TEMPERATURE ###########################""")
        t = self.c.execute(f"""SELECT * FROM PLACES_TEMP WHERE ID = {p_id} """)
        day_temp = t.fetchall()[0]
        for i in range(1, len(day_temp)):
            if i % 2 != 0:
                print(f"\n\nDay {int(i / 2 - 0.5)} \nMin Temperature: ", day_temp[i])
            else:
                print(f"Max Temperature: ", day_temp[i])

    def shows_wind(self, p_id):
        # wind speed and direction for each day
        print("""\n\n######################### WIND ###########################""")
        t = self.c.execute(f"""SELECT * FROM PLACES_WIND WHERE ID = {p_id} """)
        day_temp = t.fetchall()[0]
        for i in range(1, len(day_temp)):
            if i % 2 != 0:
                print(f"\n\nDay {int(i / 2 - 0.5)} \nWind Speed: ", day_temp[i])
            else:
                print(f"Direction : ", day_temp[i])

    def shows_humi(self, p_id):
        # humidity for each days
        print("""\n\n######################### HUMIDITY ###########################""")
        t = self.c.execute(f"""SELECT * FROM PLACES_HUMIDITY WHERE ID = {p_id} """)
        day_humi = t.fetchall()[0]

        for i in range(1, len(day_humi)):
            print(f"\n\nDAY {i - 1}\n    Humidity: ", day_humi[i])

    def shows_visi(self, p_id):
        # visibility for each days
        print("""\n\n######################### VISIBILITY ###########################""")
        t = self.c.execute(f"""SELECT * FROM PLACES_VISIBILITY WHERE ID = {p_id} """)
        day_vis = t.fetchall()[0]

        for i in range(1, len(day_vis)):
            print(f"\n\nDAY {i - 1}\n    Visibility: ", day_vis[i])

    def shows_pres(self, p_id):
        # air pressure for each days
        print("""\n\n######################### AIR PRESSURE ###########################""")
        t = self.c.execute(f"""SELECT * FROM PLACES_AIR_PRESSURE WHERE ID = {p_id} """)
        day_pres = t.fetchall()[0]

        for i in range(1, len(day_pres)):
            print(f"\n\nDAY {i - 1}\n    Air Pressure: ", day_pres[i])

    def shows_cloud(self, p_id):
        # cloud cover for each days
        print("""\n\n######################### CLOUD COVER ###########################""")
        t = self.c.execute(f"""SELECT * FROM PLACES_CLOUD_COVER WHERE ID = {p_id} """)
        day_cloud = t.fetchall()[0]

        for i in range(1, len(day_cloud)):
            print(f"\n\nDAY {i - 1}\n    Cloud Cover: ", day_cloud[i])

    def shows_cities(self, p_id):
        # the weather details for each cities in each days
        print("""\n\n######################### CITIES WEATHER ###########################""")
        for i in range(6):
            print(f'\n\n\n########## Day {i}')
            t = self.c.execute(f"""
                     WITH CITY_T AS
                     (SELECT CITY_NAME, CITY.WOEID, DISTANCE 
                     FROM CITY JOIN CITY_PLACES ON CITY.WOEID = CITY_PLACES.WOEID
                     WHERE CITY_PLACES.ID = {p_id})

                     SELECT * 
                     FROM CITIES_WEATHER{i} JOIN CITY_T ON CITIES_WEATHER{i}.WOEID = CITY_T.WOEID

                     """)

            city_weather = t.fetchall()
            for j in range(len(city_weather)):
                print(f"""
                
                        City Name: {city_weather[j][-3]}
                        City WOEID: {city_weather[j][0]}
                        Distance: {city_weather[j][-1]}
                        Local Time: {city_weather[j][1]}
                        Weather: {city_weather[j][2]}
                        Max Temperature: {city_weather[j][4]}
                        Min Temperature: {city_weather[j][3]}
                        AVG Temperature: {city_weather[j][5]}
                        Wind Speed: {city_weather[j][6]}
                        Wind Direction: {city_weather[j][7]}
                        Humidity: {city_weather[j][8]}
                        Air Pressure: {city_weather[j][9]}
                        visibility: {city_weather[j][10]}
                        Predictability: {city_weather[j][11]}
                """)

    def shows_ana(self, p_id):
        print("""\n\n######################### ANALYSIS ###########################""")
        diff_place = []  # store the difference of Min_Max temp of places
        diff_city = {}  # store the difference of Min_Max temp of cities

        t = self.c.execute(f"""
                 SELECT PLACE  
                 FROM TRAVEL
                 WHERE ID = {p_id}
                 """)
        place_name = t.fetchall()[0][0]

        # create list for each cities
        t = self.c.execute(f"""
                 SELECT WOEID  
                 FROM CITY_PLACES
                 WHERE ID = {p_id}
                 """)
        woeids = t.fetchall()
        for woeid in woeids:
            diff_city[woeid[0]] = diff_city.get(woeid[0], [])

        for i in range(6):
            # each days data
            t = self.c.execute(f"""
                 SELECT CITY_PLACES.WOEID, DAY{i}_MIN_TEMP, DAY{i}_MAX_TEMP 
                 FROM CITY_PLACES JOIN CITIES_TEMP ON CITY_PLACES.WOEID = CITIES_TEMP.WOEID
                 WHERE CITY_PLACES.ID = {p_id}
                 """)
            c_t = t.fetchall()
            for j in range(len(c_t)):
                # each cities temp diff
                diff_city[c_t[j][0]].append(c_t[j][2] - c_t[j][1])

            # place temp diff
            t1 = self.c.execute(f"""
                 SELECT DAY{i}_MIN_TEMP, DAY{i}_MAX_TEMP 
                 FROM PLACES_TEMP
                 WHERE ID = {p_id}
                 """)
            p_t = t.fetchall()[0]
            diff_place.append(p_t[1] - p_t[0])

        keys = list(diff_city.keys())
        vals = list(diff_city.values())
        for i in range(len(keys)):
            # each city

            # get city's name
            t2 = self.c.execute(f"""
                 SELECT CITY_NAME 
                 FROM CITY
                 WHERE WOEID = {keys[i]}
                 """)
            name = t2.fetchall()[0][0]

            # graph
            day = ['DAY0', 'DAY1', 'DAY2', 'DAY3', 'DAY4', 'DAY5']
            x = list(range(len(day)))
            plt.figure(i)
            plt.subplot(111)
            plt.title(f"Temperature Difference between {place_name} and {name}")

            plt.bar(x, diff_place, width=0.5, label=f"{place_name}", tick_label=day, fc='y')
            for xn in range(len(x)):
                x[xn] = x[xn] + 0.5
            plt.bar(x, vals[i], 0.5, label=f"{name}", color='g')

            count = 0
            for j in range(len(vals[i])):

                if vals[i][j] > diff_place[j]:
                    # city_diif > place_diff
                    count += 1

            plt.legend()
            plt.show()

            if count / len(diff_place) > 0.5:

                print(
                    f"\n\nTemparature change huge in city '{name}' than in this places '{place_name}', you'd better bring more clothes")
            else:

                print(
                    f"\n\nTemparature change less in city '{name}' than in this places '{place_name}', you could only bring your wallet XD")


# In[4]:


class user_part():

    def __init__(self):

        self.conn = sqlite3.connect(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "\data\weather.db")
        self.c = self.conn.cursor()
        self.ds = data_shows()
        print("##################### Thanks for using this product! #######################")

    def check_quit(self):
        print("Do you want to quit?   1.Y   2.N")

        quit_or_not = input("""Please input the number for the one you want:""")

        if quit_or_not == '1':
            print("\n\n\n         Thanks for using the BEST weather software                ")
            print("                      HAPPY VACATION                 ")
            print("\n\n\n                     Quit Successfully                ")
            return None
        elif quit_or_not == '2':
            self.choose_partern()
        else:
            print("\n##################### PLEASE INPUT THE CORRECT NUMBER##################### \n")
            self.check_quit()

    def choose_partern(self):
        # user choose the part they want to use
        try:
            print("""
                        Which information would you like to gain:
                        0. Quit
                        1. The Places suggest by us
                        2. The Analysis Report
                    """)
            part = int(input("""Please input the number for the one you want:"""))

        except ValueError:
            print("\n ##################### PLEASE INPUT THE CORRECT NUMBER! #####################\n")
            self.choose_partern()

        except:
            print("\n ##################### UNKNOWN ERROR! ##################### \n")
            self.choose_partern()

        else:
            if part == 1:
                self.suggestion()
            elif part == 2:
                self.ana_report()
            elif part == 0:
                print("\n\n\n         Thanks for using the BEST weather software                ")
                print("                      HAPPY VACATION                 ")
                print("\n\n\n                     Quit Successfully                ")
                return None
            else:
                print("\n##################### PLEASE INPUT THE CORRECT NUMBER##################### \n")
                self.choose_partern()

    def suggestion(self):
        # suggest the place should go
        place_id = []
        t = self.c.execute("""SELECT * FROM PLACES_WEATHER """)
        weather = t.fetchall()

        if len(weather) == 0:
            print("It seems no places to go LOL, now you have time to play games and save the money.")
            return None

        print("\n\n\nAccording to the weather and visibility \nThose are the places we suggest you to go:")

        for i in range(len(weather)):
            # choose the place could go
            if list(weather[i]).count('clear-day') >= 5:
                # reqirement 1 : sunny day more than 5  
                t1 = self.c.execute(f"""SELECT * FROM PLACES_VISIBILITY WHERE ID = {weather[i][0]} """)
                vis = list(t1.fetchall()[0])

                count = 0
                for j in range(1, len(vis) - 1):
                    # check the visibility > 6
                    if vis[j] >= 6:
                        count += 1

                if count >= 6:
                    # requirement 2: num of days that have good visibility should >= 6 
                    place_id.append(vis[0])

        i = 0
        if place_id != []:
            for p_id in place_id:
                i += 1
                t = self.c.execute(f"""SELECT * FROM TRAVEL WHERE ID = {p_id}""")
                place = t.fetchall()
                if place[0][2] == None:
                    print(i, ".", place[0][1], 'locate in', place[0][3])
                else:
                    print(i, ".", place[0][1], 'locate in', place[0][2], ',', place[0][3])
        else:
            print(
                "\n\n\n#########################  No suggestion Sorry!!! You'd better stay at home and play some games !!! ")
        self.choose_place(i, place_id)

    def choose_place(self, num, place_id):
        # user choose the place that he/she interested
        print("""\n\n\n                Which Place's detail do you want to know?""")
        try:
            d_num = int(
                input(f"""\n\nNote:From 0 - {num}, 0 means Quit.\nPlease input the number for the one you want:"""))

        except ValueError:
            print("\n ##################### PLEASE INPUT THE CORRECT NUMBER! #####################\n")

            self.choose_place(num, place_id)

        except:
            print("\n ##################### UNKNOWN ERROR! ##################### \n")
            self.choose_place(self, num, place_id)
        else:
            if d_num == 0:
                self.check_quit()
                return None
            elif d_num >= 1 and d_num <= num:
                self.shows_detail(place_id[d_num - 1])
            else:
                print("\n ##################### PLEASE INPUT THE CORRECT NUMBER! ##################### \n")
                self.choose_place(num, place_id)

    def shows_detail(self, p_id):

        print("""                 
                                    What information you want?
                        0. All
                        1. Weather
                        2. Temprature
                        3. Wind
                        4. Humility
                        5. Visibility
                        6. Pressure
                        7. Cloudcover
                        8. Weather of the cities next to the place
                        9. Analysis
                        10. Quit
                        
            Note : You could combine them by using comma(','), for example: 1,2 
                        """)

        c_num = []
        n_num = ()
        ip = input(f"""Please input the number for the one you want:""")
        if len(ip) >= 1:
            # more than 1 input
            for i in ip.split(','):
                if i.isdigit():
                    # check is digital?
                    if int(i) >= 0 and int(i) <= 10:
                        # in the range
                        c_num.append(int(i))

        if c_num == []:
            print("""##################### PLEASE INPUT CORRECTLY! #####################""")
            self.shows_detail(p_id)

        else:
            # manage the inputs
            c_num.sort()
            n_num = set(c_num)

        for i in n_num:
            if i == 0:
                self.ds.shows_all(p_id)

            elif i == 1:
                self.ds.shows_weather(p_id)

            elif i == 2:
                self.ds.shows_temp(p_id)

            elif i == 3:
                self.ds.shows_wind(p_id)

            elif i == 4:
                self.ds.shows_humi(p_id)

            elif i == 5:
                self.ds.shows_visi(p_id)

            elif i == 6:
                self.ds.shows_pres(p_id)

            elif i == 7:
                self.ds.shows_cloud(p_id)

            elif i == 8:
                self.ds.shows_cities(p_id)

            elif i == 9:
                self.ds.shows_ana(p_id)

            elif i == 10:
                self.check_quit()
                return None

        self.shows_detail(p_id)

    def ana_report(self):

        print("""\n\n\n####################################################################################################
####################################### ANALYSIS REPORT ############################################""")
        print("""\n\n\n\n                                           DIRECTORY
                            
                            0. Quit
                            1. All temperature difference between places and cities
                            2. Analysis about temperature relate to lattitude and longitude
                            3. Analysis about wind speed relate to lattitude and longitude""")

        r = report()
        c = input("""                 Please choose which report you want to read""").strip()

        if c == '0':
            self.check_quit()
            return None
        elif c == '1':
            r.temp_diff()
            self.ana_report()
        elif c == '2':
            r.temp_lati_longi()
            self.ana_report()
        elif c == '3':
            r.wind_lat_log()
            self.ana_report()
        else:
            print("""################################ Please input Correctly #################################""")
            self.ana_report()


# In[5]:


class report():
    def __init__(self):

        self.conn = sqlite3.connect(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "\data\weather.db")
        self.c = self.conn.cursor()

    def temp_diff(self):
        # showing the temperature difference between cities and places

        t = self.c.execute(f"""
                     SELECT ID  
                     FROM TRAVEL
                     """)
        p_ids = t.fetchall()  # get all the p_id

        rate = 0

        for pp_id in p_ids:
            # for all the places

            p_id = pp_id[0]  # place_id
            diff_place = []  # store the difference of Min_Max temp of places
            diff_city = {}  # store the difference of Min_Max temp of cities

            t = self.c.execute(f"""
                     SELECT PLACE  
                     FROM TRAVEL
                     WHERE ID = {p_id}
                     """)
            place_name = t.fetchall()[0][0]

            # create list for each cities
            t = self.c.execute(f"""
                     SELECT WOEID  
                     FROM CITY_PLACES
                     WHERE ID = {p_id}
                     """)
            woeids = t.fetchall()
            for woeid in woeids:
                diff_city[woeid[0]] = diff_city.get(woeid[0], [])

            for i in range(6):
                # each days data
                t = self.c.execute(f"""
                     SELECT CITY_PLACES.WOEID, DAY{i}_MIN_TEMP, DAY{i}_MAX_TEMP 
                     FROM CITY_PLACES JOIN CITIES_TEMP ON CITY_PLACES.WOEID = CITIES_TEMP.WOEID
                     WHERE CITY_PLACES.ID = {p_id}
                     """)
                c_t = t.fetchall()
                for j in range(len(c_t)):
                    # each cities
                    diff_city[c_t[j][0]].append(c_t[j][2] - c_t[j][1])

                # place
                t1 = self.c.execute(f"""
                     SELECT DAY{i}_MIN_TEMP, DAY{i}_MAX_TEMP 
                     FROM PLACES_TEMP
                     WHERE ID = {p_id}
                     """)
                p_t = t.fetchall()[0]
                diff_place.append(p_t[1] - p_t[0])

            keys = list(diff_city.keys())
            vals = list(diff_city.values())
            for i in range(len(keys)):
                # each city

                # get city's name
                t2 = self.c.execute(f"""
                     SELECT CITY_NAME 
                     FROM CITY
                     WHERE WOEID = {keys[i]}
                     """)
                name = t2.fetchall()[0][0]

                ############### graph for temp diff 

                print(f"""\n\n\n################### Graph for {place_name} and {name}""")

                day = ['DAY0', 'DAY1', 'DAY2', 'DAY3', 'DAY4', 'DAY5']
                x = list(range(len(day)))
                plt.figure(i)
                plt.subplot(111)
                plt.title(f"Temperature Difference between {place_name} and {name}")

                plt.bar(x, diff_place, width=0.5, label=f"{place_name}", tick_label=day, fc='y')
                for xn in range(len(x)):
                    x[xn] = x[xn] + 0.5
                plt.bar(x, vals[i], 0.5, label=f"{name}", color='g')
                plt.legend()
                plt.show()

                ######## for rate
                large = 0
                small = 0
                draw = 0

                for j in range(len(vals[i])):
                    if vals[i][j] > diff_place[j]:
                        # city_diif > place_diff
                        large += 1

                    elif vals[i][j] == diff_place[j]:
                        # city_diif = place_diff
                        draw += 1

                    else:
                        # city_diif < place_diff
                        small += 1

                ############ graph of rate

                x = [large / 6, small / 6, draw / 6]
                plt.figure(i)
                plt.subplot(111)
                plt.title(f"Rate of Temperature Difference between {place_name} and {name}")

                plt.pie(x, labels=["C > P", "C < P", "C = P"], colors=('b', 'g', 'r'))
                plt.legend()
                plt.show()

                if large / 6 > 0.5:
                    print(f"""It seems temperature changes huge in city '{name}' than in place '{place_name}'
{x[0] * 100}% of days temperature changes larger in city '{name}' than in place '{place_name}'
{x[1] * 100}% of days temperature changes less in city '{name}' than in place '{place_name}'
{x[2] * 100}% of days temperature changes same in city '{name}' and in place '{place_name}'""")
                elif small / 6 > 0.5:
                    print(f"""It seems temperature changes less in city '{name}' than in place '{place_name}'
{x[0] * 100}% of days temperature changes larger in city '{name}' than in place '{place_name}'
{x[1] * 100}% of days temperature changes less in city '{name}' than in place '{place_name}'
{x[2] * 100}% of days temperature changes same in city '{name}' and in place '{place_name}'""")
                elif draw / 6 > 0.5:
                    print(f"""It seems temperature difference are the same in city '{name}' and in place '{place_name}'
{x[0] * 100}% of days temperature changes larger in city '{name}' than in place '{place_name}'
{x[1] * 100}% of days temperature changes less in city '{name}' than in place '{place_name}'
{x[2] * 100}% of days temperature changes same in city '{name}' and in place '{place_name}'""")
                else:
                    print(f"""It seems temperature difference are dynamic in city '{name}' and in place '{place_name}'
{x[0] * 100}% of days temperature changes larger in city '{name}' than in place '{place_name}'
{x[1] * 100}% of days temperature changes less in city '{name}' than in place '{place_name}'
{x[2] * 100}% of days temperature changes same in city '{name}' and in place '{place_name}'""")

    def temp_lati_longi(self):

        # places data
        p_id = []
        p_lat = []
        p_log = []
        p_avg_diff_temp = []

        t = self.c.execute("""
                SELECT  LOCATION.ID, LATI, LONGI, 
                        DAY0_MAX_TEMP, DAY0_MIN_TEMP, 
                        DAY1_MAX_TEMP, DAY1_MIN_TEMP, 
                        DAY2_MAX_TEMP, DAY2_MIN_TEMP, 
                        DAY3_MAX_TEMP, DAY3_MIN_TEMP, 
                        DAY4_MAX_TEMP, DAY4_MIN_TEMP,
                        DAY5_MAX_TEMP, DAY5_MIN_TEMP,
                        DAY6_MAX_TEMP, DAY6_MIN_TEMP,
                        DAY7_MAX_TEMP, DAY7_MIN_TEMP 
                
                FROM LOCATION JOIN PLACES_TEMP
                ON LOCATION.ID = PLACES_TEMP.ID
                
                 """)

        p_temps = t.fetchall()
        for i in range(len(p_temps)):
            temp_diff = []
            p_id.append(p_temps[i][0])  # store id
            p_lat.append(p_temps[i][1])  # store lat
            p_log.append(p_temps[i][2])  # store log
            for j in range(3, len(p_temps[i])):
                # calculate average temp diff
                if j % 2 != 0:
                    temp_diff.append(p_temps[i][j] - p_temps[i][j + 1])  # temp diff
            p_avg_diff_temp.append((sum(temp_diff) / len(temp_diff)) * 20)

        plt.figure(1)
        plt.gcf().set_size_inches(18.5, 18.5)
        plt.subplot(111)
        plt.title(f"Temperature Difference Graph for Places")

        plt.scatter(p_log, p_lat, s=p_avg_diff_temp, alpha=0.5, c=p_id)
        plt.xlabel('longitude')
        plt.ylabel('latitude')
        plt.show()

        # cities data

        woeid = []
        c_lat = []
        c_log = []
        c_avg_diff_temp = []

        t = self.c.execute("""
                SELECT  CITY.WOEID, LATT_LONG, 
                        DAY0_MAX_TEMP, DAY0_MIN_TEMP, 
                        DAY1_MAX_TEMP, DAY1_MIN_TEMP, 
                        DAY2_MAX_TEMP, DAY2_MIN_TEMP, 
                        DAY3_MAX_TEMP, DAY3_MIN_TEMP, 
                        DAY4_MAX_TEMP, DAY4_MIN_TEMP,
                        DAY5_MAX_TEMP, DAY5_MIN_TEMP

                FROM CITY JOIN CITIES_TEMP
                ON CITY.WOEID = CITIES_TEMP.WOEID
                 """)

        p_temps = t.fetchall()
        for i in range(len(p_temps)):
            temp_diff = []
            woeid.append(p_temps[i][0])  # store id
            lat, log = p_temps[i][1].split(',')
            c_lat.append(float(lat))  # store lat
            c_log.append(float(log))  # store log
            for j in range(2, len(p_temps[i])):
                # calculate average temp diff
                if j % 2 == 0:
                    temp_diff.append(p_temps[i][j] - p_temps[i][j + 1])  # temp diff
            c_avg_diff_temp.append((sum(temp_diff) / len(temp_diff)) * 20)

        plt.figure(2)
        plt.gcf().set_size_inches(18.5, 18.5)
        plt.subplot(111)
        plt.title(f"Temperature Difference Graph for Cities")

        plt.scatter(c_log, c_lat, s=c_avg_diff_temp, alpha=0.5, c='g')
        plt.xlabel('longitude')
        plt.ylabel('latitude')
        plt.show()

        # combine

        plt.figure(3)
        plt.gcf().set_size_inches(18.5, 18.5)
        plt.subplot(111)
        plt.title(f"Temperature Difference Graph for Combine")

        plt.scatter(c_log, c_lat, label='Cities', s=c_avg_diff_temp, alpha=0.5, c='r')
        plt.scatter(p_log, p_lat, label='Places', s=p_avg_diff_temp, alpha=0.5, c='b')
        plt.xlabel('longitude')
        plt.ylabel('latitude')
        plt.legend()
        plt.show()

        print("""######### Conclusion: It seems that the temperature difference is mostly large in natural scenery than in the cites.
At the same time, it seems like the natural scenery and cities in the southwest and the middle get some huge temperature change.""")

    def wind_lat_log(self):

        # places data
        p_id = []
        p_lat = []
        p_log = []
        p_avg_wind_speed = []

        t = self.c.execute("""
                SELECT  LOCATION.ID, LATI, LONGI, 
                        DAY0_WIND_SPEED, 
                        DAY1_WIND_SPEED,
                        DAY2_WIND_SPEED, 
                        DAY3_WIND_SPEED,
                        DAY4_WIND_SPEED,
                        DAY5_WIND_SPEED,
                        DAY6_WIND_SPEED,
                        DAY7_WIND_SPEED
                
                FROM LOCATION JOIN PLACES_WIND
                ON LOCATION.ID = PLACES_WIND.ID
                 """)

        p_temps = t.fetchall()
        for i in range(len(p_temps)):
            temp_ws = []
            p_id.append(p_temps[i][0])  # store id
            p_lat.append(p_temps[i][1])  # store lat
            p_log.append(p_temps[i][2])  # store log
            for j in range(3, len(p_temps[i])):
                # calculate average temp diff
                temp_ws.append(p_temps[i][j])  # temp diff
            p_avg_wind_speed.append((sum(temp_ws) / len(temp_ws)) * 20)

        plt.figure(1)
        plt.gcf().set_size_inches(18.5, 18.5)
        plt.subplot(111)
        plt.title(f"Average Wind Speed Graph for Places")

        plt.scatter(p_log, p_lat, s=p_avg_wind_speed, alpha=0.5, c=p_id)
        plt.xlabel('longitude')
        plt.ylabel('latitude')
        plt.show()

        # cities data

        woeid = []
        c_lat = []
        c_log = []
        c_avg_wind_speed = []

        t = self.c.execute("""
                SELECT  CITY.WOEID, LATT_LONG, 
                        DAY0_WIND_SPEED, 
                        DAY1_WIND_SPEED,
                        DAY2_WIND_SPEED, 
                        DAY3_WIND_SPEED,
                        DAY4_WIND_SPEED,
                        DAY5_WIND_SPEED

                FROM CITY JOIN CITIES_WIND
                ON CITY.WOEID = CITIES_WIND.WOEID
                 """)

        p_temps = t.fetchall()
        for i in range(len(p_temps)):
            temp_ws = []
            woeid.append(p_temps[i][0])  # store id
            lat, log = p_temps[i][1].split(',')
            c_lat.append(float(lat))  # store lat
            c_log.append(float(log))  # store log
            for j in range(2, len(p_temps[i])):
                # calculate average temp diff
                temp_ws.append(p_temps[i][j])  # wind speed diff
            c_avg_wind_speed.append((sum(temp_ws) / len(temp_ws)) * 20)

        plt.figure(2)
        plt.gcf().set_size_inches(18.5, 18.5)
        plt.subplot(111)
        plt.title(f"Average Wind Speed Graph for Cities")

        plt.scatter(c_log, c_lat, s=c_avg_wind_speed, alpha=0.5, c='g')
        plt.xlabel('longitude')
        plt.ylabel('latitude')
        plt.show()

        # combine

        plt.figure(3)
        plt.gcf().set_size_inches(18.5, 18.5)
        plt.subplot(111)
        plt.title(f"Average Wind Speed Graph for Combine")

        plt.scatter(c_log, c_lat, label='Cities', s=c_avg_wind_speed, alpha=0.5, c='r')
        plt.scatter(p_log, p_lat, label='Places', s=p_avg_wind_speed, alpha=0.5, c='b')
        plt.xlabel('longitude')
        plt.ylabel('latitude')
        plt.legend()
        plt.show()

        print(
            """########  Conclusion : It seems that the average wind speed no huge difference depends on the location, 
but the location still has some effect on wind speed; coastline places have faster wind speeds. Also, the wind speed
is faster in the natural scenery than in the cities.""")


def parse_args():
    description = "you should add those parameter"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--remote', type=str,
                        help='For remote use')
    parser.add_argument('--local', type=str,
                        help='For local use')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    # print(f"You are in file : {__file__}")
    args = parse_args()

    if args.remote:
        print("\n\n###################### Remote Processing ########################")

        print("\n\n###################### Getting 50 Beautiful Places in the US ########################")
        t = travel()
        t.travel()
        print("\n\n###################### Data Management complete ########################")

        print("\n\n###################### Getting Location Data  ########################")
        l = location()
        l.fifty_beauty()
        print("\n\n###################### Data Management complete ########################")

        print("\n\n###################### Checking cities near by ########################")
        nc = near_city()
        nc.fifty_beauty()
        print("\n\n###################### Data Management complete ########################")

        print("\n\n###################### Searching Cities' Data ########################")
        wc = weather_of_cities()
        wc.fifty_beauty()
        print("\n\n###################### Data Management complete ########################")

        print("\n\n###################### Searching Places' Data ########################")
        wp = weather_of_places()
        wp.fifty_beauty()
        print("\n\n###################### Data Management complete ########################")

        up = user_part()
        up.choose_partern()
    elif args.local:
        conn = sqlite3.connect(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "\data\weather.db")
        c = conn.cursor()

        try:
            c.execute('''SELECT * FROM TRAVEL''')
            c.fetchall()
        except:
            print("""\n\n################## Error Detected #######################""")
            time.sleep(1)
            print("""\n\n################## Entering Safe Mode #######################""")
            print("""\n################## Do you want to continue? #######################""")
            cho = input("Please input the number for your choice: 1.Yes 2.No")

            if cho.strip() == '1':
                print("""\n\n################## Entering Remote Part #######################""")
                print("\n\n###################### Remote Processing ########################")

                print("\n\n###################### Getting 50 Beautiful Places in the US ########################")
                t = travel()
                t.travel()
                print("\n\n###################### Data Management complete ########################")

                print("\n\n###################### Getting Location Data  ########################")
                l = location()
                l.fifty_beauty()
                print("\n\n###################### Data Management complete ########################")

                print("\n\n###################### Checking cities near by ########################")
                nc = near_city()
                nc.fifty_beauty()
                print("\n\n###################### Data Management complete ########################")

                print("\n\n###################### Searching Cities' Data ########################")
                wc = weather_of_cities()
                wc.fifty_beauty()
                print("\n\n###################### Data Management complete ########################")

                print("\n\n###################### Searching Places' Data ########################")
                wp = weather_of_places()
                wp.fifty_beauty()
                print("\n\n###################### Data Management complete ########################")

                up = user_part()
                up.choose_partern()

            elif cho.strip() == '2':
                print("""\n\n################## System Closed #######################""")

            else:

                print("""\n\n################## Unexcept Input Detected #######################""")
                print("""\n\n################## Force System Shutdown #######################""")
                time.sleep(1)
                print("""\n\n################## System Closed #######################""")

        else:
            up = user_part()
            up.choose_partern()
    else:
        print("Not available Parameter")


def main():
    conn = sqlite3.connect(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "\data\weather.db")
    c = conn.cursor()

    try:
        c.execute('''SELECT * FROM TRAVEL''')
        c.fetchall()
    except:
        print("""\n\n################## Error: No Database Detected #######################""")

        print(
            """\n\n################## Please download the database "weather.db" from github: https://github.com/xielidawan/Inf510_project.git #######################""")

        print("""\n\n################## System Closed #######################""")

    else:
        up = user_part()
        up.choose_partern()
