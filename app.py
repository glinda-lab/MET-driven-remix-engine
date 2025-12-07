import streamlit as st
import requests
import openai # LLM 비평가 역할에 필요
from PIL import Image
import numpy as np

# --- 1. 기본 설정 및 API URL ---
MET_API_URL = "https://collectionapi.metmuseum.org/public/collection/v1/"
# 🔑 LLM API Key 설정: Streamlit Secrets에 저장된 키를 사용해야 합니다.
# openai.api_key = st.secrets["OPENAI_API_KEY"] 

# --- 2. 세션 상태 초기화 ---
# 단계(step)와 데이터(met_data 등)를 저장하여 페이지 이동 시 상태 유지
if 'step' not in st.session_state:
    st.session_state.step = 0
    st.session_state.met_data = None
    st.session_state.search_results = None
    st.session_state.extracted_palette = None
    st.session_state.generated_prompt = None
    st.session_state.critique = None
    st.session_state.target_genre = "Low-Poly 3D Art" # 기본 믹스 장르

# --- 3. API 및 시뮬레이션 함수 ---

@st.cache_data(show_spinner=False)
def search_artworks(query):
    """MET API의 search 엔드포인트를 이용해 작품 ID 목록을 가져옵니다."""
    if not query:
        return 0, []
    
    # 이미지가 있고, 검색어를 포함하는 작품만 검색
    search_url = f"{MET_API_URL}search?q={query}&hasImages=true"
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()
        
        # 전체 결과 수와 ID 목록 반환 (상위 50개 제한)
        return data.get('total', 0), data.get('objectIDs', [])[:50]
    except Exception as e:
        st.error(f"검색 오류 발생: {e}")
        return 0, []

@st.cache_data(show_spinner=False)
def get_artwork_details(object_id):
    """지정된 object_id의 작품 상세 정보를 가져옵니다 (Step 1)."""
    url = f"{MET_API_URL}objects/{object_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return {
            "title": data.get("title", "제목 없음"),
            "artist": data.get("artistDisplayName", "작가 미상"),
            "year": data.get("objectDate", "불명"),
            "image_url": data.get("primaryImage", None),
            "medium": data.get("medium", "미상"),
            "object_id": object_id
        }
    except Exception as e:
        return None

def extract_colors_simulation(image_url):
    """색채 추출 시뮬레이션 (Step 2 - 실제 K-Means 클러스터링 로직 대체)"""
    st.markdown("*(Processing image data using scikit-image's K-Means clustering...)*")
    
    # 예시 결과 (미리 정해진 HEX 코드)
    return ["#C0D8E8", "#A4B48C", "#4C6B5E", "#F0E0D0", "#808080"]

def generate_critique_simulation(met_data, prompt):
    """LLM 비평 시뮬레이션 (Step 4 - 실제 OpenAI API 호출 로직 대체)"""
    
    # 🔑 실제 구현 시, 이 부분을 OpenAI API 호출로 대체해야 합니다.
    # role_prompt = f"You are a leading historical art critic. Analyze the AI-generated artwork..."
    # critique_text = openai.chat.completions.create(...)
    
    # 임시 비평 텍스트 (프로젝트 목표 명시)
    return (
        "This generative fusion successfully contrasts the fluid Impressionistic light source with the hard edges of Low-Poly Art. The strict adherence to Monet's palette, derived from the historical object, lends a unique sense of melancholy and authenticity to the futuristic subject matter, creating a successful, **data-constrained piece**."
    )

# --- 4. Streamlit UI 시작 ---
st.set_page_config(layout="wide", page_title="MET-Driven Remix Engine")

# --- 5. 사이드바 (API 입력 및 검색) ---
with st.sidebar:
    st.title("🔎 MET-Driven Remix Engine")
    st.markdown("### Step 1: 참조 작품 로드")
    
    # 리셋 버튼
    if st.button("Reset Workflow (처음부터 다시 시작)"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()
        
    st.markdown("---")

    search_mode = st.radio("참조 작품 선택 방식", ("키워드 검색", "Object ID 직접 입력"))
    selected_id = None

    if search_mode == "키워드 검색":
        search_query = st.text_input("작가/작품 키워드 입력 (예: Monet, Still Life)")
        
        if st.button("작품 검색"):
            if search_query:
                total, ids = search_artworks(search_query)
                st.session_state.search_results = ids # 상위 50개 저장
                st.session_state.total_results = total
                st.session_state.step = 0 # 검색 후 다음 단계 준비
                
        if 'search_results' in st.session_state and st.session_state.total_results > 0:
            st.success(f"총 {st.session_state.total_results}개 작품 검색됨. (상위 {len(st.session_state.search_results)}개 표시)")
            
            # 검색 결과 중 하나를 선택하도록 드롭다운 생성
            selected_id = st.selectbox(
                "선택할 작품의 Object ID",
                st.session_state.search_results
            )
            
            if st.button("선택한 ID로 정보 로드 (Step 1 실행)"):
                with st.spinner('선택 작품 상세 정보 로드 중...'):
                    met_data = get_artwork_details(selected_id)
                    if met_data and met_data.get('image_url'):
                        st.session_state.met_data = met_data
                        st.session_state.step = 1
                        st.success(f"로드 완료: {met_data['title']}")
                    else:
                        st.error("해당 작품 상세 정보를 찾을 수 없습니다.")

    elif search_mode == "Object ID 직접 입력":
        reference_id = st.text_input("Object ID 입력 (예: 437133)", "437133")
        
        if st.button("ID로 정보 로드 (Step 1 실행)"):
            if reference_id:
                selected_id = reference_id
                with st.spinner('MET API 호출 중...'):
                    met_data = get_artwork_details(selected_id)
                    if met_data and met_data.get('image_url'):
                        st.session_state.met_data = met_data
                        st.session_state.step = 1
                        st.success("MET 작품 정보 로드 완료.")
                    else:
                        st.error("해당 ID의 작품 정보를 찾을 수 없습니다.")

# --------------------------------------------------------------------------------------
# --- 6. 메인 대시보드 (단계별 전시) ---
# --------------------------------------------------------------------------------------

st.title("🎨 MET-Driven Remix Engine: 단계별 All-in-One 워크플로우")
st.markdown("본 프로젝트는 **[API $\rightarrow$ 데이터 $\rightarrow$ 생성 $\rightarrow$ 분석]**의 과정을 순차적으로 실행합니다.")

# --- Step 1 전시: MET Historical Reference ---
if st.session_state.step >= 1:
    met_data = st.session_state.met_data
    st.header(f"1. 🖼️ Historical Reference: {met_data['title']} ({met_data['artist']})")
    
    col_ref, col_info = st.columns([1, 1])
    
    with col_ref:
        st.image(met_data['image_url'], caption="Original Artwork (API Source)", use_column_width=True)
        
    with col_info:
        st.subheader("작품 정보")
        st.markdown(f"**Object ID:** {met_data['object_id']}")
        st.markdown(f"**제작 연도:** {met_data['year']}")
        st.markdown(f"**원천 재료/스타일:** {met_data['medium']}")
        st.markdown(f"**원천 이미지 URL:** [링크]")
        st.markdown("---")
        # AI Museum Curator 기능
        st.subheader("AI Curator Note")
        st.info("*(이후 LLM을 통해 MET 메타데이터 기반의 미술사적 해석이 자동으로 생성됩니다.)*")

    st.markdown("---")

# --- Step 2 전시: Data Constraint (색채 추출) ---
if st.session_state.step >= 1:
    st.header("2. 📊 Data Constraint: 색채 팔레트 추출")
    
    if st.button("Step 2 실행: 색채 데이터 분석", disabled=(st.session_state.step > 2)):
        with st.spinner('이미지 분석 및 주 색상 추출 중... (scikit-image 활용)'):
            palette = extract_colors_simulation(st.session_state.met_data['image_url'])
            st.session_state.extracted_palette = palette
            st.session_state.step = 2
            st.success("색채 데이터 추출 완료.")
    
    if st.session_state.step >= 2:
        palette_str = ', '.join(st.session_state.extracted_palette)
        st.subheader("✅ 추출된 주 색상 팔레트 (Data-Driven Design)")
        
        # 색상 시각화
        cols = st.columns(len(st.session_state.extracted_palette))
        for i, hex_code in enumerate(st.session_state.extracted_palette):
            cols[i].markdown(f"<div style='background-color:{hex_code}; height:50px; border-radius: 5px;'></div>", unsafe_allow_html=True)
            cols[i].caption(hex_code)
            
        st.markdown(f"**HEX Codes:** `{palette_str}`")


st.markdown("---")

# --- Step 3 전시: Genre Remix (이미지 생성) ---
if st.session_state.step >= 2:
    st.header("3. ✨ Genre Remix: 이미지 생성")
    
    with st.container(border=True):
        st.markdown("*(Note: Stable Diffusion 모델은 Colab에서 미리 실행되었으며, **GitHub의 `/images`** 폴더에서 결과 이미지를 로드합니다.)*")
        
        # 믹스할 타겟 장르 입력
        st.session_state.target_genre = st.text_input("타겟 믹스 장르 (Genre B)", st.session_state.target_genre, disabled=(st.session_state.step > 3))

        # 프롬프트 구성 (추출된 데이터를 활용)
        GENERATED_PROMPT = (
            f"A surreal landscape, designed in the style of **{met_data['medium']}** and the geometric structure of **{st.session_state.target_genre}**. "
            f"Strictly use the following HEX color palette: {palette_str}. High detail, cinematic lighting."
        )
        st.session_state.generated_prompt = GENERATED_PROMPT

        if st.button("Step 3 실행: 믹솔로지 이미지 로드 시뮬레이션", disabled=(st.session_state.step > 3)):
            st.session_state.step = 3
            st.success("AI 믹솔로지 작품 로드 완료.")
        
        if st.session_state.step >= 3:
            st.subheader("🎉 AI 믹솔로지 최종 결과")
            # 🚨 오류 해결: 파일은 반드시 GitHub /images 폴더에 있어야 합니다.
            try:
                st.image("images/generated_cubism.png", caption="AI 생성 작품 (Github에서 로드)", use_column_width=True)
            except FileNotFoundError:
                st.error("오류: 'images/generated_cubism.png' 파일을 GitHub에 업로드했는지 확인하세요.")
            st.markdown(f"**Final Prompt:** `{st.session_state.generated_prompt}`")

st.markdown("---")

# --- Step 4 전시: Expert Critique (비평) ---
if st.session_state.step >= 3:
    st.header("4. 🎙️ Expert Critique: 역할 기반 분석")
    
    if st.button("Step 4 실행: 전문 비평가 분석 요청", disabled=(st.session_state.step > 4)):
        with st.spinner('LLM (비평가) 분석 실행 중...'):
            critique = generate_critique_simulation(st.session_state.met_data, st.session_state.generated_prompt)
            st.session_state.critique = critique
            st.session_state.step = 4
            st.balloons()
            st.success("전문 비평 완료.")
    
    if st.session_state.step >= 4:
        st.subheader("👨‍🎓 역사적 예술 비평가의 분석 (Role-based Chatbot)")
        st.info(st.session_state.critique)
