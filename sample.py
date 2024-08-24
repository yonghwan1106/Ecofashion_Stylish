import streamlit as st
import requests
import xml.etree.ElementTree as ET

st.title("실시간 대기오염 정보 조회")

url = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMinuDustFrcstDspth'
params = {
    'serviceKey': 'S1kBo55wOyrX9FdzDMbXL4blXSOj%2BmYuvk2s%2B%2Bw5iTb%2Ba7Uu3NWwqPjz6wv7H0JVRaHn4zM3AAJIHy8rTAiHLw%3D%3D',
    'returnType': 'xml',
    'numOfRows': '100',
    'pageNo': '1',
    'searchDate': '2024-08-14',
    'InformCode': 'PM10'
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx

    # Parse the XML response
    root = ET.fromstring(response.content)

    # Extract relevant information (this may need to be adjusted based on the actual XML structure)
    for item in root.findall('.//item'):
        informGrade = item.find('informGrade').text
        informCause = item.find('informCause').text
        
        st.subheader("대기오염 정보")
        st.write(f"등급: {informGrade}")
        st.write(f"원인: {informCause}")

except requests.RequestException as e:
    st.error(f"API 요청 중 오류가 발생했습니다: {e}")
except ET.ParseError:
    st.error("XML 파싱 중 오류가 발생했습니다.")
except AttributeError:
    st.error("예상한 데이터를 찾을 수 없습니다. API 응답 구조를 확인해주세요.")
