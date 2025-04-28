import re
import json
import tiktoken
from pathlib import Path
from llm.llm_executor import run_prompt
from llm.chat_openai import chat
from prompt_templates import get_clarifier_prompt

tokenizer = tiktoken.encoding_for_model("gpt-4o")

def get_summarizer_prompt(i, total):
    """获取模块识别prompt，从prompt_templates库中获取"""
    return get_clarifier_prompt(i + 1, total)

def parse_module_list(text: str):
    cleaned = re.sub(r"^```(json)?", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned.strip())
    return json.loads(cleaned)

async def summarize_text(all_text: str, output_path: Path):
    print("🧠 Sending to LLM for full summarization with chunked prompt...")

    all_modules = await run_prompt(
        chat=chat,
        user_message=all_text,
        model="gpt-4o",
        tokenizer=tokenizer,
        max_input_tokens=2000,
        parse_response=parse_module_list,
        merge_result=lambda acc, x: acc + x if acc else x,
        get_system_prompt=get_summarizer_prompt
    )

    aggregated_modules = {}

    def merge_module(existing, new):
        for key in ["responsibilities", "key_apis", "data_inputs", "data_outputs", "depends_on"]:
            existing_list = existing.get(key, [])
            new_list = new.get(key, [])

            if isinstance(existing_list, str):
                existing_list = [existing_list]
            elif not isinstance(existing_list, list):
                existing_list = []

            if isinstance(new_list, str):
                new_list = [new_list]
            elif not isinstance(new_list, list):
                new_list = []

            merged = existing_list.copy()
            for item in new_list:
                if item not in merged:
                    merged.append(item)
            existing[key] = merged

        if "target_path" not in existing and "target_path" in new:
            existing["target_path"] = new["target_path"]

    for module in all_modules:
        name = module["module_name"]
        if name not in aggregated_modules:
            for key in ["responsibilities", "key_apis", "data_inputs", "data_outputs", "depends_on"]:
                val = module.get(key)
                if val is None:
                    module[key] = []
                elif isinstance(val, str):
                    module[key] = [val]
                elif not isinstance(val, list):
                    try:
                        module[key] = list(val)
                    except:
                        module[key] = []
            aggregated_modules[name] = module
        else:
            merge_module(aggregated_modules[name], module)

    for name, data in aggregated_modules.items():
        mod_dir = output_path / name
        mod_dir.mkdir(parents=True, exist_ok=True)
        with open(mod_dir / "full_summary.json", "w") as f:
            json.dump(data, f, indent=2)

    print(f"✅ Summarization complete. Modules written: {len(aggregated_modules)}")
