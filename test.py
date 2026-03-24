import os
from llama_cpp import Llama

# 1. 모델 경로 설정
MODEL_PATH = "models/Qwen3.5-9B-Q8_0.gguf"

if not os.path.exists(MODEL_PATH):
    print(f"파일을 찾을 수 없습니다.")
    print(f"'{MODEL_PATH}' 경로에 파일이 있는지, 파일명이 정확한지 확인해주세요.")
    exit(1)

print("loading {MODEL_PATH} on the GPU")

# 2. 모델 로드
llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=-1,
    n_ctx=2048,      # 모델이 한 번에 기억할 수 있는 최대 토큰 수
    verbose=True     # 실행 로그 출력 (터미널 로그 중 'BLAS = 1'이 뜨면 GPU 가속 성공)
)

print("\n model loaded\n")

# 3. 추론 (채팅 형식)
response = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "당신은 친절하고 똑똑한 어시스턴트입니다."},
        {"role": "user", "content": "자기소개를 15자 이내로 하십시오."}
    ],
    max_tokens=50,
    temperature=0.7
)

# 4. 결과 출력
print("=====================================")
print("응답:")
print(response["choices"][0]["message"]["content"])
print("=====================================")
print(f'prompt_tokens: {response["usage"]["prompt_tokens"]}')
print(f'completion_tokens: {response["usage"]["completion_tokens"]}')
print(f'total_tokens: {response["usage"]["total_tokens"]}')
