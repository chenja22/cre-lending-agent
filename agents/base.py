import os
from anthropic import Anthropic
from dotenv import load_dotenv
from ui import console

load_dotenv()

class BaseAgent:
    def __init__(self, name: str, system_prompt: str, model: str = "claude-haiku-4-5-20251001", max_tokens: int = 2048):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.max_tokens = max_tokens
        self.client = Anthropic()

    def run(self, user_message: str) -> str:
        with console.status(f"[cyan]{self.name}[/cyan]  thinking…", spinner="dots"):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
        return response.content[0].text

    def run_structured(self, user_message: str, output_schema) -> object:
        with console.status(f"[cyan]{self.name}[/cyan]  thinking…", spinner="dots"):
            response = self.client.beta.messages.parse(
                model="claude-sonnet-4-5",
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=[{"role": "user", "content": user_message}],
                output_format=output_schema,
            )
        return response.parsed_output
