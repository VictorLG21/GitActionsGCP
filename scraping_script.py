# pip install pandas
# pip install requests
# pip install beautifulsoup4

import pandas as pd
import requests
from bs4 import BeautifulSoup
from google.cloud import storage
import re
import mysql.connector as bd
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

#cnx = bd.connect(user='root', password = 'root', host = '104.154.155.31', database = 'Times')
#conn = cnx.cursor()

credentials = GoogleCredentials.get_application_default()

service = discovery.build('sqladmin', 'v1beta4', credentials=credentials)

# Project ID of the project that contains the instance.
project = 'DataOps'  # TODO: Update placeholder value.

# Database instance ID. This does not include the project ID.
instance = 'root'  # TODO: Update placeholder value.


def scrape_this(uri="/pages/forms/"):
  page = requests.get("https://scrapethissite.com" + uri)
  soup = BeautifulSoup(page.text, "html.parser")

  div = soup.find(id="hockey")  
  table = div.find("table")

  data_rows = table.find_all("tr", attrs={"class": "team"})
  parsed_data = list()
  stat_keys = [col.attrs["class"][0] for col in data_rows[0].find_all("td")]

  for row in data_rows:
    tmp_data = dict()
    for attr in stat_keys:
      attr_val = row.find(attrs={"class": attr}).text
      tmp_data[attr] = re.sub(r"^\s+|\s+$", "", attr_val)
    parsed_data.append(tmp_data)

  data_df = pd.DataFrame(parsed_data)
  return data_df

page = requests.get("https://scrapethissite.com/pages/forms/")
soup = BeautifulSoup(page.text, "html.parser")
pagination = soup.find("ul", attrs={"class": "pagination"})
link_elms = pagination.find_all("li")
links = [link_elm.find("a").attrs["href"] for link_elm in link_elms]
links = set(links)

temp_dfs = list()
for link in links:
  tmp_df = scrape_this(uri=link)
  temp_dfs.append(tmp_df)
hockey_team_df = pd.concat(temp_dfs, axis=0).reset_index()
hockey_team_df.sort_values(["year", "name"], inplace=True)

for time in hockey_team_df.values:
  database_body = {
    'id':time[0],
    'nome':time[1],
    'vitoria':time[3],
    'derrota':time[4]
}
  request = service.databases().insert(project=project, instance=instance, body=database_body)
  response = request.execute()