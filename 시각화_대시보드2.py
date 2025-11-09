# =========================================================
# 📦 필요 라이브러리 가져오기
# =========================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os # 파일 존재 여부 확인을 위해 os 라이브러리 추가

# =========================================================
# ⚙️ 페이지 설정
# =========================================================
st.set_page_config(
    page_title='대구시 공영주차장 태양광 & 혼잡도 통합 대시보드',
    page_icon='☀️⚡',
    layout='wide',
    initial_sidebar_state='expanded'
)

# =========================================================
# 📂 데이터 경로 설정 (GitHub/로컬 폴더 기준)
# =========================================================
MAIN_DATA_PATH = '태양광_ESS_필요면적_정확단위_결과.xlsx'
CONGESTION_DATA_PATH = '혼잡도_요일별_시간별_요약.xlsx'

# =========================================================
# 📂 데이터 불러오기
# =========================================================
# 파일 존재 여부 확인 함수
def check_file_existence(file_path):
    if not os.path.exists(file_path):
        st.error(f"⚠️ **파일을 찾을 수 없습니다:** `{file_path}`. 이 파일을 `app.py` 파일과 같은 폴더에 넣어주세요.")
        st.stop()

# 1. 태양광 적합도/위치 정보 (main_df)
@st.cache_data
def load_main_data():
    check_file_existence(MAIN_DATA_PATH)
    try:
        df = pd.read_excel(MAIN_DATA_PATH)
    except Exception as e:
        st.error(f"메인 데이터 파일 로딩 오류: {e}")
        st.stop()
    # '주차장_ID' 컬럼이 없으면 에러 메시지를 표시
    if '주차장_ID' not in df.columns:
        st.error("메인 데이터 파일(`태양광_ESS_필요면적_정확단위_결과.xlsx`)에 **'주차장_ID'** 컬럼이 없어 상세 혼잡도 연동이 불가합니다.")
        st.stop()
    return df

main_df = load_main_data()

# 2. 혼잡도 시간별/요일별 상세 데이터 (congestion_sheets)
@st.cache_data
def load_congestion_data():
    check_file_existence(CONGESTION_DATA_PATH)
    # index_col=0: 첫 번째 컬럼(시간)을 인덱스로 설정
    try:
        sheets = pd.read_excel(CONGESTION_DATA_PATH, sheet_name=None, index_col=0)
    except Exception as e:
        st.error(f"혼잡도 상세 파일 로딩 오류: {e}")
        st.stop()
    return sheets

congestion_sheets = load_congestion_data()

# 혼잡도 데이터 시트 이름에 맞춰 요일 목록
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# =========================================================
# 🧭 사이드바 설정
# =========================================================
st.sidebar.header("📍 필터 선택")

# 담당구 목록
gu_list = ['전체', '중구', '북구', '동구', '서구', '남구', '수성구', '달서구', '군위군']
selected_gu = st.sidebar.selectbox('담당구 선택', gu_list)

# 구 선택 필터링
if selected_gu == '전체':
    filtered_df = main_df.copy()
else:
    filtered_df = main_df[main_df['지번주소'].str.contains(selected_gu, na=False)]

# 주차장 목록 (전체 옵션 포함)
parking_list = ['전체'] + list(filtered_df['주차장명'].unique())
selected_parking = st.sidebar.selectbox('주차장 선택', parking_list)

# 태양광 적합 여부 필터
solar_options = ['전체', '적합', '부적합']
selected_solar = st.sidebar.selectbox('태양광 적합 여부', solar_options)

# 혼잡도 필터
cong_options = ['전체', '여유', '보통', '혼잡']
selected_cong = st.sidebar.selectbox('혼잡도 상태', cong_options)

# 최종 필터링 적용
if selected_solar != '전체':
    filtered_df = filtered_df[filtered_df['태양광 적합 여부'] == selected_solar]

if selected_cong != '전체':
    filtered_df = filtered_df[filtered_df['혼잡도'] == selected_cong]

# '전체'가 아닌 특정 주차장이 선택된 경우
if selected_parking != '전체':
    filtered_df = filtered_df[filtered_df['주차장명'] == selected_parking]
    selected_parking_info = filtered_df.iloc[0] if not filtered_df.empty else None
else:
    selected_parking_info = None

# =========================================================
# 🎨 색상 매핑 설정
# =========================================================
color_map = {
    '여유': '#2ecc71',   # 초록
    '보통': '#f39c12',   # 주황
    '혼잡': '#e74c3c'    # 빨강
}

# =========================================================
# 🗺️ 지도 시각화 (첫 번째 컬럼)
# =========================================================
st.markdown("## ☀️⚡ 대구시 공영주차장 태양광 & 혼잡도 통합 대시보드")
st.markdown("---")
col1, col2 = st.columns([2, 1])

with col1:
    title_text = "🗺️ 대구시 공영주차장 태양광 설치 적합도 지도" if selected_gu == '전체' \
        else f"🗺️ {selected_gu} 공영주차장 태양광 설치 지도"
    st.subheader(title_text)

    if filtered_df.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    else:
        fig = px.scatter_mapbox(
            filtered_df,
            lat='위도',
            lon='경도',
            hover_name='주차장명',
            hover_data=['지번주소', '태양광 적합 여부', '혼잡도', '주차장_ID'],
            color='혼잡도',
            color_discrete_map=color_map,
            zoom=11,
            height=650,
            size_max=15
        )

        # 지도 스타일 및 중심점 설정
        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox_center={"lat": 35.8714, "lon": 128.6014},
            margin={"r":0, "t":20, "l":0, "b":0},
            legend_title_text="혼잡도 상태"
        )

        # 범례 커스텀
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.05, xanchor="center", x=0.5, bgcolor="rgba(255,255,255,0.8)")
        )

        st.plotly_chart(fig, use_container_width=True)


# =========================================================
# 📊 혼잡도 상세 시각화 (두 번째 컬럼 - 주차장 ID 연동)
# =========================================================
with col2:
    if selected_parking_info is not None:
        parking_name = selected_parking_info['주차장명']
        
        # '주차장_ID' 컬럼을 연동 키로 사용
        # load_main_data에서 이미 '주차장_ID' 컬럼 존재 여부를 확인했음
        parking_id = str(selected_parking_info['주차장_ID']) # ID는 문자열로 변환하여 사용
        
        st.subheader(f"📊 {parking_name} 혼잡도 상세 (ID: {parking_id})")
            
        # 요일 선택 드롭다운 (메인 페이지에 배치)
        selected_day = st.selectbox('요일 선택', days)

        # 해당 주차장의 ID가 혼잡도 데이터에 있는지 확인
        if selected_day in congestion_sheets and parking_id in congestion_sheets[selected_day].columns:
            
            df_cong = congestion_sheets[selected_day].copy()
            df_cong = df_cong * 100 # 0~100%로 변환

            fig_cong = go.Figure()

            # 선택된 주차장의 혼잡도 데이터만 사용
            y_data = df_cong[parking_id]
            
            fig_cong.add_trace(go.Scatter(
                x=y_data.index, # 인덱스 (시간) 사용
                y=y_data,
                mode='lines+markers',
                name=parking_id,
                text=[f"{v:.1f}%" for v in y_data],
                hovertemplate='%{text}<extra></extra>'
            ))

            fig_cong.update_layout(
                title=f"**{selected_day}** 혼잡도 변화 (%)",
                xaxis_title="시간",
                yaxis_title="혼잡도 (%)",
                hovermode="x unified",
                template="plotly_white",
                height=550 
            )
            st.plotly_chart(fig_cong, use_container_width=True)

        else:
            st.info(f"선택된 주차장 (ID: **{parking_id}**)의 혼잡도 상세 데이터가 '{selected_day}' 시트 또는 데이터셋에 없습니다. (데이터셋 확인 필요)")
    else:
        st.info("지도에서 확인할 주차장을 사이드바에서 **하나만 선택**하시면, 해당 주차장의 상세 혼잡도 정보를 볼 수 있습니다.")

# =========================================================
# 📝 메인 테이블 (추가 정보 제공)
# =========================================================
st.markdown("---")
st.subheader("📋 필터링된 주차장 목록")
st.dataframe(filtered_df[['주차장명', '지번주소', '주차장_ID', '태양광 적합 여부', '혼잡도']], use_container_width=True)