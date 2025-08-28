import streamlit as st
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import urllib.request
import os
import re
from collections import Counter

# ===== 0) 한글 폰트 자동 다운로드 =====
font_path = "NanumGothic.ttf"
font_url = "https://raw.githubusercontent.com/naver/nanumfont/master/ttf/NanumGothic.ttf"
if not os.path.exists(font_path):
    try:
        urllib.request.urlretrieve(font_url, font_path)
    except Exception:
        st.error("폰트 다운로드 실패. 아래 링크에서 수동 다운로드해주세요.")
        st.markdown("[NanumGothic.ttf 다운로드](https://hangeul.naver.com/2017/nanum)")
        st.stop()

st.set_page_config(page_title="한글 워드클라우드 생성기", layout="wide")
st.title("한글 워드클라우드 생성기 (명사 기반)")

# ===== 1) 명사 추출기 준비 =====
def get_noun_extractor():
    try:
        from konlpy.tag import Okt
        okt = Okt()
        def extract_nouns_okt(text: str):
            return okt.nouns(text)
        return extract_nouns_okt, "Okt"
    except Exception:
        def extract_nouns_fallback(text: str):
            tokens = re.findall(r"[가-힣A-Za-z0-9]+", text)
            return [t for t in tokens if len(t) >= 2]
        return extract_nouns_fallback, "fallback"

extract_nouns, extractor_name = get_noun_extractor()

# ===== 2) 레이아웃 구성 =====
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📂 파일 업로드")
    uploaded_text = st.file_uploader("텍스트 파일 (.txt)", type="txt")
    uploaded_mask = st.file_uploader("마스크 이미지 (PNG/JPG)", type=["png", "jpg", "jpeg"])
    min_token_len = st.slider("토큰 최소 길이", 1, 5, 2)
    top_n = st.slider("상위 N개 단어", 20, 500, 200, step=10)
    min_count = st.slider("최소 빈도", 1, 10, 2)
    user_stopwords_text = st.text_input(
        "추가 불용어(쉼표로 구분)", 
        value="그리고,하지만,있다,하는,것,수,위한,등,이번,오늘"
    )

with col2:
    if uploaded_text is not None:
        text = uploaded_text.read().decode("utf-8")

        # 불용어 처리
        stopwords = set(STOPWORDS)
        extra = {w.strip() for w in user_stopwords_text.split(",") if w.strip()}
        stopwords.update(extra)

        # 마스크 이미지 처리
        mask_array = None
        if uploaded_mask is not None:
            image = Image.open(uploaded_mask).convert("RGB")
            image = image.resize((800, 800))
            mask_array = np.array(image)

        # 명사 추출
        tokens = extract_nouns(text)
        tokens = [t for t in tokens if len(t) >= min_token_len and t not in stopwords]

        # 빈도 계산
        freq = Counter(tokens)
        freq = {w: c for w, c in freq.items() if c >= min_count}
        freq_sorted = dict(Counter(freq).most_common(top_n))

        if len(freq_sorted) == 0:
            st.warning("조건에 맞는 단어가 없습니다. 필터를 조정하세요.")
        else:
            st.subheader("🖼 생성된 워드클라우드")
            wc = WordCloud(
                font_path=font_path,
                background_color="white",
                width=800,
                height=800,
                mask=mask_array
            ).generate_from_frequencies(freq_sorted)

            fig, ax = plt.subplots(figsize=(10, 10))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

            with st.expander("상위 단어/빈도 보기"):
                st.write(sorted(freq_sorted.items(), key=lambda x: x[1], reverse=True))
    else:
        st.info("왼쪽에서 📄 텍스트 파일을 업로드하세요.")

