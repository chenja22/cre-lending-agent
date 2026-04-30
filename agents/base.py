import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    def __init__(self, name: str, system_prompt: str, model: str = "claude-haiku-4-5-20251001", max_tokens: int = 2048):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.max_tokens = max_tokens
        self.client = Anthropic()

    def run(self, user_message: str) -> str:
        print(f"\n[{self.name}] Running...")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        result = response.content[0].text
        print(f"\n[{self.name}] Done.")
        return result