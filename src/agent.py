from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Retrieve top-k relevant chunks from the store
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."

        # 2. Build prompt with numbered chunks as context
        context_blocks = []
        for i, r in enumerate(results, 1):
            source = r.get("metadata", {}).get("source", r.get("id", f"doc_{i}"))
            context_blocks.append(f"[{i}] (Nguồn: {source}):\n{r['content']}")

        context_str = "\n\n".join(context_blocks)
        prompt = (
            "Bạn là một trợ lý hỏi đáp dựa trên cơ sở tri thức.\n"
            "Hãy trả lời câu hỏi dưới đây DỰA TRÊN ngữ cảnh được cung cấp. "
            "Nếu ngữ cảnh không có thông tin, hãy nói rõ là không tìm thấy.\n\n"
            f"--- NGỮ CẢNH ---\n{context_str}\n\n"
            f"--- CÂU HỎI ---\n{question}\n\n"
            "--- CÂU TRẢ LỜI ---"
        )

        # 3. Call LLM to generate an answer
        return self.llm_fn(prompt)

