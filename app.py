import streamlit as st
import requests
import xmltodict
from datetime import datetime
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import logging
from urllib.parse import unquote

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)

# 제목 및 설명
st.title('에코패션 스타일리스트')
st.write('미세먼지 정보를 바탕으로 AI가 옷차림을 추천해드립니다.')

# Claude API 키 입력
claude_api_key = st.text_input("Claude API 키를 입력하세요", type="password")
if claude_api_key:
    st.success("API 키가 입력되었습니다.")
else:
    st.warning("Claude API 키를 입력해주세요.")

# 날짜 선택
search_date = st.date_input("날짜 선택", datetime.now())

# 공공 데이터 API 키
encoded_key = 'S1kBo55wOyrX9FdzDMbXL4blXSOj%2BmYuvk2s%2B%2Bw5iTb%2Ba7Uu3NWwqPjz6wv7H0JVRaHn4zM3AAJIHy8rTAiHLw%3D%3D'
PUBLIC_API_KEY = unquote(encoded_key)  # URL 디코딩

def get_dust_forecast(search_date):
    url = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMinuDustFrcstDspth'
    params = {
        'serviceKey': PUBLIC_API_KEY,
        'returnType': 'xml',
        'numOfRows': '100',
        'pageNo': '1',
        'searchDate': search_date.strftime('%Y-%m-%d'),
        'InformCode': 'PM10'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
        
        # 응답 내용 로깅
        logging.debug(f"API URL: {response.url}")
        logging.debug(f"Raw API Response: {response.content}")
        
        dict_data = xmltodict.parse(response.content)
        
        # 파싱된 데이터 로깅
        logging.debug(f"Parsed API Response: {dict_data}")

        # API 응답 구조 확인 및 안전한 데이터 접근
        response_data = dict_data.get('response', {})
        header = response_data.get('header', {})
        body = response_data.get('body', {})

        result_code = header.get('resultCode')
        result_msg = header.get('resultMsg')

        if result_code != '00':
            st.error(f"API 오류 (코드: {result_code}): {result_msg}")
            return None

        items = body.get('items', {}).get('item', [])
        if isinstance(items, dict):
            items = [items]
        
        if items:
            return items[0]  # 첫 번째 항목만 반환
        else:
            st.warning("해당 날짜의 미세먼지 정보가 없습니다.")
            return None

    except requests.RequestException as e:
        st.error(f"API 요청 중 오류가 발생했습니다: {e}")
        logging.exception("API request error")
        return None
    except Exception as e:
        st.error(f"예상치 못한 오류가 발생했습니다: {e}")
        logging.exception("Unexpected error occurred")
        return None

def get_clothing_recommendation(claude_api_key, pm10_value, temperature, humidity):
    anthropic = Anthropic(api_key=claude_api_key)
    
    prompt = f"""{HUMAN_PROMPT} 현재 날씨 조건:
    - 미세먼지(PM10): {pm10_value}μg/m³
    - 기온: {temperature}°C
    - 습도: {humidity}%

    위 날씨 조건을 고려하여 적절한 옷차림을 추천해주세요. 건강과 스타일을 모두 고려해야 합니다.
    추천 내용에는 다음이 포함되어야 합니다:
    1. 상의
    2. 하의
    3. 신발
    4. 액세서리 (마스크, 모자, 선글라스 등)
    5. 특별한 주의사항

    추천 이유도 간단히 설명해주세요.{AI_PROMPT}"""

    try:
        completion = anthropic.completions.create(
            model="claude-2.0",
            prompt=prompt,
            max_tokens_to_sample=500,
            temperature=0.7
        )
        return completion.completion
    except Exception as e:
        st.error(f"AI 추천을 가져오는데 실패했습니다: {str(e)}")
        return None

if st.button('미세먼지 정보 확인 및 옷차림 추천받기'):
    if not claude_api_key:
        st.error('Claude API 키를 입력해주세요.')
    else:
        dust_info = get_dust_forecast(search_date)
        
        if dust_info:
            st.subheader('미세먼지 예보')
            st.write(f"예보 일시: {dust_info.get('dataTime', '정보 없음')}")
            st.write(f"예보 지역: {dust_info.get('informGrade', '정보 없음')}")
            st.write(f"예보 개황: {dust_info.get('informOverall', '정보 없음')}")
            
            pm10_value = dust_info.get('pm10Value', '75')  # 기본값 설정
            temperature = 22  # 예시 값 (실제로는 날씨 API에서 가져와야 함)
            humidity = 60  # 예시 값 (실제로는 날씨 API에서 가져와야 함)
            
            st.subheader('날씨 정보')
            st.write(f"미세먼지(PM10): {pm10_value}μg/m³")
            st.write(f"기온: {temperature}°C")
            st.write(f"습도: {humidity}%")
            
            st.subheader('AI 옷차림 추천')
            recommendation = get_clothing_recommendation(claude_api_key, pm10_value, temperature, humidity)
            if recommendation:
                st.write(recommendation)
        else:
            st.error('미세먼지 정보를 가져오는데 실패했습니다. 다시 시도해주세요.')

# 사이드바: 내 옷장
st.sidebar.title('내 옷장')
st.sidebar.write('면 티셔츠')
st.sidebar.write('데님 재킷')
st.sidebar.write('마스크')
st.sidebar.write('선글라스')

# 푸터
st.sidebar.markdown('---')
st.sidebar.write('© 2023 에코패션 스타일리스트')

# 데이터 출처 표시
st.markdown("데이터 출처: 환경부/한국환경공단")