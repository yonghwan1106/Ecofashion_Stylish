import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from urllib.parse import unquote

def fetch_air_pollution_data(selected_date, debug_mode=False):
    url = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMinuDustFrcstDspth'
    encoded_key = 'S1kBo55wOyrX9FdzDMbXL4blXSOj%2BmYuvk2s%2B%2Bw5iTb%2Ba7Uu3NWwqPjz6wv7H0JVRaHn4zM3AAJIHy8rTAiHLw%3D%3D'
    decoded_key = unquote(encoded_key)  # URL 디코딩
    params = {
        'serviceKey': decoded_key,
        'returnType': 'xml',
        'numOfRows': '100',
        'pageNo': '1',
        'searchDate': selected_date.strftime("%Y-%m-%d"),
        'InformCode': 'PM10'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        if debug_mode:
            st.subheader("API 응답 (XML)")
            st.code(response.text)
        root = ET.fromstring(response.content)
        
        error_msg = root.find('.//errMsg')
        if error_msg is not None and error_msg.text != "NORMAL SERVICE.":
            return None, f"API 오류: {error_msg.text}"
        
        items = root.findall('.//item')
        
        if items:
            result = {
                "date": selected_date,
                "grade": "정보 없음",
                "cause": "정보 없음",
                "pm10": "정보 없음"
            }
            for item in items:
                inform_grade = item.find('informGrade')
                inform_cause = item.find('informCause')
                pm10_value = item.find('.//pm10Value') or item.find('.//pm10Value24')  # PM10 값 찾기
                
                if inform_grade is not None:
                    result["grade"] = inform_grade.text
                if inform_cause is not None:
                    result["cause"] = inform_cause.text
                if pm10_value is not None:
                    result["pm10"] = pm10_value.text
            
            return result, None
        else:
            return None, f"{selected_date} 날짜의 대기오염 정보가 없습니다."
    except requests.RequestException as e:
        return None, f"API 요청 중 오류가 발생했습니다: {e}"
    except ET.ParseError as e:
        return None, f"XML 파싱 중 오류가 발생했습니다: {e}"
    except Exception as e:
        return None, f"예상치 못한 오류가 발생했습니다: {e}"

def main():
    st.title("실시간 대기오염 정보 조회")
    
    # 날짜 선택 (오늘부터 7일 전까지만 선택 가능)
    max_date = datetime.now().date()
    min_date = max_date - timedelta(days=7)
    selected_date = st.date_input(
        "조회할 날짜를 선택하세요",
        min_value=min_date,
        max_value=max_date,
        value=max_date,
    )
    
    debug_mode = st.checkbox("디버그 모드")
    
    if st.button("대기오염 정보 조회"):
        result, error = fetch_air_pollution_data(selected_date, debug_mode)
        if error:
            st.error(error)
        elif result:
            st.subheader("대기오염 정보")
            st.write(f"날짜: {result['date']}")
            st.write(f"등급: {result['grade']}")
            st.write(f"원인: {result['cause']}")
            st.write(f"PM10 값: {result['pm10']} µg/m³")
        
        if debug_mode:
            st.subheader("API 요청 정보")
            debug_params = {
                'serviceKey': "서비스 키 (보안상 숨김)",
                'returnType': 'xml',
                'numOfRows': '100',
                'pageNo': '1',
                'searchDate': selected_date.strftime("%Y-%m-%d"),
                'InformCode': 'PM10'
            }
            st.json(debug_params)

if __name__ == "__main__":
    main()