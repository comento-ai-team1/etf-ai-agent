import os
from datetime import date, timedelta
from urllib.parse import unquote

import requests
from dotenv import load_dotenv


ETF_API_URL = (
    "https://apis.data.go.kr/1160100/"
    "GetSecuritiesProductInfoService_V2/getETFPriceInfo_V2"
)


def get_latest_etf(name: str):
    load_dotenv()

    api_key = os.getenv("ETF_DATA_API_KEY")
    if not api_key:
        raise RuntimeError("ETF_DATA_API_KEY가 없습니다.")

    today = date.today()

    try:
        response = requests.get(
            ETF_API_URL,
            params={
                "serviceKey": unquote(api_key),
                "resultType": "json",
                "numOfRows": 40,
                "pageNo": 1,
                "itmsNm": name,
                "beginBasDt": (today - timedelta(days=30)).strftime("%Y%m%d"),
                "endBasDt": (today + timedelta(days=1)).strftime("%Y%m%d"),
            },
            timeout=20,
        )
    except requests.RequestException as error:
        raise RuntimeError(
            f"ETF API 연결 실패: {type(error).__name__}"
        ) from None

    if response.status_code != 200:
        raise RuntimeError(
            f"ETF API HTTP 오류: {response.status_code}"
        )

    try:
        data = response.json()
    except ValueError:
        raise RuntimeError("ETF API 응답이 JSON이 아닙니다.") from None

    if "OpenAPI_ServiceResponse" in data:
        error = data["OpenAPI_ServiceResponse"]["cmmMsgHeader"]
        raise RuntimeError(
            f"ETF API 오류 코드: {error.get('returnReasonCode')}"
        )

    body = data.get("response", {}).get("body", {})
    items = body.get("items") or {}
    rows = items.get("item", []) if isinstance(items, dict) else []

    if isinstance(rows, dict):
        rows = [rows]

    exact_rows = [
        row for row in rows
        if row.get("itmsNm") == name
    ]

    if not exact_rows:
        return None

    latest = max(
        exact_rows,
        key=lambda row: row.get("basDt", ""),
    )

    return {
        "name": latest.get("itmsNm"),
        "code": latest.get("srtnCd"),
        "date": latest.get("basDt"),
        "close": latest.get("clpr"),
        "nav": latest.get("nav"),
        "source": "금융위원회 증권상품시세정보",
        "source_url": "https://www.data.go.kr/data/15094806/openapi.do",
    }