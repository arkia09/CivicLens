"""Finds out WHICH part of the request makes the Gemma API fail.
Usage: python diag_gemma.py test_pics/garbage.jpg"""
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

import gemma

load_dotenv()
client = genai.Client(api_key=os.environ["GEMMA_API_KEY"])
img, mime = gemma.prepare_image(open(sys.argv[1], "rb").read())
print(f"image after resize: {len(img)//1024} KB")

SYS = "You are a helpful assistant. Reply briefly."
THINK = types.ThinkingConfig(thinking_level="minimal")
steps = [  # (label, use_image, use_system, use_thinking)
    ("text only", False, False, False),
    ("+ system instruction", False, True, False),
    ("+ thinking=minimal", False, True, True),
    ("image, no thinking", True, True, False),
    ("image + thinking=minimal", True, True, True),
]

for model in ("gemma-4-26b-a4b-it", "gemma-4-31b-it"):
    print(f"\n== {model}")
    for label, use_img, use_sys, use_think in steps:
        contents = ["Describe this photo in one sentence."] if use_img else ["Say hello."]
        if use_img:
            contents.insert(0, types.Part.from_bytes(data=img, mime_type=mime))
        cfg = types.GenerateContentConfig(
            system_instruction=SYS if use_sys else None,
            thinking_config=THINK if use_think else None,
            max_output_tokens=200,
        )
        try:
            r = client.models.generate_content(model=model, contents=contents, config=cfg)
            print(f"  OK    {label}: {(r.text or '')[:60]!r}")
        except Exception as e:
            print(f"  FAIL  {label}: {str(e)[:90]}")
