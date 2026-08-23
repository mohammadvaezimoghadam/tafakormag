#!/usr/bin/env python3
"""
tests/e2e/test_runner.py

Unified CLI Test Runner for Tafakor Monorepo E2E & Integration Test Suites.
Supports tiered execution:
- Tier 1: Feature Coverage (tests/e2e/test_tier1_feature_coverage.py)
- Tier 2: Boundary & Edge Cases (tests/e2e/test_tier2_boundary_cases.py)
- Tier 3: Pairwise Combinations (tests/e2e/test_tier3_pairwise_combinations.py)
- Tier 4: Real-World Workloads (tests/e2e/test_tier4_real_world_workloads.py)
- All: Runs all E2E tiers + Core non-regression suite
- Non-Regression: Core apps (Accounts, Notes, Donations, Integration tests)

Usage:
    python tests/e2e/test_runner.py --tier 1
    python tests/e2e/test_runner.py --tier 1 2
    python tests/e2e/test_runner.py --tier 3 --verbose
    python tests/e2e/test_runner.py --tier 4 --failfast
    python tests/e2e/test_runner.py --all
    python tests/e2e/test_runner.py --non-regression
    python tests/e2e/test_runner.py --all --report test_results.json
"""

import os
import sys
import time
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup repository paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
TESTS_DIR = REPO_ROOT / "tests"
E2E_DIR = TESTS_DIR / "e2e"

# Ensure UTF-8 output on Windows terminals
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure") and sys.stderr.encoding != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Tier mapping definitions
TIER_SUITES = {
    "1": {
        "name": "Tier 1: Feature Coverage",
        "file": E2E_DIR / "test_tier1_feature_coverage.py",
        "description": "Comprehensive feature-by-feature verification (>=5 cases per feature)",
        "type": "pytest"
    },
    "2": {
        "name": "Tier 2: Boundary & Edge Cases",
        "file": E2E_DIR / "test_tier2_boundary_cases.py",
        "description": "Boundary values, unicode variations, corrupt inputs, edge conditions",
        "type": "pytest"
    },
    "3": {
        "name": "Tier 3: Pairwise Combinations",
        "file": E2E_DIR / "test_tier3_pairwise_combinations.py",
        "description": "Pairwise combinatorial cross-feature interaction testing",
        "type": "pytest"
    },
    "4": {
        "name": "Tier 4: Real-World Workloads",
        "file": E2E_DIR / "test_tier4_real_world_workloads.py",
        "description": "10 realistic end-to-end multi-step application scenarios",
        "type": "pytest"
    }
}

NON_REGRESSION_TARGETS = [
    {
        "name": "Core Non-Regression: Django App Tests",
        "command_args": ["backend/manage.py", "test", "apps.accounts", "apps.notes", "apps.donations"],
        "description": "Core Django unit and integration tests (Accounts, Notes, Donations)",
        "type": "django"
    },
    {
        "name": "Core Non-Regression: Integration Suite",
        "file": TESTS_DIR / "integration",
        "description": "Cross-service API integration tests",
        "type": "pytest"
    }
]


class Colors:
    """ANSI color escape sequences for terminal output formatting."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

    @classmethod
    def disable(cls):
        cls.HEADER = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.RED = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''
        cls.RESET = ''


def get_environment() -> Dict[str, str]:
    """Prepares subprocess environment with proper PYTHONPATH and DJANGO settings."""
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    new_paths = [str(REPO_ROOT), str(BACKEND_DIR)]
    
    if pythonpath:
        new_paths.append(pythonpath)
    
    env["PYTHONPATH"] = os.pathsep.join(new_paths)
    env["DJANGO_SETTINGS_MODULE"] = "note_platform.settings"
    env["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    return env


def ensure_database_ready() -> str:
    """
    Verifies database connectivity, applies pending migrations,
    and returns detected database engine.
    """
    env = get_environment()
    cmd = [sys.executable, "backend/manage.py", "migrate", "--noinput"]
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Warning: Pre-flight migration returned code {res.returncode}: {res.stderr}")

    db_engine = "SQLite"
    try:
        cmd_engine = [
            sys.executable, "-c",
            "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'note_platform.settings'); "
            "django.setup(); from django.conf import settings; print(settings.DATABASES['default']['ENGINE'])"
        ]
        res_eng = subprocess.run(cmd_engine, cwd=str(REPO_ROOT), env=env, capture_output=True, text=True)
        if res_eng.returncode == 0:
            engine_str = res_eng.stdout.strip()
            if "sqlite" in engine_str.lower():
                db_engine = "SQLite"
            elif "postgresql" in engine_str.lower() or "postgres" in engine_str.lower():
                db_engine = "PostgreSQL"
            else:
                db_engine = engine_str
    except Exception:
        pass
    return db_engine


def run_pytest_suite(
    target_path: Path,
    verbose: bool = False,
    failfast: bool = False,
    keyword: Optional[str] = None,
    extra_args: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Runs a pytest target via subprocess."""
    start_time = time.time()
    
    if not target_path.exists():
        return {
            "name": str(target_path.name),
            "status": "SKIPPED",
            "exit_code": 0,
            "duration": 0.0,
            "stdout": f"File not found: {target_path}",
            "stderr": "",
            "message": f"Test target file {target_path.name} not found (pending creation or skipped)"
        }

    cmd = [sys.executable, "-m", "pytest", str(target_path)]
    
    if verbose:
        cmd.append("-v")
    if failfast:
        cmd.append("-x")
    if keyword:
        cmd.extend(["-k", keyword])
    
    # Avoid config collisions with reuse-db if running locally
    cmd.extend(["-o", "addopts="])
    
    if extra_args:
        cmd.extend(extra_args)

    env = get_environment()
    
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        duration = time.time() - start_time
        status = "PASSED" if proc.returncode == 0 else "FAILED"
        return {
            "name": str(target_path.name),
            "status": status,
            "exit_code": proc.returncode,
            "duration": round(duration, 2),
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "command": " ".join(cmd)
        }
    except Exception as exc:
        duration = time.time() - start_time
        return {
            "name": str(target_path.name),
            "status": "ERROR",
            "exit_code": 1,
            "duration": round(duration, 2),
            "stdout": "",
            "stderr": str(exc),
            "message": f"Failed to execute pytest: {exc}"
        }


def run_django_suite(
    command_args: List[str],
    verbose: bool = False,
    failfast: bool = False
) -> Dict[str, Any]:
    """Runs a Django test command via subprocess."""
    start_time = time.time()
    cmd = [sys.executable] + command_args
    if verbose:
        cmd.append("-v2")
    if failfast:
        cmd.append("--failfast")

    env = get_environment()
    
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        duration = time.time() - start_time
        status = "PASSED" if proc.returncode == 0 else "FAILED"
        return {
            "name": " ".join(command_args[2:]),
            "status": status,
            "exit_code": proc.returncode,
            "duration": round(duration, 2),
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "command": " ".join(cmd)
        }
    except Exception as exc:
        duration = time.time() - start_time
        return {
            "name": " ".join(command_args),
            "status": "ERROR",
            "exit_code": 1,
            "duration": round(duration, 2),
            "stdout": "",
            "stderr": str(exc),
            "message": f"Failed to execute django test: {exc}"
        }


def print_summary_table(results: List[Dict[str, Any]], total_duration: float, db_engine: str = "SQLite"):
    """Prints a structured summary table of all executed suites."""
    print("\n" + "=" * 88)
    title = f"TAFAKOR MONOREPO - E2E TEST RUNNER (Engine: {db_engine})"
    print(f"{Colors.BOLD}{Colors.CYAN}{title:^88}{Colors.RESET}")
    print("=" * 88)
    print(f"{'Suite / Target':<38} | {'Status':<12} | {'Duration':<10} | {'Exit Code':<10}")
    print("-" * 38 + "-+-" + "-" * 12 + "-+-" + "-" * 10 + "-+-" + "-" * 10)

    passed_count = 0
    failed_count = 0
    skipped_count = 0
    error_count = 0

    for r in results:
        status = r["status"]
        if status == "PASSED":
            status_str = f"{Colors.GREEN}{Colors.BOLD}PASSED{Colors.RESET}"
            passed_count += 1
        elif status == "FAILED":
            status_str = f"{Colors.RED}{Colors.BOLD}FAILED{Colors.RESET}"
            failed_count += 1
        elif status == "SKIPPED":
            status_str = f"{Colors.YELLOW}SKIPPED{Colors.RESET}"
            skipped_count += 1
        else:
            status_str = f"{Colors.RED}ERROR{Colors.RESET}"
            error_count += 1

        name_display = r["name"]
        if len(name_display) > 36:
            name_display = name_display[:33] + "..."

        dur_str = f"{r['duration']:.2f}s"
        code_str = str(r["exit_code"])
        print(f"{name_display:<38} | {status_str:<21} | {dur_str:<10} | {code_str:<10}")

    print("-" * 88)
    overall_status = f"{Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED{Colors.RESET}" if (failed_count == 0 and error_count == 0) else f"{Colors.RED}{Colors.BOLD}SOME TESTS FAILED{Colors.RESET}"
    print(f"Total Suites: {len(results)} | Passed: {passed_count} | Failed: {failed_count} | Skipped: {skipped_count} | Errors: {error_count}")
    print(f"Total Execution Time: {total_duration:.2f}s | Result: {overall_status}")
    print("=" * 88 + "\n")


def build_parser() -> argparse.ArgumentParser:
    """Builds argument parser for the test runner CLI."""
    parser = argparse.ArgumentParser(
        prog="test_runner.py",
        description="Unified CLI Test Runner for Tafakor Monorepo E2E and Non-Regression Test Suites."
    )
    
    # Tier and target selection
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "--tier", "-t",
        nargs="+",
        choices=["1", "2", "3", "4"],
        help="Run specific E2E tier(s): 1 (Feature Coverage), 2 (Boundary), 3 (Pairwise), 4 (Workloads)"
    )
    group.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all E2E test tiers (1..4) + core non-regression test suite"
    )
    group.add_argument(
        "--non-regression", "-nr",
        action="store_true",
        help="Run only the core platform non-regression test suite (Accounts, Notes, Donations)"
    )
    group.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available test tiers and suites without running"
    )

    # Execution modifiers
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--failfast", "-x",
        action="store_true",
        help="Stop execution on first failure"
    )
    parser.add_argument(
        "--keyword", "-k",
        type=str,
        default=None,
        help="Filter pytest test cases by keyword expression"
    )
    parser.add_argument(
        "--report", "-r",
        type=str,
        default=None,
        help="Save execution summary report to specified JSON file"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check targets and report planned execution without running tests"
    )

    return parser


def main() -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    if args.no_color or (os.name == 'nt' and not os.getenv('WT_SESSION') and not os.getenv('ANSICON')):
        pass

    # Handle --list
    if args.list:
        print("\nAvailable Test Tiers & Suites:")
        print("-" * 60)
        for tier_num, info in TIER_SUITES.items():
            print(f"  Tier {tier_num}: {info['name']}")
            print(f"          Target: {info['file'].relative_to(REPO_ROOT)}")
            print(f"          Detail: {info['description']}\n")
        print("  Non-Regression:")
        for nr in NON_REGRESSION_TARGETS:
            print(f"          Name: {nr['name']}")
            print(f"          Detail: {nr['description']}\n")
        return 0

    # Determine execution plan
    suites_to_run: List[Dict[str, Any]] = []

    if args.all:
        for tier_num in ["1", "2", "3", "4"]:
            suites_to_run.append(TIER_SUITES[tier_num])
        suites_to_run.extend(NON_REGRESSION_TARGETS)
    elif args.tier:
        for t in args.tier:
            if t in TIER_SUITES:
                suites_to_run.append(TIER_SUITES[t])
    elif args.non_regression:
        suites_to_run.extend(NON_REGRESSION_TARGETS)
    else:
        # Default behavior if no arguments provided: run all tiers
        for tier_num in ["1", "2", "3", "4"]:
            suites_to_run.append(TIER_SUITES[tier_num])

    if args.dry_run:
        print("\n[Dry Run] Planned Test Suites to Execute:")
        for s in suites_to_run:
            target = s.get("file", s.get("command_args"))
            print(f"  - {s['name']}: {target}")
        return 0

    db_engine = ensure_database_ready()

    print(f"\n{Colors.BOLD}{Colors.HEADER}Starting Tafakor Test Runner (Engine: {db_engine})...{Colors.RESET}")
    print(f"Target count: {len(suites_to_run)} test suite(s)")

    results: List[Dict[str, Any]] = []
    overall_start_time = time.time()
    exit_code = 0

    for suite in suites_to_run:
        print(f"\n{Colors.CYAN}---> Running {suite['name']}...{Colors.RESET}")
        
        if suite["type"] == "pytest":
            res = run_pytest_suite(
                target_path=suite["file"],
                verbose=args.verbose,
                failfast=args.failfast,
                keyword=args.keyword
            )
        elif suite["type"] == "django":
            res = run_django_suite(
                command_args=suite["command_args"],
                verbose=args.verbose,
                failfast=args.failfast
            )
        else:
            res = {
                "name": suite["name"],
                "status": "ERROR",
                "exit_code": 1,
                "duration": 0.0,
                "message": f"Unknown suite type: {suite['type']}"
            }

        results.append(res)

        if res["status"] == "PASSED":
            print(f"{Colors.GREEN}[PASS] {suite['name']} PASSED ({res['duration']:.2f}s){Colors.RESET}")
            if args.verbose and res.get("stdout"):
                print(res["stdout"])
        elif res["status"] == "SKIPPED":
            print(f"{Colors.YELLOW}[SKIP] {suite['name']} SKIPPED: {res.get('message')}{Colors.RESET}")
        else:
            print(f"{Colors.RED}[FAIL] {suite['name']} FAILED (Exit Code: {res['exit_code']}){Colors.RESET}")
            if res.get("stdout"):
                print(res["stdout"])
            if res.get("stderr"):
                print(f"{Colors.RED}{res['stderr']}{Colors.RESET}")
            exit_code = 1
            if args.failfast:
                print(f"\n{Colors.RED}Fail-fast triggered. Aborting remaining suites.{Colors.RESET}")
                break

    total_duration = time.time() - overall_start_time
    print_summary_table(results, total_duration, db_engine=db_engine)

    # Save JSON report if requested
    if args.report:
        report_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_duration_seconds": round(total_duration, 2),
            "database_engine": db_engine,
            "exit_code": exit_code,
            "results": results
        }
        try:
            report_path = Path(args.report).resolve()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"Execution report successfully written to: {report_path}")
        except Exception as e:
            print(f"{Colors.RED}Failed to write JSON report: {e}{Colors.RESET}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
