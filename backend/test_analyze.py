import asyncio
from routes.analyze import run_ensemble

async def test_headlines():
    headlines = [
        "NASA announces successful test of Mars oxygen generator.",
        "Microsoft launches new AI-powered features in Office 365.",
        "India surpasses China as the world's most populous country, UN reports.",
        "WHO declares end of global COVID-19 emergency status.",
        "Scientists confirm the Earth is flat after new satellite images.",
        "Elon Musk buys the Taj Mahal to convert it into a luxury hotel.",
        "Apple announces free iPhone giveaway for all citizens worldwide.",
        "UN approves teleportation technology for international travel starting 2027."
    ]
    for h in headlines:
        print(f"\n--- Testing: {h} ---")
        try:
            res = await run_ensemble(h)
            print(f"Verdict: {res.verdict}")
            print(f"Confidence: {res.confidence}")
            print(f"Engines: {res.engines_used}")
            print(f"Signals: {res.convergence_signals}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_headlines())
