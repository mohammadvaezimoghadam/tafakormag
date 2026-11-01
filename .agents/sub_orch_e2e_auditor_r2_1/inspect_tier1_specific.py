import ast
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def inspect_functions(filename, lines_to_check):
    with open(filename, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    tree = ast.parse(content, filename=filename)
    
    print('='*80)
    print('INSPECTING:', filename)
    print('='*80)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test'):
            if node.lineno in lines_to_check:
                source = ast.get_source_segment(content, node)
                print(f"\n--- Line {node.lineno}: {node.name} ---")
                print(source)

# Inspect Tier 1 Feature 09 (Cross-DB search), Feature 11, 12, 13, 14, 15, 16, 18
inspect_functions('tests/e2e/test_tier1_feature_coverage.py', [
    875, 885, 891, 897, 904, # F09 Search
    986, 1001, 1005, # F11 Frontend Core
    1019, 1032, 1038, 1042, # F12 Lazy loading
    1089, # F13 Marketplace
    1196, 1210, # F15 Composer
    1248, 1260, 1278, 1283, # F16 Test Runner
    1373 # F18 SQL Injection
])
