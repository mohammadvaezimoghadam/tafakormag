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

inspect_functions('tests/e2e/test_tier2_boundary_cases.py', [
    984, 995, 1002, 1007, 1023, # F11 Frontend Core
    1043, 1052, 1063, 1071, 1079, # F12 Dynamic lazy loading
    1186, 1193, 1200, 1216, 1225, # F14 Quran views
    1250, 1261, 1273, 1287, # F15 Composer action
    1340, 1353, 1360, 1371, 1386 # F16 Test runner
])

inspect_functions('tests/e2e/test_tier3_pairwise_combinations.py', [
    513, 653
])

inspect_functions('tests/e2e/test_tier4_real_world_workloads.py', [
    484, 630, 688
])
