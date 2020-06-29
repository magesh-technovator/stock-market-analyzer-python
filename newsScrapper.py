#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 07:36:47 2020

@author: MAGESHWARAN
"""

import requests
import bs4
import pytz
from tqdm import tqdm

SEARCH_URL = "http://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data=&cid=&mbsearch_str=&topsearch_type=1&search_str="
PREFIX_URL = "http://www.moneycontrol.com"


class MoneyControlNews(object):

    def __init__(self, ticker):
        
        # Declaring all the instance variable for the class
        self.ticker = ticker
        self.a = []     # Stores the announcements listed on the given page
        self.more_anno_link = ""    # Link of the announcement page for the company
        self.more_news_link = ""    # Link of news page for the company
        self.anno_page = "https://www.moneycontrol.com/stocks/company_info/stock_notices.php?sc_did="
        self.template_next_a_page = ""     # For storing the link of the next page of the announcement
        self.a_page_links = []    # Stores the list of links all the announcement pages.
        self.link = ""      # Link to the front page of the company we are looking for on moneycontrol
        self.present_a_page = 0

        self.fetch_ticker()
        self.__fetch_a_next_page_link()


    def fetch_ticker(self):
        try:
            self.link = SEARCH_URL+self.ticker
            r = requests.get(self.link)
            if r.status_code==200:
                print("Fetched page for ticker : "+self.ticker)
                # Creating a bs4 object to store the contents of the requested page
                self.soup = bs4.BeautifulSoup(r.content, 'html.parser')
                try:
                    self.more_anno_link = str(self.soup.find("div", attrs={"class":"clearfix viewmore brdtp"}).find("a", {"title": "View More"})["href"]) # class name extracted after looking at the document
                except:
                    self.more_anno_link = str(self.soup.find("div", attrs={"class":"col_right"}).find("a", {"title": "View More"})["href"]) # class name extracted after looking at the document
                    
                # self.more_news_link = str(self.soup.find("div", attrs={"class":"col_right"}).find("a", {"title": "View More"})["href"]) # class name extracted after looking at the document
                self.anno_page = self.anno_page + self.more_anno_link.split("/")[-1]
                
            elif r.status_code==404:
                print("Page not found")
            else:
                print("A different status code received : "+str(r.status_code))

        except requests.ConnectionError as ce:
            print("There is a network problem (DNS Failure, refused connectionn etc.). Error : "+str(ce))
            raise Exception
        
        except requests.Timeout as te:
            print("Request timed out. Error : "+str(te))
            raise Exception
        
        except requests.TooManyRedirects as tmre:
            print("The request exceeded the maximum no. of redirections. Error : "+str(tmre))
            raise Exception
        
        except requests.exceptions.RequestException as oe:
            print("Any type of request related error : "+str(oe))
            raise Exception
        
        except Exception as e:
            print(e)

    def __fetch_a_next_page_link(self):
        print(self.anno_page)
        # self.template_next_a_page = self.more_anno_link
        # Fetches the template URL for fetching different announcement pages
        r = requests.get(self.anno_page)
        
        announcement_soup = bs4.BeautifulSoup(r.content, 'html.parser')
        # print(announcement_soup)
        # print(announcement_soup.find("div", attrs={"class":"brd_top MT20 MB20"}).find_all("a"))
        # Checking whether the link for the next page is available or not
        if len(announcement_soup.find("div", attrs={"class":"brd_top MT20 MB20"}).find_all("a")) > 0:
            # a = announcement_soup.find("div", attrs={"class":"brd_top MT20 MB20"}).find_all("a")[2]["href"]
            self.template_next_a_page = self.anno_page + "&pno="

    def fetch_a(self, page_no=""):

        # Clear all the previous data in "a" instance variable
        self.a = []

        r = requests.get(self.template_next_a_page + str(page_no))

        if page_no:
            self.present_a_page = page_no

        announcement_soup = bs4.BeautifulSoup(r.content, 'html.parser')
        announcement_soup = announcement_soup.find("ul", attrs={"class":"announe_list MT20"})
        # print(announcement_soup)
        
        raw_links = announcement_soup.find_all("a")
        
        # List of links of all the announcements on the given page
        list_of_links = []
        for x in tqdm(raw_links):
            
            if ".pdf" not in x["href"] and "autono" in x["href"]:
                link = x['href']
                list_of_links.append(link)
                try:
                    a = requests.get(x['href'])
                    anno_page = bs4.BeautifulSoup(a.content, "html.parser")
    
                    title = ""
                    content = ""
    
                    date = next(anno_page.find("p", attrs={"class":"gL_10"}).children)
                    date = self.format_date(date)
    
                    
                    # Checking whether the title of the announcement is available or not
                    if anno_page.find("span", attrs={"class":"bl_15"}):
                        title = anno_page.find("span", attrs={"class":"bl_15"}).text
    
                    # Checking whether content is available or not
                    if anno_page.find("p", attrs={"class":"PT10 b_12"}):
                        content = anno_page.find("p", attrs={"class":"PT10 b_12"}).text
                     
                    anno = {"link":link, "content":content, "title":title, "date":date}
                    self.a.append(anno)
                except:
                    pass
        
        return self.a

    def format_date(self,datetime):
        datetime = datetime.split(" ")
        
        date = datetime[0].split("-")
        time = datetime[1]

        date[0] = date[0][:-2]
        month = {
            'Jan':'01',
            'Feb':'02',
            'Mar':'03',
            'Apr':'04',
            'May':'05',
            'Jun':'06',
            'Jul':'07',
            'Aug':'08',
            'Sep':'09',
            'Oct':'10',
            'Nov':'11',
            'Dec':'12'
        }
        date[1] = month[date[1]]
        date.reverse()
        date = '-'.join(date)
        final = date+" "+time
        return final


if __name__ == "__main__":
    allNews = {}
    
    import pandas as pd
    df = pd.read_excel("overallData_latest.xlsx")
    
    symbols = df["Symbol"]
    for symbol in tqdm(symbols):
        try:
            scrappe = MoneyControlNews(symbol)
            
            allNews[symbol] = scrappe.fetch_a()
        except Exception as e:
            print(str(e))
            allNews[symbol] = str(e)

    news_df = pd.DataFrame(allNews)
    
    news_df.to_excel("overallNews.xlsx")
    