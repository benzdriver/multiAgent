# generator/autogen_module_generator.py

from dotenv import load_dotenv
load_dotenv()

import json
import asyncio
from pathlib import Path
from core.llm.prompt_cleaner import clean_code_output
from core.llm.chat_autogen import chat
from memory.structured_context import get_structured_context
from prompt_templates import get_generator_prompt

input_dir = Path("data/output/modules")
output_dir = Path("data/generated_code")
output_dir.mkdir(parents=True, exist_ok=True)

# Load summary index
summary_index = {}
try:
    with open(Path("data/output/summary_index.json"), "r") as f:
        summary_index = json.load(f)
except FileNotFoundError:
    print("Warning: summary_index.json not found")

total_tokens_used = 0

async def generate_module(module_name: str, prompt: str, resolved_path: Path):
    global total_tokens_used
    result_text = await chat(user_message=prompt, model="gpt-4o")

    if isinstance(result_text, str):
        cleaned_text = clean_code_output(result_text)
    else:
        cleaned_text = clean_code_output(result_text.messages[-1].content)

    resolved_path.mkdir(parents=True, exist_ok=True)
    with open(resolved_path / f"{module_name.lower()}.ts", "w") as f:
        f.write(cleaned_text)

    print(f"✅ Module generated: {module_name}")

def construct_prompt(module_summary):
    """
    Constructs a prompt for code generation based on the module summary.
    Includes dependency context to help with generating proper imports and references.
    
    Args:
        module_summary (dict): The module summary containing name, responsibilities, etc.
        
    Returns:
        str: A prompt suitable for code generation
    """
    return get_generator_prompt(module_summary)

async def generate_all_modules():
    """
    Generates code for all modules defined in the input directory
    """
    modules = [p for p in input_dir.iterdir() if p.is_dir()]
    for module_path in modules:
        module_name = module_path.name
        summary_path = module_path / "full_summary.json"
        
        if not summary_path.exists():
            print(f"⚠️ Skipping {module_name}: no summary found")
            continue
            
        with open(summary_path, "r") as f:
            summary = json.load(f)
            
        # Create prompt and generate code
        prompt = construct_prompt(summary)
        
        # Resolve the output path
        target_path = Path(summary.get("target_path", ""))
        resolved_path = output_dir / target_path
        
        await generate_module(module_name, prompt, resolved_path)
        
    print(f"🎉 All modules generated successfully!")

if __name__ == "__main__":
    asyncio.run(generate_all_modules())
