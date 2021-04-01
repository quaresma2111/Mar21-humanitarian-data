#!/usr/bin/env python
# coding: utf-8

# In[2]:


#Necessary Libraries
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
import warnings
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import imageio
from bokeh.plotting import figure, save
import seaborn as sns
from shapely.geometry import Point,Polygon
from datetime import datetime

get_ipython().run_line_magic('matplotlib', 'inline')


# ## Web Scraper to Download the Data

# In[3]:


#Set the URL and get the html data in a Beatiful Soup Object
url = "https://data.humdata.org/dataset/site-location-of-rohingya-refugees-in-cox-s-bazar"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'}
page = requests.get(url, headers=headers)
soup = BeautifulSoup(page.content, 'html.parser')

#Skip to the resource list where excel files are present
main_content = soup.find(class_="hdx-bs3 resource-list")

#Get all the href links to download the excel files
all_links = []
for link in main_content.find_all('a', href=True):
    all_links.append(link['href'])

#Download the files and save all data in a Master Sheet
warnings.filterwarnings("ignore") #Don't print warnings

base = "https://data.humdata.org"
data_all = pd.DataFrame(columns=["New_Camp_SSID","New_Camp_Name","Site_Name_Alias","Settlement Type","District",
                                 "Upazila","Union","Geo_Code","Total_HH","Total_Pop","Latitude","Longitude","date"])

for i in all_links:
    match = re.findall('download/(\d+)_',i)
    if match != []:
        #print(match)
        download_url = base+i
        resp = requests.get(download_url,verify=False)
        output = open('test.xlsx', 'wb')
        output.write(resp.content)
        data = pd.read_excel("test.xlsx")         
        data['date'] = match[0]
        data_all = data_all.append(data)
        
#data_all.to_excel("All_Data.xlsx",index=False)


# ## Map the Locations of the Camps using Geopandas 

# In[4]:


#Subset for data only where lat/long is present
data_all = data_all[data_all.Latitude != ' ']

#Convert the string dates into datetime objects in the raw data
data_all.index = range(len(data_all))
data_all['Date2'] = ''

for i in range(len(data_all)):
    try:
        data_all['Date2'][i] = pd.to_datetime(data_all['date'][i], format='%Y%m%d')
    except:
        data_all['Date2'][i] = pd.to_datetime(data_all['date'][i], format='%y%m%d')


# In[5]:


# Import the national and regional boundary shape files of Bangladesh
base_path = ''

admin0_shp = gpd.read_file(base_path + 'bgd_adm_bbs_20201113_SHP/bgd_admbnda_adm0_bbs_20201113.shp')
admin1_shp = gpd.read_file(base_path + 'bgd_adm_bbs_20201113_SHP/bgd_admbnda_adm1_bbs_20201113.shp')
admin2_shp = gpd.read_file(base_path + 'bgd_adm_bbs_20201113_SHP/bgd_admbnda_adm2_bbs_20201113.shp')
admin3_shp = gpd.read_file(base_path + 'bgd_adm_bbs_20201113_SHP/bgd_admbnda_adm3_bbs_20201113.shp')

admin = pd.read_excel(base_path + 'bgd_adminboundaries_tabulardata.xlsx')


# In[6]:


#Convert the lat/long data of site locations into appropriate format
crs = {'init':'epsg:4326'}
geometry = [Point(xy) for xy in zip(data_all['Longitude'],data_all['Latitude'])]
all_location_data = gpd.GeoDataFrame(data_all,crs=crs,geometry=geometry)


# In[7]:


#Filter for the districts where the camps are located
relevant = list(data_all['Upazila'].unique())
base_data = admin3_shp[admin3_shp.ADM3_EN.isin(relevant)]

base_data.head()


# ## Plot the Locations of the Camps 

# In[8]:


data_all.head()


# In[12]:


latest_date


# In[18]:


#Set the axes and size of plot
fig, ax = plt.subplots(figsize=(15,15))
ax.set_aspect("equal")

#Title of Plot
#ax.set_title('Location of Refugee Camps in Bangladesh, as on: ' + latest_date.strftime("%Y/%m/%d"))
             #fontdict={'fontsize': 25, 'fontweight' : 3})

#Base data with ADM3 (Sub-District) Boundaries of Bangladesh
base = base_data.plot(ax=ax, color='white', edgecolor='black')

for index,row in base_data.iterrows():
    plt.text(base_data.geometry[index].centroid.x, base_data.geometry[index].centroid.y, base_data.ADM3_EN[index], fontsize=20) 

#Plot the locations of the Refugee Camps with the most recent data based on date
all_location_data = all_location_data.to_crs(admin3_shp.crs)
latest_date = all_location_data['Date2'].max()
latest_location_data = all_location_data[all_location_data.date == latest_date]
latest_location_data.plot(ax=ax, marker='p', color='blue', markersize=50);
plt.show()

#Save the map as .png file.
#fig.savefig('camp_locations.png', dpi=300)

