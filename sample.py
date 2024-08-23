import requests

url = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMinuDustFrcstDspth'
params = {
    'serviceKey': 'S1kBo55wOyrX9FdzDMbXL4blXSOj%2BmYuvk2s%2B%2Bw5iTb%2Ba7Uu3NWwqPjz6wv7H0JVRaHn4zM3AAJIHy8rTAiHLw%3D%3D',
    'returnType': 'xml',
    'numOfRows': '100',
    'pageNo': '1',
    'searchDate': '2024-08-14',
    'InformCode': 'PM10'
}

response = requests.get(url, params=params)
print(response.content)