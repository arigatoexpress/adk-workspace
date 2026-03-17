from google.adk.agents import LlmAgent
from google.genai import Client
try:
    client = Client(vertexai=True, project="test", location="us-central1")
    agent = LlmAgent(name="test", model="gemini-1.5-flash", client=client)
    print("SUCCESS: LlmAgent accepted client")
except Exception as e:
    print(f"FAILURE: {e}")
