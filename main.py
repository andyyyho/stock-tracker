import httpx
import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

def parseDateToUnixTimeStamp(trade):
    month_to_numeric = {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sept': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12,
    }
    date_items = trade['published_trade_date'].split(' ')
    date = datetime.datetime(int(date_items[0]), month_to_numeric[date_items[2]], int(date_items[1]))
    unix_timestamp = time.mktime(date.timetuple())
    print(date)
    return unix_timestamp

def getTrade(row):
    trade = {}
    a_tags = row.find_all("a")
    # Only a valid trade if there are two a tags
    if len(a_tags) <= 1:
        return

    trade["name"] = a_tags[1].text
    trade["ticker"] = row.find("span", class_="q-field issuer-ticker").text

    # first value is the published, second is actual trade date
    year = row.findAll("div", class_="q-label")
    # first value is published, second is actual trade date, third is days reported after trade, fourth is size
    cell_value = row.findAll("div", class_="q-value")
    
    trade["published_trade_date"] = year[0].text
    trade["published_trade_date"] += cell_value[0].text
    trade["actual_trade_date"] = year[1].text
    trade["actual_trade_date"] += cell_value[1].text
    trade["days_reported_after"] = cell_value[2].text

    trade["type"] = row.find("span", class_="tx-type").text
    try:
        trade["amount"] = cell_value[4].text
    except:
        trade["amount"] = "N/A"
        no_listed_price = row.find("span", class_="no-price")
    if not no_listed_price:
        price = row.find("span", "q-field trade-price").text
        trade["price"] = price
    else:
        trade["price"] = "N/A"
        
    return trade

def get_stock_price(symbol, unix_timestamp, open):
    
    # Scrape this data from the yahoo finance site 
    # TODO: Fix this time interval to get the correct stock price
    url = f"https://finance.yahoo.com/quote/{symbol}/history?period1={int(unix_timestamp-86400)}&period2={int(unix_timestamp)}&interval=1d&filter=history&frequency=1d&includeAdjustedClose=true"
    print(url)
    response = httpx.get(url)
    # TODO: Need to use webdriver here, have to press "Apply for time filter to be applied"
    # TODO: Determine if we look at the open stock price or the close
    # if open:
    pass

# Setup client and make request
url = "https://www.capitoltrades.com/trades?politician=P000197"
driver = webdriver.Chrome()
driver.get(url)

# Wait for client-side filtering
time.sleep(2)

# Reject All Cookies
element = driver.find_element(By.XPATH, "//*[text()='Reject All']")
element.click()

soup = BeautifulSoup(driver.page_source, "html.parser")

# Collect data from all pages
data_available = True
trades = []
while data_available:
    soup = BeautifulSoup(driver.page_source, "html.parser")
    # Store trades in an array
    trade_rows = soup.find_all("tr")
    for row in trade_rows:
        trade = getTrade(row)
        if trade is None:
            continue
        trades.append(trade)

    nextLink = driver.find_element(By.CLASS_NAME, "next")
    data_available = nextLink.is_enabled()
    if data_available:
        driver.execute_script("arguments[0].scrollIntoView();", nextLink)
        try:
            nextLink.click()
        except:
            popup = driver.find_element(By.CLASS_NAME, "close-icon")
            popup.click()
            nextLink.click()
        time.sleep(2)

# Print all trades stored
for trade in trades:
    print(trade)

# TODO: REMOVE BELOW
# Testing get_stock_price 
unix_timestamp = parseDateToUnixTimeStamp(trades[0])
get_stock_price(trades[0]['ticker'].split(':')[0], unix_timestamp, False)