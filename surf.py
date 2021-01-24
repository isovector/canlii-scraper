from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import random

options = Options()

driver = webdriver.Firefox(firefox_options=options, executable_path='geckodriver')
driver.get('https://canlii.org')

def find_same_domain(els):
    matching = []
    for el in els:
        href = el.get_attribute("href")
        if href is not None and href.startswith('https://www.canlii.org/en/ca') and '#' not in href and '.pdf' not in href:
            matching.append(el)
    return random.choice(matching)

while True:
    time.sleep(random.uniform(2, 20))
    try:
        aels = driver.find_elements_by_css_selector('a')
        find_same_domain(aels).click()
    except:
        print "oops"
        pass





