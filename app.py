#!/usr/bin/env python3
"""
Streamlit Web Interface for University Knowledge Base RAG Assistant.
Run with: streamlit run app.py
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

from bench import CachedBatchOpenAIEmbedder, get_embedder, load_corpus_documents
from src.agent import KnowledgeBaseAgent
from src.chunking import HeadingChunker, RecursiveChunker, SentenceChunker
from src.store import EmbeddingStore

# Page configuration
st.set_page_config(
    page_title="Trợ Lý Quy Chế Đại Học — VinUni AI20k",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern, aesthetic UI
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .source-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .badge-score {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-source {
        background-color: #f1f5f9;
        color: #334155;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-family: monospace;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Load cached system resources
@st.cache_resource(show_spinner="Đang nạp kho tri thức vector từ dữ liệu...")
def load_rag_store(strategy: str = "recursive"):
    embedder = get_embedder()
    store = EmbeddingStore(collection_name=f"streamlit_rag_{strategy}", embedding_fn=embedder)
    if strategy == "heading":
        chunker = HeadingChunker(chunk_size=500)
    elif strategy == "sentence":
        chunker = SentenceChunker(max_sentences_per_chunk=3)
    else:
        chunker = RecursiveChunker(chunk_size=500)
    docs = load_corpus_documents(chunker=chunker)
    store.add_documents(docs)
    return store, embedder, len(docs)


store, embedder, total_corpus_chunks = load_rag_store("recursive")

# Initialize OpenAI client
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


def get_openai_client():
    if openai_api_key:
        try:
            from openai import OpenAI
            return OpenAI(api_key=openai_api_key)
        except Exception:
            return None
    return None


openai_client = get_openai_client()

# Sidebar controls
with st.sidebar:
    st.markdown("### 🎓 **VinUni AI20k Lab 7**")
    st.markdown("**Data Foundations: Embedding & Vector Store**")
    st.markdown("---")

    st.markdown("#### ⚙️ **Bộ lọc Metadata Đa Chiều**")
    
    audience_filter_option = st.selectbox(
        "👥 Đối tượng (Audience):",
        options=[
            "Tất cả",
            "Sinh viên (student)",
            "Giảng viên (faculty)",
            "Cán bộ coi thi / Nhân viên (staff)",
        ],
        index=0,
    )

    dept_filter_option = st.selectbox(
        "🏢 Đơn vị ban hành (Department):",
        options=[
            "Tất cả",
            "Phòng Đào tạo (phòng đào tạo)",
            "Phòng Khảo thí (phòng khảo thí)",
            "Phòng Công tác giảng viên (phòng công tác giảng viên)",
        ],
        index=0,
    )

    cat_filter_option = st.selectbox(
        "📑 Phân loại chủ đề (Category):",
        options=[
            "Tất cả",
            "Quy chế đào tạo",
            "Kiểm tra và thi cử",
            "Hồ sơ học vụ",
            "Dạy và học",
            "Đánh giá tốt nghiệp",
        ],
        index=0,
    )

    metadata_filter: dict[str, str] = {}
    if "student" in audience_filter_option:
        metadata_filter["audience"] = "student"
    elif "faculty" in audience_filter_option:
        metadata_filter["audience"] = "faculty"
    elif "staff" in audience_filter_option:
        metadata_filter["audience"] = "staff"

    if "phòng đào tạo" in dept_filter_option:
        metadata_filter["department"] = "phòng đào tạo"
    elif "phòng khảo thí" in dept_filter_option:
        metadata_filter["department"] = "phòng khảo thí"
    elif "phòng công tác giảng viên" in dept_filter_option:
        metadata_filter["department"] = "phòng công tác giảng viên"

    if cat_filter_option != "Tất cả":
        metadata_filter["category"] = cat_filter_option.lower()

    if not metadata_filter:
        metadata_filter = None

    if metadata_filter:
        st.info(f"🔎 Đang lọc: `{metadata_filter}`")

    st.markdown("#### 🔍 **Cài đặt truy xuất**")
    top_k = st.slider("Số lượng Chunks truy xuất (Top-K):", min_value=1, max_value=5, value=3)
    show_sources = st.checkbox("Hiển thị nguồn trích dẫn & điểm số", value=True)


    st.markdown("---")
    st.markdown("#### 💡 **Câu hỏi mẫu (Benchmark Queries)**")
    sample_queries = [
        ("Xin hoãn thi giữa kỳ (SV)", "Khi sinh viên xin hoãn thi giữa kỳ, hồ sơ cần được xử lý như thế nào?", {"audience": "student"}),
        ("Bộ phận duyệt vắng thi", "Bộ phận nào của Trường sẽ xem xét các trường hợp có lí do chính đáng để vắng thi giữa kỳ?", None),
        ("Thời hạn lưu trữ đề thi", "Thời hạn lưu trữ đề thi các môn học hệ đại học chính quy của Trường là bao lâu?", None),
        ("Hình thức SV tài năng", "Sinh viên thuộc chương trình tài năng có các hình thức nào?", None),
        ("Tên gọi khác điểm giữa kỳ", "Trong các thành phần điểm của điểm môn học thì điểm giữa kỳ có tên gọi khác là gì?", None),
    ]

    for label, query_text, q_filter in sample_queries:
        if st.button(f"👉 {label}", use_container_width=True):
            st.session_state.pending_prompt = query_text
            if q_filter:
                st.session_state.force_filter = q_filter
            st.rerun()

    st.markdown("---")
    st.markdown(f"📊 **Kho tri thức:** `{store.get_collection_size()}` chunks")
    st.markdown(f"🤖 **Embedding Model:** `text-embedding-3-small`")
    st.markdown(f"🧠 **LLM:** `gpt-4o-mini`")

    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main page Header
st.markdown('<div class="main-title">🏛️ Trợ Lý Quy Chế Đại Học (RAG)</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Hỏi đáp thông tin học vụ, khảo thí, văn bằng, giáo trình dựa trên cơ sở tri thức chính xác.</div>',
    unsafe_allow_html=True,
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Xin chào! Tôi là Trợ lý AI giải đáp thắc mắc về quy chế đào tạo, khảo thí và văn bằng. Bạn cần tra cứu thông tin gì hôm nay?",
            "sources": [],
        }
    ]

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources") and show_sources:
            with st.expander(f"📚 Xem {len(msg['sources'])} nguồn trích dẫn được truy xuất"):
                for idx, src in enumerate(msg["sources"], 1):
                    score = src.get("score", 0.0)
                    doc_id = src.get("metadata", {}).get("source_file", src.get("id", "doc"))
                    aud = src.get("metadata", {}).get("audience", "all")
                    dept = src.get("metadata", {}).get("department", "chưa rõ")
                    cat = src.get("metadata", {}).get("category", "chưa rõ")
                    snippet = src.get("content", "")
                    st.markdown(
                        f"""
                        <div class="source-card">
                            <div>
                                <b>#{idx}</b> <span class="badge-source">{doc_id}</span>
                                <span class="badge-score">Cosine: {score:.4f}</span>
                                <span style="font-size: 0.8rem; color: #475569; margin-left: 8px;">
                                    👥 <i>{aud}</i> | 🏢 <i>{dept}</i> | 📑 <i>{cat}</i>
                                </span>
                            </div>
                            <div style="margin-top: 6px; font-size: 0.92rem; color: #1e293b; white-space: pre-wrap;">{snippet}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


# Determine prompt input
prompt = st.chat_input("Nhập câu hỏi của bạn tại đây (ví dụ: quy định thi, phúc khảo, làm khóa luận...)...")
if hasattr(st.session_state, "pending_prompt") and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if prompt:
    # Use forced filter if clicked from sample queries
    active_filter = getattr(st.session_state, "force_filter", metadata_filter)
    if hasattr(st.session_state, "force_filter"):
        del st.session_state.force_filter

    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt, "sources": []})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Retrieval
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm thông tin trong cơ sở tri thức..."):
            if active_filter:
                retrieved_chunks = store.search_with_filter(prompt, top_k=top_k, metadata_filter=active_filter)
            else:
                retrieved_chunks = store.search(prompt, top_k=top_k)

        if not retrieved_chunks:
            reply_text = "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."
            st.markdown(reply_text)
            st.session_state.messages.append({"role": "assistant", "content": reply_text, "sources": []})
        else:
            # Build context blocks
            context_blocks = []
            for i, r in enumerate(retrieved_chunks, 1):
                src_file = r.get("metadata", {}).get("source_file", r.get("id", f"doc_{i}"))
                context_blocks.append(f"[{i}] (Nguồn: {src_file}):\n{r['content']}")

            context_str = "\n\n".join(context_blocks)
            filter_note = f"\n(Lưu ý: Đang áp dụng lọc đối tượng: {active_filter})" if active_filter else ""
            system_prompt = (
                "Bạn là một trợ lý hỏi đáp dựa trên cơ sở tri thức học vụ của trường đại học.\n"
                "Hãy trả lời câu hỏi DỰA DUY NHẤT TRÊN ngữ cảnh được cung cấp dưới đây một cách ngắn gọn, súc tích và chính xác.\n"
                "Chú ý đọc kỹ các điều kiện, tiêu chí và mốc thời gian cụ thể được nêu trong câu hỏi (ví dụ: mốc tính từ ngày thi đầu tiên của đợt thi vs ngày thi của môn học cụ thể).\n"
                "Nếu ngữ cảnh không có thông tin để trả lời, hãy nói rõ là không tìm thấy trong tài liệu, TUYỆT ĐỐI KHÔNG tự bịa đặt.\n\n"
                f"--- NGỮ CẢNH ---{filter_note}\n{context_str}\n\n"
                f"--- CÂU HỎI ---\n{prompt}\n\n"
                "--- CÂU TRẢ LỜI ---"
            )

            # Generate answer (with streaming if OpenAI client is present)
            if openai_client:
                stream = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": system_prompt}],
                    temperature=0.0,
                    stream=True,
                )
                answer = st.write_stream(stream)
            else:
                answer = (
                    "⚠️ [Chế độ Offline] Không có OpenAI API key.\n\n"
                    "Đoạn trích phù hợp nhất tìm thấy:\n"
                    + retrieved_chunks[0]["content"][:300]
                )
                st.markdown(answer)

            # Display source drawer
            if show_sources and retrieved_chunks:
                with st.expander(f"📚 Xem {len(retrieved_chunks)} nguồn trích dẫn được truy xuất"):
                    for idx, src in enumerate(retrieved_chunks, 1):
                        score = src.get("score", 0.0)
                        doc_id = src.get("metadata", {}).get("source_file", src.get("id", "doc"))
                        aud = src.get("metadata", {}).get("audience", "all")
                        dept = src.get("metadata", {}).get("department", "chưa rõ")
                        cat = src.get("metadata", {}).get("category", "chưa rõ")
                        snippet = src.get("content", "")
                        st.markdown(
                            f"""
                            <div class="source-card">
                                <div>
                                    <b>#{idx}</b> <span class="badge-source">{doc_id}</span>
                                    <span class="badge-score">Cosine: {score:.4f}</span>
                                    <span style="font-size: 0.8rem; color: #475569; margin-left: 8px;">
                                        👥 <i>{aud}</i> | 🏢 <i>{dept}</i> | 📑 <i>{cat}</i>
                                    </span>
                                </div>
                                <div style="margin-top: 6px; font-size: 0.92rem; color: #1e293b; white-space: pre-wrap;">{snippet}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )


            # Save assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": retrieved_chunks,
            })
