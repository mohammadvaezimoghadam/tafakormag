import ast
import re
import glob

def analyze_suite(filename):
    with open(filename, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    tree = ast.parse(content, filename=filename)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name.startswith('Test')]
    
    print('=' * 80)
    print(f'ANALYZING: {filename} ({len(classes)} Test Classes)')
    print('=' * 80)
    
    for cls in classes:
        methods = [m for m in cls.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test')]
        print(f"\n--- {cls.name} ({len(methods)} tests) ---")
        
        for m in methods:
            m_code = ast.get_source_segment(content, m) or ''
            
            flags = []
            if 'APIClient' in m_code or 'client.' in m_code:
                flags.append('API')
            if any(x in m_code for x in ['objects.create', 'objects.get', 'objects.filter', 'objects.all', 'objects.update', 'objects.bulk_create']):
                flags.append('ORM')
            if 'ManifestValidator' in m_code or 'validate_manifest' in m_code:
                flags.append('Validator')
            if 'PluginRegistry' in m_code or 'registry.' in m_code or 'plugin_registry' in m_code:
                flags.append('Registry')
            if 'QuranNormalizer' in m_code or 'normalizer' in m_code.lower():
                flags.append('Normalizer')
            if 'QuranReferenceFormatter' in m_code or 'format_markdown' in m_code:
                flags.append('Formatter')
            if 'import_quran' in m_code or 'call_command' in m_code:
                flags.append('Importer')
            if 'QuranSearchService' in m_code or 'search' in m_code.lower():
                flags.append('Search')
            
            local_classes = [n.name for n in ast.walk(m) if isinstance(n, ast.ClassDef)]
            if local_classes:
                flags.append(f'LOCAL_CLS:{local_classes}')
            
            local_funcs = [n.name for n in m.body if isinstance(n, ast.FunctionDef)]
            if local_funcs:
                flags.append(f'LOCAL_FUNC:{local_funcs}')
            
            flag_str = ', '.join(flags) if flags else 'NO_CORE_TARGET'
            print(f"  Line {m.lineno:4d}: {m.name:<55} -> {flag_str}")

for f in ['tests/e2e/test_tier1_feature_coverage.py', 'tests/e2e/test_tier2_boundary_cases.py', 'tests/e2e/test_tier3_pairwise_combinations.py', 'tests/e2e/test_tier4_real_world_workloads.py']:
    analyze_suite(f)
