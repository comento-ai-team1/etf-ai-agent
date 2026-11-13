from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, urlparse


def valid_yyyymmdd(value):
    if not isinstance(value, str) or len(value) != 8 or not value.isdigit():
        return False

    try:
        datetime.strptime(value, "%Y%m%d")
        return True
    except ValueError:
        return False


def valid_positive_number(value):
    try:
        number = Decimal(str(value))
        return number.is_finite() and number > 0
    except (InvalidOperation, TypeError):
        return False


def validate_etf_data(data, expected_name):
    """ETF 시세 자료가 답변에 사용 가능한지 확인합니다."""
    if not isinstance(data, dict):
        return False, "시세 자료 형식 오류"

    if data.get("name") != expected_name:
        return False, "요청한 상품과 조회된 상품이 다름"

    if not data.get("code"):
        return False, "종목코드 누락"

    data_date = data.get("date")
    if not valid_yyyymmdd(data_date):
        return False, "자료 기준일 오류"

    if datetime.strptime(data_date, "%Y%m%d").date() > date.today():
        return False, "자료 기준일이 미래 날짜임"

    if not valid_positive_number(data.get("close")):
        return False, "종가 오류"

    if not valid_positive_number(data.get("nav")):
        return False, "NAV 오류"

    if not data.get("source"):
        return False, "출처 이름 누락"

    source_url = urlparse(str(data.get("source_url", "")))
    if source_url.scheme != "https" or source_url.hostname != "www.data.go.kr":
        return False, "출처 링크 오류"

    return True, "정상"


def validate_disclosure_result(result, expected_name):
    """DART 공시 목록의 제목·날짜·링크를 확인합니다."""
    if not isinstance(result, dict):
        return False, "공시 자료 형식 오류"

    if result.get("etf_name") != expected_name:
        return False, "요청한 상품과 공시 검색 상품이 다름"

    start_date = result.get("start_date")
    end_date = result.get("end_date")

    if not valid_yyyymmdd(start_date) or not valid_yyyymmdd(end_date):
        return False, "공시 검색 기간 오류"

    if start_date > end_date:
        return False, "공시 검색 시작일이 종료일보다 늦음"

    matches = result.get("matches")
    if not isinstance(matches, list):
        return False, "공시 목록 형식 오류"

    if not isinstance(result.get("search_complete"), bool):
        return False, "검색 완료 상태 오류"

    for item in matches:
        if not isinstance(item, dict):
            return False, "공시 항목 형식 오류"

        if not str(item.get("title", "")).strip():
            return False, "공시 제목 누락"

        filing_date = item.get("date")
        if not valid_yyyymmdd(filing_date):
            return False, "공시 날짜 오류"

        if not start_date <= filing_date <= end_date:
            return False, "공시 날짜가 검색 기간 밖에 있음"

        link = urlparse(str(item.get("url", "")))
        receipt_number = parse_qs(link.query).get("rcpNo", [""])[0]

        if (
            link.scheme != "https"
            or link.hostname != "dart.fss.or.kr"
            or not receipt_number.isdigit()
        ):
            return False, "DART 공시 링크 오류"

    return True, "정상"