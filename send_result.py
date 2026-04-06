import requests
import json
import argparse
import os

API_URL = "http://aitask.cbsmediahub.com/api_test_json.asp" 

def send_json_to_server(data, job_id):
    """메모리의 JSON 객체(dict)를 웹서버로 전송"""
    try:
        print(f"📡 서버로 전송 중... (Job ID: {job_id})")
        target_url = f"{API_URL}?jobid={job_id}"
        
        # json 파라미터로 dict를 넘기면 자동으로 직렬화하여 전송함
        response = requests.post(target_url, json=data, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ 전송 성공! (서버 응답: {response.json()})")
            return True
        else:
            print(f"❌ 전송 실패 (HTTP {response.status_code}): {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류 발생: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 알 수 없는 오류 발생: {str(e)}")
        return False

def send_file_to_server(file_path, job_id):
    """저장된 JSON 파일을 읽어서 서버로 전송 (CLI용)"""
    if not os.path.exists(file_path):
        print(f"❌ 오류: '{file_path}' 파일을 찾을 수 없습니다.")
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return send_json_to_server(data, job_id)
    except json.JSONDecodeError:
        print(f"❌ 오류: '{file_path}' 파일이 올바른 JSON 형식이 아닙니다.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="분석 결과 JSON을 웹 서버로 전송합니다.")
    parser.add_argument("--file", default="latest_result.json", help="전송할 JSON 파일 경로")
    parser.add_argument("--jobid", required=True, help="저장할 Job ID (필수)")
    args = parser.parse_args()
    send_file_to_server(args.file, args.jobid)