import re

def clean_code_output(raw: str) -> str:
    """
    Cleans raw LLM output by removing:
    - // filename.ts header comments
    - ```markdown code block wrappers
    - trailing TERMINATE, END, ---
    """
    lines = raw.strip().splitlines()

    # Remove filename comment like: // module.ts
    if lines and lines[0].strip().startswith("//") and lines[0].strip().endswith(".ts"):
        lines = lines[1:]

    cleaned = "\n".join(lines).strip()

    # Remove markdown code block if wrapped
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned.strip())

    # Remove terminator-like endings
    cleaned = re.sub(r"(TERMINATE|END|CONTINUE|---)+\s*$", "", cleaned.strip(), flags=re.IGNORECASE)

    return cleaned.strip()
