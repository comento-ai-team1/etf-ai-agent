import json


def route_question(question, client):
    response = client.responses.create(
        model="gpt-5.4-mini",
        instructions=(
            "너는 ETF 챗봇의 메인 오케스트레이터다. "
            "사용자에게 답하지 말고, 질문에 필요한 기능만 선택하라. "
            "etf_price는 지원 ETF의 종가, NAV, 기준일 질문에 사용한다. "
            "disclosure는 지원 ETF의 DART 공시 질문에 사용한다. "
            "faq는 ETF의 일반 개념과 용어 설명에 사용한다. "
            "unsupported는 특정 ETF 상품의 시세나 공시를 요청했지만 "
            "그 상품이 지원 ETF 목록에 없는 경우에 사용한다. "
            "clarify는 어떤 상품을 말하는지 알 수 없거나 "
            "무엇을 묻는지 불분명한 경우에만 사용한다. "
            "예를 들어 '달토끼 우주여행 ETF의 종가'는 unsupported이고, "
            "'ETF 가격 알려줘'는 clarify다. "
            "종가와 공시를 모두 요청하면 두 경로를 모두 선택한다. "
            "지원 ETF는 KODEX 200과 "
            "KODEX 인도Nifty미드캡100뿐이다. "
            "지원하지 않는 상품의 etf_name은 none으로 설정하라. "
            "자료 조회 결과나 수치를 만들어내지 마라."
        ),
        input=question,
        text={
            "format": {
                "type": "json_schema",
                "name": "etf_question_route",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "routes": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "etf_price",
                                    "disclosure",
                                    "faq",
                                    "unsupported",
                                    "clarify",
                                ],
                            },
                        },
                        "etf_name": {
                            "type": "string",
                            "enum": [
                                "KODEX 200",
                                "KODEX 인도Nifty미드캡100",
                                "none",
                            ],
                        },
                    },
                    "required": ["routes", "etf_name"],
                    "additionalProperties": False,
                },
            }
        },
        max_output_tokens=300,
        store=False,
    )

    if not response.output_text:
        raise RuntimeError("질문 분류 결과가 비어 있습니다.")

    result = json.loads(response.output_text)

    routes = list(dict.fromkeys(result["routes"]))
    etf_name = result["etf_name"]

    if not routes:
        routes = ["clarify"]

    if etf_name == "none" and any(
        route in routes for route in ["etf_price", "disclosure"]
    ):
        routes = ["clarify"]

    return {
        "routes": routes,
        "etf_name": etf_name,
    }