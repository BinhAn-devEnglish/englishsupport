import streamlit as st
import pandas as pd
from gtts import gTTS
import base64
from io import BytesIO
import random
import time

# ==========================================
# PHẦN 1: CẤU HÌNH KẾT NỐI
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
                options = []
                correct = ""
                j = i + 1
                while j < len(df):
                    next_col_b = str(df.iloc[j, 1]).strip()
                    opt_val = str(df.iloc[j, 2]).strip()
                    if opt_val == "nan" or opt_val == "" or "Câu" in next_col_b or next_col_b.isdigit():
                        break
                    if opt_val.endswith('*') or opt_val.endswith('★'):
                        clean_val = opt_val[:-1].strip()
                        correct = clean_val
                        options.append(clean_val)
                    else:
                        options.append(opt_val)
                    j += 1
                if q_text and options:
                    tests[curr_test].append({"question": q_text, "options": options, "correct": correct})
                i = j 
            else: i += 1
        return {k: v for k, v in tests.items() if len(v) > 0}
    except Exception as e:
        st.error(f"Lỗi cấu trúc Sheet: {e}")
        return {}

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
# PHẦN 3: GIAO DIỆN CÁC CHẾ ĐỘ CHƠI
# ==========================================

# GAME 1: FLASHCARD
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

# GAME 2: QUIZ (CHỮ)
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

# GAME 3: MEMORY (5s)
def game_memory_audio(data):
    if "mem_idx" not in st.session_state: st.session_state.mem_idx = 0
    if "mem_state" not in st.session_state: st.session_state.mem_state = "init"

    item = data[st.session_state.mem_idx % len(data)]
    
    st.markdown("### 🧠 Ghi nhớ: Hình & Âm")
    st.caption("Nhìn hình, nghe âm thanh. Sau 5 giây chữ sẽ biến mất!")
    
    st.image(get_img_url(item), width=500)
    
    text_container = st.empty()
    control_container = st.empty()

    if st.session_state.mem_state == "init":
        text_container.title(f"🔤 {item['word']}")
        autoplay_audio(item['word'])
        
        progress_text = "Đang ghi nhớ... (5s)"
        my_bar = st.progress(0, text=progress_text)
        
        for percent_complete in range(100):
            time.sleep(0.05)
            my_bar.progress(percent_complete + 1, text=progress_text)
        
        my_bar.empty()
        text_container.empty()
        st.session_state.mem_state = "hidden"
        st.rerun()

    elif st.session_state.mem_state == "hidden":
        text_container.info("❓ Con có nhớ từ vừa rồi là gì không? Hãy đọc to lên nhé!")
        if control_container.button("Xem đáp án 👀", type="primary"):
            st.session_state.mem_state = "reveal"
            st.rerun()
            
    elif st.session_state.mem_state == "reveal":
        text_container.success(f"🎉 Đáp án: {item['word']}")
        autoplay_audio(item['word'])
        if control_container.button("Câu tiếp theo ➡️"):
            st.session_state.mem_idx += 1
            st.session_state.mem_state = "init"
            st.rerun()

# --- GAME MỚI: NGHE VÀ CHỌN ẢNH (3 LẦN) ---
def game_listening_choice(data):
    if len(data) < 3:
        st.warning("Bài học này cần ít nhất 3 từ vựng để chơi game này.")
        return

    # Khởi tạo trạng thái cho câu hỏi mới
    if "li_target" not in st.session_state:
        # 1. Chọn 3 từ ngẫu nhiên làm option
        options = random.sample(data, 3)
        st.session_state.li_options = options
        # 2. Chọn 1 từ làm đáp án đúng
        st.session_state.li_target = random.choice(options)
        # 3. Trạng thái đã trả lời hay chưa
        st.session_state.li_answered = False
        st.session_state.li_correct = False

    target = st.session_state.li_target
    options = st.session_state.li_options

    st.markdown("### 🎧 Nghe và Chọn hình đúng")
    st.caption("Bấm nút Loa để nghe từ (đọc 3 lần), sau đó chọn hình tương ứng.")

    # Phần Âm thanh
    # Ghép chuỗi để đọc 3 lần: "Apple. Apple. Apple."
    text_3_times = f"{target['word']}. {target['word']}. {target['word']}"
    
    col_audio, col_next = st.columns([1, 1])
    with col_audio:
        if st.button("🔊 NGHE LẠI (x3)", type="primary"):
            autoplay_audio(text_3_times)
            
    # Tự động đọc lần đầu tiên khi mới vào câu hỏi
    if "li_autoplaied" not in st.session_state or st.session_state.li_autoplaied != target['word']:
        autoplay_audio(text_3_times)
        st.session_state.li_autoplaied = target['word']

    st.divider()

    # Hiển thị 3 hình ảnh
    cols = st.columns(3)
    
    for i, opt in enumerate(options):
        with cols[i]:
            # Hiển thị ảnh
            st.image(get_img_url(opt), use_container_width=True)
            
            # Nút chọn
            # Nếu đã trả lời rồi thì khóa nút lại hoặc hiện kết quả
            if st.session_state.li_answered:
                if opt == target:
                    st.success(f"✅ {opt['word']}")
                else:
                    st.error("❌")
            else:
                if st.button(f"Chọn Hình {i+1}", key=f"btn_li_{i}", use_container_width=True):
                    st.session_state.li_answered = True
                    if opt == target:
                        st.session_state.li_correct = True
                        st.toast("Chính xác! 🎉", icon="✅")
                    else:
                        st.session_state.li_correct = False
                        st.toast("Sai rồi! 😢", icon="❌")
                    st.rerun()

    st.divider()
    
    # Phần kết quả và chuyển câu
    if st.session_state.li_answered:
        if st.session_state.li_correct:
            st.success(f"Chính xác! Đó là **{target['word']}**")
        else:
            st.error(f"Chưa đúng rồi. Đáp án là hình có từ **{target['word']}**")
            
        if st.button("Câu tiếp theo ➡️", type="primary"):
            # Xóa trạng thái để reset game cho vòng sau
            del st.session_state.li_target
            del st.session_state.li_options
            del st.session_state.li_answered
            del st.session_state.li_correct
            st.rerun()

# GAME TEST (BÀI KIỂM TRA)
def game_test_graded(data, lesson_name):
    if "active_test_name" not in st.session_state or st.session_state.active_test_name != lesson_name:
        st.session_state.ans_t = {}
        st.session_state.sub = False
        st.session_state.active_test_name = lesson_name

    total_q = len(data)
    answered_count = len(st.session_state.ans_t)
    
    st.sidebar.markdown(f"### 📊 Tiến độ: {answered_count}/{total_q}")
    st.sidebar.progress(answered_count / total_q)
    
    st.sidebar.write("Trạng thái câu hỏi:")
    grid = st.sidebar.columns(5)
    for i in range(total_q):
        with grid[i % 5]:
            if i in st.session_state.ans_t:
                st.markdown(f"✅**{i+1}**")
            else:
                st.markdown(f"⚪**{i+1}**")

    st.title(f"📋 {lesson_name}")
    name = st.text_input("Enter your name:", key="name_user")
    
    if not name: 
        st.warning("Please enter your name to start the test.")
        return

    st.divider()

    for idx, item in enumerate(data):
        st.markdown(f"#### Question {idx+1}: {item['question']}")
        
        saved_ans = st.session_state.ans_t.get(idx)
        try:
            old_idx = item['options'].index(saved_ans) if saved_ans in item['options'] else None
        except:
            old_idx = None

        ans = st.radio(
            f"Q{idx}", 
            item['options'], 
            index=old_idx, 
            key=f"t_{lesson_name}_{idx}", 
            disabled=st.session_state.sub,
            label_visibility="collapsed"
        )
        
        if ans and ans != saved_ans:
            st.session_state.ans_t[idx] = ans
            st.rerun()
        
        st.divider()
        
    if not st.session_state.sub:
        if st.button("SUBMIT TEST", use_container_width=True, type="primary"):
            if len(st.session_state.ans_t) < total_q:
                st.error(f"⚠️ Bạn chưa làm xong! Còn thiếu {total_q - len(st.session_state.ans_t)} câu.")
            else:
                st.session_state.sub = True
                st.rerun()
        
    if st.session_state.sub:
        score = sum(1 for i, item in enumerate(data) if st.session_state.ans_t.get(i) == item['correct'])
        st.balloons()
        st.success(f"### 🎉 Well done, {name.upper()}!\n### 🏆 Your Score: {score}/{len(data)}")
        if st.button("Restart"): 
            st.session_state.ans_t = {}
            st.session_state.sub = False
            st.rerun()

# ==========================================
# PHẦN 4: MAIN APP
# ==========================================
st.set_page_config(page_title="English for Kids", layout="centered")

st.markdown("""<style> [data-testid="stSidebar"] { width: 250px; } </style>""", unsafe_allow_html=True)

# MENU CHÍNH
menu = st.sidebar.radio("Menu:", 
    ["📖 Learning", 
     "🧠 Memory Game (5s)", 
     "🎧 Listening Game (x3)", # <--- MỤC MỚI
     "🎮 Quiz Game", 
     "📝 Test"]
)

if menu == "📝 Test":
    tests = load_data_sheet2()
    if tests:
        choice = st.sidebar.selectbox("Select Test:", list(tests.keys()))
        game_test_graded(tests[choice], choice)
    else: st.info("Waiting for Google Sheets connection...")
else:
    lessons = load_data_sheet1()
    if lessons:
        topic_choice = st.sidebar.selectbox("Select Lesson:", list(lessons.keys()))
        
        if menu == "📖 Learning": 
            game_flashcard(lessons[topic_choice])
        elif menu == "🧠 Memory Game (5s)": 
            game_memory_audio(lessons[topic_choice])
        elif menu == "🎧 Listening Game (x3)":
            game_listening_choice(lessons[topic_choice]) # <--- GỌI HÀM MỚI
        else: 
            game_quiz_stars(lessons[topic_choice])
            
    else: st.info("Connecting to Lesson data...")
