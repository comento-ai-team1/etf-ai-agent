import os
from datetime import date, timedelta

import requests
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv("DART_API_KEY")

if not api_key:
    raise SystemExit("DART_API_KEY를 찾지 못했습니다.")

today = date.today()
start = today - timedelta(days=30)

try:
    response = requests.get(
        "https://opendart.fss.or.kr/api/list.json",
        params={
            "crtfc_key": api_key,
            "bgn_de": start.strftime("%Y%m%d"),
            "end_de": today.strftime("%Y%m%d"),
            "page_count": 3,
        },
        timeout=15,
    )

    print("HTTP 상태:", response.status_code)

    if response.status_code != 200:
        raise SystemExit("DART 서버 응답을 확인해야 합니다.")

    data = response.json()
    print("DART 상태:", data.get("status"), data.get("message"))

    for item in data.get("list", []):
        print(item["rcept_dt"], item["corp_name"], item["report_nm"])

except requests.RequestException as error:
    print("연결 오류:", type(error).__name__)