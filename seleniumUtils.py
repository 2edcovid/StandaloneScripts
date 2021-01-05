import os
import time
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import base64


def saveDownloadFile(browser, localPath):
  retval = False

  fileName = getDownloadedFileName(browser)

  if fileName: 
    content = getFileContents(browser, fileName)

    with open(localPath, 'wb') as f:
      f.write(content)

  if os.path.exists(localPath):
    print("Downloaded {}".format(localPath))
    retval = True

  return retval
    

def saveScreenshot(browser, fileName):
  if os.path.exists(fileName):
    os.remove(fileName)
  browser.save_screenshot(fileName)
  if os.path.exists(fileName):
    print('{} captured'.format(fileName))


def getFileContents(browser, path):

  elem = browser.execute_script( \
    "var input = window.document.createElement('INPUT'); "
    "input.setAttribute('type', 'file'); "
    "input.hidden = true; "
    "input.onchange = function (e) { e.stopPropagation() }; "
    "return window.document.documentElement.appendChild(input); " )

  elem._execute('sendKeysToElement', {'value': [ path ], 'text': path})

  result = browser.execute_async_script( \
    "var input = arguments[0], callback = arguments[1]; "
    "var reader = new FileReader(); "
    "reader.onload = function (ev) { callback(reader.result) }; "
    "reader.onerror = function (ex) { callback(ex.message) }; "
    "reader.readAsDataURL(input.files[0]); "
    "input.remove(); "
    , elem)

  if not result.startswith('data:') :
    raise Exception("Failed to get file content: %s" % result)

  return base64.b64decode(result[result.find('base64,') + 7:])


def getDownloadedFileName(browser):
  fileName = None
  browser.get("chrome://downloads/")
  files = browser.execute_script( \
    "return  document.querySelector('downloads-manager')  "
    " .shadowRoot.querySelector('#downloadsList')         "
    " .items.filter(e => e.state === 'COMPLETE')          "
    " .map(e => e.filePath || e.file_path || e.fileUrl || e.file_url); ")
  if len(files) >= 1:
    fileName = files[0]
  return fileName


def getBrowser(url, local=False, height=1062, width=1914, zoom=0):
  if local:
      browser = webdriver.Chrome()
  else:
      options = webdriver.ChromeOptions()
      options.add_argument('--no-sandbox')
      options.add_argument('--disable-dev-shm-usage')
      options.add_experimental_option('prefs', {
        "download.prompt_for_download": False, #To auto download the file
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
        })

      browser = webdriver.Remote("http://selenium:4444/wd/hub", desired_capabilities=options.to_capabilities())

  browser.set_window_position(0, 0)
  browser.set_window_size(width, height)
  time.sleep(10)
  try:
    browser.get(url)
  except TimeoutException as e:
    print('timeout retry')
    browser.get(url)
  time.sleep(20)

  if zoom:
    browser.execute_script("document.body.style.zoom='{}%'".format(zoom))
    time.sleep(10)
  return browser


def closeBrowser(browser):
  browser.close()
  browser.quit()
