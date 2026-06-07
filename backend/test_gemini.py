import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GOOGLE_API_KEY")

for model in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro", "gemini-1.0-pro"]:
    print(f"Testing {model}...")
    try:
        llm = ChatGoogleGenerativeAI(model=model, temperature=0, google_api_key=key)
        res = llm.invoke("Hi")
        print(f"Success! {model} responded: {res.content}")
    except Exception as e:
        print(f"Failed {model}: {e}")
