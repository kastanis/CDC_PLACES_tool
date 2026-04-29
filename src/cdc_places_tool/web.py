"""Small local web UI for reporter-facing PLACES queries."""

from __future__ import annotations

import json
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from cdc_places_tool.data import place_label
from cdc_places_tool.feedback import log_question, summarize_question_log
from cdc_places_tool.render import measure_to_text, result_to_text
from cdc_places_tool.router import route_question
from cdc_places_tool.semantic import SemanticLayer


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CDC PLACES Reporter Tool</title>
  <style>
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: #f7f7f4; color: #20231f; }
    header { padding: 28px 32px 18px; border-bottom: 1px solid #d8d8d0; background: #ffffff; }
    h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }
    p { line-height: 1.45; }
    main { max-width: 1180px; margin: 0 auto; padding: 24px 20px 48px; display: grid; gap: 18px; grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr); }
    section { background: #ffffff; border: 1px solid #d8d8d0; border-radius: 8px; padding: 18px; }
    label { display: block; font-weight: 700; margin-bottom: 8px; }
    textarea, select, input { width: 100%; box-sizing: border-box; border: 1px solid #b9b9ae; border-radius: 6px; padding: 10px; font: inherit; background: #fff; }
    textarea { min-height: 92px; resize: vertical; }
    button { border: 0; border-radius: 6px; background: #245b4f; color: #fff; font-weight: 700; padding: 10px 14px; cursor: pointer; }
    button.secondary { background: #42473f; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }
    pre { white-space: pre-wrap; background: #f1f1eb; border: 1px solid #deded5; border-radius: 8px; padding: 14px; min-height: 180px; overflow: auto; }
    .hint { color: #5f665d; font-size: 14px; margin-top: 8px; }
    .measure-list { columns: 2; padding-left: 18px; }
    @media (max-width: 840px) { main, .row { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <h1>CDC PLACES Reporter Tool</h1>
    <p>Ask approved questions over imported county-level PLACES estimates. Answers keep units, source cautions, and semantic definitions attached.</p>
  </header>
  <main>
    <section>
      <label for="question">Plain-English question</label>
      <textarea id="question">Which California counties have the highest uninsured rates?</textarea>
      <div class="actions">
        <button id="ask">Ask</button>
        <button class="secondary" data-example="Compare Fresno County, CA and Los Angeles County, CA on poor mental health">Compare</button>
        <button class="secondary" data-example="Summarize Harris County, TX">Summarize</button>
        <button class="secondary" data-example="Explain uninsured">Explain</button>
      </div>
      <p class="hint">Allowed operations: rank, compare, summarize, explain. Questions are logged locally so the semantic layer can improve over time.</p>
      <pre id="answer">Ready.</pre>
    </section>
    <section>
      <div class="row">
        <div>
          <label for="measure">Measure</label>
          <select id="measure"></select>
        </div>
        <div>
          <label for="state">State</label>
          <input id="state" placeholder="CA">
        </div>
      </div>
      <div class="actions">
        <button id="rank">Rank selected measure</button>
        <button class="secondary" id="feedback">Feedback summary</button>
      </div>
      <h2>Available Measures</h2>
      <ul class="measure-list" id="measures"></ul>
    </section>
  </main>
  <script>
    const metadata = __METADATA__;
    const question = document.querySelector("#question");
    const answer = document.querySelector("#answer");
    const measureSelect = document.querySelector("#measure");
    const stateInput = document.querySelector("#state");
    const measureList = document.querySelector("#measures");

    metadata.measures.forEach((measure) => {
      const option = document.createElement("option");
      option.value = measure.id;
      option.textContent = measure.label;
      measureSelect.appendChild(option);
      const item = document.createElement("li");
      item.textContent = `${measure.id}: ${measure.label}`;
      measureList.appendChild(item);
    });

    async function ask(text) {
      answer.textContent = "Working...";
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });
      const payload = await response.json();
      answer.textContent = payload.answer;
    }

    document.querySelector("#ask").addEventListener("click", () => ask(question.value));
    document.querySelector("#rank").addEventListener("click", () => {
      const label = measureSelect.options[measureSelect.selectedIndex].textContent;
      const state = stateInput.value.trim();
      ask(`Which ${state ? state + " " : ""}counties have the highest ${label}?`);
    });
    document.querySelector("#feedback").addEventListener("click", async () => {
      answer.textContent = "Loading feedback summary...";
      const response = await fetch("/api/feedback");
      const payload = await response.json();
      answer.textContent = payload.summary;
    });
    document.querySelectorAll("[data-example]").forEach((button) => {
      button.addEventListener("click", () => {
        question.value = button.dataset.example;
        ask(question.value);
      });
    });
  </script>
</body>
</html>
"""


def make_handler(rows: list[dict], layer: SemanticLayer) -> type[BaseHTTPRequestHandler]:
    class PlacesHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                metadata = {
                    "measures": [
                        {"id": measure.id, "label": measure.label}
                        for measure in layer.measures.values()
                    ],
                    "places": [place_label(row) for row in rows],
                    "dataset": layer.dataset,
                }
                body = HTML.replace("__METADATA__", json.dumps(metadata, default=str))
                self.send_html(body)
                return
            if parsed.path == "/api/places":
                self.send_json({"places": [place_label(row) for row in rows]})
                return
            if parsed.path == "/api/feedback":
                self.send_json({"summary": format_feedback_summary()})
                return
            query = parse_qs(parsed.query)
            if parsed.path == "/api/ask" and "question" in query:
                self.answer_question(query["question"][0])
                return
            self.send_error(404)

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/api/ask":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return
            self.answer_question(str(payload.get("question", "")))

        def answer_question(self, question: str) -> None:
            routed = route_question(question, rows, layer)
            log_question(
                question=question,
                ok=routed.ok,
                operation=routed.operation,
                measure_id=routed.measure.id if routed.measure else None,
                message=routed.message,
            )
            if not routed.ok:
                self.send_json({"ok": False, "answer": routed.message})
                return
            if routed.operation == "explain" and routed.measure:
                self.send_json({"ok": True, "answer": measure_to_text(layer, routed.measure)})
                return
            if routed.result:
                self.send_json({"ok": True, "answer": result_to_text(routed.result, layer)})
                return
            self.send_json({"ok": False, "answer": "No answer was generated."})

        def send_html(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def send_json(self, payload: dict) -> None:
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: object) -> None:
            return

    return PlacesHandler


def format_feedback_summary() -> str:
    summary = summarize_question_log()
    lines = [
        f"Total questions: {summary['total_questions']}",
        f"Accepted: {summary['accepted_questions']}",
        f"Refused: {summary['refused_questions']}",
        "",
        "Operations",
    ]
    lines.extend(f"- {operation}: {count}" for operation, count in summary["operations"])
    lines.append("")
    lines.append("Measures")
    lines.extend(f"- {measure}: {count}" for measure, count in summary["measures"])
    if summary["recent_refusals"]:
        lines.append("")
        lines.append("Recent refusals")
        lines.extend(f"- {entry.question} -> {entry.message}" for entry in summary["recent_refusals"])
    return "\n".join(lines)


def run_server(rows: list[dict], layer: SemanticLayer, host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(rows, layer))
    print(f"Serving CDC PLACES Reporter Tool at http://{escape(host)}:{port}")
    server.serve_forever()
