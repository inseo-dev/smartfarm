import base64
import requests
from PIL import Image
from io import BytesIO
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


def download_and_resize_image(image_url, output_path, size=(256,256)):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img_resized = img.resize(size)
    img_resized.save(output_path)


def create_prompt():
    prompt = """
너는 스마트팜을 관리하는 식물학 전문가 AI이다.

첨부된 이미지와 현재 환경 데이터를 기반으로 다음 정보를 반환하라:
이미지는 현재 식물 사진이고, 생장 단계도 고려해서 재배 환경 결과를 알려줘

현재 환경:
- 온도: 22.5°C
- 습도: 55%
- 조도: 8000 lux
- 일조 시간: 12시간
- 토양 습도: 35%

# 답변할 양식

1. 식물 정보
   - 이름 (한국어, 영어명 모두)
   - 생장 단계 (한국어 단계명 + 영어 단계명 + 설명 bullet point)
   - 발육 상태 (색상, 형태, 병충해, 결구 진행 상태)

2. 권장 재배 환경
   - 온도 (°C)
   - 습도 (%)
   - 일조 시간 (시간)
   - 조도 (lux)
   - 토양 습도 (%)

먼저 일반 설명 형태로 요약하고,
그 다음 반드시 JSON 형태로 권장 재배환경 내용을 반환하라.
5가지 속성을 키로 넣어서 반환"""

    return prompt


def analyze_plant_image(image_path, prompt_text):
    model = ChatOpenAI(model="gpt-4o")

    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": prompt_text
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                },
            },
        ]
    )

    response = model.invoke([message])
    return response.content


if __name__ == "__main__":
    image_url = "https://onlyhydroponics.in/cdn/shop/products/LettuceButterhead.jpg?v=1683217664&width=1946"

    resized_image = "lettuce_256.jpg"
    download_and_resize_image(image_url, resized_image, size=(256,256))

    prompt = create_prompt()
    result = analyze_plant_image(resized_image, prompt)

    print("AI 분석 결과:\n")

    
    sentences = result.split(". ")

    for sentence in sentences:
        print(sentence.strip() + ".\n")
