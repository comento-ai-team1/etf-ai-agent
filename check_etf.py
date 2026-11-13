import os
from datetime import date, timedelta
from urllib.parse import unquote

import requests
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("ETF_DATA_API_KEY")
if not api_key:
    raise SystemExit(".env에서 ETF_DATA_API_KEY를 찾지 못했습니다.")

target_name = "KODEX 인도Nifty미드캡100"
today = date.today()

url = (
    "https://apis.data.go.kr/1160100/"
    "GetSecuritiesProductInfoService_V2/getETFPriceInfo_V2"
)

try:
    response = requests.get(
        url,
        params={
            "serviceKey": unquote(api_key),
            "resultType": "json",
            "numOfRows": 20,
            "pageNo": 1,
            "itmsNm": target_name,
            "beginBasDt": (today - timedelta(days=14)).strftime("%Y%m%d"),
            "endBasDt": (today + timedelta(days=1)).strftime("%Y%m%d"),
        },
        timeout=20,
    )

    print("HTTP 상태:", response.status_code)
    data = response.json()

    if "OpenAPI_ServiceResponse" in data:
        error = data["OpenAPI_ServiceResponse"]["cmmMsgHeader"]
        print("API 오류 코드:", error.get("returnReasonCode"))
        print("API 오류 내용:", error.get("returnAuthMsg"))
        raise SystemExit

    result = data.get("response", {})
    header = result.get("header", {})
    body = result.get("body", {})

    print("API 결과:", header.get("resultMsg"))
    print("검색 건수:", body.get("totalCount"))

    items = body.get("items") or {}
    rows = items.get("item", []) if isinstance(items, dict) else []

    if isinstance(rows, dict):
        rows = [rows]

    rows = [
        row for row in rows
        if row.get("itmsNm") == target_name
    ]
    rows.sort(key=lambda row: row.get("basDt", ""), reverse=True)

    if not rows:
        print("최근 14일 안에 해당 ETF의 조회 결과가 없습니다.")
    else:
        for row in rows[:3]:
            print(
                "기준일:", row.get("basDt"),
                "| 종목:", row.get("itmsNm"),
                "| 종목코드:", row.get("srtnCd"),
                "| 종가:", row.get("clpr"),
                "| NAV:", row.get("nav"),
            )

except requests.RequestException as error:
    print("연결 오류:", type(error).__name__)
except ValueError:
    print("서버 응답을 JSON으로 읽지 못했습니다.")