#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 10:38:59 2020

@author: MAGESHWARAN
"""

from companyDataScrapper import MoneyControlScrapper
from newsScrapper import MoneyControlNews
from tqdm import tqdm
import pandas as pd


df = pd.read_csv("symlinks.csv")

symbols = df["Symbol"]
urls = df["symbol_url"]

moneycontrol = MoneyControlScrapper()
allCompanyData = {}
allCompanyNews = {}

for symbol, url in tqdm(zip(symbols, urls)):
    
    temp = moneycontrol.get_analysis(url)
    if temp:
        allCompanyData[symbol] = temp
    
    try:
        scrappe = MoneyControlNews(symbol)
        allCompanyNews[symbol] = scrappe.fetch_a()
    
    except Exception as e:
        print(str(e))
        allCompanyNews[symbol] = str(e)

df = pd.DataFrame(allCompanyData).transpose()

df.to_excel("selectiveStocksData.xlsx")

news_df = pd.DataFrame(allCompanyNews)
news_df.to_excel("selectiveStocksNews.xlsx")