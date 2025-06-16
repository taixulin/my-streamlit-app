import streamlit as st
from PIL import Image
import openai
import base64
from io import BytesIO
import re

# OpenAI 金鑰
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 網站標題與說明
st.markdown("<h1 style='color:green;'>🥬 食材價格估計</h1>", unsafe_allow_html=True)
st.markdown("上傳圖片或輸入食材名稱，ChatGPT 幫你估算台灣市場價格 💰")

# 上傳圖片 + 輸入文字
uploaded_file = st.file_uploader("📷 上傳食材圖片（可選）", type=["jpg", "jpeg", "png"])
input_text = st.text_input("📝 或輸入食材名稱（多個請用逗號分隔）")

# 儲存食材名稱
food_list = []

# 圖片辨識
if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    st.image(img, caption="你上傳的圖片", use_container_width=True)

    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    prompt1 = """
請觀察這張圖片，列出你所看到的所有可食用食材（中文），一行只列出一個名稱，請不要加入說明或價格。
例如：
番茄
"""

    with st.spinner("🧠 GPT 正在辨識圖片中的食材..."):
        response1 = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是一位擅長辨識圖片中食材的助手"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt1},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                    ]
                }
            ]
        )
        result1 = response1.choices[0].message.content
        food_list += [line.strip() for line in result1.split("\n") if line.strip()]

# 文字輸入
if input_text.strip():
    extra_foods = [x.strip() for x in input_text.replace("，", ",").split(",") if x.strip()]
    food_list += extra_foods

# 去重
food_list = list(set(food_list))

if food_list:
    st.markdown("### 🧠 確認的食材名稱")
    st.write(", ".join(food_list))

    # 生成價格估計
    prompt2 = f"""
請根據台灣市場常見價格，給出以下食材的大約價格範圍 (每公斤/每顆/每把等)，並標註單位：
{', '.join(food_list)}
請用簡單清單格式輸出，例如：
番茄：約40~70元/公斤
"""

    with st.spinner("💰 GPT 正在提供價格估計..."):
        response2 = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "你是台灣市場食材價格專家"},
                {"role": "user", "content": prompt2}
            ]
        )
        price_result = response2.choices[0].message.content
        st.markdown("### 💵 食材價格估計")
        st.write(price_result)

        # 總額估算
        min_total = 0
        max_total = 0
        pattern = re.compile(r"(\d+)\s*~\s*(\d+)")
        for line in price_result.split("\n"):
            match = pattern.search(line)
            if match:
                min_price = int(match.group(1))
                max_price = int(match.group(2))
                min_total += min_price
                max_total += max_price

        if min_total > 0 and max_total > 0:
            st.markdown("### 🧾 總價格估計")
            st.success(f"這些食材的總價格大約是 **{min_total} ~ {max_total} 元**（視市場價格變動而異）")
else:
    st.info("請上傳圖片或輸入食材名稱來估算價格")
add app.py
