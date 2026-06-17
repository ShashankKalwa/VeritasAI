import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Setup dummy keys so we don't hit the stubs
os.environ["GOOGLE_AI_API_KEY"] = "YOUR_GEMINI_API_KEY" # This will hit the stub in claim_extractor and reason_claim
os.environ["SEARCH_API_KEY"] = "TODO_your_tavily_key" # This will hit the stub in evidence_retriever

from routes.analyze import process_analysis

async def main():
    print("Testing process_analysis V2...")
    text = "A new study published in The Lancet confirms that eating 5 apples a day cures cancer 100% of the time."
    try:
        resp = await process_analysis(input_type="text", content=text)
        import json
        print(json.dumps(resp, indent=2))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
