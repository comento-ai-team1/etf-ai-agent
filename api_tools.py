import json

from langchain_core.tools import tool

from dart_api import find_etf_disclosure_titles
from etf_api import get_latest_etf
from result_validator import (
    validate_disclosure_result,
    validate_etf_data,
)


@tool
def get_etf_price(etf_name: str) -> str:
    """
    ETF 상품의 최근 자료 기준일 종가와 NAV를
    금융위원회 공공데이터 API에서 조회한다.

    사용자가 특정 ETF의 종가, 가격, NAV 또는
    자료 기준일을 질문할 때 사용한다.

    반환되는 가격은 실시간 가격이 아니라
    공공데이터에 등록된 최근 기준일 가격이다.
    """

    etf_name = etf_name.strip()

    if not etf_name:
        return json.dumps(
            {
                "success": False,
                "message": "조회할 ETF 상품명이 없습니다.",
            },
            ensure_ascii=False,
        )

    try:
        data = get_latest_etf(etf_name)

    except RuntimeError as error:
        return json.dumps(
            {
                "success": False,
                "message": str(error),
            },
            ensure_ascii=False,
        )

    if data is None:
        return json.dumps(
            {
                "success": False,
                "message": (
                    f"'{etf_name}'의 시세 자료를 "
                    "공공데이터 API에서 찾지 못했습니다."
                ),
            },
            ensure_ascii=False,
        )

    valid, reason = validate_etf_data(
        data,
        etf_name,
    )

    if not valid:
        return json.dumps(
            {
                "success": False,
                "message": f"ETF 시세 검증 실패: {reason}",
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "success": True,
            "data": {
                "product_name": data.get("name"),
                "product_code": data.get("code"),
                "data_date": data.get("date"),
                "close_price": data.get("close"),
                "nav": data.get("nav"),
                "real_time": False,
                "source_name": data.get("source"),
                "source_url": data.get("source_url"),
            },
        },
        ensure_ascii=False,
    )


@tool
def search_etf_disclosure(etf_name: str) -> str:
    """
    특정 ETF 상품과 관련된 최근 DART 펀드공시 제목을 조회한다.

    사용자가 ETF의 공시, 투자설명서, 일괄신고서,
    기재정정 자료를 질문할 때 사용한다.

    현재 DART 공시 검색은 삼성자산운용의 KODEX 200과
    KODEX 인도Nifty미드캡100 상품을 지원한다.
    공시의 구체적인 변경 내용을 임의로 요약하지 않는다.
    """

    etf_name = etf_name.strip()

    if not etf_name:
        return json.dumps(
            {
                "success": False,
                "message": "조회할 ETF 상품명이 없습니다.",
            },
            ensure_ascii=False,
        )

    try:
        result = find_etf_disclosure_titles(etf_name)

    except ValueError:
        return json.dumps(
            {
                "success": False,
                "message": (
                    f"'{etf_name}'은 현재 DART 공시 검색 "
                    "지원 대상이 아닙니다. 현재 KODEX 200과 "
                    "KODEX 인도Nifty미드캡100을 지원합니다."
                ),
            },
            ensure_ascii=False,
        )

    except RuntimeError as error:
        return json.dumps(
            {
                "success": False,
                "message": str(error),
            },
            ensure_ascii=False,
        )

    valid, reason = validate_disclosure_result(
        result,
        etf_name,
    )

    if not valid:
        return json.dumps(
            {
                "success": False,
                "message": f"DART 공시 검증 실패: {reason}",
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "success": True,
            "etf_name": result.get("etf_name"),
            "search_period": {
                "start_date": result.get("start_date"),
                "end_date": result.get("end_date"),
            },
            "disclosures": result.get("matches", []),
            "notice": (
                "상품명이 제목에 일치하는 공시 후보입니다. "
                "구체적인 변경 내용은 공시 원문에서 확인해야 합니다."
            ),
            "source_name": "전자공시시스템 DART",
            "source_url": "https://dart.fss.or.kr/",
        },
        ensure_ascii=False,
    )


EXTERNAL_API_TOOLS = [
    get_etf_price,
    search_etf_disclosure,
]