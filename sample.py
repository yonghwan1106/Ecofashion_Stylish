import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

st.title("실시간 대기오염 정보 조회")

# 날짜 선택 위젯
selected_date = st.date_input(
    "조회할 날짜를 선택하세요",
    min_value=datetime.now().date() - timedelta(days=30),  # 30일 전부터
    max_value=datetime.now().date(),  # 오늘까지
    value=datetime.now().date(),  # 기본값은 오늘
)

# API 정보
url = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMinuDustFrcstDspth'
params = {
    'serviceKey': 'S1kBo55wOyrX9FdzDMbXL4blXSOj%2BmYuvk2s%2B%2Bw5iTb%2Ba7Uu3NWwqPjz6wv7H0JVRaHn4zM3AAJIHy8rTAiHLw%3D%3D',
    'returnType': 'xml',
    'numOfRows': '100',
    'pageNo': '1',
    'searchDate': selected_date.strftime("%Y-%m-%d"),
    'InformCode': 'PM10'
}

# 디버그 모드 토글
debug_mode = st.checkbox("디버그 모드")

# 조회 버튼
if st.button("대기오염 정보 조회"):
    try:
        # API 요청
        response = requests.get(url, params=params)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        
        if debug_mode:
            st.subheader("API 응답 (XML)")
            st.code(response.text)

        # XML 파싱
        root = ET.fromstring(response.content)
        
        # 결과 항목 찾기
        items = root.findall('.//item')
        
        if items:
            for item in items:
                inform_grade = item.find('informGrade')
                inform_cause = item.find('informCause')
                
                if inform_grade is not None and inform_cause is not None:
                    st.subheader("대기오염 정보")
                    st.write(f"날짜: {selected_date}")
                    st.write(f"등급: {inform_grade.text}")
                    st.write(f"원인: {inform_cause.text}")
                else:
                    st.warning("필요한 정보를 찾을 수 없습니다.")
        else:
            st.info(f"{selected_date} 날짜의 대기오염 정보가 없습니다.")

    except requests.RequestException as e:
        st.error(f"API 요청 중 오류가 발생했습니다: {e}")
        if debug_mode:
            st.error(f"상세 오류: {str(e)}")
    except ET.ParseError as e:
        st.error("XML 파싱 중 오류가 발생했습니다.")
        if debug_mode:
            st.error(f"상세 오류: {str(e)}")
    except Exception as e:
        st.error(f"예상치 못한 오류가 발생했습니다: {str(e)}")

    if debug_mode:
        st.subheader("API 요청 정보")
        st.json(params)
