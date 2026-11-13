import os
from datetime import date, timedelta
from io import BytesIO
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv


DART_LIST_URL = "https://opendart.fss.or.kr/api/list.json"
DART_CORP_CODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"
ISSUER_NAME = "삼성자산운용"

SUPPORTED_ETFS = {
    "KODEX 200",
    "KODEX 인도Nifty미드캡100",
}


def get_api_key():
    load_dotenv()

    api_key = os.getenv("DART_API_KEY")
    if not api_key:
        raise RuntimeError("DART_API_KEY가 없습니다.")

    return api_key


def normalize_name(text):
    """띄어쓰기와 특수문자를 빼고 상품명을 비교합니다."""
    return "".join(
        character
        for character in text.upper()
        if character.isalnum()
    )


def title_matches_etf(title, etf_name):
    title_key = normalize_name(title)
    etf_key = normalize_name(etf_name)

    if etf_key not in title_key:
        return False

    # KODEX 200타겟 등 다른 상품을 KODEX 200으로
    # 잘못 표시하지 않도록 보수적으로 확인합니다.
    if etf_key == "KODEX200":
        following = title_key.split(etf_key, 1)[1]

        return (
            not following
            or following.startswith("증권")
            or following.startswith("상장지수")
            or following.startswith("ETF")
        )

    return True


def find_issuer_corp_code(api_key):
    try:
        response = requests.get(
            DART_CORP_CODE_URL,
            params={"crtfc_key": api_key},
            timeout=30,
        )
        response.raise_for_status()

        with ZipFile(BytesIO(response.content)) as archive:
            xml_name = next(
                name
                for name in archive.namelist()
                if name.lower().endswith(".xml")
            )
            root = ET.fromstring(archive.read(xml_name))

    except (requests.RequestException, BadZipFile, StopIteration, ET.ParseError) as error:
        raise RuntimeError(
            f"DART 회사 고유번호 조회 실패: {type(error).__name__}"
        ) from None

    for company in root.findall("list"):
        if company.findtext("corp_name") == ISSUER_NAME:
            corp_code = company.findtext("corp_code")

            if corp_code:
                return corp_code

    raise RuntimeError(
        f"DART에서 {ISSUER_NAME}의 회사 고유번호를 찾지 못했습니다."
    )


def find_etf_disclosure_titles(etf_name, max_pages=10, limit=3):
    """
    최근 90일 삼성자산운용의 펀드공시 제목 중
    ETF 상품명이 일치하는 공시 후보를 찾습니다.
    """
    if etf_name not in SUPPORTED_ETFS:
        raise ValueError("현재 지원하지 않는 ETF 상품입니다.")

    api_key = get_api_key()
    corp_code = find_issuer_corp_code(api_key)

    today = date.today()
    start = today - timedelta(days=89)

    matches = []
    total_pages = 0
    scanned_pages = 0

    for page_no in range(1, max_pages + 1):
        try:
            response = requests.get(
                DART_LIST_URL,
                params={
                    "crtfc_key": api_key,
                    "corp_code": corp_code,
                    "bgn_de": start.strftime("%Y%m%d"),
                    "end_de": today.strftime("%Y%m%d"),
                    "pblntf_ty": "G",
                    "sort": "date",
                    "sort_mth": "desc",
                    "page_no": page_no,
                    "page_count": 100,
                },
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()

        except requests.RequestException as error:
            raise RuntimeError(
                f"DART 공시 조회 실패: {type(error).__name__}"
            ) from None
        except ValueError:
            raise RuntimeError(
                "DART 공시 응답을 읽지 못했습니다."
            ) from None

        status = data.get("status")

        if status == "013":
            break

        if status != "000":
            raise RuntimeError(
                f"DART 조회 오류: {status} {data.get('message', '')}"
            )

        scanned_pages += 1
        total_pages = int(data.get("total_page") or 0)

        for item in data.get("list", []):
            title = item.get("report_nm", "")

            if not title_matches_etf(title, etf_name):
                continue

            receipt_no = item.get("rcept_no", "")

            matches.append({
                "date": item.get("rcept_dt", ""),
                "company": item.get("corp_name", ""),
                "title": title,
                "url": (
                    "https://dart.fss.or.kr/dsaf001/main.do"
                    f"?rcpNo={receipt_no}"
                ),
            })

            if len(matches) >= limit:
                break

        if len(matches) >= limit or page_no >= total_pages:
            break

    return {
        "etf_name": etf_name,
        "matches": matches,
        "start_date": start.strftime("%Y%m%d"),
        "end_date": today.strftime("%Y%m%d"),
        "scanned_pages": scanned_pages,
        "total_pages": total_pages,
        "search_complete": scanned_pages >= total_pages,
    }