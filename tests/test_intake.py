import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.intake import IntakeAgent

agent = IntakeAgent()
result = agent.run("data/sample_deal")

import json
print(json.dumps(result, indent=2))