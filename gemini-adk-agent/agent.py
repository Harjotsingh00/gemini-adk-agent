"""
Gemini ADK Text Summarizer Agent
Single focused task: Summarize text input
Quota-efficient: uses gemini-1.5-flash with minimal tokens
"""

import os
import re
import json
import google.generativeai as genai

# ── ADK-style Tool ────────────────────────────────────────────────────────────

class SummarizeTool:
    name = "summarize_text"
    description = "Summarizes input text into a short paragraph and 3 key points."

    def build_prompt(self, text: str) -> str:
        # Keep prompt SHORT to save quota — no fluff, direct instruction
        return (
            "Summarize the following text. "
            "Reply ONLY as JSON: "
            '{\"summary\":\"2-3 sentence summary\",\"key_points\":[\"point1\",\"point2\",\"point3\"]}\n\n'
            f"TEXT:\n{text[:2000]}"   # hard cap input to save tokens
        )

    def parse(self, raw: str) -> dict:
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        return json.loads(clean)


# ── ADK-style Agent ───────────────────────────────────────────────────────────

class SummarizerAgent:
    """
    ADK-pattern agent with a single registered tool.
    Model: gemini-1.5-flash  (fastest, cheapest quota)
    """

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY is not set.")
        genai.configure(api_key=api_key)

        # gemini-1.5-flash = lowest quota cost, still very capable
        self.model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config=genai.GenerationConfig(
                temperature=0.2,        # low temp → deterministic, fewer retries
                max_output_tokens=300,  # small output → saves quota
            ),
        )
        self.tool = SummarizeTool()

    def run(self, text: str) -> dict:
        """Main ADK runner — accepts text, returns structured summary."""
        text = text.strip()
        if not text:
            return {"status": "error", "message": "No input text provided."}

        prompt = self.tool.build_prompt(text)

        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()
            result = self.tool.parse(raw)
            return {"status": "success", "data": result}
        except json.JSONDecodeError:
            # Return raw if JSON parse fails — still valid response
            return {"status": "success", "data": {"summary": raw, "key_points": []}}
        except Exception as e:
            return {"status": "error", "message": str(e)}
