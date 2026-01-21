import streamlit as st
import pandas as pd
from gtts import gTTS
import base64
from io import BytesIO
import random

# ==========================================
# PHẦN 1: CẤU HÌNH KẾT NỐI & DỮ LIỆU
# ==========================================
SHEET_ID = '1JHq0t1Vy1MfYYpWrBLRf_jZfNSp0NKZ7D2Swp6M59R0'
URL_SHEET1 = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0'
URL_SHEET2 = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=775101469'

@st.cache_data(ttl=5)
def load_data_sheet1():
    try:
        df = pd.read_csv(URL_SHEET1)
        lessons = {}
        curr = "Bài học"
        for _, row in df.iterrows():
            a, b, c = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2])
            d = str(row.iloc[3]) if len(row) > 3 else ""
            if a != "nan" and b == "nan": curr = a
            if b != "nan" and b.lower() not in ["word", "từ vựng"]:
                if curr not in lessons: lessons[curr] = []
                lessons[curr].append({"word": b, "example": c, "image": d})
        return lessons
    except: return {}

@st.cache_data(ttl=5)
def load_data_sheet2():
    try:
        df = pd.read_csv(URL_SHEET2, header=None, dtype=str).fillna("nan")
        tests = {}
        curr_test = "Chưa phân loại"
        i = 0
        while i < len(df):
            col_a = str(df.iloc[i, 0]).strip()
            col_b = str(df.iloc[i, 1]).strip()
            col_c = str(df.iloc[i, 2]).strip()
            if col_a != "nan" and col_a != "":
                curr_test = col_a
                if curr_test not in tests: tests[curr_test] = []
            is_question_start = "Câu" in col_b or col_b.isdigit()
            if is_question_start and col_c != "nan":
                q_text = col_c
                options, correct = [], ""
                j = i + 1
                while j < len(df):
                    next_col_b = str(df.iloc[j, 1]).strip()
                    opt_val = str(df.iloc[j, 2]).strip()
                    if opt_val == "nan" or opt_val == "" or "Câu" in next_col_b or next_col_b.isdigit(): break
                    if opt_val.endswith('*') or opt_val.endswith('★'):
                        clean_val = opt_val[:-1].strip()
                        correct = clean_val
                        options.append(clean_val)
                    else: options.append(opt_val)
                    j += 1
                if q_text and options:
                    tests[curr_test].append({"question": q_text, "options": options, "correct": correct})
                i = j 
            else: i += 1
        return {k: v for k, v in tests.items() if len(v) > 0}
    except: return {}

# ==========================================
# PHẦN 2: CÁC CÔNG CỤ HỖ TRỢ
# ==========================================
def autoplay_audio(text):
    try:
        tts = gTTS(text=str(text), lang='en')
        data = BytesIO()
        tts.write_to_fp(data)
        b64 = base64.b64encode(data.getvalue()).decode()
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64}">', unsafe_allow_html=True)
    except: pass

def get_img_url(item):
    img = str(item.get('image', '')).strip()
    if img and "http" in img: return img
    return f"https://loremflickr.com/800/600/{item.get('word', 'kid')},cartoon/all"

# ==========================================
# PHẦN 3: GIAO DIỆN HỌC TẬP & TRÒ CHƠI
# ==========================================
def game_flashcard(data):
    if "f_idx" not in st.session_state: st.session_state.f_idx = 0
    item = data[st.session_state.f_idx % len(data)]
    st.image(get_img_url(item), use_container_width=True)
    st.title(f"🔤 {item['word']}")
    st.info(f"Example: {item['example']}")
    c1, c2 = st.columns(2)
    if c1.button("🔊 Word"): autoplay_audio(item['word'])
    if c2.button("🔊 Example"): autoplay_audio(item['example'])
    st.divider()
    n1, n2, n3 = st.columns([1,1,1])
    if n1.button("⬅️ Back"): st.session_state.f_idx -= 1; st.rerun()
    n2.write(f"Page: {st.session_state.f_idx % len(data) + 1}/{len(data)}")
    if n3.button("Next ➡️"): st.session_state.f_idx += 1; st.rerun()

def game_quiz_stars(data):
    if "q_idx" not in st.session_state: st.session_state.q_idx = 0
    if "stars" not in st.session_state: st.session_state.stars = 0
    item = data[st.session_state.q_idx % len(data)]
    st.sidebar.markdown(f"## ⭐ Stars: {st.session_state.stars}")
    st.image(get_img_url(item), width=400)
    correct = item['word']
    if "opts" not in st.session_state or st.session_state.last_q != correct:
        others = [d['word'] for d in data if d['word'] != correct]
        st.session_state.opts = random.sample(others, min(len(others), 3)) + [correct]
        random.shuffle(st.session_state.opts)
        st.session_state.last_q = correct
    ans = st.radio("Choose the correct word:", st.session_state.opts, index=None, key=f"q_{st.session_state.q_idx}")
    if ans == correct:
        st.success("Correct! +1 ⭐")
        if st.button("Next Question"): st.session_state.stars += 1; st.session_state.q_idx += 1; st.rerun()

def game_test_graded(data, lesson_name):
    if "ans_t" not in st.session_state: st.session_state.ans_t = {}
    if "sub" not in st.session_state: st.session_state.sub = False
    
    # Theo dõi tiến độ ở Sidebar
    total_q = len(data)
    done_q = len(st.session_state.ans_t)
    st.sidebar.markdown(f"### 📊 Tiến độ: {done_q}/{total_q}")
    st.sidebar.progress(done_q / total_q)
    
    st.sidebar.write("Trạng thái câu:")
    grid = st.sidebar.columns(5)
    for i in range(total_q):
        with grid[i % 5]:
            st.write(f"{'✅' if i in st.session_state.ans_t else '⚪'}{i+1}")

    st.title(f"📋 {lesson_name}")
    name = st.text_input("Enter your name:", key="name_user")
    if not name: 
        st.warning("Please enter your name to start.")
        return

    st.divider()
    for idx, item in enumerate(data):
        st.markdown(f"#### Câu {idx+1}: {item['question']}")
        saved_ans = st.session_state.ans_t.get(idx)
        old_idx = item['options'].index(saved_ans) if saved_ans in item['options'] else None
        
        ans = st.radio(f"Q{idx}", item['options'], index=old_idx, key=f"t_{idx}", 
                       disabled=st.session_state.sub, label_visibility="collapsed")
        if ans and ans != saved_ans:
            st.session_state.ans_t[idx] = ans
            st.rerun()
        st.divider()

    if not st.session_state.sub:
        if st.button("NỘP BÀI (SUBMIT)", use_container_width=True, type="primary"):
            if len(st.session_state.ans_t) < total_q:
                st.error(f"Bạn còn thiếu {total_q - len(st.session_state.ans_t)} câu!")
            else:
                st.session_state.sub = True
                st.rerun()

    if st.session_state.sub:
        score = sum(1 for i, item in enumerate(data) if st.session_state.ans_t.get(i) == item['correct'])
        st.balloons()
        st.success(f"### 🎉 Chúc mừng {name.upper()}!\n### 🏆 Điểm của bạn: {score}/{len(data)}")
        if st.button("Làm lại (Restart)"):
            st.session_state.ans_t = {}
            st.session_state.sub = False
            st.rerun()

# ==========================================
# PHẦN 4: CẤU HÌNH GIAO DIỆN CHÍNH
# ==========================================
st.set_page_config(page_title="English for Kids", layout="centered")

# CSS ẩn Header thừa, Footer nhưng giữ Menu điều hướng
st.markdown("""
    <style>
        header {visibility: hidden;}
        footer {visibility: hidden;}
        #MainMenu {visibility: visible;}
        .stProgress > div > div > div > div { background-color: #2ecc71; }
        div.stButton > button:first-child { border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("Menu chính:", ["📖 Học tập", "🎮 Trò chơi Quiz", "📝 Bài kiểm tra"])

if menu == "📝 Bài kiểm tra":
    tests = load_data_sheet2()
    if tests:
        choice = st.sidebar.selectbox("Chọn bài thi:", list(tests.keys()))
        game_test_graded(tests[choice], choice)
    else: st.info("Đang kết nối dữ liệu đề thi...")
else:
    lessons = load_data_sheet1()
    if lessons:
        topic = st.sidebar.selectbox("Chọn bài học:", list(lessons.keys()))
        if menu == "📖 Học tập": game_flashcard(lessons[topic])
        else: game_quiz_stars(lessons[topic])
    else: st.info("Đang kết nối dữ liệu bài học...")
