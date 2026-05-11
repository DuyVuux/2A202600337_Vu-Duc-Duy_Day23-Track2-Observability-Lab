"""
BONUS-llm-native-obs — LangChain → self-hosted Langfuse trace.

Before running:
  1. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY (from http://localhost:3001)
  2. pip install "langfuse>=3.0" "langchain>=0.2" langchain-community
"""
import os
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

# Force local host if not set
os.environ["LANGFUSE_HOST"] = os.getenv("LANGFUSE_HOST", "http://localhost:3001")

from langchain_core.prompts import PromptTemplate
from langchain_community.llms.fake import FakeListLLM
# Langfuse v2.x requires this import:
from langfuse.callback import CallbackHandler

PUBLIC_KEY  = os.getenv("LANGFUSE_PUBLIC_KEY",  "pk-lf-REPLACE_ME")
SECRET_KEY  = os.getenv("LANGFUSE_SECRET_KEY",  "sk-lf-REPLACE_ME")
HOST        = os.getenv("LANGFUSE_HOST",         "http://localhost:3001")

# Initialize Langfuse Handler
langfuse_handler = CallbackHandler(
    public_key=PUBLIC_KEY,
    secret_key=SECRET_KEY,
    host=HOST,
    trace_name="day23-llm-trace",
)

# Mock LLM for local testing
mock_llm = FakeListLLM(responses=[
    "SLO burn-rate alerting measures how fast you are consuming your error budget. "
    "A fast burn (>14.4x) pages immediately; a slow burn (>6x) pages within hours.",
    "Cardinality is the number of unique label combinations in Prometheus. "
    "High-cardinality labels like user_id create millions of time series and crash Prometheus.",
    "Observability answers: what is my system doing right now, and why?",
])

# Create prompt and chain using LCEL
prompt = PromptTemplate.from_template("You are an SRE assistant. Answer concisely.\n\nQuestion: {question}\n\nAnswer:")
chain = prompt | mock_llm

QUESTIONS = [
    "What is SLO burn-rate alerting?",
    "What is Prometheus cardinality?",
    "What does observability mean in one sentence?",
]

print(f"Sending {len(QUESTIONS)} traces to {HOST} ...")
for q in QUESTIONS:
    result = chain.invoke(
        {"question": q},
        config={"callbacks": [langfuse_handler]}
    )
    print(f"\nQ: {q}\nA: {result}")

langfuse_handler.auth_check()
langfuse_handler.langfuse.flush()
print(f"\n✅ Done — open {HOST}/traces to see your traces.")