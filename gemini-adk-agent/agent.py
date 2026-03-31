import os
import json
import re
import urllib.request
import urllib.error


class SummarizeTool:
    name = "summarize_text"
    description = "Summarizes input text into key points."

    def build_prompt(self, text):
        return (
            'Summarize the text below. Reply ONLY as JSON: '
            '{"summary":"2-3 sentences","key_points":["pt1","pt2","pt3"]}'
            '\n\nTEXT:\n' + text[:1500]
        )

    def parse(self, raw):
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        return json.loads(clean)


class SummarizerAgent:
    API_URL = ("https://generativelanguage.googleapis.com/v1beta"
               "/models/gemini-2.0-flash:generateContent")

    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise EnvironmentError("GEMINI_API_KEY not set.")
        self.tool = SummarizeTool()

    def run(self, text):
        text = text.strip()
        if not text:
            return {"status": "error", "message": "No text provided."}

        payload = json.dumps({
            "contents": [{"parts": [{"text": self.tool.build_prompt(text)}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 300}
        }).encode()

        req = urllib.request.Request(
            f"{self.API_URL}?key={self.api_key}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.loads(r.read())
            raw = body["candidates"][0]["content"]["parts"][0]["text"].strip()
            try:
                return {"status": "success", "data": self.tool.parse(raw)}
            except Exception:
                return {"status": "success", "data": {"summary": raw, "key_points": []}}
        except urllib.error.HTTPError as e:
            return {"status": "error", "message": e.read().decode()}
        except Exception as e:
            return {"status": "error", "message": str(e)}
