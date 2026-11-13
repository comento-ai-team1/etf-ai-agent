from langchain_agent import run_etf_agent


test_questions = [
    "KODEX 200의 최근 종가와 NAV를 알려줘",
    "KODEX 200의 관련 공시를 알려줘",
    "KODEX 200의 종가와 관련 공시를 같이 알려줘",
]


for number, question in enumerate(test_questions, start=1):
    print("=" * 70)
    print(f"{number}. 사용자 질문")
    print(question)

    result = run_etf_agent(question)

    print("\n사용한 도구")
    print(result["used_tools"])

    print("\n최종 답변")
    print(result["answer"])

    print()