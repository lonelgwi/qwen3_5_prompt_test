import os
import time
from llama_cpp import Llama
from prompts import STT_SYSTEM_PROMPT, STT_INPUT_DATA, JOB_ID  # 프롬프트 파일 임포트 # 임포트 부분에 JOB_ID 추가

time1 = time.time()

# 1. 모델 경로 설정
MODEL_PATH = "models/Qwen3.5-9B-Q8_0.gguf"

if not os.path.exists(MODEL_PATH):
    print(f"파일을 찾을 수 없습니다.")
    print(f"'{MODEL_PATH}' 경로에 파일이 있는지, 파일명이 정확한지 확인해주세요.")
    exit(1)

print(f"loading {MODEL_PATH} on the GPU")

# 2. 모델 로드
llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=-1,
    n_ctx=60000,      # 모델이 한 번에 기억할 수 있는 최대 토큰 수
    verbose=False     # 실행 로그 출력 (터미널 로그 중 'BLAS = 1'이 뜨면 GPU 가속 성공)
)

time2 = time.time()

print("\n model loaded\n")

# 3. 추론 (채팅 형식)
response = llm.create_chat_completion(
messages=[
        {"role": "system", "content": STT_SYSTEM_PROMPT},
        {"role": "user", "content": f"다음 텍스트를 처리해줘: \n{STT_INPUT_DATA}"}
    ],
    max_tokens=10240,
    temperature=0.3 
)

time3 = time.time()

# 4. 결과 출력 부분 수정
print("=====================================")
print(f"작업 ID (Job ID): {JOB_ID}")  # 이 줄을 추가하세요
print(f"모델 로드: {time2-time1:2f}초")
print(f"추론: {time3-time2:2f}초")
print(f"총 소요시간: {time3-time1:2f}초")
print(f"입력 토큰: {response['usage']['prompt_tokens']}")
print(f"출력 토큰: {response['usage']['completion_tokens']}")
print(f"토큰 합계: {response['usage']['total_tokens']}")
print("-------------------------------------")
print("AI 분석 결과 (JSON):")
print(response["choices"][0]["message"]["content"])
print("=====================================")
