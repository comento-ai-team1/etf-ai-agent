import shutil
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent

SUBMISSION_ROOT = PROJECT_DIR / "submission"
FOLDER_NAME = "2주차_프로토타입_조병관"

PACKAGE_DIR = SUBMISSION_ROOT / FOLDER_NAME
ZIP_PATH = SUBMISSION_ROOT / f"{FOLDER_NAME}.zip"


FILES_TO_INCLUDE = [
    "app.py",
    "langchain_agent.py",
    "agent_tools.py",
    "api_tools.py",
    "etf_api.py",
    "dart_api.py",
    "result_validator.py",
    "build_database.py",
    "requirements.txt",
    "README.md",
    ".env.example",
    ".streamlit/config.toml",
    "data/etf_chatbot.db",
    "data/source/etf_products.csv",
    "data/source/faq.csv",
]


def make_submission():
    SUBMISSION_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    copied_files = []
    missing_files = []

    for relative_path in FILES_TO_INCLUDE:
        source_path = PROJECT_DIR / relative_path
        destination_path = PACKAGE_DIR / relative_path

        if not source_path.exists():
            missing_files.append(relative_path)
            continue

        destination_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source_path,
            destination_path,
        )

        copied_files.append(relative_path)

    shutil.make_archive(
        base_name=str(
            SUBMISSION_ROOT / FOLDER_NAME
        ),
        format="zip",
        root_dir=SUBMISSION_ROOT,
        base_dir=FOLDER_NAME,
    )

    print("=" * 60)
    print("과제 제출 ZIP 생성 완료")
    print(f"ZIP 파일: {ZIP_PATH}")
    print(f"포함된 파일: {len(copied_files)}개")
    print("=" * 60)

    for file_name in copied_files:
        print(f"[포함] {file_name}")

    if missing_files:
        print("\n누락된 파일")

        for file_name in missing_files:
            print(f"[없음] {file_name}")

    print("\n보안상 제외한 항목")
    print("- 실제 .env와 API 키")
    print("- .venv 가상환경")
    print("- __pycache__와 pyc 파일")
    print("- 응답 로그")
    print("- Git 내부 파일")


if __name__ == "__main__":
    make_submission()