import os
import json
import asyncio
import subprocess
from pathlib import Path
import time
import shutil
import argparse
from datetime import datetime

# Configuration
MAX_ROUNDS = 3
VALIDATOR_REPORT_PATH = Path("data/validator_report.json")
# 创建以时间戳命名的根日志目录
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_ROOT_DIR = Path(f"data/logs/{TIMESTAMP}")
FIX_LOG_DIR = LOG_ROOT_DIR / "fix_rounds"
SUMMARY_REPORT_PATH = LOG_ROOT_DIR / "fix_summary.md"
# 是否要强制运行所有轮次，不管是否有改善
FORCE_ALL_ROUNDS = False

# 确保日志根目录存在
def ensure_log_dirs():
    """确保所有日志目录存在"""
    LOG_ROOT_DIR.mkdir(parents=True, exist_ok=True)
    FIX_LOG_DIR.mkdir(parents=True, exist_ok=True)
    # 创建一个指向最新日志的符号链接
    latest_link = Path("data/logs/latest")
    if latest_link.exists():
        if latest_link.is_symlink():
            latest_link.unlink()
        else:
            shutil.rmtree(latest_link)
    latest_link.symlink_to(LOG_ROOT_DIR.resolve(), target_is_directory=True)

def run_validator():
    """Run the validator and return whether it succeeded"""
    print("\n🔍 Running architecture validator...")
    try:
        # Don't capture output to allow real-time viewing
        result = subprocess.run(["python", "run_validator.py"], check=True)
        print("✅ Validator completed")
        
        # 将验证报告复制到时间戳目录
        if VALIDATOR_REPORT_PATH.exists():
            shutil.copy(VALIDATOR_REPORT_PATH, LOG_ROOT_DIR / "validator_report.json")
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Validator failed with exit code {e.returncode}")
        return False

def run_fixer():
    """Run the fixer and return whether it succeeded"""
    print("\n🔧 Running architecture fixer...")
    try:
        # Don't capture output to allow real-time viewing
        result = subprocess.run(["python", "-m", "core.fixer.structure_fixer"], check=True)
        print("✅ Fixer completed")
        
        # 将修复日志复制到时间戳目录
        fix_log = Path("data/fix_log.md")
        if fix_log.exists():
            shutil.copy(fix_log, LOG_ROOT_DIR / "fix_log.md")
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Fixer failed with exit code {e.returncode}")
        return False

def count_issues(report_path):
    """Count the number of issues in the report"""
    if not report_path.exists():
        return 0
    
    try:
        data = json.loads(report_path.read_text())
        structure_scan = data.get("structure_scan", {})
        ai_issues = data.get("ai_review", {})
        
        # Count structure scan issues
        structure_issues = sum(len(issues) for issues in structure_scan.values())
        
        # Count AI review issues
        # 1. Overlapping responsibilities
        overlaps = len(ai_issues.get("overlapping_responsibilities", []))
        # 2. Undefined dependencies
        undefined = len(ai_issues.get("undefined_dependencies", []))
        # 3. Missing or redundant modules
        missing_redundant = ai_issues.get("missing_or_redundant_modules", {})
        missing = len(missing_redundant.get("missing", []))
        redundant = len(missing_redundant.get("redundant", []))
        
        total_issues = structure_issues + overlaps + undefined + missing + redundant
        
        details = {
            "structure_issues": structure_issues,
            "overlapping_responsibilities": overlaps,
            "undefined_dependencies": undefined,
            "missing_modules": missing,
            "redundant_modules": redundant,
            "total": total_issues
        }
        
        return details
    except Exception as e:
        print(f"❌ Failed to parse report: {e}")
        return {"total": 0, "error": str(e)}

def backup_report(round_num):
    """Backup the current validation report and fix log"""
    # Create round directory
    round_dir = FIX_LOG_DIR / f"round_{round_num}"
    round_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup validation report
    if VALIDATOR_REPORT_PATH.exists():
        shutil.copy(VALIDATOR_REPORT_PATH, round_dir / "validator_report.json")
    
    # Backup fix log
    fix_log = Path("data/fix_log.md")
    if fix_log.exists():
        shutil.copy(fix_log, round_dir / "fix_log.md")
    
    return round_dir

def generate_round_summary(round_num, issues_before, issues_after, round_dir):
    """Generate a summary for the current round"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    summary = f"""## Fix Round {round_num} - {timestamp}

### Issues Before Fix
- Structure issues: {issues_before.get('structure_issues', 0)}
- Overlapping responsibilities: {issues_before.get('overlapping_responsibilities', 0)}
- Undefined dependencies: {issues_before.get('undefined_dependencies', 0)}
- Missing modules: {issues_before.get('missing_modules', 0)}
- Redundant modules: {issues_before.get('redundant_modules', 0)}
- Total issues: {issues_before.get('total', 0)}

### Issues After Fix
- Structure issues: {issues_after.get('structure_issues', 0)}
- Overlapping responsibilities: {issues_after.get('overlapping_responsibilities', 0)}
- Undefined dependencies: {issues_after.get('undefined_dependencies', 0)}
- Missing modules: {issues_after.get('missing_modules', 0)}
- Redundant modules: {issues_after.get('redundant_modules', 0)}
- Total issues: {issues_after.get('total', 0)}

### Improvement
- Issues fixed: {issues_before.get('total', 0) - issues_after.get('total', 0)}
- Improvement percentage: {calculate_improvement(issues_before.get('total', 0), issues_after.get('total', 0))}%

"""
    
    # Save round summary
    round_summary_path = round_dir / "round_summary.md"
    round_summary_path.write_text(summary)
    
    return summary

def calculate_improvement(before, after):
    """Calculate improvement percentage"""
    if before == 0:
        return 0
    improvement = ((before - after) / before) * 100
    return round(improvement, 2)

def generate_fix_summary(all_rounds):
    """Generate overall fix summary"""
    if not all_rounds:
        return "No fix rounds recorded."
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    summary = f"""# Architecture Fix Summary - {timestamp}

## Overview
- Total rounds: {len(all_rounds)}
- Initial issue count: {all_rounds[0]['before']['total']}
- Final issue count: {all_rounds[-1]['after']['total']}
- Overall improvement: {calculate_improvement(all_rounds[0]['before']['total'], all_rounds[-1]['after']['total'])}%

## Detailed Round Information

"""
    
    for round_data in all_rounds:
        round_num = round_data['round']
        before = round_data['before']
        after = round_data['after']
        
        summary += f"""### Round {round_num}
- Issues before: {before['total']}
- Issues after: {after['total']}
- Improvement: {calculate_improvement(before['total'], after['total'])}%
- Details: [Round {round_num} Summary](fix_rounds/round_{round_num}/round_summary.md)

"""
    
    return summary

async def run_fix_loop():
    """Run the validation and fixing loop process"""
    global FORCE_ALL_ROUNDS
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Run the validation and fixing loop process')
    parser.add_argument('--force-all-rounds', action='store_true', help='Force running all rounds regardless of improvement')
    args = parser.parse_args()
    
    if args.force_all_rounds:
        FORCE_ALL_ROUNDS = True
        print("⚠️ Force all rounds mode enabled - will run all rounds regardless of improvement")
    
    # 确保日志目录存在
    ensure_log_dirs()
    print(f"📁 All logs will be saved to: {LOG_ROOT_DIR}")
    
    # Record data for all rounds
    all_rounds = []
    
    # Run initial validation
    if not run_validator():
        print("❌ Initial validation failed, cannot continue")
        return
    
    # Check initial issue count
    issues_before = count_issues(VALIDATOR_REPORT_PATH)
    if issues_before.get('total', 0) == 0:
        print("✅ Initial validation found no issues, no fixes needed")
        return
    
    print(f"\n📊 Initial issues statistics:")
    print(f"- Structure issues: {issues_before.get('structure_issues', 0)}")
    print(f"- Overlapping responsibilities: {issues_before.get('overlapping_responsibilities', 0)}")
    print(f"- Undefined dependencies: {issues_before.get('undefined_dependencies', 0)}")
    print(f"- Missing modules: {issues_before.get('missing_modules', 0)}")
    print(f"- Redundant modules: {issues_before.get('redundant_modules', 0)}")
    print(f"- Total issues: {issues_before.get('total', 0)}")
    
    # Run fix loop
    previous_total_issues = issues_before.get('total', 0)
    consecutive_no_improvement = 0
    
    for round_num in range(1, MAX_ROUNDS + 1):
        print(f"\n\n{'='*30}")
        print(f"🔄 Starting fix round {round_num}/{MAX_ROUNDS}")
        print(f"{'='*30}\n")
        
        # Backup report before fixing
        round_dir = backup_report(round_num)
        
        # Run fixer
        if not run_fixer():
            print(f"❌ Fixer failed in round {round_num}, stopping loop")
            break
        
        # Run validator again to check if issues were fixed
        if not run_validator():
            print(f"❌ Validator failed in round {round_num}, stopping loop")
            break
        
        # Count issues after fix
        issues_after = count_issues(VALIDATOR_REPORT_PATH)
        
        # Generate and save round summary
        round_summary = generate_round_summary(round_num, issues_before, issues_after, round_dir)
        print(f"\n📝 Round {round_num} summary:")
        print(round_summary)
        
        # Record round data
        all_rounds.append({
            'round': round_num,
            'before': issues_before,
            'after': issues_after
        })
        
        # Check if there's improvement
        current_total_issues = issues_after.get('total', 0)
        has_improvement = current_total_issues < previous_total_issues
        
        if not has_improvement:
            consecutive_no_improvement += 1
            if consecutive_no_improvement >= 2 and not FORCE_ALL_ROUNDS:
                print(f"⚠️ No improvement detected for {consecutive_no_improvement} consecutive rounds, stopping loop")
                break
        else:
            consecutive_no_improvement = 0  # 重置连续无改善计数
        
        # Update issues_before for next round
        issues_before = issues_after
        previous_total_issues = current_total_issues
        
        # Stop if no issues left
        if current_total_issues == 0:
            print("✅ All issues resolved, stopping loop")
            break
        
        # Pause between rounds
        if round_num < MAX_ROUNDS:
            print(f"\n⏳ Pausing for 5 seconds before next round...")
            await asyncio.sleep(5)
    
    # Generate and save overall fix summary
    fix_summary = generate_fix_summary(all_rounds)
    SUMMARY_REPORT_PATH.write_text(fix_summary)
    print(f"\n📋 Overall fix summary saved to {SUMMARY_REPORT_PATH}")

if __name__ == "__main__":
    asyncio.run(run_fix_loop())  