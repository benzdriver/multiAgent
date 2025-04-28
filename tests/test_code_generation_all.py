import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parent.parent))
from generator.autogen_module_generator import construct_prompt

# ✅ Test 1: prompt includes dependency context
def test_prompt_includes_dependency_context():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod_dir = Path(tmpdir) / "modules/Consultants"
        mod_dir.mkdir(parents=True)
        summary = {
            "module_name": "Consultants",
            "responsibilities": ["Manage consultants"],
            "key_apis": ["registerConsultant()"],
            "depends_on": ["AuthService"],
            "target_path": "backend/services"
        }
        (mod_dir / "full_summary.json").write_text(json.dumps(summary))

        summary_index = {
            "AuthService": {"target_path": "backend/services", "depends_on": [], "responsibilities": []}
        }

        import generator.autogen_module_generator as modgen
        modgen.summary_index = summary_index

        prompt = construct_prompt(summary)
        assert "AuthService located at `backend/services/authservice.ts`" in prompt

# ✅ Test 2: generated code contains import from dependency
def test_generated_code_has_dependency_import():
    full_summary = {
        "module_name": "Consultants",
        "responsibilities": ["Manage consultants"],
        "key_apis": ["registerConsultant()"],
        "depends_on": ["AuthService"],
        "target_path": "backend/services"
    }
    module_dir = Path("data/output/modules/Consultants")
    module_dir.mkdir(parents=True, exist_ok=True)
    with open(module_dir / "full_summary.json", "w") as f:
        json.dump(full_summary, f)

    summary_index = {
        "AuthService": {"target_path": "backend/services", "depends_on": [], "responsibilities": []}
    }
    import generator.autogen_module_generator as modgen
    modgen.summary_index = summary_index

    out_file = Path("data/generated_code/backend/services/consultants.ts")
    if out_file.exists():
        out_file.unlink()

    subprocess.run([
        "python", "-m", "generator.autogen_module_generator", "--only", "Consultants"
    ], check=True)

    assert out_file.exists(), "Code file not generated."
    content = out_file.read_text()
    assert "AuthService" in content
    assert "authservice" in content.lower()

# ✅ Test 3: summarizer handles malformed LLM response
def test_summarizer_handles_string_fields():
    from clarifier.summarizer import summarize_text

    with tempfile.TemporaryDirectory() as tmpdir:
        all_text = "The system must allow consultants to register, login, and be verified."
        output_path = Path(tmpdir) / "modules"
        output_path.mkdir(parents=True)

        from unittest.mock import AsyncMock
        import clarifier.summarizer as sm

        async def fake_run_prompt(**kwargs):
            return [
                {
                    "module_name": "Consultants",
                    "responsibilities": "Should manage consultants",
                    "key_apis": ["registerConsultant()"],
                    "data_inputs": [],
                    "data_outputs": [],
                    "depends_on": [],
                    "target_path": "backend/services"
                }
            ]

        sm.run_prompt = fake_run_prompt
        sm.chat = AsyncMock()

        import asyncio
        asyncio.run(summarize_text(all_text, output_path))

        f = output_path / "Consultants" / "full_summary.json"
        assert f.exists()
        data = json.loads(f.read_text())
        assert isinstance(data["responsibilities"], list)

# ✅ Test 4: summary_index.json is generated correctly
def test_generate_summary_index():
    from clarifier.index_generator import generate_summary_index

    with tempfile.TemporaryDirectory() as tmpdir:
        mod_dir = Path(tmpdir) / "modules/AuthService"
        mod_dir.mkdir(parents=True)
        mod_data = {
            "module_name": "AuthService",
            "responsibilities": ["login"],
            "depends_on": [],
            "target_path": "backend/services"
        }
        with open(mod_dir / "full_summary.json", "w") as f:
            json.dump(mod_data, f)

        out_path = Path(tmpdir) / "summary_index.json"
        generate_summary_index(mod_dir.parent, out_path)

        assert out_path.exists()
        index = json.loads(out_path.read_text())
        assert "AuthService" in index
        assert index["AuthService"]["target_path"] == "backend/services"

# ✅ Test 5: end-to-end clarifier integration
def test_clarifier_end_to_end():
    from clarifier.clarifier import main
    input_dir = Path("data/input")
    assert any(input_dir.glob("*.md")), "Input markdown files are missing"

    main()

    modules_path = Path("data/output/modules")
    index_path = Path("data/output/summary_index.json")

    assert modules_path.exists()
    assert any(modules_path.glob("*/full_summary.json"))
    assert index_path.exists()
    data = json.loads(index_path.read_text())
    assert len(data) > 0
