import os

from dotenv import load_dotenv
from openai import OpenAI

from orchestrator import route_question


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise SystemExit("OPENAI_API_KEY를 찾지 못했습니다.")

client = OpenAI(api_key=api_key)

questions = [
    "ETF와 주식은 어떻게 달라?",
    "KODEX 200의 최근 종가와 NAV를 알려줘",
    "KODEX 200의 종가와 관련 공시를 같이 알려줘",
]

for question in questions:
    result = route_question(question, client)
    print("질문:", question)
    print("분류:", result)
    print()