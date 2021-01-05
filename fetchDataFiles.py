import time
import os
from seleniumUtils import *
import requests
import fileNames
import urls
import commitChecker


def getHospitalData():
    filePath = None

    browser = getBrowser(urls.mainPage, height=1700, zoom=90)
    time.sleep(20)
    link = browser.find_element_by_link_text('Iowa Hospitalizations by County')
    html = link.get_attribute('outerHTML')
    htmlList = html.split('"')
    linkURL = htmlList[1]
    print(linkURL)

    if 'drive.google' in linkURL:
      linkURL = linkURL.replace('https://drive.google.com/file/d/', '')
      fileID = linkURL.replace('/view?usp=sharing', '')

      linkURL = 'https://drive.google.com/uc?export=download&id={}'.format(fileID)
    
    browser.get(linkURL)
    time.sleep(40)

    timeString = time.strftime("%Y-%m-%d %H%M")
    localFilePath = fileNames.countyHospitalFormat.format(timeString)
    if saveDownloadFile(browser, fileNames.storageDir, localFilePath):
      filePath = localFilePath
    closeBrowser(browser)

    return filePath


def getSummary():
    try:
      print('loading Summary Page')
      browser = getBrowser(urls.summaryPage, height=2400, zoom=90)
      time.sleep(40)
      saveScreenshot(browser, fileNames.summaryScreenshot) 
 
      elements = browser.find_elements_by_class_name('cd-control-menu_container_2gtJe') 
      button = elements[-2].find_element_by_css_selector("button[class='db-button small button cd-control-menu_option_wH8G6 cd-control-menu_expand_VcWkC cd-control-menu_button_2VfJA cd-control-menu_db-button_2UMcr ng-scope']") 
      print('Clicking Download Button') 
      browser.execute_script("$(arguments[0].click());", button) 
      time.sleep(20) 
 
      timeString = time.strftime("%Y-%m-%d %H%M") 
      localPath = fileNames.storageSummaryFormat.format(timeString) 
      saveDownloadFile(browser, fileNames.storageDir, localPath) 
 
      closeBrowser(browser)
    except Exception as e:
      print('issue getting summary data {}'.format(e))


def getCSVs():
    print('attempting csv download')
    timeString = time.strftime("%Y-%m-%d %H%M")

    filenameLists = [
      os.path.join(fileNames.storageDir,'IndividualsTested{}.csv'.format(timeString)),
      os.path.join(fileNames.storageDir,'IndividualsTestedGraph{}.csv'.format(timeString)),
      os.path.join(fileNames.storageDir,'IndividualsPositive{}.csv'.format(timeString)),
      os.path.join(fileNames.storageDir,'IndividualsPositiveGraph{}.csv'.format(timeString)),
      os.path.join(fileNames.storageDir,'TotalRecovered{}.csv'.format(timeString)),
      os.path.join(fileNames.storageDir,'TotalRecoveredGraph{}.csv'.format(timeString)),
      os.path.join(fileNames.storageDir,'TotalDeaths{}.csv'.format(timeString)),
      os.path.join(fileNames.storageDir,'TotalDeathsGraph{}.csv'.format(timeString)),
      os.path.join(fileNames.storageDir,'UnderlyingCauseDeaths{}.csv'.format(timeString)),
      os.path.join(fileNames.storageDir,'UnderlyingCauseDeathsGraph{}.csv'.format(timeString)),
      os.path.join(fileNames.storageDir,'ContributingFactorsDeaths{}.csv'.format(timeString)),
      os.path.join(fileNames.storageDir,'ContributingFactorsDeathsGraph{}.csv'.format(timeString)),
    ]

    for i in range(12):
      browser = getBrowser(urls.summaryPage)
      time.sleep(20)
      buttons = browser.find_elements_by_css_selector('button[aria-label="Export data"]')
      browser.execute_script("$(arguments[0].click());", buttons[i])
      time.sleep(10)

      localPath = filenameLists[i]
      saveDownloadFile(browser, fileNames.storageDir, localPath)

    closeBrowser(browser)


def getAccessVals():
  browser = getBrowser(urls.accessPage)
  
  titles = browser.find_elements_by_class_name('ss-title')
  elements = browser.find_elements_by_class_name('ss-value')

  vals = {}
  for i in range(len(titles)):
    vals[titles[i].get_attribute('innerHTML')] = elements[i].get_attribute('innerHTML')
  closeBrowser(browser)
  return vals


def getGeoJSON():
  r = requests.get(urls.dailyGeoJson, stream=True)
  if r.status_code == 200:
    filePath = fileNames.originalGeoJson
    if os.path.exists(filePath):
      os.remove(filePath)
    open(filePath, 'wb').write(r.content)
  return filePath


def getOriginalMap():
  browser = getBrowser(urls.argisMap)
  saveScreenshot(browser, fileNames.mapScreenshot)
  closeBrowser(browser)


def getCases():
  browser = getBrowser(urls.casePage, height=6200, zoom=90)
  time.sleep(40)
  saveScreenshot(browser, fileNames.caseScreenshot)
  closeBrowser(browser)


def getRecovery():
  browser = getBrowser(urls.recoveredPage, height=2500)
  time.sleep(40)
  saveScreenshot(browser, fileNames.recoveryScreenshot)
  closeBrowser(browser)


def getDeaths():
  browser = getBrowser(urls.deathsPage, height=2500)
  time.sleep(40)
  saveScreenshot(browser, fileNames.deathsScreenshot)
  closeBrowser(browser)


def getLTC():
  browser = getBrowser(urls.ltcPage, height=400)
  time.sleep(40)
  saveScreenshot(browser, fileNames.ltcScreenshot)
  closeBrowser(browser)


def getRMCCData():
  browser = getBrowser(urls.rmccPage, height=3300)
  time.sleep(40)
  saveScreenshot(browser, fileNames.rmccScreenshot)
  closeBrowser(browser)


def getSerologyData():
  browser = getBrowser(urls.serologyPage, zoom=80, height=400)
  time.sleep(40)
  saveScreenshot(browser, fileNames.serologyScreenshot)
  closeBrowser(browser)



if __name__ == "__main__":
  getOriginalMap()
  getGeoJSON()
  print(getAccessVals())

  getCSVs()
  getHospitalData()
  getSummary()
  getCases()
  getRecovery()
  getDeaths()
  getLTC()
  getRMCCData()
  getSerologyData()
    
