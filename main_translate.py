import SparkLLM_Thread
import streamlit as st
from streamlit_chat import message
import time

# 页面配置
st.set_page_config(
    page_title="多风格翻译",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="auto"
)

# 简洁清新的CSS样式
st.markdown("""
    <style>
    .title {
        color: #34495e;
        text-align: center;
        font-size: 32px;
        font-weight: 600;
        margin-bottom: 20px;
    }
    .stButton>button {
        background-color: #1abc9c;
        color: white;
        border-radius: 8px;
        padding: 8px 20px;
        font-size: 14px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #16a085;
    }
    .chat-box {
        background-color: #f9fbfc;
        padding: 15px;
        border-radius: 10px;
        margin-top: 20px;
    }
    .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #dfe6e9;
        font-size: 14px;
    }
    .stRadio > label {
        font-size: 14px;
        color: #2c3e50;
    }
    .footer {
        text-align: center;
        color: #95a5a6;
        font-size: 12px;
        margin-top: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.subheader("翻译设置")
    language = st.selectbox("目标语言", ["中文", "日文", "韩文", "法文", "英文"])
    show_original = st.checkbox("显示原文", value=True)

# 主页面
st.markdown('<div class="title">✨ 多风格翻译</div>', unsafe_allow_html=True)

# 输入区域
col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_area("", placeholder="输入需要翻译的文本...", height=120, key="input")
with col2:
    style = st.radio(
        "风格",
        ('默认风格', '英国维多利亚', '莎士比亚', '日本俳句', '日本和歌', '美国硬汉', 
         '南方哥特', '嘻哈', '古文', '学术', '琼瑶', '法国浪漫', '俄国现实'),
        index=0
    )
    translate_btn = st.button("翻译")

# 翻译风格提示词（简化和优化）
style_prompts = {
    '默认风格': '',
    '英国维多利亚': ', 使用维多利亚时代典雅文风翻译。',
    '莎士比亚': ', 用莎士比亚戏剧诗意风格翻译。',
    '日本俳句': ', 按俳句五-七-五节奏翻译。',
    '日本和歌': ', 用和歌柔美风格翻译。',
    '美国硬汉': ', 仿海明威简洁硬朗风格翻译。',
    '南方哥特': ', 用南方哥特阴郁风格翻译。',
    '嘻哈': ', 用嘻哈俚语和节奏翻译。',
    '古文': ', 用古诗词精炼风格翻译。',
    '学术': ', 用严谨学术风格翻译。',
    '琼瑶': ', 用琼瑶诗意多情风格翻译。',
    '法国浪漫': ', 用法国浪漫主义华丽风格翻译。',
    '俄国现实': ', 用俄国现实主义深沉风格翻译。'
}

# 初始化session state
if 'history' not in st.session_state:
    st.session_state['history'] = []

# 翻译逻辑
def translate():
    if user_input:
        with st.spinner("翻译中..."):
            prompt = f"{user_input}\n请将上述内容翻译为{language}{style_prompts[style]}"
            output = SparkLLM_Thread.main(
                uid='0', chat_id='0', appid='XX', 
                api_key='XX', 
                api_secret='XX', 
                gpt_url='wss://spark-api.xf-yun.com/v4.0/chat', 
                question=[{"role": "user", "content": prompt}]
            )
            st.session_state['history'].append({
                "input": user_input,
                "output": output,
                "time": time.strftime("%H:%M")
            })

if translate_btn and user_input:
    translate()

# 显示结果
if st.session_state['history']:
    st.markdown('<div class="chat-box">', unsafe_allow_html=True)
    if st.button("清除记录", key="clear"):
        st.session_state['history'] = []
        st.rerun()
    
    for i, entry in enumerate(reversed(st.session_state['history'])):
        with st.expander(f"结果 - {entry['time']}"):
            if show_original:
                st.markdown("**原文**")
                message(entry['input'], is_user=True, key=f"{i}_in")
            st.markdown("**译文**")
            message(entry['output'], key=f"{i}_out")
    st.markdown('</div>', unsafe_allow_html=True)

# 页脚
st.markdown('<p class="footer">Powered by Haohao & SparkLLM</p>', unsafe_allow_html=True)