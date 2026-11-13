import csv
import sqlite3
from pathlib import Path


# 프로젝트 경로
BASE_DIR = Path(__file__).resolve().parent

# 원본 CSV 경로
ETF_CSV_PATH = BASE_DIR / "data" / "source" / "etf_products.csv"
FAQ_CSV_PATH = BASE_DIR / "data" / "source" / "faq.csv"

# 생성할 SQLite DB
DB_PATH = BASE_DIR / "data" / "etf_chatbot.db"


def clean_text(value):
    """CSV의 빈 값과 공백을 정리합니다."""
    if value is None:
        return ""

    return str(value).strip()


def create_tables(cursor):
    """ETF와 FAQ 테이블을 생성합니다."""

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS etf_products (
            product_code TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            asset_manager TEXT,
            asset_category TEXT,
            underlying_index TEXT,
            total_fee_percent REAL,
            risk_grade TEXT,
            listing_date TEXT,
            top_holdings TEXT,
            holdings_date TEXT,
            source_name TEXT,
            source_url TEXT,
            source_date TEXT,
            verified_at TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS faq (
            faq_id TEXT PRIMARY KEY,
            category TEXT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            keywords TEXT,
            source_name TEXT,
            source_url TEXT,
            source_date TEXT,
            verified_at TEXT
        )
        """
    )

    # 검색 속도를 높이기 위한 인덱스
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_etf_product_name
        ON etf_products(product_name)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_faq_question
        ON faq(question)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_faq_category
        ON faq(category)
        """
    )


def load_etf_products(cursor):
    """ETF 상품 CSV를 DB에 저장합니다."""

    if not ETF_CSV_PATH.exists():
        print(f"ETF CSV 파일을 찾을 수 없습니다: {ETF_CSV_PATH}")
        return 0

    cursor.execute("DELETE FROM etf_products")

    saved_count = 0

    with open(
        ETF_CSV_PATH,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        required_columns = {
            "product_code",
            "product_name",
        }

        if not required_columns.issubset(reader.fieldnames or []):
            print("ETF CSV에 product_code와 product_name 열이 필요합니다.")
            return 0

        for row in reader:
            product_code = clean_text(row.get("product_code"))
            product_name = clean_text(row.get("product_name"))

            if not product_code or not product_name:
                continue

            total_fee = clean_text(
                row.get("total_fee_percent")
            )

            try:
                total_fee = float(total_fee) if total_fee else None
            except ValueError:
                total_fee = None

            cursor.execute(
                """
                INSERT OR REPLACE INTO etf_products (
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
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product_code,
                    product_name,
                    clean_text(row.get("asset_manager")),
                    clean_text(row.get("asset_category")),
                    clean_text(row.get("underlying_index")),
                    total_fee,
                    clean_text(row.get("risk_grade")),
                    clean_text(row.get("listing_date")),
                    clean_text(row.get("top_holdings")),
                    clean_text(row.get("holdings_date")),
                    clean_text(row.get("source_name")),
                    clean_text(row.get("source_url")),
                    clean_text(row.get("source_date")),
                    clean_text(row.get("verified_at")),
                ),
            )

            saved_count += 1

    return saved_count


def load_faq(cursor):
    """FAQ CSV를 DB에 저장합니다."""

    if not FAQ_CSV_PATH.exists():
        print(f"FAQ CSV 파일을 찾을 수 없습니다: {FAQ_CSV_PATH}")
        return 0

    cursor.execute("DELETE FROM faq")

    saved_count = 0

    with open(
        FAQ_CSV_PATH,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        required_columns = {
            "faq_id",
            "question",
            "answer",
        }

        if not required_columns.issubset(reader.fieldnames or []):
            print(
                "FAQ CSV에 faq_id, question, answer 열이 필요합니다."
            )
            return 0

        for row in reader:
            faq_id = clean_text(row.get("faq_id"))
            question = clean_text(row.get("question"))
            answer = clean_text(row.get("answer"))

            if not faq_id or not question or not answer:
                continue

            cursor.execute(
                """
                INSERT OR REPLACE INTO faq (
                    faq_id,
                    category,
                    question,
                    answer,
                    keywords,
                    source_name,
                    source_url,
                    source_date,
                    verified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    faq_id,
                    clean_text(row.get("category")),
                    question,
                    answer,
                    clean_text(row.get("keywords")),
                    clean_text(row.get("source_name")),
                    clean_text(row.get("source_url")),
                    clean_text(row.get("source_date")),
                    clean_text(row.get("verified_at")),
                ),
            )

            saved_count += 1

    return saved_count


def show_result(cursor, etf_count, faq_count):
    """저장 결과를 확인합니다."""

    cursor.execute("SELECT COUNT(*) FROM etf_products")
    saved_etf_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM faq")
    saved_faq_count = cursor.fetchone()[0]

    print("=" * 60)
    print("ETF 챗봇 DB 생성 완료")
    print(f"DB 위치: {DB_PATH}")
    print("-" * 60)
    print(f"ETF CSV 처리 건수: {etf_count}")
    print(f"ETF DB 저장 건수: {saved_etf_count}")
    print(f"FAQ CSV 처리 건수: {faq_count}")
    print(f"FAQ DB 저장 건수: {saved_faq_count}")
    print("=" * 60)

    print("\n[ETF 상품 예시]")

    cursor.execute(
        """
        SELECT product_code, product_name, asset_manager
        FROM etf_products
        ORDER BY product_name
        LIMIT 5
        """
    )

    for code, name, manager in cursor.fetchall():
        print(f"{code} | {name} | {manager}")

    print("\n[FAQ 예시]")

    cursor.execute(
        """
        SELECT faq_id, category, question
        FROM faq
        ORDER BY faq_id
        LIMIT 5
        """
    )

    for faq_id, category, question in cursor.fetchall():
        print(f"{faq_id} | {category} | {question}")


def build_database():
    """전체 DB 생성 과정입니다."""

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    try:
        create_tables(cursor)

        etf_count = load_etf_products(cursor)
        faq_count = load_faq(cursor)

        connection.commit()

        show_result(
            cursor,
            etf_count,
            faq_count
        )

    except Exception as error:
        connection.rollback()
        print(f"DB 생성 중 오류가 발생했습니다: {error}")

    finally:
        connection.close()


if __name__ == "__main__":
    build_database()