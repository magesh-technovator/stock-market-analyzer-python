#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 27 20:51:09 2020

@author: MAGESHWARAN
"""

import requests
from bs4 import BeautifulSoup
import copy
import re
import os
import json
from tqdm import tqdm
import pandas as pd
import ast

# Libraries required to limit the time taken by a request
import signal
from contextlib import contextmanager

class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


class MoneyControlScrapper(object):
    
    def get_response(self, aurl):
        hdr= {'User-Agent':'Mozilla/5.0'}
        retry = 0
        while retry < 5:
            try: 
                # Waiting 60 seconds to recieve a responser object
                with time_limit(30):
                    content = requests.get(aurl,headers=hdr).content
                break
            
            except Exception:
                print("Error opening url!!")
                print(aurl)
                retry += 1
                continue
        
        if retry == 5:
            return None
        return content
    
    # Procedure to return a parseable BeautifulSoup object of a given url
    def get_soup(self, aurl):
        response = self.get_response(aurl)
        if response:
            soup = BeautifulSoup(response,'html.parser')
        else:
            return None
        return soup
    
    
    def handle_no_swot_data(self, swot, data):
        for type_ in swot.keys():
            data[swot[type_]] = "Data Not Available"
            data["Symbol"] = "Symbol Unavailable"
            return data
    
    
    def get_symbol(self, soup, data):
        symbol_finder = soup.find("p", {"class":"bsns_pcst disin"})
        if not symbol_finder or "NSE:" not in symbol_finder.get_text():
            data["Symbol"] = "Symbol Unavailable"
            return data
        
        print(symbol_finder.get_text().split("NSE:")[1].split()[0].strip().lstrip())
        data["Symbol"] = symbol_finder.get_text().split("NSE:")[1].split()[0].strip().lstrip()
        return data
        
    def get_swot_analysis(self, soup, data):
        swot = {"S":"Strengths", "W": "Weaknesses", "O": "Opportunities",
                "T": "Threat"}
        
        swot_div = soup.find("div", {"class": "swot_feature"})
        if not swot_div:
            data = self.handle_no_swot_data(swot, data)
            return data
        
        link = swot_div.find("a")["href"]
        
        new_soup = self.get_soup(link)
        
        if new_soup == None:
            data = self.handle_no_swot_data(swot, data)
            return data
        
        data = self.get_symbol(new_soup, data)
        swot_points = new_soup.find("section", {"id": "swot_details"}).find("input")["value"]
        
        if not swot_points:
            data = self.handle_no_swot_data(swot, data)
            return data
        
        swot_points = ast.literal_eval(swot_points)
        for type_ in swot.keys():
            try:
                if swot_points[type_]["count"]:
                    data[swot[type_]] = swot_points[type_]["info"]
                else:
                    data[swot[type_]] = "No {} found".format(swot[type_])
            except:
               data[swot[type_]] = "Exception, No {} found".format(swot[type_])
               
        
        data["swot_url"] = link
        return data
        
    def get_technical_analysis(self, soup):
        data = {'Moving Averages': '', 'Technical Indicators': '',
                'Moving Averages Crossovers': ''}
        
        ta = soup.find("div", {"id": "techan_daily"})
        table = ta.find("table", {"class": "mctable1"})
        
        for row in table.find_all("tr"):
            values = row.find_all("td")
            
            if values:
                try:
                    data[values[0].get_text().lstrip().strip()] = values[1].get_text()
                except:
                    pass
                
        return data
    
    def get_valuation(self, soup, data):
        ta = soup.find("div", {"id": "standalone_valuation"})
        lists = ta.find_all("li", {"class": "clearfix"})
        
        for row in lists[:-1]:
            data[row.find("div", {"class":"value_txtfl"}).get_text()] = row.find("div", {"class":"value_txtfr"}).get_text()
        
        return data
    
    def get_community_sentiment(self, soup, data):
        chart = soup.find("ul", {"class": "buy_sellper"})
        if chart:
            lists = chart.find_all("li")
            if lists:
                for row in lists:
                    if "Sentiment" not in data.keys():
                        data["Sentiment"] = row.get_text()
                    else:
                        data["Sentiment"] = data["Sentiment"] + ", " + row.get_text()
            else:
                data["Sentiment"] = "Data Unavailable"
        else:
            data["Sentiment"] = "Data Unavailable"
        return data
    
    def get_analysis(self, url):
        soup= self.get_soup(url)
        
        if soup == None:
            return None
        
        data = self.get_technical_analysis(soup)
        data["symbol_url"] = url
        data = self.get_valuation(soup, data)
        data = self.get_community_sentiment(soup, data)
        data = self.get_swot_analysis(soup, data)
        
        return data
        
    def get_alpha_quotes(self, aurl):
        soup = self.get_soup(aurl)
        allStocksData = {}
        # print(aurl)
        
        list_ = soup.find('table',{'class':'pcq_tbl MT10'})
        
        companies = list_.find_all('a')
        print(len(companies))
        for company in tqdm(companies):
            if company.get_text() != '':
                report = self.get_analysis(company['href'])
                if report:
                    allStocksData[company.get_text()] = report
                    
        return allStocksData
            

if __name__ == '__main__':
    url = 'http://www.moneycontrol.com/india/stockpricequote'
    
    print("Initializing")
    moneycontrol = MoneyControlScrapper()
    allStocksData = moneycontrol.get_alpha_quotes(url)
    
    with open("allData.json", "w") as fp:
        json.dump(allStocksData, fp)
    
    df = pd.DataFrame(allStocksData).transpose()
    
    df.to_excel("overallData_temp.xlsx")
    