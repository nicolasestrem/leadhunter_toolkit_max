from typing import List, Optional
from openai import OpenAI

class LLMClient:
    def __init__(self, api_key: str = "", base_url: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key or "not-needed"  # Default for local LLMs like LM Studio
        # Ensure base_url ends with /v1 for OpenAI compatibility
        if base_url:
            base_url = base_url.rstrip('/')
            if not base_url.endswith('/v1'):
                base_url = f"{base_url}/v1"
        self.base_url = base_url or None
        self.model = model

    def summarize_leads(self, leads: List[dict], instruction: str = "Summarize the top opportunities in 10 bullets.") -> str:
        if not self.base_url:
            return "No LLM base URL configured. Please set it in Settings."
        if not leads:
            return "No leads to summarize."
        try:
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            text = "\n".join([f"- {l.get('name') or l.get('domain')} | {', '.join(l.get('emails', [])[:2])} | {l.get('city') or ''}" for l in leads[:50]])
            prompt = f"{instruction}\n\nLeads:\n{text}"
            resp = client.chat.completions.create(model=self.model, messages=[{"role":"user","content":prompt}], temperature=0.2)
            if resp and resp.choices and len(resp.choices) > 0:
                return resp.choices[0].message.content or "No response from LLM."
            return "Empty response from LLM."
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
