from agent_tools import search_etf_product, search_faq


print("=" * 60)
print("1. ETF 상품 DB 검색")
print("=" * 60)

etf_result = search_etf_product.invoke(
    {
        "search_term": "TIGER 미국S&P500"
    }
)

print(etf_result)


print("\n" + "=" * 60)
print("2. ETF FAQ 검색")
print("=" * 60)

faq_result = search_faq.invoke(
    {
        "user_question": "ETF와 주식은 어떻게 달라?"
    }
)

print(faq_result)