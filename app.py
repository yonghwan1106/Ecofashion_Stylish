import streamlit as st
import requests
import xmltodict
from datetime import datetime
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import logging
from urllib.parse import unquote
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="에코패션 스타일리스트", page_icon="👔", layout="wide")

# CSS 스타일 추가
st.markdown("""
<style>
    .main-header {font-size:40px; font-weight:bold; color:#1E88E5;}
    .sub-header {font-size:30px; font-weight:bold; color:#4CAF50;}
    .info-text {font-size:18px; color:#333333;}
    .sidebar-header {font-size:24px; font-weight:bold; color:#FF5722;}
    .recommendation-text {font-size:20px; color:#673AB7; background-color:#E8EAF6; padding:10px; border-radius:5px;}
    .footer {font-size:14px; color:#757575; text-align:center;}
</style>
""", unsafe_allow_html=True)

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)


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
            # 가장 최근의 예보 정보만 반환
            latest_forecast = max(items, key=lambda x: x.get('dataTime', ''))
            return latest_forecast
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

# 스마트 옷장 분석
def analyze_wardrobe(items):
    analysis = []
    for item in items:
        analysis.append({
            'name': item,
            'material': '면' if item in ['티셔츠', '셔츠'] else '데님' if item == '청바지' else '합성섬유',
            'style': '캐주얼' if item in ['티셔츠', '청바지', '운동화'] else '정장',
            'dust_protection': 3 if item in ['재킷', '코트'] else 2
        })
    return pd.DataFrame(analysis)

# 쇼핑 가이드
def shopping_guide(dust_level):
    if dust_level > 80:
        return "🛒 미세먼지 차단 마스크, 공기정화 기능이 있는 재킷을 추천합니다."
    elif dust_level > 50:
        return "🛍️ 경량 방진 재킷, 안티폴루션 스프레이를 추천합니다."
    else:
        return "👕 일반적인 의류로 충분합니다. 필요시 가벼운 마스크를 착용하세요."

# 세탁 충고
def cleaning_advice(dust_exposure):
    if dust_exposure > 80:
        return "🧼 오늘 착용한 옷은 즉시 세탁하고, 실외에서 말리지 마세요."
    elif dust_exposure > 50:
        return "🧽 오늘 착용한 옷은 가볍게 털어내고, 다음 착용 전 세탁을 권장합니다."
    else:
        return "👚 일반적인 세탁 주기를 유지하세요."

def get_weather_data(search_date):
    # 여기에 실제 날씨 API를 호출하는 코드를 작성합니다.
    # 현재는 예시 값을 반환합니다.
    return {
        "temperature": 22,
        "humidity": 60
    }


# 챗봇
def initialize_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []

def display_chat_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def get_chatbot_response(claude_api_key, user_input):
    anthropic = Anthropic(api_key=claude_api_key)
    
    messages = [
        {"role": "human", "content": "당신은 에코패션 스타일리스트 AI 어시스턴트입니다. 사용자의 패션과 환경에 대한 질문에 답변해주세요."},
        {"role": "assistant", "content": "네, 저는 에코패션 스타일리스트 AI 어시스턴트입니다. 환경을 고려한 패션에 대해 조언해드릴 수 있습니다. 어떤 도움이 필요하신가요?"},
    ] + st.session_state.messages + [
        {"role": "human", "content": user_input}
    ]

    response = anthropic.completions.create(
        model="claude-2.0",
        prompt=f"{HUMAN_PROMPT} {user_input}{AI_PROMPT}",
        max_tokens_to_sample=300,
        temperature=0.7
    )

    return response.completion

def add_chatbot_to_sidebar():
    st.sidebar.markdown("---")
    st.sidebar.markdown("<h2 class='sidebar-header'>챗봇 어시스턴트</h2>", unsafe_allow_html=True)
    
    initialize_chat_history()
    display_chat_messages()

    if user_input := st.sidebar.chat_input("무엇을 도와드릴까요?"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.sidebar.chat_message("user"):
            st.markdown(user_input)

        with st.sidebar.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = get_chatbot_response(st.session_state.claude_api_key, user_input)
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# 메인 앱 로직

def main():
    st.markdown("<h1 class='main-header'>🌿 에코패션 스타일리스트 🌿</h1>", unsafe_allow_html=True)
    st.markdown("<p class='info-text'>미세먼지 정보를 바탕으로 AI가 옷차림을 추천해드립니다.</p>", unsafe_allow_html=True)

    # 사이드바 설정
    with st.sidebar:
        claude_api_key = st.text_input("Claude API 키를 입력하세요", type="password")
        search_date = st.date_input("날짜 선택", datetime.now())
        wardrobe_items = st.multiselect(
            "오늘 입을 수 있는 옷을 선택하세요",
            ["티셔츠", "셔츠", "청바지", "슬랙스", "재킷", "코트", "운동화", "구두"]
        )

    add_chatbot_to_sidebar()

    col1, col2 = st.columns(2)

    with col1:
        if st.button('미세먼지 정보 확인 및 옷차림 추천받기'):
            if not claude_api_key:
                st.error('Claude API 키를 입력해주세요.')
            else:
                with st.spinner('정보를 가져오는 중...'):
                    # 날씨/환경 정보 데이터 호출
                    dust_info = get_dust_forecast(search_date)
                    weather_data = get_weather_data(search_date)

                    if dust_info and weather_data:
                        st.markdown("<h2 class='sub-header'>미세먼지 예보</h2>", unsafe_allow_html=True)
                        st.info(f"예보 일시: {dust_info.get('dataTime', '정보 없음')}")
                        st.info(f"예보 지역: {dust_info.get('informGrade', '정보 없음')}")
                        st.info(f"예보 개황: {dust_info.get('informOverall', '정보 없음')}")

                        pm10_value = int(dust_info.get('pm10Value', 0))
                        temperature = weather_data["temperature"]
                        humidity = weather_data["humidity"]

                        st.markdown("<h2 class='sub-header'>날씨 정보</h2>", unsafe_allow_html=True)
                        col_weather1, col_weather2, col_weather3 = st.columns(3)
                        col_weather1.metric("미세먼지(PM10)", f"{pm10_value}μg/m³")
                        col_weather2.metric("기온", f"{temperature}°C")
                        col_weather3.metric("습도", f"{humidity}%")

                        # Claude API 호출
                        st.markdown("<h2 class='sub-header'>AI 옷차림 추천</h2>", unsafe_allow_html=True)
                        recommendation = get_clothing_recommendation(claude_api_key, pm10_value, temperature, humidity)
                        if recommendation:
                            st.markdown(f"<p class='recommendation-text'>{recommendation}</p>", unsafe_allow_html=True)

                        # 쇼핑 가이드 및 세탁 조언
                        st.markdown("<h2 class='sub-header'>쇼핑 가이드</h2>", unsafe_allow_html=True)
                        st.write(shopping_guide(pm10_value))

                        st.markdown("<h2 class='sub-header'>세탁 및 관리 조언</h2>", unsafe_allow_html=True)
                        st.write(cleaning_advice(pm10_value))
                    else:
                        st.error('정보를 가져오는데 실패했습니다. 다시 시도해주세요.')

    with col2:
        # 스마트 옷장 분석
        st.markdown("<h2 class='sub-header'>스마트 옷장 분석</h2>", unsafe_allow_html=True)
        if wardrobe_items:
            wardrobe_analysis = analyze_wardrobe(wardrobe_items)
            st.dataframe(wardrobe_analysis)

            # 의류 분석 시각화
            fig = px.bar(wardrobe_analysis, x='name', y='dust_protection', 
                         title='의류별 미세먼지 차단 효과',
                         labels={'name': '의류 아이템', 'dust_protection': '미세먼지 차단 효과'},
                         color='style')
            st.plotly_chart(fig)
        else:
            st.info("옷장에서 아이템을 선택해주세요.")

        # 스타일 커뮤니티
        st.markdown("<h2 class='sub-header'>스타일 커뮤니티</h2>", unsafe_allow_html=True)
        user_style = st.text_input("오늘의 스타일을 공유해주세요!")
        if user_style:
            st.success(f"스타일이 공유되었습니다: {user_style}")

    # 푸터
    st.markdown("---")
    st.markdown("<p class='footer'>© 2024 에코패션 스타일리스트 | 데이터 출처: 환경부/한국환경공단</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()