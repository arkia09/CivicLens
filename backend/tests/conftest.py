import os

# Set before main is imported, so a local .env can't send tests to the real services.
os.environ["USE_MOCK"] = "true"
os.environ["DEDUPE_IMAGES"] = "true"
os.environ.pop("SERPAPI_KEY", None)
