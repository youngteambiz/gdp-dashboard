import sys
import openai
import streamlit as st
from pinecone import Pinecone

# Ensure the default encoding is UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# 初始化 Pinecone
pinecone_api_key = "d81b5f77-4498-4206-9bb6-93465e872257"
pc = Pinecone(api_key=pinecone_api_key)

index_name = "global-market-data"
dimension = 1536
metric = "cosine"
host = "https://global-market-data-rzhox6n.svc.aped-4627-b74a.pinecone.io"  # Replace with your Pinecone host URL

index = pc.Index(index_name, host=host)

# 设置 OpenAI API 密钥
openai.api_key = "sk-SdsESq8lplaDr2sO4sEvjxJFNIMgQtkaKm11dBdJ19BxbzrE"
openai.api_base = "https://api.fe8.cn/v1"

# 获取文本的嵌入表示
def get_embedding(user_input):
    try:
        response = openai.Embedding.create(
            input=user_input,
            model="text-embedding-3-small"  # 确保使用有效的嵌入模型
        )
        if 'data' in response:
            embedding = response['data'][0]['embedding']
            return embedding
        else:
            st.error("Error: 'data' not found in response")
            return None
    except Exception as e:
        st.error(f"An error occurred while fetching embedding: {e}")
        return None

# 在 Pinecone 中搜索
def search_pinecone(user_input):
    query_embedding = get_embedding(user_input)
    if query_embedding is None:
        return {"matches": []}  # 返回空结果
    try:
        result = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True,
            include_values=False  # 只需要 metadata 和 score
        )
        return result
    except Exception as e:
        st.error(f"An error occurred while querying Pinecone: {e}")
        return {"matches": []}

# 处理用户输入并返回结果
def process_input(user_input, threshold=0.8):  # 增加 threshold 参数
    pinecone_results = search_pinecone(user_input)
    
    # 检查是否存在匹配结果以及匹配分数是否达到阈值
    if (pinecone_results["matches"] and 
        pinecone_results["matches"][0]['score'] >= threshold):
        # 如果有符合阈值的结果，则返回 Pinecone 的内容
        pinecone_texts = [match["metadata"]["text"] for match in pinecone_results["matches"]]
        final_reply = "\n\n".join(pinecone_texts)
    else:
        # 如果 Pinecone 没有相关内容或得分低于阈值，则使用 ChatGPT 回复
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_input}]
        )
        gpt_reply = response.choices[0].message['content']
        final_reply = f"Sorry, thre's no relevant content you requested in the company's database . Here's response from chatGPT to you:\n\n{gpt_reply}"

    return final_reply

# Streamlit 页面布局
st.set_page_config(layout="wide")
st.title("Intelligent analysis of global market")

# 设置页面宽度
page_width = st.container()
with page_width:
    col1, col2 = st.columns([1, 1.5])  # 调整列的比例

    # 左侧输入框和按钮
    with col1:
        user_input = st.text_area("Prompt entering", height=300)
        threshold = st.slider("Semantic Similarity Threshold", 0.0, 1.0, 0.8, step=0.05)
        clear_submit_cols = st.columns([1, 3])
        with clear_submit_cols[0]:
            if st.button("Clear"):
                user_input = ""
                st.experimental_rerun()
        with clear_submit_cols[1]:
            if st.button("Submit"):
                response = process_input(user_input, threshold)
    
    # 右侧输出框
    with col2:
        if 'response' in locals():
            st.text_area("Answers", value=response, height=300)

# 设置整体宽度在60%-80%之间
st.markdown(
    """
    <style>
    .reportview-container .main .block-container {
        max-width: 80%;
        padding: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



