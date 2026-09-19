from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import (
    FixedSizeChunker,
    HeadingChunker,
    RecursiveChunker,
    SentenceChunker,
    strip_frontmatter,
)
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GeminiEmbedder,
    LocalEmbedder,
    MockEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

# 5 Benchmark queries from data/BENCHMARK.md with multi-attribute metadata
BENCHMARK_QUERIES = [
    {
        "id": 1,
        "type": "Hỏi quy trình & Lọc đối tượng",
        "query": "Khi sinh viên xin hoãn thi giữa kỳ, hồ sơ cần được xử lý như thế nào?",
        "gold_answer": "Sinh viên có lý do chính đáng không thể dự thi giữa kỳ phải nộp đơn kèm minh chứng cho Phòng Đào tạo Đại học trong vòng 03 ngày kể từ ngày thi.",
        "expected_docs": ["quy-che-dao-tao-chinh-quy"],
        "filter": {"audience": "student"},
        "keywords": ["03 ngày", "3 ngày", "nộp đơn"],
    },
    {
        "id": 2,
        "type": "Tra cứu thẩm quyền/bộ phận",
        "query": "Bộ phận nào của Trường sẽ xem xét các trường hợp có lí do chính đáng để vắng thi giữa kỳ?",
        "gold_answer": "P.ĐTĐH",
        "expected_docs": ["quy-dinh-to-chuc-thi", "quy-che-dao-tao-chinh-quy", "quy-dinh-tieu-chuan-giang-vien"],
        "filter": {},
        "keywords": ["p.đtđh", "phòng đào tạo đại học"],
    },
    {
        "id": 3,
        "type": "Tra số liệu thời hạn",
        "query": "Thời hạn lưu trữ đề thi các môn học hệ đại học chính quy của Trường là bao lâu?",
        "gold_answer": "9 năm",
        "expected_docs": ["quy-dinh-khoa-luan-tot-nghiep", "quy-dinh-to-chuc-thi", "quy-dinh-tieu-chuan-giang-vien"],
        "filter": {},
        "keywords": ["9 năm"],
    },
    {
        "id": 4,
        "type": "Liệt kê hình thức",
        "query": "Sinh viên thuộc chương trình tài năng có các hình thức nào?",
        "gold_answer": "chính thức và dự bị",
        "expected_docs": ["quy-trinh-phan-cong-can-bo-coi-thi", "quy-dinh-tieu-chuan-giang-vien", "quy-che-dao-tao-chinh-quy", "quy-dinh-to-chuc-thi"],
        "filter": {},
        "keywords": ["chính thức và dự bị"],
    },
    {
        "id": 5,
        "type": "Tra cứu thuật ngữ/tên gọi",
        "query": "Trong các thành phần điểm của điểm môn học thì điểm giữa kỳ có tên gọi khác là gì?",
        "gold_answer": "điểm thi giữa học phần",
        "expected_docs": ["quy-dinh-khoa-luan-tot-nghiep", "quy-che-dao-tao-chinh-quy", "quy-dinh-day-hoc-truc-tuyen"],
        "filter": {},
        "keywords": ["điểm thi giữa học phần"],
    },
]


def load_corpus_documents(
    data_dir: Path = Path("data/university"),
    chunker=None,
) -> list[Document]:
    """
    Read each .md file, parse YAML frontmatter into metadata,
    chunk the markdown body, and wrap each chunk as a Document.
    """
    if chunker is None:
        chunker = RecursiveChunker(chunk_size=500)

    documents: list[Document] = []
    md_files = sorted(data_dir.glob("*.md"))

    for p in md_files:
        if p.name in ("BENCHMARK.md", "MANIFEST.md"):
            continue
        raw_text = p.read_text(encoding="utf-8")
        stem = p.stem

        # Extract frontmatter
        frontmatter = {}
        content = raw_text
        if raw_text.startswith("---"):
            parts = raw_text.split("---", 2)
            if len(parts) >= 3:
                fm_text = parts[1]
                content = parts[2].strip()
                frontmatter = {
                    k.strip(): v.strip(' \t"\'')
                    for k, v in re.findall(r"^(\w+):\s*(.+)$", fm_text, re.M)
                }

        # Ensure doc_id is in metadata
        frontmatter["doc_id"] = stem
        frontmatter["source_file"] = p.name

        # Chunk the content
        chunks = chunker.chunk(content)
        for i, chunk_text in enumerate(chunks):
            chunk_doc = Document(
                id=f"{stem}#{i}",
                content=chunk_text,
                metadata={**frontmatter, "chunk_index": i},
            )
            documents.append(chunk_doc)

    return documents


import hashlib
import json


class CachedBatchOpenAIEmbedder:
    """OpenAI embedder with batch API calls and local disk caching to save cost & time."""

    def __init__(self) -> None:
        self.underlying = OpenAIEmbedder()
        self._cache_file = Path(".embedding_cache.json")
        self._cache: dict[str, list[float]] = {}
        if self._cache_file.exists():
            try:
                self._cache = json.loads(self._cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        self._backend_name = self.underlying._backend_name

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float] | None] = [None] * len(texts)
        missing_indices = []
        missing_texts = []

        for idx, t in enumerate(texts):
            h = hashlib.md5(t.encode("utf-8")).hexdigest()
            if h in self._cache:
                results[idx] = self._cache[h]
            else:
                missing_indices.append(idx)
                missing_texts.append(t)

        if missing_texts:
            print(f"Embedding {len(missing_texts)} new texts with OpenAI (batched)...")
            for i in range(0, len(missing_texts), 500):
                batch = missing_texts[i : i + 500]
                resp = self.underlying.client.embeddings.create(
                    model=self.underlying.model_name, input=batch
                )
                for j, item in enumerate(resp.data):
                    emb = [float(v) for v in item.embedding]
                    orig_idx = missing_indices[i + j]
                    results[orig_idx] = emb
                    h = hashlib.md5(batch[j].encode("utf-8")).hexdigest()
                    self._cache[h] = emb

            try:
                self._cache_file.write_text(json.dumps(self._cache), encoding="utf-8")
            except Exception:
                pass

        return results

    def __call__(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]


def get_embedder():
    """Select embedding backend based on .env or default to mock."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "").strip().lower()

    if provider == "openai" or os.getenv("OPENAI_API_KEY"):
        try:
            embedder = CachedBatchOpenAIEmbedder()
            print(f"[Embedder] Using OpenAI Cached Batch ({embedder._backend_name})")
            return embedder
        except Exception as e:
            print(f"[Embedder] OpenAI init failed ({e}), falling back to MockEmbedder")

    if provider == "gemini" or os.getenv("GEMINI_API_KEY"):
        try:
            embedder = GeminiEmbedder()
            print(f"[Embedder] Using Gemini ({embedder._backend_name})")
            return embedder
        except Exception as e:
            print(f"[Embedder] Gemini init failed ({e}), falling back to MockEmbedder")

    if provider == "local":
        try:
            embedder = LocalEmbedder()
            print(f"[Embedder] Using Local SentenceTransformers ({embedder._backend_name})")
            return embedder
        except Exception as e:
            print(f"[Embedder] Local init failed ({e}), falling back to MockEmbedder")

    print("[Embedder] Using MockEmbedder fallback")
    return _mock_embed


def run_benchmark(strategy_name: str = "recursive", chunker=None, output_file: str | None = None) -> list[dict]:
    embedder = get_embedder()
    store = EmbeddingStore(collection_name="university_bench", embedding_fn=embedder)

    print(f"\nLoading documents using strategy: {strategy_name}...")
    docs = load_corpus_documents(chunker=chunker)
    print(f"Total chunks created: {len(docs)}")

    store.add_documents(docs)
    print(f"Loaded {store.get_collection_size()} records into EmbeddingStore.")

    lines = []
    lines.append(f"================================================================")
    lines.append(f"BENCHMARK RESULTS — Strategy: {strategy_name}")
    lines.append(f"Embedder: {getattr(embedder, '_backend_name', 'mock')}")
    lines.append(f"Total corpus chunks: {len(docs)}")
    lines.append(f"================================================================\n")

    results_summary = []
    for item in BENCHMARK_QUERIES:
        qid = item["id"]
        qtype = item["type"]
        query = item["query"]
        gold = item["gold_answer"]
        gold = item["gold_answer"]
        expected_docs = item.get("expected_docs", [item.get("expected_doc", "")])
        keywords = item.get("keywords", [])
        meta_filter = item["filter"]

        lines.append(f"--- [Query {qid}] ({qtype}) ---")
        lines.append(f"Câu hỏi: {query}")
        lines.append(f"Gold answer: {gold}")
        lines.append(f"File kỳ vọng: {', '.join(expected_docs)}")
        lines.append(f"Metadata filter: {meta_filter if meta_filter else 'None'}")

        # Search with or without filter
        top_results = store.search_with_filter(query, top_k=3, metadata_filter=meta_filter or None)
        
        hit = False
        hit_rank = -1
        lines.append(f"Top-3 retrieved chunks:")
        for rank, r in enumerate(top_results, 1):
            r_doc_id = r["metadata"].get("doc_id", "")
            r_score = r.get("score", 0.0)
            snippet = r["content"][:180].replace("\n", " ")
            has_kw = any(kw.lower() in r["content"].lower() for kw in keywords) if keywords else False
            is_match = (r_doc_id in expected_docs) or has_kw
            if is_match and not hit:
                hit = True
                hit_rank = rank
            match_marker = "✅ [MATCH]" if is_match else "  "
            lines.append(f"  {rank}. {match_marker} (Score: {r_score:.4f}) [{r_doc_id}] {snippet}...")

        # Generate Agent Answer with LLM if OpenAI client is present
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and top_results:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                context_str = "\n\n".join(
                    f"[{i}] ({c['metadata'].get('doc_id')}): {c['content']}"
                    for i, c in enumerate(top_results, 1)
                )
                prompt = (
                    "Bạn là một trợ lý hỏi đáp dựa trên cơ sở tri thức học vụ của trường đại học.\n"
                    "Hãy trả lời câu hỏi DỰA DUY NHẤT TRÊN ngữ cảnh được cung cấp dưới đây một cách ngắn gọn, súc tích và chính xác.\n\n"
                    f"--- NGỮ CẢNH ---\n{context_str}\n\n"
                    f"--- CÂU HỎI ---\n{query}\n\n"
                    "--- CÂU TRẢ LỜI ---"
                )
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                )
                agent_answer = resp.choices[0].message.content.strip()
                lines.append(f"🤖 AI Answer: {agent_answer}")
            except Exception as e:
                lines.append(f"🤖 AI Answer: (Lỗi: {e})")

        score_point = 2 if hit_rank == 1 else (1 if hit else 0)
        lines.append(f"-> Đánh giá: {'Đạt' if hit else 'Chưa trúng'} (Top-{hit_rank if hit else 'None'}, Điểm: {score_point}/2)\n")
        
        results_summary.append({
            "id": qid,
            "type": qtype,
            "hit": hit,
            "hit_rank": hit_rank,
            "score": score_point,
        })

    total_score = sum(r["score"] for r in results_summary)
    lines.append(f"================================================================")
    lines.append(f"TỔNG KẾT: {total_score}/10 điểm benchmark")
    lines.append(f"================================================================")

    output_text = "\n".join(lines)
    print(output_text)

    if output_file:
        Path(output_file).write_text(output_text, encoding="utf-8")
        print(f"\n-> Đã lưu kết quả vào: {output_file}")

    return results_summary


if __name__ == "__main__":
    import sys
    strat = sys.argv[1] if len(sys.argv) > 1 else "recursive"
    
    chunker = None
    if strat == "fixed":
        chunker = FixedSizeChunker(chunk_size=500, overlap=50)
    elif strat == "sentence":
        chunker = SentenceChunker(max_sentences_per_chunk=3)
    elif strat == "heading":
        chunker = HeadingChunker(chunk_size=500)
    else:
        chunker = RecursiveChunker(chunk_size=500)

    run_benchmark(strategy_name=strat, chunker=chunker, output_file="ket_qua_benchmark.txt")
