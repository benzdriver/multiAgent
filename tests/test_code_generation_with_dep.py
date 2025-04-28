# tests/test_code_generation_with_dep.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import os
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch
from generator.autogen_module_generator import construct_prompt

def test_prompt_includes_dependency_context():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock module input dir structure
        mock_modules_dir = Path(tmpdir) / "modules"
        mock_modules_dir.mkdir(parents=True)
        consultants_dir = mock_modules_dir / "Consultants"
        consultants_dir.mkdir()
        consultants_summary = {
            "module_name": "Consultants",
            "responsibilities": ["Manage consultants"],
            "key_apis": ["registerConsultant()"],
            "depends_on": ["AuthService"],
            "target_path": "backend/services"
        }
        with open(consultants_dir / "full_summary.json", "w") as f:
            json.dump(consultants_summary, f)

        # Create corresponding mock summary_index
        mock_index_path = Path(tmpdir) / "summary_index.json"
        summary_index = {
            "Consultants": consultants_summary,
            "AuthService": {
                "target_path": "backend/services",
                "depends_on": [],
                "responsibilities": []
            }
        }
        with open(mock_index_path, "w") as f:
            json.dump(summary_index, f)

        # Patch global paths in module
        with patch("generator.autogen_module_generator.input_dir", mock_modules_dir), \
             patch("generator.autogen_module_generator.summary_index", summary_index):

            from generator.autogen_module_generator import construct_prompt
            prompt = construct_prompt(consultants_summary)

            assert "AuthService located at `backend/services/authservice.ts`" in prompt
