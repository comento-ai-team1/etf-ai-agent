from dart_api import find_etf_disclosure_titles


result = find_etf_disclosure_titles("KODEX 200")

print("상품:", result["etf_name"])
print("검색 기간:", result["start_date"], "~", result["end_date"])
print(
    "확인한 페이지:",
    result["scanned_pages"],
    "/",
    result["total_pages"],
)
print("검색 완료:", result["search_complete"])
print("제목 일치 후보:", len(result["matches"]))

for item in result["matches"]:
    print(item["date"], "|", item["title"])
    print(item["url"])