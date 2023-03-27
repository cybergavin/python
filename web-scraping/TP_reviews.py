# @cybergavin - https://github.com/cybergavin
# This program scrapes Trustpilot reviews for a given business domain name and optionally a given number of pages (how many pages of reviews to extract)
# NOTE: This program is for educational purposes. Some website owners may have terms that make it illegal to scrape their websites. You are responsible for your use of this program.
#
################################################################################################################################################################
from bs4 import BeautifulSoup
import sys
import requests
import pandas as pd
import json

# Usage
if len(sys.argv) != 2 and len(sys.argv) != 3:
    print(f"\nMissing input argument!\nUSAGE: python3 {sys.argv[0]} <business domain> [number of review pages]\nExamples: python3 {sys.argv[0]} amazon.com\tOR\tpython3 {sys.argv[0]} amazon.com 5\n")
    exit()

# Initialize lists
body = []
business_domain = sys.argv[1]
output = f'{business_domain}.csv'

# Set Trustpilot page numbers to scrape here
from_page = 1
if len(sys.argv) == 3 and int(sys.argv[2]) > 1:
    num_pages = int(sys.argv[2])
    to_page = num_pages + 1
else:
    num_pages = 1

# Function to scrape TrustPilot reviews
def scrape_trustpilot(url):
    response = requests.get(url)
    web_page = response.text
    soup = BeautifulSoup(web_page, "html.parser")
    reviews_raw = soup.find("script", id = "__NEXT_DATA__").string
    reviews_raw = json.loads(reviews_raw)
    rev = reviews_raw["props"]["pageProps"]["reviews"]
    for i in range(len(rev)):
        instance = rev[i]
        body_ = instance["text"].replace("\n"," ")
        body.append(body_)

# Scrape the most recent reviews first
scrape_trustpilot(f"https://www.trustpilot.com/review/{sys.argv[1]}?sort=recency")

# Then scrape the desired number of pages
if num_pages > 1:
    for i in range(from_page, to_page + 1):
        scrape_trustpilot(f"https://www.trustpilot.com/review/{sys.argv[1]}?sort=recency&page={i}")

# Use pandas to write to write to csv
df = {'Body' : body }
rev_df = pd.DataFrame(df)
rev_df.drop_duplicates(subset=['Body'], keep='first', inplace=True)
rev_df.to_csv(output,index=False,header=False)
