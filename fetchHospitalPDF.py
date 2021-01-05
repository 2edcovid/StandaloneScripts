import requests
import time
import fileNames
import csv
import json

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

    for stringData in viewer.canvas.strings:
      if not stringData.isnumeric():
        compiled = compiled + stringData
      else:
        countyHospitalData[compiled] = stringData
        if compiled == 'Wright':
          break
        compiled = ""
  except Exception as e:
    print('no hospital data {}'.format(e))

  return countyHospitalData


def writeJson(filePath, data):
  if os.path.exists(filePath):
    os.remove(filePath)
  with open(filePath, 'w') as fp:
    json.dump(data, fp)


if __name__ == "__main__":
  timeString = time.strftime("%Y-%m-%d %H%M")
  hospitalPDFData = readPDF(getHospitalData(timeString))
  writeJson('hospitalData-{}.csv'.format(timeString), hospitalPDFData)