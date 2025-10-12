from typing import List, Optional
from openai import OpenAI

class LLMClient:
    def __init__(self, api_key: str = "", base_url: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url or None
        self.model = model

    def summarize_leads(self, leads: List[dict], instruction: str = "Summarize the top opportunities in 10 bullets.") -> str:
        if not self.api_key:
            return "No API key provided."
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        text = "\n".join([f"- {l.get('name') or l.get('domain')} | {', '.join(l.get('emails', [])[:2])} | {l.get('city') or ''}" for l in leads[:50]])
        prompt = f"{instruction}\n\nLeads:\n{text}"
        resp = client.chat.completions.create(model=self.model, messages=[{"role":"user","content":prompt}], temperature=0.2)
        return resp.choices[0].message.content or ""
