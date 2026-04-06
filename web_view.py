import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse


HTML_PAGE = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI 추출 결과 뷰어</title>
  <style>
    :root {
      --bg: #f4f6f8;
      --card: #ffffff;
      --border: #dfe3e8;
      --text: #2f3a4a;
      --muted: #6b778c;
      --chip: #e9edf3;
      --chip-text: #223047;
      --primary: #2f6fed;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", "Malgun Gothic", sans-serif;
    }

    .container {
      max-width: 1100px;
      margin: 18px auto;
      padding: 0 12px;
    }

    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px;
      margin-bottom: 12px;
      box-shadow: 0 1px 1px rgba(15, 23, 42, 0.02);
    }

    .card-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
    }

    .title {
      margin: 0;
      font-size: 30px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }

    .section-title {
      margin: 0;
      font-size: 18px;
      font-weight: 700;
    }

    .small-note {
      font-size: 13px;
      color: var(--muted);
    }

    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .chip {
      background: var(--chip);
      color: var(--chip-text);
      border-radius: 999px;
      padding: 8px 14px;
      font-size: 16px;
      line-height: 1.2;
    }

    .overview-box {
      border: 1px solid var(--border);
      border-radius: 8px;
      min-height: 96px;
      padding: 14px;
      background: #fbfcfe;
      font-size: 19px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: keep-all;
    }

    .controls {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .btn {
      border: 1px solid var(--border);
      border-radius: 8px;
      background: #fff;
      color: var(--text);
      padding: 6px 10px;
      font-size: 13px;
      cursor: pointer;
    }

    .btn:hover {
      border-color: #c8d0dc;
    }

    .re-list {
      border-top: 1px solid var(--border);
    }

    .node {
      border-bottom: 1px solid #ebeff5;
      padding: 0;
    }

    .row {
      display: grid;
      grid-template-columns: auto 1fr auto;
      align-items: center;
      gap: 10px;
      min-height: 52px;
      padding-right: 8px;
    }

    .left {
      display: flex;
      align-items: center;
      gap: 6px;
      min-width: 0;
    }

    .toggle {
      width: 26px;
      height: 26px;
      border: none;
      border-radius: 6px;
      background: transparent;
      color: #4d5b70;
      font-size: 14px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    .toggle:hover { background: #f0f3f8; }
    .toggle-placeholder { width: 26px; height: 26px; display: inline-block; }

    .index {
      min-width: 48px;
      color: #7d8ba0;
      font-weight: 700;
      font-size: 15px;
    }

    .content {
      min-width: 0;
      font-size: 34px;
      line-height: 1.3;
      font-weight: 700;
      letter-spacing: -0.02em;
      padding: 8px 0;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .timestamp {
      color: #5f6f87;
      font-size: 32px;
      font-variant-numeric: tabular-nums;
      letter-spacing: 0.01em;
    }

    .children {
      margin-left: 30px;
      border-left: 2px solid #edf1f7;
    }

    .depth-2 .content { font-size: 28px; font-weight: 600; }
    .depth-2 .timestamp { font-size: 26px; }
    .depth-3 .content { font-size: 23px; font-weight: 500; }
    .depth-3 .timestamp { font-size: 22px; }
    .depth-4 .content,
    .depth-5 .content { font-size: 19px; font-weight: 500; }
    .depth-4 .timestamp,
    .depth-5 .timestamp { font-size: 18px; }

    .error {
      color: #c53030;
      font-size: 14px;
      white-space: pre-wrap;
      margin-top: 10px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1 class="title">AI 분석 결과</h1>

    <section class="card">
      <div class="card-head">
        <h2 class="section-title">AI 추출 키워드</h2>
        <span class="small-note" id="keyword-count">0개</span>
      </div>
      <div class="chips" id="keywords"></div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2 class="section-title">AI 요약</h2>
      </div>
      <div class="overview-box" id="overview"></div>
    </section>

    <section class="card">
      <div class="card-head">
        <h2 class="section-title">Reconstruction (depth 1 보기)</h2>
        <div class="controls">
          <button class="btn" id="collapse-all">모두 접기</button>
          <button class="btn" id="expand-depth1">depth 1만 펼치기</button>
        </div>
      </div>
      <div class="re-list" id="reconstruction"></div>
      <div class="error" id="error"></div>
    </section>
  </div>

  <script>
    let reconstructionData = [];
    const expanded = new Set();

    function pad2(num) {
      return String(num).padStart(2, "0");
    }

    function formatTime(sec) {
      const n = Number(sec);
      if (!Number.isFinite(n) || n < 0) return "--:--:--";
      const s = Math.floor(n);
      const h = Math.floor(s / 3600);
      const m = Math.floor((s % 3600) / 60);
      const r = s % 60;
      return `${pad2(h)}:${pad2(m)}:${pad2(r)}`;
    }

    function getNodeKey(node, depth, localIndex) {
      if (node && node.index !== undefined && node.index !== null) {
        return String(node.index);
      }
      return `${depth}_${localIndex}`;
    }

    function renderNodes(nodes, depth = 1) {
      const wrapper = document.createElement("div");
      nodes.forEach((node, idx) => {
        const key = getNodeKey(node, depth, idx);
        const children = Array.isArray(node.subitems) ? node.subitems : [];
        const hasChildren = children.length > 0;
        const isOpen = expanded.has(key);

        const nodeEl = document.createElement("div");
        nodeEl.className = `node depth-${Math.min(depth, 5)}`;

        const row = document.createElement("div");
        row.className = "row";
        row.style.paddingLeft = `${Math.max(0, depth - 1) * 14}px`;

        const left = document.createElement("div");
        left.className = "left";

        if (hasChildren) {
          const toggle = document.createElement("button");
          toggle.className = "toggle";
          toggle.type = "button";
          toggle.textContent = isOpen ? "▼" : "▶";
          toggle.setAttribute("aria-label", "토글");
          toggle.onclick = () => {
            if (expanded.has(key)) expanded.delete(key);
            else expanded.add(key);
            renderReconstruction();
          };
          left.appendChild(toggle);
        } else {
          const placeholder = document.createElement("span");
          placeholder.className = "toggle-placeholder";
          left.appendChild(placeholder);
        }

        const indexEl = document.createElement("span");
        indexEl.className = "index";
        indexEl.textContent = `#${node.index ?? idx}`;
        left.appendChild(indexEl);

        const contentEl = document.createElement("div");
        contentEl.className = "content";
        contentEl.textContent = node.content || "(내용 없음)";

        const tsEl = document.createElement("div");
        tsEl.className = "timestamp";
        tsEl.textContent = formatTime(node.start);

        row.appendChild(left);
        row.appendChild(contentEl);
        row.appendChild(tsEl);
        nodeEl.appendChild(row);

        if (hasChildren && isOpen) {
          const childWrap = document.createElement("div");
          childWrap.className = "children";
          childWrap.appendChild(renderNodes(children, depth + 1));
          nodeEl.appendChild(childWrap);
        }

        wrapper.appendChild(nodeEl);
      });
      return wrapper;
    }

    function renderReconstruction() {
      const root = document.getElementById("reconstruction");
      root.innerHTML = "";
      root.appendChild(renderNodes(reconstructionData, 1));
    }

    function fillResult(data) {
      const keywords = Array.isArray(data.keywords) ? data.keywords : [];
      const chips = document.getElementById("keywords");
      chips.innerHTML = "";
      keywords.forEach((kw) => {
        const span = document.createElement("span");
        span.className = "chip";
        span.textContent = String(kw);
        chips.appendChild(span);
      });
      document.getElementById("keyword-count").textContent = `${keywords.length}개`;
      document.getElementById("overview").textContent = data.overview || "";

      reconstructionData = Array.isArray(data.reconstruction) ? data.reconstruction : [];
      expanded.clear();
      renderReconstruction();
    }

    async function loadResult() {
      const errorEl = document.getElementById("error");
      errorEl.textContent = "";
      try {
        const res = await fetch("/api/result");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        fillResult(data);
      } catch (err) {
        errorEl.textContent = `결과를 불러오지 못했습니다: ${err.message}`;
      }
    }

    document.getElementById("collapse-all").addEventListener("click", () => {
      expanded.clear();
      renderReconstruction();
    });

    document.getElementById("expand-depth1").addEventListener("click", () => {
      expanded.clear();
      reconstructionData.forEach((node, idx) => {
        expanded.add(getNodeKey(node, 1, idx));
      });
      renderReconstruction();
    });

    loadResult();
  </script>
</body>
</html>
"""


def extract_json_object(text: str) -> Dict[str, Any]:
    """Extract JSON object from raw output text or plain JSON."""
    text = text.strip()
    if not text:
        raise ValueError("빈 파일입니다.")

    # 1) Already clean JSON object.
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # 2) ```json ... ```
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text)
    if fenced:
        return json.loads(fenced.group(1))

    # 3) Fallback: first {...} block in logs
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        return json.loads(text[first : last + 1])

    raise ValueError("JSON 객체를 찾을 수 없습니다.")


def load_result(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"파일이 없습니다: {path}")

    obj = extract_json_object(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("JSON 최상위는 객체여야 합니다.")

    obj.setdefault("keywords", [])
    obj.setdefault("overview", "")
    obj.setdefault("reconstruction", [])
    return obj


def make_handler(result_path: Path):
    class Handler(BaseHTTPRequestHandler):
        def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            path = urlparse(self.path).path

            if path in ("/", "/index.html"):
                self._send_bytes(200, HTML_PAGE.encode("utf-8"), "text/html; charset=utf-8")
                return

            if path == "/api/result":
                try:
                    data = load_result(result_path)
                    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                    self._send_bytes(200, body, "application/json; charset=utf-8")
                except Exception as exc:  # noqa: BLE001
                    body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
                    self._send_bytes(500, body, "application/json; charset=utf-8")
                return

            self._send_bytes(404, b"Not found", "text/plain; charset=utf-8")

        def log_message(self, fmt: str, *args: Any) -> None:
            return

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="test.py 결과 뷰어 웹서버")
    parser.add_argument(
        "--result-file",
        default="latest_result.json",
        help="test.py 결과(JSON 또는 출력 로그) 파일 경로",
    )
    parser.add_argument("--host", default="127.0.0.1", help="바인드 호스트")
    parser.add_argument("--port", default=8000, type=int, help="바인드 포트")
    args = parser.parse_args()

    result_path = Path(args.result_file).resolve()
    handler = make_handler(result_path)
    server = ThreadingHTTPServer((args.host, args.port), handler)

    print(f"[viewer] result file: {result_path}")
    print(f"[viewer] open: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
