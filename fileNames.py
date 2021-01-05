import os

storageDir = '.'
redditCommentDir = 'RedditComments'

mapScreenshot = "Screenshot_ArgisMap.png"

originalGeoJson = 'IA_COVID19_Cases.geojson'
webGeoJson = 'data_file.geojson'

storageGeoJsonFormat = os.path.join(storageDir, "data_file_{}.geojson")
storageSummaryFormat = os.path.join(storageDir, 'Summary{}.csv')
countyHospitalFormat = 'countyHospital{}.pdf'

rmccScreenshot = "Screenshot_RMCC.png"
serologyScreenshot = "Screenshot_Serology.png"
summaryScreenshot = "Screenshot_Summary.png"
caseScreenshot = "Screenshot_Cases.png"
recoveryScreenshot = "Screenshot_Recovery.png"
deathsScreenshot = "Screenshot_Deaths.png"
ltcScreenshot = "Screenshot_LTC.png"

accessJson = 'accessVals.json'

authJson = 'gsheetAuth.json'

dailyJson = 'dailyData.json'

imgurComment = 'imgurComment.md'
redditTitle = os.path.join(redditCommentDir, 'title.md')
