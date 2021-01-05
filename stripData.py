try:
  import cv2
  import pytesseract
except Exception as e:
  print('Import error {}'.format(e))

import re
import csv
import json
import os
import glob
import fileNames
import commitChecker

import logging
logging.basicConfig(level=logging.CRITICAL)

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


def createGeoJson(localCsvFile, hospitalData, removePending=False):
    countyData = {}
    data = {}
    date = (localCsvFile.split('.csv')[0].split()[0].split('Summary')[1])
    with open(localCsvFile) as csvFile:
        csvReader = csv.DictReader(csvFile)
        for row in csvReader:
          countyHeader = 'County'
          if 'EventResidentCounty' in row:
            countyHeader = 'EventResidentCounty'
            
          countyData[row[countyHeader]] = {
                'Tested' : row['Individuals Tested'],
                'Positive' : row['Individuals Positive'],
                'Recovered' : row['Total Recovered'],
                'Deaths' : row['Total Deaths'],
            }
          try:
            countyData[row[countyHeader]]['Active'] = int(row['Individuals Positive']) - (int(row['Total Recovered']) + int(row['Total Deaths']))
          except:
            countyData[row[countyHeader]]['Active'] = row['Individuals Positive']

    with open(fileNames.originalGeoJson, 'r') as read_file:
        data = json.load(read_file)

    removeList = []
    for county in data['features']:
        name = county['properties']['Name']

        if name == 'Pending Investigation' and removePending:
          removeList.append(county)
          continue

        if name == 'Obrien':
            name = 'O\'Brien'
        try:
            props = countyData[name]
            county['properties']['Recovered'] = int(props['Recovered'])
            county['properties']['Active'] = int(props['Active'])
            county['properties']['Deaths'] = int(props['Deaths'])
            county['properties']['Confirmed'] = int(props['Positive'])
            county['properties']['Tested'] = int(props['Tested'])
            try:
              county['properties']['Hospitalized'] = int(hospitalData[name])
            except:
              county['properties']['Hospitalized'] = 0
            county['properties']['PercentRecovered'] = round(int(props['Recovered'])/county['properties']['pop_est_2018']*100,2)
            county['properties']['PercentActive'] = round(int(props['Active'])/county['properties']['pop_est_2018']*100,2)
            county['properties']['PercentDeaths'] = round(int(props['Deaths'])/county['properties']['pop_est_2018']*100,2)
            county['properties']['PercentConfirmed'] = round(int(props['Positive'])/county['properties']['pop_est_2018']*100,2)
            county['properties']['PercentTested'] = round(int(props['Tested'])/county['properties']['pop_est_2018']*100,2)
            try:
              county['properties']['PercentHospitalized'] = round(int(hospitalData[name])/county['properties']['pop_est_2018']*100,2)
            except:
              county['properties']['PercentHospitalized'] = 0
        except:
            county['properties']['Active'] = 0
            county['properties']['Tested'] = 0
            county['properties']['Hospitalized'] = 0
            county['properties']['PercentRecovered'] = 0
            county['properties']['PercentActive'] = 0
            county['properties']['PercentDeaths'] = 0
            county['properties']['PercentConfirmed'] = 0
            county['properties']['PercentTested'] = 0
            county['properties']['PercentHospitalized'] = 0

    for county in removeList:
        data['features'].remove(county)

    combinedFile = fileNames.storageGeoJsonFormat.format(date)
    with open(combinedFile, "w") as write_file:
        json.dump(data, write_file)

    with open(fileNames.webGeoJson, "w") as write_file:
        json.dump(data, write_file)
    return combinedFile


def sanitizeText(text):
  textList = text.split('\n')
  realList = []
  for string in textList:
    if string:
      string = string.replace(',', '')
      string = string.replace('=', '')
      string = string.replace(':', '')
      string = string.replace('/', '7')
      string = string.replace('?', '2')
      string = string.replace('“', '')
      string = string.strip()
      if string:
        realList.append(string)
  return realList


def convertVals(vals):
  newVals = []
  for val in vals:
    newVal = val
    if 'K' in val:
      newVal = int(float(val[:-1])*1000)
    newVals.append(newVal)
  return newVals


def writeJson(filePath, data):
  if os.path.exists(filePath):
    os.remove(filePath)
  with open(filePath, 'w') as fp:
    json.dump(data, fp)


def getRMCCData():
  print('RMCC Data')
  data = {}

  try:
    fileName = fileNames.rmccScreenshot
    img = cv2.imread(fileName)
    
    crop_img = img[1160:-30, 150:-100]
    cv2.imwrite('RMCC_crop.png', crop_img)

    try:
      hosp_img = crop_img[0:90, 0:320]
      cv2.imwrite('RMCC_hospital.png', hosp_img)
      text = pytesseract.image_to_string(hosp_img)
      sanitizedText = sanitizeText(text)
      sanitizedText = convertVals(sanitizedText)
      data['Currently Hospitalized'] = sanitizedText[1]
    except Exception as e:
      print('issue reading currently hospitalized value {}'.format(e))
    
    try:
      icu_img = crop_img[0:90, 650:950]
      cv2.imwrite('RMCC_icu.png', icu_img)
      text = pytesseract.image_to_string(icu_img)
      sanitizedText = sanitizeText(text)
      sanitizedText = convertVals(sanitizedText)
      data['In ICU'] = sanitizedText[1]
    except Exception as e:
      print('issue reading icu value {}'.format(e))
  
    try:
      admit_img = crop_img[0:90, 1250:1625]
      cv2.imwrite('RMCC_admit.png', admit_img)
      text = pytesseract.image_to_string(admit_img)
      sanitizedText = sanitizeText(text)
      sanitizedText = convertVals(sanitizedText)
      data['Newly Admitted'] = sanitizedText[1]
    except Exception as e:
      print('issue reading admit value {}'.format(e))
    
    try:
      bed_img = crop_img[800:1200, 50:550]
      cv2.imwrite('RMCC_bed.png', bed_img)
      text = pytesseract.image_to_string(bed_img)
      sanitizedText = sanitizeText(text)
      sanitizedText = convertVals(sanitizedText)
      data['Beds Available'] = sanitizedText[1]
      data['ICU Beds Available'] = sanitizedText[3]
    except Exception as e:
      print('issue reading bed values {}'.format(e))
    
    try:
      vent_img = crop_img[1450:1880, 50:550]
      cv2.imwrite('RMCC_vent.png', vent_img)
      text = pytesseract.image_to_string(vent_img)
      sanitizedText = sanitizeText(text)
      sanitizedText = convertVals(sanitizedText)
      vents = sanitizedText[1]
      if vents == 7715:
        vents = 775
      data['Vents Available'] = vents
      data['On Vent'] = sanitizedText[3]
    except Exception as e:
      print('issue reading vent values {}'.format(e))

  except Exception as e:
    print('issue reading RMCC {}'.format(e))

  print(data)
  return data


def getSummaryData():
  print('Summary Data')
  data = {}
  try:
    fileName = fileNames.summaryScreenshot
    img = cv2.imread(fileName)
    crop_img = img[200:-100, 200:-1400]
    cv2.imwrite('Summary_totals.png', crop_img)
    text = pytesseract.image_to_string(crop_img)
    textList = sanitizeText(text)
    data.update({
      # 'Total Tested' : textList[1].replace(' ', ''),
      # 'Total Cases' : textList[3].replace(' ', ''),
      # 'Total Recovered' : textList[5].replace(' ', ''),
      # 'Total Deaths' : textList[7].replace(' ', ''),
    })
  except Exception as e:
    print('issue reading summary data {}'.format(e))

  print(data)
  return data


def getSerologyData():
  print('Serology Data')
  data = {}
  try:
    fileName = fileNames.serologyScreenshot
    img = cv2.imread(fileName)
    crop_img = img[100:-20, 200:-600]
    cv2.imwrite('Serology_totals.png', crop_img)
    text = pytesseract.image_to_string(crop_img)
    textList = sanitizeText(text)
    vals = convertVals(textList[1].split())

    data.update({
      'Individual Serologic Tests' : vals[0],
      'Individual Serologic Negatives' : vals[1],
      'Individual Serologic Positives' : vals[2],
    })
  except Exception as e:
    print('issue reading serology data {}'.format(e))

  print(data)
  return data


def getPCRData(crop_img):
  print('PCR Test Data')
  data = {}
  pcrImg = crop_img[100:420, 10:-10]
  cv2.imwrite('Cases_pcr.png', pcrImg)

  try:
    totalPCR = crop_img[100:420, 10:500]
    cv2.imwrite('Cases_total_pcr.png', totalPCR)
    text = pytesseract.image_to_string(totalPCR)
    sanitizedText = sanitizeText(text)
    pcrText = []
    for text in sanitizedText:
      newText = text.replace(' ', '')
      if newText.isnumeric():
        pcrText.append(newText)
    pcrText = convertVals(pcrText)
    data['Total PCR Tests'] = pcrText[0]
    data['Individual PCR Tests'] = pcrText[1]
  except Exception as e:
    print('issue reading total pcr values {}'.format(e))

  try:
    negativePCR = crop_img[100:420, 600:1100]
    cv2.imwrite('Cases_negative_pcr.png', negativePCR)
    text = pytesseract.image_to_string(negativePCR)
    sanitizedText = sanitizeText(text)
    pcrText = []
    for text in sanitizedText:
      newText = text.replace(' ', '')
      if newText.isnumeric():
        pcrText.append(newText)
    pcrText = convertVals(pcrText)
    data['Total PCR Negatives'] = pcrText[0]
    data['Individual PCR Negatives'] = pcrText[1]
  except Exception as e:
    print('issue reading negative pcr values {}'.format(e))

  try:
    positivePCR = crop_img[100:420, 1200:1700]
    cv2.imwrite('Cases_positive_pcr.png', positivePCR)
    text = pytesseract.image_to_string(positivePCR)
    sanitizedText = sanitizeText(text)
    pcrText = []
    for text in sanitizedText:
      newText = text.replace(' ', '')
      if newText.isnumeric():
        pcrText.append(newText)
    pcrText = convertVals(pcrText)
    data['Total PCR Positives'] = pcrText[0]
    data['Individual PCR Positives'] = pcrText[1]
  except Exception as e:
    print('issue reading positive pcr values {}'.format(e))

  print(data)
  return data


def getAntigenData(crop_img):
  print('Antigen Test Data')
  data = {}
  antigenImg = crop_img[550:900, 10:-10]
  cv2.imwrite('Cases_antigen.png', antigenImg)

  try:
    text = pytesseract.image_to_string(antigenImg)
    totalAntigen = crop_img[550:900, 10:500]
    text = pytesseract.image_to_string(totalAntigen)
    sanitizedText = sanitizeText(text)
    antigenText = []
    for text in sanitizedText:
      newText = text.replace(' ', '')
      if newText.isnumeric():
        antigenText.append(newText)
    antigenText = convertVals(antigenText)
    data['Total Antigen Tests'] = antigenText[0]
    data['Individual Antigen Tests'] = antigenText[1]
  except Exception as e:
    print('issue reading total antigen values {}'.format(e))

  try:
    negativeAntigen = crop_img[550:900, 600:1100]
    text = pytesseract.image_to_string(negativeAntigen)
    sanitizedText = sanitizeText(text)
    antigenText = []
    for text in sanitizedText:
      newText = text.replace(' ', '')
      if newText.isnumeric():
        antigenText.append(newText)
    antigenText = convertVals(antigenText)
    data['Total Antigen Negatives'] = antigenText[0]
    data['Individual Antigen Negatives'] = antigenText[1]
  except Exception as e:
    print('issue reading negative antigen values {}'.format(e))

  try:
    positiveAntigen = crop_img[550:900, 1200:1700]
    text = pytesseract.image_to_string(positiveAntigen)
    sanitizedText = sanitizeText(text)
    antigenText = []
    for text in sanitizedText:
      newText = text.replace(' ', '')
      if newText.isnumeric():
        antigenText.append(newText)
    antigenText = convertVals(antigenText)
    data['Total Antigen Positives'] = antigenText[0]
    data['Individual Antigen Positives'] = antigenText[1]
  except Exception as e:
    print('issue reading positive antigen values {}'.format(e))

  print(data)
  return data


def getTestTotalsData(crop_img):
  print('Total Test Data')
  data = {}

  try:
    totalsImg = crop_img[1000:1150, 10:-500]
    cv2.imwrite('Cases_totals.png', totalsImg)
    text = pytesseract.image_to_string(totalsImg)
    sanitizedText = sanitizeText(text)[1].split()
    sanitizedText = convertVals(sanitizedText)
    data.update({
      'Total Tests' : sanitizedText[0],
      'Total Negative' : sanitizedText[1],
      'Total Positive' : sanitizedText[2],
    })
  except Exception as e:
    print('issue reading total test values {}'.format(e))

  try:
    individualsImg = crop_img[1450:1600, 10:-500]
    cv2.imwrite('Cases_individuals.png', individualsImg)
    text = pytesseract.image_to_string(individualsImg)
    sanitizedText = sanitizeText(text)[1].split()
    sanitizedText = convertVals(sanitizedText)
    data.update({
      'Total Individual Tests' : sanitizedText[0],
      'Total Individuals Negative' : sanitizedText[1],
      'Total Individuals Positive' : sanitizedText[2],
    })
  except Exception as e:
    print('issue reading individual test values {}'.format(e))

  print(data)
  return data


def getCaseData():
  print('Case Data')
  data = {}
  fileName = fileNames.caseScreenshot
  img = cv2.imread(fileName)
  crop_img = img[100:-80, 100:-100]
  cv2.imwrite('Cases_crop.png', crop_img)

  data.update(getPCRData(crop_img))
  data.update(getAntigenData(crop_img))
  data.update(getTestTotalsData(crop_img))

  try:
    breakDownImg = crop_img[-200:-10, 10:-10]
    cv2.imwrite('Cases_breakdown.png', breakDownImg)
    text = pytesseract.image_to_string(breakDownImg)
    sanitizedText = sanitizeText(text)[1].split()
    sanitizedText = convertVals(sanitizedText)
    data.update({
      'Cases With Preexisting Condition' : sanitizedText[0],
      'Cases With No Preexisting Condition' : sanitizedText[1],
      'Cases Preexisting Condition Unknown' : sanitizedText[2],
    })
  except Exception as e:
    print('issue reading case breakdown data {}'.format(e))

  print(data)
  return data


def getDeathData():
  print('Death Data')
  data = {}
  fileName = fileNames.deathsScreenshot
  img = cv2.imread(fileName)

  try:
    crop_img = img[100:200, 100:-100]
    cv2.imwrite('Deaths_total.png', crop_img)
    text = pytesseract.image_to_string(crop_img)
    textList = sanitizeText(text)
    vals = convertVals(textList[1].split())
    data['Total Deaths'] = vals[0]
    data['Underlying Cause Deaths'] = vals[1]
    data['Contributing Factor Deaths'] = vals[2]
  except Exception as e:
    print('issue reading total deaths {}'.format(e))

  try:
    crop_img = img[-150:-10, 100:-100]
    cv2.imwrite('Deaths_breakdown.png', crop_img)
    text = pytesseract.image_to_string(crop_img)
    textList = sanitizeText(text)
    vals = convertVals(textList[1].split())

    data.update({
      'Deaths With Preexisting Condition' : vals[0],
      'Deaths With No Preexisting Condition' : vals[1],
      'Deaths Preexisting Condition Unknown' : '0'
    })
  except Exception as e:
    print('issue reading death breakdown {}'.format(e))

  print(data)
  return data


def getRecoveryData():
  print('Reovery Data')
  data = {}
  fileName = fileNames.recoveryScreenshot
  img = cv2.imread(fileName)

  try:
    crop_img = img[100:200, 100:500]
    cv2.imwrite('Recovery_total.png', crop_img)
    text = pytesseract.image_to_string(crop_img)
    textList = sanitizeText(text)
    vals = convertVals(textList[0].split())
    data['Total Recovered'] = vals[1]
  except Exception as e:
    print('issue reading total recovered {}'.format(e))

  try:
    crop_img = img[2000:-200, 100:-100]
    cv2.imwrite('Recovery_breakdown.png', crop_img)
    text = pytesseract.image_to_string(crop_img)
    textList = sanitizeText(text)

    vals = convertVals(textList[1].split())

    data.update({
      'Recovered With Preexisting Condition' : vals[0],
      'Recovered With No Preexisting Condition' : vals[1],
      'Recovered Preexisting Condition Unknown' : vals[2],
    })
  except Exception as e:
    print('issue reading recovery breakdown {}'.format(e))

  print(data)
  return data


def getLTCData():
  print('LTC Data')
  data = {}

  try:
    fileName = fileNames.ltcScreenshot
    img = cv2.imread(fileName)
    crop_img = img[150:-20, 100:-100]
    cv2.imwrite('LTC_totals.png', crop_img)
    text = pytesseract.image_to_string(crop_img)
    textList = sanitizeText(text)

    vals = convertVals(textList[1].split())

    data = {
      'Current LTC Outbreaks' : vals[0],
      'LTC Positives' : vals[1],
      'LTC Recovered' : vals[2],
      'LTC Deaths' : vals[3],
    }
  except Exception as e:
    print('issue reading LTC data {}'.format(e))

  print(data)
  return data


def loadAllData():
  data = {}
  local = True

  # data.update(getSummaryData())
  data.update(getSerologyData())
  data.update(getCaseData())
  data.update(getRMCCData())

  data.update(getDeathData())
  data.update(getRecoveryData())
  data.update(getLTCData())

  return data


def readHospitalData():
  list_of_pdfs = glob.glob(os.path.join(fileNames.storageDir, '*.pdf'))
  list_of_pdfs.sort()
  pdfFile = list_of_pdfs[-1]

  hospitalData = None
  hospitalData = readPDF(pdfFile)
  print(hospitalData)
    
  return hospitalData


if __name__ == "__main__":

  if commitChecker.stillNeedTodaysData():
    data = loadAllData()
    writeJson(fileNames.dailyJson, data)

    hospitalData = readHospitalData()

    list_of_files = glob.glob(os.path.join(fileNames.storageDir, '*.csv'))
    list_of_files.sort()
    csvFile = list_of_files[-1]

    createGeoJson(csvFile, hospitalData)

    print(data)
