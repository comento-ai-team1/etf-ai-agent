import json
import re
import sqlite3
from pathlib import Path

from langchain_core.tools import tool


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "etf_chatbot.db"


def get_database_connection():
    """SQLite DB에 연결합니다."""

    if not DB_PATH.exists():
        raise RuntimeError(
            "ETF 챗봇 DB를 찾을 수 없습니다. "
            "먼저 build_database.py를 실행해 주세요."
        )

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def remove_empty_values(data):
    """조회 결과에서 비어 있는 값을 제외합니다."""

    return {
        key: value
        for key, value in data.items()
        if value not in (None, "")
    }


@tool
def search_etf_product(search_term: str) -> str:
    """
    ETF 상품명 또는 6자리 종목코드로 ETF 상품 DB를 검색한다.

    상품의 운용사, 자산 유형, 기초지수, 총보수, 위험등급,
    상장일, 구성종목과 자료 출처가 필요할 때 사용한다.

    실시간 가격이나 종가, NAV 조회에는 사용하지 않는다.
    """

    search_term = search_term.strip()

    if not search_term:
        return json.dumps(
            {
                "success": False,
                "message": "검색할 ETF 상품명이나 종목코드가 없습니다.",
                "results": [],
            },
            ensure_ascii=False,
        )

    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                product_code,
                product_name,
                asset_manager,
                asset_category,
                underlying_index,
                total_fee_percent,
                risk_grade,
                listing_date,
                top_holdings,
                holdings_date,
                source_name,
                source_url,
                source_date,
                verified_at
            FROM etf_products
            WHERE
                product_code = ?
                OR product_name = ?
                OR product_name LIKE ?
            ORDER BY
                CASE
                    WHEN product_code = ? THEN 1
                    WHEN product_name = ? THEN 2
                    ELSE 3
                END,
                product_name
            LIMIT 5
            """,
            (
                search_term,
                search_term,
                f"%{search_term}%",
                search_term,
                search_term,
            ),
        )

        rows = cursor.fetchall()

        results = [
            remove_empty_values(dict(row))
            for row in rows
        ]

        if not results:
            return json.dumps(
                {
                    "success": False,
                    "message": (
                        f"'{search_term}'과 일치하는 ETF 상품을 "
                        "DB에서 찾지 못했습니다."
                    ),
                    "results": [],
                },
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "success": True,
                "message": f"{len(results)}개 상품을 찾았습니다.",
                "results": results,
            },
            ensure_ascii=False,
        )

    finally:
        connection.close()


def tokenize_question(text):
    """FAQ 검색을 위해 질문을 간단한 단어로 분리합니다."""

    tokens = re.findall(
        r"[가-힣A-Za-z0-9]+",
        text.lower(),
    )

    stop_words = {
        "etf",
        "무엇인가요",
        "무엇",
        "뭐야",
        "뭔가요",
        "어떻게",
        "알려줘",
        "알려주세요",
        "설명해줘",
        "설명해주세요",
        "궁금해",
        "질문",
    }

    return [
        token
        for token in tokens
        if len(token) >= 2
        and token not in stop_words
    ]


@tool
def search_faq(user_question: str) -> str:
    """
    ETF 기본 개념, 거래 방법, 가격정보, 비용, 분배금,
    구성종목, 투자위험에 관한 질문을 FAQ DB에서 검색한다.

    종가, NAV 수치나 특정 상품의 실시간 정보가 아니라
    ETF 일반 지식과 금융 용어 설명이 필요할 때 사용한다.
    """

    user_question = user_question.strip()

    if not user_question:
        return json.dumps(
            {
                "success": False,
                "message": "검색할 질문이 없습니다.",
                "results": [],
            },
            ensure_ascii=False,
        )

    query_tokens = tokenize_question(user_question)

    connection = get_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                faq_id,
                category,
                question,
                answer,
                keywords,
                source_name,
                source_url,
                source_date,
                verified_at
            FROM faq
            """
        )

        rows = cursor.fetchall()
        scored_results = []

        for row in rows:
            faq_data = dict(row)

            searchable_text = " ".join(
                [
                    str(faq_data.get("category") or ""),
                    str(faq_data.get("question") or ""),
                    str(faq_data.get("keywords") or ""),
                ]
            ).lower()

            score = 0

            # 사용자 질문 전체가 FAQ 질문과 가까운 경우
            if user_question.lower() in str(
                faq_data.get("question") or ""
            ).lower():
                score += 10

            # 질문에 포함된 단어가 FAQ 내용에 있는지 확인
            for token in query_tokens:
                if token in searchable_text:
                    score += 2

            if score > 0:
                result = remove_empty_values(faq_data)
                result["match_score"] = score
                scored_results.append(result)

        scored_results.sort(
            key=lambda item: item["match_score"],
            reverse=True,
        )

        results = scored_results[:3]

        if not results:
            return json.dumps(
                {
                    "success": False,
                    "message": (
                        "관련 FAQ를 찾지 못했습니다. "
                        "질문을 조금 더 구체적으로 입력해 주세요."
                    ),
                    "results": [],
                },
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "success": True,
                "message": f"{len(results)}개의 관련 FAQ를 찾았습니다.",
                "results": results,
            },
            ensure_ascii=False,
        )

    finally:
        connection.close()


ETF_AGENT_TOOLS = [
    search_etf_product,
    search_faq,
]