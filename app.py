"""
서울 저가 커피 브랜드 카페 입지 분석 대시보드
Streamlit 버전 - dashboard_data.json 기반
"""

import json
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ──────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="서울 카페 입지 분석",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# 데이터 로드
# ──────────────────────────────────────────────
@st.cache_data
def load_data(_cache_key=None):
    """dashboard_data.json 및 detailed_analysis.json 로드 (캐시)"""
    json_path = os.path.join(os.path.dirname(__file__), "dashboard_data.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 신규 상세 지표 로드
    detailed_json_path = os.path.join(os.path.dirname(__file__), "detailed_analysis.json")
    detailed_data = {}
    if os.path.exists(detailed_json_path):
        with open(detailed_json_path, "r", encoding="utf-8") as f:
            detailed_data = json.load(f)

    # 행정동 DataFrame
    df_dong = pd.DataFrame(data["dong_data"])
    
    # 상세 지표 병합
    def get_detailed_metric(row, metric):
        name = row['dong_name'].replace('·', '').replace('.', '').replace('•', '').strip()
        return detailed_data.get(name, {}).get(metric, 0)

    if detailed_data:
        metrics_to_add = [
            'opportunity_score', 'penetration_rate', 'peak_sales_ratio', 
            'weekday_sales_ratio', 'avg_op_days', 'closure_rate', 'competition_intensity',
            'penetration_score', 'commercial_index'
        ]
        for m in metrics_to_add:
            df_dong[m] = df_dong.apply(lambda r: get_detailed_metric(r, m), axis=1)

    # 브랜드 컬럼 분리
    brands_df = pd.json_normalize(df_dong["brands"])
    brands_df.columns = [f"cnt_{c}" for c in brands_df.columns]
    df_dong = pd.concat([df_dong.drop(columns=["brands"]), brands_df], axis=1)

    # 지도 포인트 DataFrame
    df_map = pd.DataFrame(data["map_points"])
    
    # 지도 포인트에 행정동 이름 머지 (필터링용)
    if not df_map.empty and 'dong_name' not in df_map.columns:
        df_map = pd.merge(
            df_map, 
            df_dong[['dong_code', 'dong_name']], 
            on='dong_code', 
            how='left'
        )

    # 추천 DataFrame
    df_rec = pd.DataFrame(data["recommend_top"])

    return data, df_dong, df_map, df_rec

data, df_dong, df_map, df_rec = load_data()

BRANDS      = data["brands"]
BRAND_COLORS = data["brand_colors"]
BRAND_STATS  = data["brand_stats"]

# 브랜드별 평균 매력도 계산 (전역 사용)
BRAND_ATTR_MAP = {}
for b in BRANDS:
    dong_with_brand = df_dong[df_dong[f"cnt_{b}"] > 0]
    BRAND_ATTR_MAP[b] = dong_with_brand["attractiveness_score"].mean() if not dong_with_brand.empty else 0

# ──────────────────────────────────────────────
# 테마 및 가이드 설정
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎨 테마 설정")
    theme_mode = st.radio("테마 선택", ["Light", "Dark"], horizontal=True, label_visibility="collapsed")
    st.divider()

is_light = (theme_mode == "Light")

# 테마별 색상 정의
THEME = {
    "bg": "#f8f9fa" if is_light else "#0d1117",
    "surface": "#ffffff" if is_light else "#161b22",
    "surface2": "#f1f3f5" if is_light else "#21262d",
    "border": "#dee2e6" if is_light else "#30363d",
    "text": "#212529" if is_light else "#e6edf3",
    "text_sub": "#495057" if is_light else "#8b949e",
    "accent": "#005cc5" if is_light else "#58a6ff",
    "shadow": "rgba(0, 0, 0, 0.08)" if is_light else "rgba(0, 0, 0, 0.4)",
}

# 라이트 모드 시인성 확보를 위한 브랜드 색상
ADJUSTED_BRAND_COLORS = {}
for b, c in data["brand_colors"].items():
    if is_light:
        # 주요 브랜드 시인성 보정
        manual_colors = {
            "더벤티": "#d12d2d", "매머드커피": "#09a39a", "메가커피": "#b18e00",
            "빽다방": "#2e8b57", "컴포즈커피": "#8a63d2", "이디야": "#1e40af", "바나프레소": "#ef4444"
        }
        ADJUSTED_BRAND_COLORS[b] = manual_colors.get(b, c)
    else:
        ADJUSTED_BRAND_COLORS[b] = c

# ──────────────────────────────────────────────
# 커스텀 CSS
# ──────────────────────────────────────────────
st.markdown(f"""
<style>
/* 전체 배경 */
[data-testid="stAppViewContainer"] {{ background: {THEME["bg"]}; color: {THEME["text"]}; }}
[data-testid="stSidebar"] {{ background: {THEME["surface"]}; border-right: 1px solid {THEME["border"]}; }}
[data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}

/* 텍스트 색상 강제 적용 */
h1, h2, h3, h4, h5, h6, p, span, label, div {{ color: {THEME["text"]}; }}
.stMarkdown p {{ color: {THEME["text"]}; }}

/* 헤더 */
.main-header {{
    background: {THEME["surface"]};
    background-image: linear-gradient(135deg, {THEME["surface"]}, {THEME["bg"]});
    border: 1px solid {THEME["border"]};
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
    box-shadow: 0 4px 15px {THEME["shadow"]};
    text-align: center;
}}
.main-header h1 {{
    font-size: 1.8rem; font-weight: 900;
    background: linear-gradient(90deg, {THEME["accent"]}, #8a63d2);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0;
}}
.main-header p {{ color: {THEME["text_sub"]}; margin: 8px 0 0; font-size: .9rem; font-weight: 500; }}

/* 브랜드 카드 */
.brand-card {{
    background: {THEME["surface"]};
    border: 1px solid {THEME["border"]};
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 2px 8px {THEME["shadow"]};
}}
.brand-name {{ font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; }}
.brand-val  {{ font-size: 1.8rem; font-weight: 900; }}
.brand-sub  {{ font-size: .72rem; color: {THEME["text_sub"]}; }}

/* 메트릭 카드 */
[data-testid="metric-container"] {{
    background: {THEME["surface"]} !important;
    border: 1px solid {THEME["border"]} !important;
    border-radius: 10px !important;
    padding: 14px !important;
    box-shadow: 0 2px 6px {THEME["shadow"]} !important;
}}

/* 점수 설명 카드 */
.stp-card {{
    background: {THEME["surface"]};
    border-radius: 10px;
    padding: 16px;
    border: 1px solid {THEME["border"]};
    border-left: 4px solid var(--stp-color, {THEME["accent"]});
    box-shadow: 0 2px 8px {THEME["shadow"]};
}}
.stp-name  {{ font-size: .9rem; font-weight: 800; margin-bottom: 10px; }}
.stp-formula {{
    font-family: 'Roboto Mono', monospace;
    font-size: .75rem;
    font-weight: 700;
    background: {THEME["surface2"]};
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 10px;
    line-height: 1.6;
    white-space: pre-line;
    color: {THEME["text"]};
    border: 1px dashed {THEME["border"]};
}}
.stp-note {{ font-size: .72rem; color: {THEME["text_sub"]}; line-height: 1.6; font-weight: 500; }}

/* 지도 툴팁 스타일 수정 */
.deckgl-tooltip {{
    background: {THEME["surface"]} !important;
    color: {THEME["text"]} !important;
    border: 1px solid {THEME["border"]} !important;
    font-weight: 500;
}}

/* 탭 바 텍스트 강화 */
[data-testid="stMarkdownContainer"] p {{
    font-weight: 500;
}}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Plotly 공통 레이아웃
# ──────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor=THEME["surface"],
    plot_bgcolor=THEME["surface"],
    font=dict(color=THEME["text"], family="Noto Sans KR"),
    margin=dict(l=10, r=10, t=30, b=10),
)
GRID_STYLE = dict(gridcolor=THEME["border"], zerolinecolor=THEME["border"])

# ──────────────────────────────────────────────
# 🔍 전역 필터 (브랜드 선택) - 헤더보다 먼저 정의
# ──────────────────────────────────────────────
# 사이드바에 브랜드 선택 위젯 배치
global_selected_brands = st.sidebar.multiselect(
    "🏷️ 관심 브랜드 선택 (미선택 시 전체)",
    BRANDS,
    help="선택한 브랜드에 대해서만 데이터가 표시됩니다."
)

# 필터링된 브랜드 목록 및 컬럼 정의
ACTIVE_BRANDS = global_selected_brands if global_selected_brands else BRANDS
ACTIVE_BRAND_COLS = [f"cnt_{b}" for b in ACTIVE_BRANDS]

# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────
header_brands = " · ".join(ACTIVE_BRANDS[:5]) + (" 외" if len(ACTIVE_BRANDS) > 5 else "")
st.markdown(f"""
<div class="main-header">
  <h1>☕ 서울 저가 커피 브랜드 입지 분석</h1>
  <p>행정동별 브랜드 현황 · 매출 분석 · 입지 추천 | {header_brands}</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 사이드바
# ──────────────────────────────────────────────
with st.sidebar:
    st.divider()

    st.markdown("### 🔍 필터")
    st.divider()
    selected_tab = st.radio(
        "분석 메뉴",
        ["📊 브랜드 개요", "🗺️ 지도", "🏙️ 행정동 분석", "📊 상세 지표 비교", "📊 입지분석 시각화", "⭐ 입지 추천"],
        label_visibility="collapsed",
    )
    st.divider()

    if selected_tab == "🏙️ 행정동 분석":
        all_dongs = sorted(df_dong["dong_name"].unique())
        dong_search = st.selectbox("🏙️ 행정동 선택", ["전체"] + all_dongs)
        brand_filter = st.selectbox("브랜드 필터", ["전체"] + ACTIVE_BRANDS)
        sort_by = st.selectbox(
            "정렬 기준",
                        ["total_brand_count", "attractiveness_score", "monthly_sales", "opportunity_score", "penetration_rate", "peak_sales_ratio", "closure_rate"],
            format_func=lambda x: {
                "total_brand_count": "총 브랜드 수",
                "attractiveness_score": "매력도 점수",
                "monthly_sales": "지역 평균 매출",
                "opportunity_score": "기회 지수 (종사자/저가카페)",
                "penetration_rate": "저가 브랜드 침투율",
                "peak_sales_ratio": "피크 시간 매출 비중",
                "closure_rate": "폐업률",
            }[x],
        )

    elif selected_tab == "⭐ 입지 추천":
        rec_brand = st.selectbox("브랜드 선택", ["전체"] + ACTIVE_BRANDS)
        rec_sort = st.selectbox(
            "정렬 기준",
            ["attractiveness_score", "demand_score", "cost_score"],
            format_func=lambda x: {
                "attractiveness_score": "매력도 점수",
                "demand_score": "수요 점수",
                "cost_score": "비용 점수",
            }[x],
        )
        all_dongs = sorted(df_dong["dong_name"].unique())
        rec_search = st.multiselect("🏙️ 행정동 선택", all_dongs, placeholder="행정동을 선택하세요 (미선택 시 전체)")

    elif selected_tab == "🗺️ 지도":
        map_brands = st.multiselect(
            "표시할 브랜드",
            ACTIVE_BRANDS,
            default=ACTIVE_BRANDS,
        )
        all_dongs = sorted(df_dong["dong_name"].unique())
        map_dongs = st.multiselect(
            "📍 행정동 선택",
            all_dongs,
            placeholder="동 이름을 선택하세요 (미선택 시 전체)",
            help="선택한 행정동의 매장만 지도에 표시합니다."
        )

    st.divider()
    st.caption(f"행정동 {len(df_dong)}개 · 매장 {len(df_map):,}개")

    # 점수 계산 방법 설명 (항상 접근 가능)
    with st.expander("❓ 점수 계산 방법"):
        st.markdown("""
**Min-Max 정규화(0~1)** 후 3가지 점수를 가중 합산합니다.

| 점수 | 공식 | 의미 |
|---|---|---|
| 📈 **수요** | (정규화_지역매출×0.5 + 정규화_종사자×0.5)×100 | 높을수록 ↑ |
| ⚔️ **경쟁** | (1 − 정규화_카페수)×100 | 카페 적을수록 ↑ |
| 💰 **비용** | (1 − 정규화_부동산가)×100 | 임대료 낮을수록 ↑ |
| ⭐ **매력도** | 수요×0.4 + 경쟁×0.3 + 비용×0.3 | 종합 입지 지수 |

**지표 정의:**
- **상권 활력도**: 최근 3년간의 **개업률과 폐업률**을 분석하여 4단계로 분류합니다.
  - **다이나믹**: 개업률↑, 폐업률↑ (상권 교체 활발)
  - **상권확장**: 개업률↑, 폐업률↓ (성장세)
  - **정체**: 개업률↓, 폐업률↓ (안정기)
  - **상권축소**: 개업률↓, 폐업률↑ (쇠퇴기)
        """)
        st.info("💡 **지역 평균 매출 지수 유의사항**: 본 지표는 브랜드가 진출한 행정동 중 **가장 매출이 낮은 지역과 높은 지역의 평균값**을 나타냅니다. (행정동별 전체 카페 평균 기준)")

# ══════════════════════════════════════════════
# 탭 1: 브랜드 개요
# ══════════════════════════════════════════════
if selected_tab == "📊 브랜드 개요":

    # 🆕 정렬 기준 선택
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader("⭐ 브랜드 랭킹 상위 10", help="서울시 행정동 데이터를 바탕으로 산산된 브랜드별 성과 지표 랭킹입니다.")
    with c2:
        sort_method = st.selectbox(
            "정렬 기준",
            ["입지 매력도", "총 매장 수", "진출 행정동", "지역 평균 매출"],
            label_visibility="collapsed"
        )

    # 브랜드별 지표 정렬을 위해 전역 BRAND_ATTR_MAP 사용
            
    # 정렬 키 정의
    sort_key_map = {
        "입지 매력도": lambda b: BRAND_ATTR_MAP.get(b, 0),
        "총 매장 수": lambda b: BRAND_STATS[b]["total_stores"],
        "진출 행정동": lambda b: BRAND_STATS[b]["dong_count"],
        "지역 평균 매출": lambda b: BRAND_STATS[b].get("avg_monthly_sales", 0)
    }
    
    # 선택된 기준에 따라 정렬 후 상위 10개 선택
    top_10_brands = sorted(ACTIVE_BRANDS, key=sort_key_map[sort_method], reverse=True)[:10]

    st.caption(f"**{sort_method}** 기준 상위 10개 브랜드가 표시됩니다.")

    # 브랜드 카드 (2행 5열 구성)
    for row_idx in range(0, len(top_10_brands), 5):
        row_brands = top_10_brands[row_idx : row_idx + 5]
        cols = st.columns(5)
        for i, brand in enumerate(row_brands):
            s = BRAND_STATS[brand]
            color = ADJUSTED_BRAND_COLORS[brand]
            attr_val = BRAND_ATTR_MAP.get(brand, 0)
            avg = s.get('avg_monthly_sales', 0)
            v_min = s.get('min_monthly_sales', 0)
            v_max = s.get('max_monthly_sales', 0)
            
            avg_str = f"{avg:,}" if avg else '-'
            mm_str = f"{v_max:,}(최대) / {v_min:,}(최소)" if avg else ''
            
            # 현재 정렬 기준 강조 표시
            highlight_style = f"color:{THEME['accent']};font-weight:900" 
            
            with cols[i]:
                st.markdown(f"""
                <div class="brand-card" style="border-top:3px solid {color}">
                  <div class="brand-name" style="color:{color}">{brand}</div>
                  <div style="font-size:1.3rem;{highlight_style if sort_method=='입지 매력도' else ''}">{attr_val:.1f}</div>
                  <div class="brand-sub">평균 매력도</div>
                  <hr style="border-color:#30363d;margin:8px 0">
                  <div class="brand-val" style="font-size:1.4rem;{highlight_style if sort_method=='총 매장 수' else ''}">{s['total_stores']:,}</div>
                  <div class="brand-sub">총 매장 수</div>
                  <hr style="border-color:#30363d;margin:8px 0">
                  <div style="font-size:1.1rem;{highlight_style if sort_method=='진출 행정동' else ''}">{s['dong_count']}</div>
                  <div class="brand-sub">진출 행정동</div>
                  <hr style="border-color:#30363d;margin:8px 0">
                  <div style="font-size:1.1rem;{highlight_style if sort_method=='지역 평균 매출' else ''}{f';color:{color}' if sort_method!='지역 평균 매출' else ''}">{avg_str}</div>
                  <div class="brand-sub">지역 평균 매출</div>
                  <!--<div class="brand-sub" style="font-size:0.6rem; margin-top:2px; font-weight:bold; color:{THEME['accent']}">{mm_str}</div>
                  <div class="brand-sub" style="font-size:0.6rem; margin-top:-2px;">(진출 지역 Max-Min 평균)</div>-->
                </div>
                """, unsafe_allow_html=True)


    st.markdown("<br>", unsafe_allow_html=True)

    # 차트 행 1
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("브랜드별 총 매장 수", help="전체 행정동을 합산한 각 브랜드의 현재 누적 매장 수입니다.")
        fig = go.Figure(go.Bar(
            x=ACTIVE_BRANDS,
            y=[BRAND_STATS[b]["total_stores"] for b in ACTIVE_BRANDS],
            marker_color=[ADJUSTED_BRAND_COLORS[b] for b in ACTIVE_BRANDS],
            text=[BRAND_STATS[b]["total_stores"] for b in ACTIVE_BRANDS],
            textposition="outside",
        ))
        fig.update_layout(**PLOT_LAYOUT, height=300)
        fig.update_xaxes(**GRID_STYLE)
        fig.update_yaxes(**GRID_STYLE)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("브랜드별 진출 행정동 수", help="서울시 424개 행정동 중 해당 브랜드가 한 점포 이상 진출해 있는 지역의 개수와 비중입니다.")
        fig = go.Figure(go.Pie(
            labels=ACTIVE_BRANDS,
            values=[BRAND_STATS[b]["dong_count"] for b in ACTIVE_BRANDS],
            marker_colors=[ADJUSTED_BRAND_COLORS[b] for b in ACTIVE_BRANDS],
            hole=0.45,
            textinfo="label+percent",
        ))
        fig.update_layout(**PLOT_LAYOUT, height=300,
            legend=dict(orientation="h", y=-0.1),
        )
        st.plotly_chart(fig, use_container_width=True)

    # 차트 행 2: 상위 30개 동 누적 막대
    st.subheader("행정동별 브랜드 분포 (총 브랜드 수 상위 30개 동)", help="저가 커피 브랜드가 가장 많이 밀집한 상위 30개 행정동의 브랜드별 점유 현황입니다.")
    top30 = df_dong[df_dong["total_brand_count"] > 0].nlargest(30, "total_brand_count")
    fig = go.Figure()
    for brand in ACTIVE_BRANDS:
        col = f"cnt_{brand}"
        if col in top30.columns:
            fig.add_trace(go.Bar(
                name=brand,
                x=top30["dong_name"],
                y=top30[col],
                marker_color=ADJUSTED_BRAND_COLORS[brand],
            ))
    fig.update_layout(
        **PLOT_LAYOUT, barmode="stack", height=350,
        legend=dict(orientation="h", y=1.05),
    )
    fig.update_xaxes(tickangle=-40, **GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE)
    st.plotly_chart(fig, use_container_width=True)

    # 차트 행 3: 연령대별 매출
    st.markdown("##### 연령대별 총 매출 합계")
    age_cols  = ["age_10","age_20","age_30","age_40","age_50","age_60"]
    age_labels = ["10대","20대","30대","40대","50대","60대+"]
    age_colors = ["#FF6B6B","#FFE66D","#4ECDC4","#58a6ff","#bc8cff","#A8E6CF"]
    age_totals = [df_dong[c].sum() / 1e8 for c in age_cols]

    fig = go.Figure(go.Bar(
        x=age_labels, y=age_totals,
        marker_color=age_colors,
        text=[f"{v:.0f}억" for v in age_totals],
        textposition="outside",
    ))
    fig.update_layout(**PLOT_LAYOUT, height=300)
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(title="매출(억원)", **GRID_STYLE)
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════
# 탭 2: 지도
# ══════════════════════════════════════════════
elif selected_tab == "🗺️ 지도":
    st.markdown("##### 📍 저가 커피 브랜드 매장 위치")

    # 필터링 (브랜드 + 행정동)
    filtered_map = df_map[df_map["brand"].isin(map_brands)] if map_brands else df_map.iloc[0:0]
    
    if map_dongs:
        filtered_map = filtered_map[filtered_map["dong_name"].isin(map_dongs)]

    if filtered_map.empty:
        st.warning("표시할 브랜드를 사이드바에서 선택하세요.")
    else:
        # 색상 컬럼 추가 (hex → RGB)
        def hex_to_rgb(h):
            h = h.lstrip("#")
            return [int(h[i:i+2], 16) for i in (0, 2, 4)] + [200]

        filtered_map = filtered_map.copy()
        filtered_map["color"] = filtered_map["brand"].map(
            lambda b: hex_to_rgb(ADJUSTED_BRAND_COLORS.get(b, "#888888"))
        )

        import pydeck as pdk
        
        # 지도 중심 결정 (선택한 동이 하나라면 해당 동의 평균 위치로)
        if map_dongs and not filtered_map.empty:
            lat_center = filtered_map["lat"].mean()
            lng_center = filtered_map["lng"].mean()
            zoom_level = 13
        else:
            lat_center = 37.5665
            lng_center = 126.9780
            zoom_level = 10.5

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=filtered_map,
            get_position=["lng", "lat"],
            get_fill_color="color",
            get_radius=80,
            pickable=True,
            auto_highlight=True,
        )
        view = pdk.ViewState(latitude=lat_center, longitude=lng_center, zoom=zoom_level, pitch=0)
        tooltip = {"html": "<b>{brand}</b><br>{name}", "style": {"background": THEME["surface"], "color": THEME["text"]}}

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view,
            tooltip=tooltip,
            map_style="light" if is_light else "dark",
        ))

        # 브랜드별 매장 수 요약
        st.markdown("---")
        summary_cols = st.columns(len(map_brands))
        brand_counts = filtered_map["brand"].value_counts()
        for i, brand in enumerate(map_brands):
            cnt = brand_counts.get(brand, 0)
            color = ADJUSTED_BRAND_COLORS[brand]
            with summary_cols[i]:
                st.markdown(f"""
                <div style="text-align:center;padding:12px;background:{THEME['surface']};
                     border:1px solid {THEME['border']};border-radius:10px;border-top:3px solid {color};
                     box-shadow:0 2px 6px {THEME['shadow']}">
                  <div style="color:{color};font-weight:700;font-size:1rem">{brand}</div>
                  <div style="font-size:1.6rem;font-weight:900;color:{THEME['text']}">{cnt}</div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# 탭 3: 행정동 분석
# ══════════════════════════════════════════════
elif selected_tab == "🏙️ 행정동 분석":

    # 필터 적용
    df_view = df_dong.copy()
    if dong_search != "전체":
        df_view = df_view[df_view["dong_name"] == dong_search]
    if brand_filter != "전체":
        col = f"cnt_{brand_filter}"
        if col in df_view.columns:
            df_view = df_view[df_view[col] > 0]
    
    # 🆕 선택된 브랜드의 매장 수 합계 재계산 (동적 합계 적용)
    if global_selected_brands:
        df_view["total_brand_count"] = df_view[ACTIVE_BRAND_COLS].sum(axis=1)
        
    df_view = df_view.sort_values(sort_by, ascending=False, na_position="last")

    st.markdown(f"##### 행정동 분석 — {len(df_view)}개 동")

    # 표시 컬럼 선택
    display_cols = ["dong_name"] + [f"cnt_{b}" for b in ACTIVE_BRANDS] + \
                   ["total_brand_count", "attractiveness_score", "monthly_sales", "total_workers"]
    display_cols = [c for c in display_cols if c in df_view.columns]

    rename_map = {"dong_name": "행정동"}
    for b in ACTIVE_BRANDS:
        rename_map[f"cnt_{b}"] = b
    rename_map.update({
        "total_brand_count": "합계",
        "attractiveness_score": "매력도",
        "monthly_sales": "월매출(억)",
        "total_workers": "근로자",
    })

    show_df = df_view[display_cols].rename(columns=rename_map).head(200).copy()
    if "월매출(억)" in show_df.columns:
        show_df.rename(columns={"월매출(억)": "지역평균매출(억)"}, inplace=True)
        show_df["지역평균매출(억)"] = (show_df["지역평균매출(억)"] / 1e8).round(1)
    if "매력도" in show_df.columns:
        show_df["매력도"] = show_df["매력도"].round(1)

    # 테이블 표시 (다중 선택 가능)
    selected_rows = st.dataframe(
        show_df,
        use_container_width=True,
        height=400,
        on_select="rerun",
        selection_mode="multi-row",
    )

    # 선택된 행정동들 가로 비교
    sel_idx = selected_rows.selection.get("rows", []) if selected_rows else []
    if sel_idx:
        sel_idx = sel_idx[:4]  # 최대 4개까지 비교
        selected_dongs = [df_dong.loc[df_view.index[i]] for i in sel_idx]

        st.markdown("---")
        st.subheader(f"🏙️ 행정동 비교 분석 ({len(selected_dongs)}개 선택)", help="선택한 행정동들의 핵심 지표를 나란히 비교합니다. 최대 4개까지 비교 가능합니다.")

        # 가로 컬럼 생성
        compare_cols = st.columns(len(selected_dongs))
        for col, d in zip(compare_cols, selected_dongs):
            with col:
                st.markdown(f"### 📍 {d['dong_name']}")
                st.metric("매력도", f"{d['attractiveness_score']:.1f}" if pd.notna(d.get('attractiveness_score')) else "-")
                mc1, mc2 = st.columns(2)
                mc1.metric("수요", f"{d['demand_score']:.1f}" if pd.notna(d.get('demand_score')) else "-")
                mc2.metric("경쟁", f"{d['competition_score']:.1f}" if pd.notna(d.get('competition_score')) else "-")
                mc3, mc4 = st.columns(2)
                mc3.metric("비용", f"{d['cost_score']:.1f}" if pd.notna(d.get('cost_score')) else "-")
                mc4.metric("기회지수", f"{d.get('opportunity_score', 0):,.1f}")

                st.markdown("---")
                st.markdown(f"**근로자** {int(d.get('total_workers',0)):,}명")
                st.markdown(f"**카페 수** {int(d.get('cafe_count',0))}개")
                st.markdown(f"**평균매출** {d.get('monthly_sales',0)/1e8:.2f}억")
                st.markdown(f"**침투율** {d.get('penetration_rate',0):.1f}%")
                st.markdown(f"**폐업률** {d.get('closure_rate',0):.1f}%")

                st.markdown("---")

                # 브랜드 분포
                st.markdown("**브랜드 분포**")
                brand_counts_dong = []
                for brand in ACTIVE_BRANDS:
                    cnt = int(d.get(f"cnt_{brand}", 0))
                    if cnt > 0:
                        brand_counts_dong.append({"브랜드": brand, "매장수": cnt})
                if brand_counts_dong:
                    df_bd = pd.DataFrame(brand_counts_dong).sort_values("매장수", ascending=True)
                    fig = px.bar(df_bd, x="매장수", y="브랜드", orientation='h',
                                 color="브랜드", color_discrete_map=ADJUSTED_BRAND_COLORS, text_auto=True)
                    fig.update_layout(**{**PLOT_LAYOUT, 'margin': dict(l=0, r=10, t=5, b=5)},
                                      height=max(120, len(df_bd)*28), showlegend=False)
                    fig.update_xaxes(title=None, **GRID_STYLE)
                    fig.update_yaxes(title=None, **GRID_STYLE)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("진출 브랜드 없음")

                # 연령대별 매출
                st.markdown("**연령대별 매출**")
                age_vals = [d.get(c, 0) / 1e6 for c in ["age_10","age_20","age_30","age_40","age_50","age_60"]]
                fig = go.Figure(go.Bar(
                    x=["10대","20대","30대","40대","50대","60+"],
                    y=age_vals,
                    marker_color=["#FF6B6B","#FFE66D","#4ECDC4","#58a6ff","#bc8cff","#A8E6CF"],
                ))
                fig.update_layout(**{**PLOT_LAYOUT, 'margin': dict(l=0, r=0, t=5, b=5)}, height=180)
                fig.update_xaxes(**GRID_STYLE)
                fig.update_yaxes(title="백만원", **GRID_STYLE)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👆 테이블에서 행을 클릭하면 상세 정보가 표시됩니다. (여러 행 선택 가능, 최대 4개)")


# ══════════════════════════════════════════════
# 탭 4: 상세 지표 비교
# ══════════════════════════════════════════════
elif selected_tab == "📊 상세 지표 비교":
    st.subheader("🔍 행정동별 상세 지표 비교 분석", help="기회 지수, 침투율, 매출 집중도 등 고도화된 지표를 바탕으로 지역 및 브랜드의 특성을 분석합니다.")

    # 1. 지표별 행정동 랭킹
    st.markdown("---")
    st.markdown("#### 🏆 지표별 행정동 랭킹")
    st.caption("서울시 전체 행정동 중 선택한 지표가 가장 높은 상위 지역을 확인합니다.")
    
    col_metric, col_sort = st.columns([2, 1])
    with col_metric:
        target_metric = st.selectbox(
            "📍 분석할 지표 선택",
            ["opportunity_score", "penetration_rate", "peak_sales_ratio", "weekday_sales_ratio", "competition_intensity", "closure_rate"],
            format_func=lambda x: {
                "opportunity_score": "🎯 기회 지수 (잠재수요)",
                "penetration_rate": "📉 저가 브랜드 침투율",
                "peak_sales_ratio": "⏰ 피크 시간 매출 비중",
                "weekday_sales_ratio": "📅 주중 매출 비중",
                "competition_intensity": "⚔️ 경쟁 강도 (밀집도)",
                "closure_rate": "⚠️ 폐업률 (안정성)"
            }[x]
        )
    
    with col_sort:
        rank_n = st.slider("표시 개수", 5, 30, 15)
    
    df_rank = df_dong.nlargest(rank_n, target_metric).sort_values(target_metric, ascending=True)
    fig = px.bar(df_rank, x=target_metric, y="dong_name", orientation='h',
                 color=target_metric, color_continuous_scale='Viridis',
                 text_auto='.1f', labels={"dong_name": "행정동", target_metric: "지표 값"})
    
    fig.update_layout(**PLOT_LAYOUT, height=max(350, rank_n * 25), showlegend=False, coloraxis_showscale=False)
    fig.update_xaxes(**GRID_STYLE)
    fig.update_yaxes(**GRID_STYLE)
    st.plotly_chart(fig, use_container_width=True)

    # 2. 브랜드별 입지 프로필 (Radar Chart)
    st.markdown("---")
    st.subheader("🧬 브랜드별 입지 전략 프로필 (Radar)", help="선택한 브랜드들이 주로 진출해 있는 지역의 입지적 특성을 6가지 지표(기회, 침투율, 피크 매출 등)의 서울 전체 대비 상대 강도로 비교합니다.")
    
    # 비교 브랜드 선택 (전역 필터에서 선택된 브랜드 중)
    compare_brands = st.multiselect("비교할 브랜드 선택", ACTIVE_BRANDS, 
                                    default=ACTIVE_BRANDS[:min(3, len(ACTIVE_BRANDS))])
    
    if compare_brands:
        # Radar Chart용 데이터 준비
        metrics_list = ["opportunity_score", "penetration_rate", "peak_sales_ratio", "weekday_sales_ratio", "competition_intensity", "closure_rate"]
        metrics_labels = ["기회 지수", "침투율", "피크 매출", "주중 매출", "경쟁 강도", "폐업률"]
        
        radar_data = []
        for b in compare_brands:
            brand_dongs = df_dong[df_dong[f"cnt_{b}"] > 0]
            if not brand_dongs.empty:
                # 해당 브랜드가 위치한 동네들의 평균값
                brand_avg = brand_dongs[metrics_list].mean()
                # 0~100 스케일링 (서울 전체 최대값 대비 백분율)
                for i, m in enumerate(metrics_list):
                    val = brand_avg[m]
                    max_val = df_dong[m].max() if df_dong[m].max() > 0 else 1
                    norm_val = (val / max_val) * 100
                    radar_data.append(dict(brand=b, metric=metrics_labels[i], value=norm_val, display_brand=b))
        
        if radar_data:
            df_radar = pd.DataFrame(radar_data)
            fig = px.line_polar(df_radar, r="value", theta="metric", color="display_brand",
                                line_close=True, range_r=[0, 100],
                                color_discrete_map=ADJUSTED_BRAND_COLORS,
                                labels={"display_brand": "브랜드", "value": "상대적 강도", "metric": "지표"})
            
            fig.update_layout(**PLOT_LAYOUT, height=500, polar=dict(
                bgcolor=THEME["surface2"],
                radialaxis=dict(visible=True, range=[0, 100], gridcolor=THEME["border"], tickfont=dict(size=8)),
                angularaxis=dict(gridcolor=THEME["border"])
            ))
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 **Radar Chart 해석**: 각 축의 값이 100에 가까울수록 해당 브랜드가 해당 지표가 서울 전체에서 가장 높은 수준의 지역을 중심으로 확장하고 있음을 나타냅니다. (예: 피크 매출 축이 길면 오피스 상권 중심 전략)")
        else:
            st.info("선택한 브랜드들의 입지 데이터를 분석 중입니다.")
    else:
        st.warning("분석할 브랜드를 1개 이상 선택하세요.")

    # 3. 상세 지표 매트릭스 (Heatmap/Table)
    st.markdown("---")
    st.subheader("📊 브랜드-상세 지표 매트릭스", help="선택한 브랜드들의 핵심 입지 지표 평균값을 수치로 직접 비교합니다.")
    
    matrix_data = []
    for b in ACTIVE_BRANDS:
        brand_dongs = df_dong[df_dong[f"cnt_{b}"] > 0]
        if not brand_dongs.empty:
            stats = brand_dongs[metrics_list].mean()
            stats['브랜드'] = b
            matrix_data.append(stats)
    
    if matrix_data:
        df_matrix = pd.DataFrame(matrix_data).set_index('브랜드')
        df_matrix.columns = metrics_labels
        
        # 가독성을 위해 소수점 정리
        st.dataframe(df_matrix.style.background_gradient(cmap='Blues', axis=0).format("{:.1f}"), use_container_width=True)
    else:
        st.caption("비교 데이터가 부족합니다.")

    # 4. 월평균매출 결측치 시각화 (Matrix Heatmap)
    st.markdown("---")
    st.markdown("#### 📊 데이터 정합성: 매출 데이터 현황 매트릭스")
    st.caption("💡 **매트릭스 확인**: 위 격자는 서울시 전 행정동을 가나다순으로 나열한 것입니다. 초록색 박스는  원본 데이터가 대조된 지역이며, 빨간색은 누락된 지역입니다.")

    # 소스 데이터 로드 및 확인
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        for _p in [os.path.join(base_dir, "data", "seoul_dong_attractiveness.csv"),
                   os.path.join(base_dir, "seoul_dong_attractiveness.csv")]:
            if os.path.isfile(_p):
                src_path = _p
                break
        else:
            raise FileNotFoundError("seoul_dong_attractiveness.csv 파일을 찾을 수 없습니다.")
        df_src = pd.read_csv(src_path, encoding='utf-8-sig')
        # preprocess.py와 동일한 정규화 적용
        df_src['행정동코드'] = df_src['행정동_코드'].astype(str).str.split('.').str[0].str.strip().str.ljust(10, '0')
        src_codes = set(df_src['행정동코드'].tolist())
    except Exception as e:
        st.error(f"소스 파일을 로드할 수 없습니다: {e}")
        src_codes = set()

    # 전체 행정동 매트릭스 데이터 구성 (가나다순 정렬)
    df_matrix_base = df_dong.sort_values("dong_name").to_dict('records')
    matrix_items = []
    for d in df_matrix_base:
        is_valid = 1 if d['dong_code'] in src_codes else 0
        matrix_items.append({
            'name': d['dong_name'],
            'code': d['dong_code'],
            'is_valid': is_valid
        })

    # 열 개수 조정 (가독성을 위해 15열로 변경)
    cols_n = 15
    rows_n = (len(matrix_items) + cols_n - 1) // cols_n
    
    # 2D 배열 생성 (데이터, 텍스트, 호버)
    z = []
    text_labels = []
    hover = []
    for r in range(rows_n):
        row_z, row_text, row_hover = [], [], []
        for c in range(cols_n):
            idx = r * cols_n + c
            if idx < len(matrix_items):
                item = matrix_items[idx]
                row_z.append(item['is_valid'])
                # 이름이 너무 길면 자름 (최대 5자)
                display_name = item['name'] if len(item['name']) <= 5 else item['name'][:4] + ".."
                row_text.append(display_name)
                status = "✅ 데이터 보유" if item['is_valid'] == 1 else "❌ 매출 데이터 결측"
                row_hover.append(f"{item['name']}<br>{status}")
            else:
                row_z.append(-1)
                row_text.append("")
                row_hover.append("")
        z.append(row_z)
        text_labels.append(row_text)
        hover.append(row_hover)

    # 히트맵 시각화
    fig = go.Figure(data=go.Heatmap(
        z=z,
        text=text_labels,
        texttemplate="%{text}",
        textfont={"size": 9, "family": "Noto Sans KR", "weight": "bold"},
        hovertext=hover,
        hoverinfo="text",
        colorscale=[
            [0, THEME["bg"]],      # 빈 칸
            [0.33, THEME["bg"]],
            [0.33, "#FF6B6B"],    # 결측 (빨강)
            [0.66, "#FF6B6B"],
            [0.66, "#4ECDC4"],    # 보유 (초록)
            [1, "#4ECDC4"]
        ],
        showscale=False,
        xgap=4, ygap=4
    ))

    fig.update_layout(
        **PLOT_LAYOUT,
        height=max(450, rows_n * 22), # 행 수에 맞춰 높이 자동 조절
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, fixedrange=True),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, autorange='reversed', fixedrange=True),
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    valid_count = len([m for m in matrix_items if m['is_valid'] == 1])
    total_count = len(matrix_items)
    missing_items = [m for m in matrix_items if m['is_valid'] == 0]
    
    st.metric("데이터 소스 확보율 (Attractiveness CSV)", f"{(valid_count/total_count)*100:.1f}%", f"{valid_count} / {total_count}개동")



# ══════════════════════════════════════════════
# 탭 5: 입지분석 시각화
# ══════════════════════════════════════════════
elif selected_tab == "📊 입지분석 시각화":
    st.markdown("##### 📊 데이터 기반 심층 분석 시각화")
    st.caption("서울시 행정동별 핵심 지표를 6가지 관점에서 분석하며, 각 브랜드별 현황을 비교합니다.")

    # ── 산식 및 설명 (Methodology) ──
    with st.expander("📐 지표 계산 산식 및 분석 방법론 확인", expanded=False):
        f1, f2, f3 = st.columns(3)
        with f1:
            st.markdown("""
            <div class="stp-card" style="--stp-color:#FF6B6B">
              <div class="stp-name" style="color:#FF6B6B">🎯 Opportunity Score</div>
              <div class="stp-formula">총 종사자 수 ÷ 저가카페 매장수</div>
              <div class="stp-note">공급(매장) 대비 수요(종사자) 불균형 지표. 높을수록 기회.</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="stp-card" style="--stp-color:#4ECDC4">
              <div class="stp-name" style="color:#4ECDC4">⏰ 피크 시간 매출 비중</div>
              <div class="stp-formula">(06~14시 매출 ÷ 전체) × 100</div>
              <div class="stp-note">오피스 상권의 활동 집중도 파악 지표.</div>
            </div>
            """, unsafe_allow_html=True)
        with f2:
            st.markdown("""
            <div class="stp-card" style="--stp-color:#FFE66D">
              <div class="stp-name" style="color:#FFE66D">📈 저가 브랜드 점유율 (U)</div>
              <div class="stp-formula">저가 점유율 구간별 점수화</div>
              <div class="stp-note">0-3%:1점 | 3-15%:4점(최적) | 15%+:2점</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="stp-card" style="--stp-color:#58a6ff">
              <div class="stp-name" style="color:#58a6ff">📅 주중 매출 비중</div>
              <div class="stp-formula">주중 ÷ (주중 + 주말) × 100</div>
              <div class="stp-note">상권 성격(직장인 vs 주거/여가) 판별 지표.</div>
            </div>
            """, unsafe_allow_html=True)
        with f3:
            st.markdown("""
            <div class="stp-card" style="--stp-color:#bc8cff">
              <div class="stp-name" style="color:#bc8cff">⚔️ 지역별 경쟁 강도</div>
              <div class="stp-formula">반경 내 카페 수 ÷ 종사자 수</div>
              <div class="stp-note">종사자 대비 카페 밀집도. 낮을수록 유리.</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="stp-card" style="--stp-color:#A8E6CF">
              <div class="stp-name" style="color:#A8E6CF">🔄 상권변화 지표</div>
              <div class="stp-formula">폐업률 & 매출 기반 분류</div>
              <div class="stp-note">다이나믹(4) / 확장(3) / 정체(2) / 축소(1)</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 1. Opportunity Score (Brand Breakdown) & 2. 저가카페 점유율 점수
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1) Opportunity Score 및 지역 상권 현황", help="🎯 기회 지수 = 총 종사자 수 ÷ 저가 커피 매장 수. 잠재적 커피 수요(근로자)를 공급(저가 매장)이 얼마나 소화하고 있는지를 나타내는 '기회도' 점수입니다.")
        top_opp = df_dong.nlargest(10, 'opportunity_score')
        
        # 브랜드별 데이터로 변환 (Stacked Bar용)
        # 상위 10개 지역에 존재하는 브랜드만 추출하여 레전드가 지저분해지는 것을 방지
        relevant_brands = [b for b in ACTIVE_BRANDS if top_opp[f'cnt_{b}'].sum() > 0]
        brand_counts = []
        for brand in relevant_brands:
            brand_counts.append(go.Bar(
                name=brand, 
                x=top_opp['dong_name'], 
                y=top_opp[f'cnt_{brand}'],
                marker_color=ADJUSTED_BRAND_COLORS[brand]
            ))
        
        # 기회 점수 라인 차트 (Secondary Y axis)
        brand_counts.append(go.Scatter(
            name="Opportunity Score",
            x=top_opp['dong_name'],
            y=top_opp['opportunity_score'],
            yaxis="y2",
            line=dict(color="#FF6B6B", width=3, dash='dot'),
            mode="lines+markers+text",
            text=top_opp['opportunity_score'].round(0),
            textposition="top center"
        ))

        fig = go.Figure(data=brand_counts)
        fig.update_layout(
            **PLOT_LAYOUT, 
            height=350,
            barmode='stack',
            yaxis=dict(title="브랜드별 매장 수"),
            yaxis2=dict(title="기회 점수", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("2) 저가 점유율 현황 (전체 vs 저가)", help="📈 저가 브랜드 점유율 분포: X축(전체 카페 수) 대비 Y축(저가 카페 수)의 상관관계를 보여줍니다. 점의 크기는 저가 비중(%)을 나타내며, 색상은 성숙도 점수(1, 4, 2)를 의미합니다.")
        
        try:
            # 여러 경로 후보에서 파일 탐색 (로컬 / Streamlit Cloud 대응)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            candidates = [
                os.path.join(base_dir, "data", "dong_lowcost_cafe_ratio.csv"),
                os.path.join(base_dir, "dong_lowcost_cafe_ratio.csv"),
            ]
            csv_path = None
            for c in candidates:
                if os.path.isfile(c):
                    csv_path = c
                    break
            if csv_path is None:
                raise FileNotFoundError("dong_lowcost_cafe_ratio.csv 파일을 찾을 수 없습니다.")
            
            try:
                df_u = pd.read_csv(csv_path, encoding='utf-8-sig')
            except:
                df_u = pd.read_csv(csv_path, encoding='cp949')
            
            df_u['penetration_rate'] = (df_u['저가카페_매장수'] / df_u['전체_카페수']) * 100
            
            def get_u_label(rate):
                if rate <= 3: return "1점 (검증부족)"
                elif rate <= 15: return "4점 (최적구간)"
                else: return "2점 (과밀경쟁)"
                
            df_u['상태'] = df_u['penetration_rate'].apply(get_u_label)
            
            fig = px.scatter(df_u, 
                           x='전체_카페수', 
                           y='저가카페_매장수',
                           size='penetration_rate',
                           color='상태',
                           hover_name='행정동명',
                           color_discrete_map={
                               "1점 (검증부족)": "#FF6B6B", 
                               "4점 (최적구간)": "#4ECDC4", 
                               "2점 (과밀경쟁)": "#FFE66D"
                           },
                           labels={'전체_카페수': '전체 카페 수', '저가카페_매장수': '저가 카페 수', 'penetration_rate': '저가 비율(%)'},
                           opacity=0.7)
            
            fig.update_layout(**PLOT_LAYOUT, height=350, showlegend=True, 
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"U-Score 데이터를 로드할 수 없습니다: {e}")

    # 3. 피크 시간 & 4. 주중 매출 (브랜드 비교 요소 추가)
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("3) 오피스 상권 집중도 (피크 시간 매출)", help="⏰ 피크 시간 매출 비중 = (06~14시 매출 ÷ 총 매출) × 100. 출근 및 점심 시간대의 매출 쏠림 정도를 통해 직장인 중심 상권인지를 판별합니다.")
        top_peak = df_dong.nlargest(10, 'peak_sales_ratio')
        fig = px.bar(top_peak, x='dong_name', y='peak_sales_ratio',
                     color='peak_sales_ratio', color_continuous_scale='Oranges',
                     text_auto='.1f')
        fig.update_layout(**PLOT_LAYOUT, height=300, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.subheader("4) 평일 상권 집중도 (주중 매출 비중)", help="📅 주중 매출 비중 = (월~금 매출 ÷ 전체 매출) × 100. 주말 대비 평일 매출이 얼마나 활발한지를 통해 오피스 밀집 지역인지 주거 지역인지 구분합니다.")
        top_weekday = df_dong.nlargest(10, 'weekday_sales_ratio')
        fig = px.bar(top_weekday, x='dong_name', y='weekday_sales_ratio',
                     color='weekday_sales_ratio', color_continuous_scale='Blues',
                     text_auto='.1f')
        fig.update_layout(**PLOT_LAYOUT, height=300, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # 5. 경쟁 강도 & 6. 상권변화 (브랜드 비교 파이 차트)
    c5, c6 = st.columns(2)
    with c5:
        st.subheader("5) 브랜드별 지역 점유율 비교 (전체)", help="서울시 전체 행정동에 걸친 각 브랜드의 총 매장 수 리스트입니다. 저가 커피 시장 내 각 브랜드의 시장 지배력을 한눈에 비교할 수 있습니다.")
        total_counts = {b: df_dong[f"cnt_{b}"].sum() for b in ACTIVE_BRANDS}
        share_df = pd.DataFrame({
            '브랜드': list(total_counts.keys()),
            '매장수': list(total_counts.values())
        })
        fig = px.pie(share_df, values='매장수', names='브랜드', 
                     color='브랜드', color_discrete_map=ADJUSTED_BRAND_COLORS,
                     hole=0.4)
        fig.update_layout(**PLOT_LAYOUT, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with c6:
        st.subheader("6) 브랜드별 입지 상권 활력도 분포", help="🔄 상권 활력도 비중: 각 브랜드의 전체 매장들이 어떤 성격의 상권(다이나믹/확장/정체/축소)에 위치해 있는지 100% 비중으로 보여줍니다. 브랜드별 입지 전략의 공격성 및 안정성을 비교할 수 있습니다.")
        
        # detailed_analysis.json에서 사전 계산된 commercial_index 사용
        ci_col = df_dong['commercial_index'].astype(int)
        
        # 브랜드별 활력도 분포 데이터 생성
        vitality_dist = []
        change_labels = {4: "다이나믹(4, best)", 3: "상권확장(3)", 2: "정체(2)", 1: "상권축소(1, worst)"}
        
        for b in ACTIVE_BRANDS:
            for idx, label in change_labels.items():
                store_count = df_dong[ci_col == idx][f"cnt_{b}"].sum()
                if store_count > 0:
                    vitality_dist.append({
                        "브랜드": b,
                        "활력도": label,
                        "매장수": int(store_count)
                    })
        
        if vitality_dist:
            df_v = pd.DataFrame(vitality_dist)
            fig = px.bar(df_v, 
                         x="브랜드", 
                         y="매장수", 
                         color="활력도",
                         color_discrete_map={
                             "다이나믹(4, best)": "#4ECDC4", 
                             "상권확장(3)": "#58a6ff", 
                             "정체(2)": "#FFE66D", 
                             "상권축소(1, worst)": "#FF6B6B"
                         },
                         category_orders={"활력도": [change_labels[4], change_labels[3], change_labels[2], change_labels[1]]})
            
            fig.update_layout(**PLOT_LAYOUT, height=350, showlegend=True, barnorm="percent",
                             legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig.update_yaxes(title="비중 (%)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("표시할 상권 활력도 데이터가 없습니다.")

    # 7. 경쟁 강도 (카페 수 ÷ 종사자 수)
    st.markdown("---")
    st.subheader("7) 경쟁 강도 — 종사자 대비 카페 밀집도", help="⚔️ 경쟁 강도 = 행정동 내 카페 수 ÷ 종사자 수. 종사자 대비 카페 수가 많을수록 경쟁이 치열합니다. 값이 낮을수록 상대적으로 유리한 입지입니다.")
    
    # 종사자 수가 0인 행정동 제외
    df_comp = df_dong[df_dong['total_workers'] > 0].copy()
    df_comp['competition_ratio'] = df_comp['cafe_count'] / df_comp['total_workers']
    
    c7a, c7b = st.columns(2)
    
    with c7a:
        # 경쟁 강도 상위 15 (경쟁 치열)
        top_comp = df_comp.nlargest(15, 'competition_ratio')
        fig = px.bar(top_comp, y='dong_name', x='competition_ratio',
                     orientation='h',
                     color='competition_ratio',
                     color_continuous_scale='Reds',
                     text=top_comp['competition_ratio'].apply(lambda x: f"{x:.4f}"),
                     labels={'competition_ratio': '경쟁 강도', 'dong_name': '행정동'})
        fig.update_layout(**PLOT_LAYOUT, height=400, showlegend=False, coloraxis_showscale=False,
                         title=dict(text="🔴 경쟁 치열 상위 15", font=dict(size=14)))
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    
    with c7b:
        # 경쟁 강도 하위 15 (진출 유리)
        bottom_comp = df_comp[df_comp['competition_ratio'] > 0].nsmallest(15, 'competition_ratio')
        fig = px.bar(bottom_comp, y='dong_name', x='competition_ratio',
                     orientation='h',
                     color='competition_ratio',
                     color_continuous_scale='Greens_r',
                     text=bottom_comp['competition_ratio'].apply(lambda x: f"{x:.4f}"),
                     labels={'competition_ratio': '경쟁 강도', 'dong_name': '행정동'})
        fig.update_layout(**PLOT_LAYOUT, height=400, showlegend=False, coloraxis_showscale=False,
                         title=dict(text="🟢 진출 유리 상위 15", font=dict(size=14)))
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    # 📊 심층 통계 분석 (기존 차트 보강)
    # ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔬 다차원 분포 및 밀도 분석", help="주요 지표(매력도, 매출, 종사자 등) 간의 상관관계와 분포 밀도를 심층 분석하여 일반적인 경향성에서 벗어난 특이 지역을 포착합니다.")
    
    c7, c8 = st.columns(2)
    with c7:
        st.markdown("###### 주요 지표 분포 (Box Plot)")
        box_df = df_dong.copy()
        box_df['지역 평균 매출(억)'] = box_df['monthly_sales'] / 1e8
        melt_df = box_df.melt(value_vars=['attractiveness_score', 'opportunity_score', '지역 평균 매출(억)'], 
                              var_name='지표', value_name='값')
        fig = px.box(melt_df, x='지표', y='값', color='지표', points="all")
        fig.update_layout(**PLOT_LAYOUT, height=380, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c8:
        st.markdown("###### 종사자-매출 밀도 Heatmap")
        dens_df = df_dong.copy()
        dens_df['sales_cr'] = dens_df['monthly_sales'] / 1e8
        fig = px.density_heatmap(dens_df, x='total_workers', y='sales_cr', 
                                 nbinsx=30, nbinsy=30, color_continuous_scale='Viridis',
                                 labels={'total_workers': '총 종사자 수', 'sales_cr': '지역 평균 매출(억)'},
                                 text_auto=True)
        fig.update_layout(**PLOT_LAYOUT, height=380, coloraxis_showscale=True)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("###### 카페 수와 매출의 상관관계 (Marginal Scatter)")
    scat_df = df_dong.copy()
    scat_df['sales_cr'] = scat_df['monthly_sales'] / 1e8
    fig = px.scatter(scat_df, x='cafe_count', y='sales_cr', 
                     marginal_x="box", marginal_y="violin",
                     hover_name='dong_name', color='attractiveness_score',
                     labels={'cafe_count': '행정동별 전체 카페 수', 'sales_cr': '지역 평균 매출(억)'},
                     opacity=0.7)
    fig.update_layout(**PLOT_LAYOUT, height=450)
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════
# 탭 4: 입지 추천
# ══════════════════════════════════════════════
elif selected_tab == "⭐ 입지 추천":

    # 필터
    df_r = df_rec.copy()
    if rec_brand != "전체":
        df_r = df_r[df_r["brand"] == rec_brand]
    if rec_search:
        df_r = df_r[df_r["dong_name"].isin(rec_search)]
    # 행정동 그룹화를 위해 충분한 데이터 확보 (동별 중복 브랜드 고려)
    df_r = df_r.sort_values(rec_sort, ascending=False).head(1000)

    st.subheader(f"⭐ 입지 추천 — {df_r['dong_name'].nunique()}개 행정동", help="매력도 점수(수요, 경쟁, 비용)를 기준으로 브랜드가 진출하기에 가장 적합한 미진출 행정동을 추천합니다.")

    if df_r.empty:
        st.warning("조건에 맞는 추천 결과가 없습니다.")
    else:
        # 동네별 그룹화 (정렬 순서 유지)
        unique_dongs = df_r["dong_name"].unique()
        grouped_recs = []
        for dong in unique_dongs:
            if len(grouped_recs) >= 30: # 최종 표시 지역 수를 30개로 제한
                break
            dong_group = df_r[df_r["dong_name"] == dong]
            
            # 브랜드별 상세 정보 구성 (브랜드 개요 기준 매력도 점수 적용)
            b_list = dong_group["brand"].tolist()
            b_details = sorted(
                [{"name": b, "score": BRAND_ATTR_MAP.get(b, 0)} for b in b_list],
                key=lambda x: x["score"],
                reverse=True
            )

            grouped_recs.append({
                "dong_name": dong,
                "data": dong_group.iloc[0], # 공통 수치 (수요, 경쟁 등)
                "brands": [x["name"] for x in b_details],
                "scores": [x["score"] for x in b_details]
            })

        # 3열 카드 그리드
        for i in range(0, len(grouped_recs), 3):
            cols = st.columns(3)
            for ci, g_idx in enumerate(range(i, min(i + 3, len(grouped_recs)))):
                g = grouped_recs[g_idx]
                r = g["data"]
                score = r.get("attractiveness_score")
                score_color = "#4ECDC4" if score and score > 60 else "#FFE66D" if score and score > 40 else "#FF6B6B"

                # 브랜드 리스트 HTML 생성
                brand_chips_html = ""
                for b, s in zip(g["brands"], g["scores"]):
                    b_color = BRAND_COLORS.get(b, "#888")
                    adj_color = ADJUSTED_BRAND_COLORS.get(b, b_color)
                    brand_chips_html += f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; 
                               background:{b_color}10; border:1px solid {b_color}30; border-radius:6px; 
                               padding:4px 8px; margin-bottom:4px;">
                        <span style="color:{adj_color}; font-size:0.85rem; font-weight:800;">{b}</span>
                        <span style="color:{THEME['text_sub']}; font-size:0.75rem; font-weight:600;">{s:.1f}점</span>
                    </div>
                    """

                with cols[ci]:
                    st.markdown(f"""
                    <div style="background:{THEME['surface']};border:1px solid {THEME['border']};border-radius:12px;
                         padding:18px;border-top:4px solid {THEME['accent']};margin-bottom:14px;box-shadow: 0 4px 10px {THEME['shadow']}">
                      <div style="font-size:.75rem;color:{THEME['text_sub']};font-weight:700">#{g_idx+1} 타겟 행정동</div>
                      <div style="font-size:1.2rem;font-weight:800;margin:6px 0;color:{THEME['text']}">{g['dong_name']}</div>
                      
                      <div style="margin:12px 0;">
                        <div style="font-size:.7rem; color:{THEME['text_sub']}; font-weight:700; margin-bottom:6px;">추천 브랜드 (매력도순)</div>
                        {brand_chips_html}
                      </div>

                      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:16px">
                        <div style="background:{THEME['surface2']};border-radius:8px;padding:10px;border:1px solid {THEME['border']}">
                          <div style="font-size:.68rem;color:{THEME['text_sub']};font-weight:700">대표 매력도</div>
                          <div style="font-size:1.2rem;font-weight:900;color:{score_color}">
                            {f"{score:.1f}" if score else "-"}
                          </div>
                        </div>
                        <div style="background:{THEME['surface2']};border-radius:8px;padding:10px;border:1px solid {THEME['border']}">
                          <div style="font-size:.68rem;color:{THEME['text_sub']};font-weight:700">수요 지수</div>
                          <div style="font-size:1.2rem;font-weight:900;color:#00897b">
                            {f"{r['demand_score']:.1f}" if r.get('demand_score') else "-"}
                          </div>
                        </div>
                      </div>
                      <div style="font-size:.8rem;color:{THEME['text']};margin-top:12px;font-weight:700;border-top:1px solid {THEME['border']};padding-top:8px">
                        근로자 {int(r.get('total_workers',0)):,}명 · 
                        카페 {int(r.get('cafe_count',0))}개 <br>
                        지역 평균 매출 <span style="color:#005cc5">{r.get('monthly_sales',0)/1e8:.2f}억 원</span>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
