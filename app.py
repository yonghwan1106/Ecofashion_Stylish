import os
import streamlit as st


# Streamlit Secrets에서 환경 변수로 API 키 설정
os.environ['ANTHROPIC_API_KEY'] = st.secrets["ANTHROPIC_API_KEY"]

# 페이지 설정
st.set_page_config(page_title="개인 탄소 발자국 거래 시스템", layout="wide")

import pandas as pd
import numpy as np
import plotly.express as px
import logging
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

from config import ANTHROPIC_API_KEY, INITIAL_CARBON_CREDITS, AI_MODEL, MAX_TOKENS
from datetime import datetime, timedelta
from ai_integration import get_ai_recommendation, analyze_carbon_trend
from visualizations import (create_carbon_footprint_gauge, create_carbon_trend_chart,
                            create_category_breakdown, create_reduction_potential_chart)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Anthropic API 키 확인
if not ANTHROPIC_API_KEY:
    st.error("ANTHROPIC_API_KEY가 설정되지 않았습니다. config.py 파일을 확인해주세요.")
    st.stop()

# Anthropic 클라이언트 초기화
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

# 초기 탄소 크레딧 설정
if 'carbon_credits' not in st.session_state:
    st.session_state.carbon_credits = INITIAL_CARBON_CREDITS

# AI 통합 사용 예
def get_ai_recommendation(user_data):
    logger.info(f"Attempting to get AI recommendation for user data: {user_data}")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"{HUMAN_PROMPT} 다음은 사용자의 탄소 발자국 데이터입니다: {user_data}. 이 사용자에게 탄소 발자국을 줄일 수 있는 개인화된 조언을 제공해주세요. 구체적인 행동 지침과 그 효과를 설명해주세요.{AI_PROMPT}"

    try:
        response = client.completions.create(
            model=AI_MODEL,
            prompt=prompt,
            max_tokens_to_sample=MAX_TOKENS,
            temperature=0.7
        )
        logger.info("Successfully received AI recommendation")
        return response.completion
    except Exception as e:
        logger.error(f"Error in getting AI recommendation: {str(e)}")
        return None



# 세션 상태 초기화 함수
def initialize_session_state():
    if 'carbon_credits' not in st.session_state:
        st.session_state.carbon_credits = 4.0  # 초기 할당량
    if 'virtual_trees' not in st.session_state:
        st.session_state.virtual_trees = 0
    if 'challenges' not in st.session_state:
        st.session_state.challenges = []

# 실시간 탄소 발자국 시뮬레이션 함수
@st.cache_data
def simulate_real_time_footprint():
    now = datetime.now()
    times = [now - timedelta(minutes=i) for i in range(60, 0, -1)]
    footprints = np.cumsum(np.random.normal(0.001, 0.0005, 60))
    return pd.DataFrame({'time': times, 'footprint': footprints})

def main():
    initialize_session_state()

    # 사이드바 - 네비게이션
    page = st.sidebar.selectbox("페이지 선택", ["홈", "탄소 크레딧 관리", "마켓플레이스", "프로필"])

    if page == "홈":
        st.title("내 탄소 발자국")
        
        # 현재 탄소 발자국 상태
        current_footprint = st.session_state.carbon_credits
        st.metric(label="현재 탄소 크레딧", value=f"{current_footprint:.2f} 톤", delta=f"{4.0 - current_footprint:.2f} 톤")
        
        # 새로운 기능: 탄소 발자국 게이지
        create_carbon_footprint_gauge(current_footprint)
        
        # 탄소 발자국 그래프
        trend_data = {'date': pd.date_range(start="2024-01-01", end="2024-12-31", freq="M"),
                      'footprint': np.cumsum(np.random.normal(0.1, 0.02, 12))}
        create_carbon_trend_chart(trend_data)
        
        # 가상 나무
        st.subheader(f"당신의 가상 숲: {st.session_state.virtual_trees} 그루")
        if st.button("나무 심기"):
            if st.session_state.carbon_credits >= 0.1:
                st.session_state.carbon_credits -= 0.1
                st.session_state.virtual_trees += 1
                st.success("가상 나무를 1그루 심었습니다!")
            else:
                st.error("탄소 크레딧이 부족합니다.")
        
        # AI 추천 받기
        if st.button("AI 추천 받기"):
            user_data = {"transport": "car", "energy_usage": "high", "diet": "meat-heavy"}
            try:
                recommendation = get_ai_recommendation(user_data)
                if recommendation:
                    st.write(recommendation)
                else:
                    st.error("AI 추천을 가져오지 못했습니다. 반환된 값이 없습니다.")
            except Exception as e:
                st.error(f"AI 추천 과정에서 오류가 발생했습니다: {str(e)}")
                logger.exception("AI 추천 과정에서 상세 오류 발생")
     
        # 카테고리별 분석
        category_data = pd.DataFrame([
            {'category': '교통', 'subcategory': '자동차', 'value': 2.5},
            {'category': '교통', 'subcategory': '대중교통', 'value': 0.8},
            {'category': '에너지', 'subcategory': '전기', 'value': 1.5},
            {'category': '에너지', 'subcategory': '가스', 'value': 1.0},
            {'category': '식습관', 'subcategory': '육류', 'value': 1.2},
            {'category': '식습관', 'subcategory': '채소', 'value': 0.3},
        ])
        create_category_breakdown(category_data)
        
        # 새로운 기능: 절감 잠재량 분석
        create_reduction_potential_chart({})
        
        # 새로운 기능: 탄소 발자국 트렌드 분석
        carbon_data = [2.5, 2.3, 2.7, 2.4, 2.2]  # 최근 5일간의 가상 데이터
        if st.button("탄소 발자국 트렌드 분석"):
            analysis = analyze_carbon_trend(carbon_data)
            st.write(analysis)

    elif page == "탄소 크레딧 관리":
        st.title("탄소 크레딧 관리")
        
        st.subheader(f"현재 보유 크레딧: {st.session_state.carbon_credits:.2f} 톤")
        
        col1, col2 = st.columns(2)
        with col1:
            buy_amount = st.number_input("구매할 크레딧 양 (톤)", min_value=0.0, max_value=10.0, step=0.1)
            if st.button("크레딧 구매"):
                st.session_state.carbon_credits += buy_amount
                st.success(f"{buy_amount} 톤의 크레딧을 구매했습니다.")
        
        with col2:
            sell_amount = st.number_input("판매할 크레딧 양 (톤)", min_value=0.0, max_value=st.session_state.carbon_credits, step=0.1)
            if st.button("크레딧 판매"):
                st.session_state.carbon_credits -= sell_amount
                st.success(f"{sell_amount} 톤의 크레딧을 판매했습니다.")

    elif page == "마켓플레이스":
        st.title("탄소 크레딧 마켓플레이스")
        
        # 가상의 거래 데이터 생성
        trades = pd.DataFrame({
            'seller': ['User' + str(i) for i in range(1, 6)],
            'amount': np.random.uniform(0.1, 2.0, 5).round(2),
            'price': np.random.uniform(5000, 15000, 5).round(-2)
        })
        
        st.table(trades)
        
        trade_amount = st.number_input("거래할 크레딧 양 (톤)", min_value=0.1, max_value=2.0, step=0.1)
        trade_price = st.number_input("가격 (원/톤)", min_value=5000, max_value=15000, step=100)
        
        if st.button("거래 등록"):
            st.success(f"{trade_amount} 톤의 크레딧을 {trade_price}원/톤에 등록했습니다.")

    elif page == "프로필":
        st.title("내 프로필")
        
        st.subheader("개인 정보")
        st.write("이름: 홍길동")
        st.write(f"연간 할당량: 4.0 톤")
        st.write(f"현재 보유 크레딧: {st.session_state.carbon_credits:.2f} 톤")
        
        st.subheader("통계")
        stats_data = pd.DataFrame({
            'category': ['교통', '에너지', '식품', '기타'],
            'amount': np.random.uniform(0.5, 1.5, 4)
        })
        fig = px.pie(stats_data, values='amount', names='category', title='카테고리별 탄소 발자국')
        st.plotly_chart(fig)
        
        st.subheader("챌린지")
        new_challenge = st.text_input("새로운 챌린지 추가")
        if st.button("챌린지 등록"):
            st.session_state.challenges.append(new_challenge)
            st.success("새로운 챌린지가 등록되었습니다!")
        
        for idx, challenge in enumerate(st.session_state.challenges):
            st.checkbox(challenge, key=f"challenge_{idx}")

    # AI 기반 예측 및 추천 (사이드바)
    st.sidebar.subheader("AI 추천")
    if st.sidebar.button("탄소 절감 팁 받기"):
        tips = [
            "대중교통을 이용하세요.",
            "전기 절약을 위해 사용하지 않는 전자기기의 플러그를 뽑으세요.",
            "일회용품 사용을 줄이고 재사용 가능한 제품을 사용하세요.",
            "육류 소비를 줄이고 채식 위주의 식단을 시도해보세요.",
            "에너지 효율이 높은 가전제품을 사용하세요."
        ]
        st.sidebar.info(np.random.choice(tips))

    # 실시간 탄소 발자국 시뮬레이션 (사이드바)
    st.sidebar.subheader("실시간 탄소 발자국")
    real_time_data = simulate_real_time_footprint()
    fig = px.line(real_time_data, x='time', y='footprint', title='최근 1시간 탄소 발자국')
    st.sidebar.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
