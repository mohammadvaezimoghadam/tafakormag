import ast
import re

files = [
    'tests/e2e/test_tier1_feature_coverage.py',
    'tests/e2e/test_tier2_boundary_cases.py',
    'tests/e2e/test_tier3_pairwise_combinations.py',
    'tests/e2e/test_tier4_real_world_workloads.py',
]

print("="*80)
print("THOROUGH FORENSIC SCAN")
print("="*80)

for fpath in files:
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    tree = ast.parse(content, filename=fpath)
    
    print(f"\nScanning {fpath}...")
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test'):
            segment = ast.get_source_segment(content, node) or ''
            
            issues = []
            
            # 1. Local classes
            local_classes = [n.name for n in ast.walk(node) if isinstance(n, ast.ClassDef)]
            if local_classes:
                issues.append(f"Local Class Definition: {local_classes}")
                
            # 2. Local functions
            local_funcs = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            if local_funcs:
                issues.append(f"Local Function Definition: {local_funcs}")
                
            # 3. Trivial flag assignment and assert (e.g. var = True; assert var)
            lines = segment.splitlines()
            for idx, l in enumerate(lines):
                if re.search(r'\b(\w+)\s*=\s*(True|False)', l):
                    var_name = re.search(r'\b(\w+)\s*=\s*(True|False)', l).group(1)
                    # Check next 3 lines for assert var_name
                    for next_l in lines[idx+1:idx+4]:
                        if re.search(r'assert\s+(' + var_name + r'|not\s+' + var_name + r'|' + var_name + r'\s+is\s+(True|False))', next_l):
                            issues.append(f"Trivial Flag Assertion: '{l.strip()}' -> '{next_l.strip()}'")
                            
            # 4. is_valid pattern
            for l in lines:
                if 'is_valid' in l and 'assert' in l:
                    issues.append(f"Local is_valid assertion: '{l.strip()}'")
                    
            # 5. In-memory promise / dictionary state tests
            if 'in_flight_promises' in segment:
                issues.append("In-memory dictionary promise simulation")
            if 'active_routes' in segment and 'cleaned_routes' in segment:
                issues.append("In-memory dictionary route filtering assertion")
            if 'corrupted_json_str' in segment:
                issues.append("Local json.loads try-except simulation")
            if 'surah_data' in segment and 'display_translation' in segment:
                issues.append("Local dict string fallback simulation")
            if 'corrupted_route' in segment and 'fallback_rendered' in segment:
                issues.append("Local corrupted route fallback flag simulation")
                
            if issues:
                print(f"  [VIOLATION] Line {node.lineno}: {node.name}")
                for iss in issues:
                    print(f"      - {iss}")
