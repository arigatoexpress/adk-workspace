import inspect
from google.adk.agents import LlmAgent
from google.genai import Client

print("=== google.genai.Client.__init__ ===")
print(inspect.signature(Client.__init__))
print(Client.__init__.__doc__)

print("\n=== google.adk.agents.LlmAgent.__init__ ===")
print(inspect.signature(LlmAgent.__init__))
print(LlmAgent.__init__.__doc__)
