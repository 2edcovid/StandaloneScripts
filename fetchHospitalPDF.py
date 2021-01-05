import requests
import time
import fileNames
import csv
import json
import re

from seleniumUtils import *
import urls

import logging
logging.basicConfig(level=logging.CRITICAL)


def getHospitalData(timeString):
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

    
    localFilePath = fileNames.countyHospitalFormat.format(timeString)
    if saveDownloadFile(browser, localFilePath):
      filePath = localFilePath
    closeBrowser(browser)

    return filePath


def readPDF(pdfFile):
  countyHospitalData = {}

  try:
    from pdfreader import PDFDocument, SimplePDFViewer
    fd = open(pdfFile, "rb")
    doc = PDFDocument(fd)
    all_pages = [p for p in doc.pages()]
    page_count = len(all_pages)
    viewer = SimplePDFViewer(fd)
    viewer.render()
  
    compiled = ""
 
    for i in range(page_count):
      pageText = "".join(viewer.canvas.strings)
      if 'Kossuth' not in pageText:
        try:
          viewer.next()
          viewer.render()
        except:
          print('end of doc and no county data')
      else:
        print('found county data')
        break

    leftoverStrings = []
    readingCountyData = True
    for stringData in viewer.canvas.strings:
      if readingCountyData:
        if not stringData.isnumeric():
          compiled = compiled + stringData
        else:
          countyHospitalData[compiled] = stringData
          if compiled == 'Wright':
            readingCountyData = False
          compiled = ""
      else:
        leftoverStrings.append(stringData)

    parsedLeftOvers = ''
    leftoverVals = []
    for string in leftoverStrings:
      if not string.isnumeric():
        parsedLeftOvers = parsedLeftOvers + string
      elif string == '19' and parsedLeftOvers.lower().endswith('covid-'):
        parsedLeftOvers = parsedLeftOvers + string
      elif parsedLeftOvers.endswith('/'):
        parsedLeftOvers = parsedLeftOvers + string
      else:
        leftoverVals.append(string)

    parsedLeftOvers = parsedLeftOvers.lower()
    parsedLeftOvers = parsedLeftOvers.replace('covid-19', '')
    parsedLeftOvers = parsedLeftOvers.replace('county', '')
    parsedLeftOvers = parsedLeftOvers.replace('patients', '')
    parsedLeftOvers = parsedLeftOvers.replace('confirmed', '')

    dateRegex = r'.+(\d+\/\d+\/\d+)'
    matches = re.match(dateRegex, parsedLeftOvers)

    date = "couldn't read date"
    if matches:
      date = matches.group(1)

    countyHospitalData['Out Of State'] = leftoverVals[0]
    countyHospitalData['Total Iowans'] = leftoverVals[1]
    countyHospitalData['Total Hospitalized'] = leftoverVals[2]
    countyHospitalData['Date'] = date

  except Exception as e:
    print('no hospital data {}'.format(e))

  return countyHospitalData

def writeHospitalCSV(filePath, data):
  csvHeaders = ["County", "Hospitalized"]
  rows = []
  
  for key in data:
    rows.append( {"County" : key,
                  "Hospitalized" : data[key]}
              )

  with open(filePath, 'w',encoding='utf-8',newline='',) as f:
    writer = csv.DictWriter(f, csvHeaders)
    writer.writeheader()
    writer.writerows(rows)

def writeJson(filePath, data):
  if os.path.exists(filePath):
    os.remove(filePath)
  with open(filePath, 'w') as fp:
    json.dump(data, fp)


if __name__ == "__main__":
  timeString = time.strftime("%Y-%m-%d %H%M")
  pdfFile = getHospitalData(timeString)
  hospitalPDFData = readPDF(pdfFile)
  # writeJson('hospitalData-{}.csv'.format(timeString), hospitalPDFData)
  writeHospitalCSV('hospitalData-{}.csv'.format(timeString), hospitalPDFData)