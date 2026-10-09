"""Try Gemma on a real photo from the command line (uses your real API key).

  python try_gemma.py photo.jpg safety_infrastructure "Rohini, Delhi" "Fill it and resurface the road"
  python try_gemma.py --quest "Rohini, Delhi"
"""
import asyncio
import sys
import warnings

from dotenv import load_dotenv

warnings.filterwarnings("ignore", message=".*protected namespace.*")
load_dotenv()
import gemma  # noqa: E402


async def main():
    if sys.argv[1] == "--quest":
        q = await gemma.generate_quest(sys.argv[2])
        print(q.model_dump_json(indent=2))
        return
    path, slot, location, solution = sys.argv[1:5]
    data = open(path, "rb").read()
    a = await gemma.analyze_photo(data, location, slot, solution)
    print(a.model_dump_json(indent=2))
    if a.usable:
        print("\nSCORE:", gemma.to_response(a).score.model_dump_json(indent=2))
    else:
        print("\nWOULD BE REJECTED (HTTP 422) with:", a.photo_check.rejection_reason)


asyncio.run(main())
