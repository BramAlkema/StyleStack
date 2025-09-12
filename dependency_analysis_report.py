#!/usr/bin/env python3
"""
Comprehensive Dependency Analysis Report for StyleStack
Generates detailed technical specification for import mapping and cross-references
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def load_analysis():
    """Load the import analysis data"""
    with open('/Users/ynse/projects/StyleStack/import_analysis.json', 'r') as f:
        return json.load(f)

def analyze_critical_paths(data: Dict) -> Dict:
    """Analyze critical dependency paths"""
    dep_graph = data['internal_dependency_graph']
    reverse_deps = data['reverse_dependencies']
    
    # Find modules that are essential (many depend on them)
    critical_modules = []
    for module, dependents in reverse_deps.items():
        if len(dependents) >= 3:  # Threshold for critical
            critical_modules.append({
                'module': module,
                'dependent_count': len(dependents),
                'dependents': list(dependents),
                'owns_dependencies': list(dep_graph.get(module, []))
            })
    
    # Sort by criticality
    critical_modules.sort(key=lambda x: x['dependent_count'], reverse=True)
    
    return {
        'critical_modules': critical_modules,
        'dependency_layers': analyze_dependency_layers(dep_graph),
        'isolated_modules': find_isolated_modules(dep_graph, reverse_deps)
    }

def analyze_dependency_layers(dep_graph: Dict) -> Dict:
    """Analyze modules by dependency layers (foundation -> application)"""
    layers = {
        'foundation': [],      # No internal dependencies
        'core': [],           # Depends only on foundation
        'services': [],       # Depends on core/foundation
        'integration': [],    # Depends on services
        'application': []     # Top-level modules
    }
    
    for module, deps in dep_graph.items():
        internal_deps = [d for d in deps if d in dep_graph]
        
        if not internal_deps:
            layers['foundation'].append(module)
        elif len(internal_deps) <= 2 and all(d in layers['foundation'] for d in internal_deps):
            layers['core'].append(module)
        elif len(internal_deps) <= 4:
            layers['services'].append(module)
        elif len(internal_deps) <= 6:
            layers['integration'].append(module)
        else:
            layers['application'].append(module)
    
    return layers

def find_isolated_modules(dep_graph: Dict, reverse_deps: Dict) -> List[str]:
    """Find modules with no dependencies and no dependents"""
    isolated = []
    all_modules = set(dep_graph.keys()) | set(reverse_deps.keys())
    
    for module in all_modules:
        has_deps = bool(dep_graph.get(module, []))
        has_dependents = bool(reverse_deps.get(module, []))
        
        if not has_deps and not has_dependents:
            isolated.append(module)
    
    return isolated

def analyze_external_dependencies(data: Dict) -> Dict:
    """Analyze external dependency patterns"""
    ext_deps = data['external_dependencies']
    
    categories = {
        'standard_library': [],
        'xml_processing': [],
        'data_processing': [],
        'performance': [],
        'office_automation': [],
        'security': [],
        'google_apis': [],
        'other': []
    }
    
    std_lib = {'typing', 'pathlib', 'dataclasses', 'json', 'time', 'logging', 
               're', 'sys', 'threading', 'zipfile', 'enum', 'collections',
               'datetime', 'os', 'tempfile', 'hashlib', 'contextlib', 
               'concurrent.futures', 'uuid', 'argparse', 'io', 'weakref',
               'sqlite3', 'math', 'subprocess', 'multiprocessing', 'random',
               'statistics', 'copy', 'base64', 'hmac', 'queue', 'gc',
               'functools', 'traceback', 'glob', 'pickle', 'zlib', 
               'tracemalloc', 'pstats', 'doctest', 'mmap', 'smtplib',
               'urllib.request', 'urllib.error', 'abc', 'importlib.metadata',
               'fnmatch', 'unittest'}
    
    xml_libs = {'xml.etree.ElementTree', 'lxml', 'lxml.etree', 'xml.parsers.expat', 'xmltodict'}
    data_libs = {'json', 'dataclasses', 'collections', 'sqlite3'}
    perf_libs = {'psutil', 'concurrent.futures', 'threading', 'multiprocessing', 'time'}
    office_libs = {'docx', 'openpyxl', 'pptx', 'PIL'}
    security_libs = {'cryptography.hazmat.primitives.ciphers', 'cryptography.hazmat.backends', 'hashlib', 'hmac'}
    google_libs = {'google.auth.transport.requests', 'google.oauth2', 'googleapiclient.discovery', 'google.auth.credentials'}
    
    for dep, count in ext_deps.items():
        if dep in std_lib:
            categories['standard_library'].append({'name': dep, 'usage_count': count})
        elif dep in xml_libs:
            categories['xml_processing'].append({'name': dep, 'usage_count': count})
        elif dep in data_libs:
            categories['data_processing'].append({'name': dep, 'usage_count': count})
        elif dep in perf_libs:
            categories['performance'].append({'name': dep, 'usage_count': count})
        elif dep in office_libs:
            categories['office_automation'].append({'name': dep, 'usage_count': count})
        elif dep in security_libs:
            categories['security'].append({'name': dep, 'usage_count': count})
        elif dep in google_libs:
            categories['google_apis'].append({'name': dep, 'usage_count': count})
        else:
            categories['other'].append({'name': dep, 'usage_count': count})
    
    # Sort each category by usage count
    for category in categories.values():
        category.sort(key=lambda x: x['usage_count'], reverse=True)
    
    return categories

def generate_module_profiles(data: Dict) -> Dict:
    """Generate detailed profiles for key modules"""
    key_modules = [
        'variable_resolver', 'ooxml_processor', 'token_integration_layer',
        'theme_resolver', 'variable_substitution', 'template_analyzer',
        'json_patch_parser', 'multi_format_ooxml_handler', 'transaction_pipeline',
        'core.types', 'handlers.types', 'substitution.types'
    ]
    
    profiles = {}
    dep_graph = data['internal_dependency_graph']
    reverse_deps = data['reverse_dependencies']
    
    for module in key_modules:
        profiles[module] = {
            'dependencies': list(dep_graph.get(module, [])),
            'dependents': list(reverse_deps.get(module, [])),
            'dependency_count': len(dep_graph.get(module, [])),
            'dependent_count': len(reverse_deps.get(module, [])),
            'criticality_score': len(reverse_deps.get(module, [])),
            'complexity_score': len(dep_graph.get(module, [])),
            'role': classify_module_role(module, dep_graph, reverse_deps)
        }
    
    return profiles

def classify_module_role(module: str, dep_graph: Dict, reverse_deps: Dict) -> str:
    """Classify the role of a module in the architecture"""
    deps = len(dep_graph.get(module, []))
    dependents = len(reverse_deps.get(module, []))
    
    if '.types' in module:
        return 'Type Definitions'
    elif dependents >= 5 and deps <= 2:
        return 'Foundation Service'
    elif dependents >= 3 and deps <= 5:
        return 'Core Service'
    elif deps >= 5:
        return 'Application/Integration Layer'
    elif dependents == 0 and deps >= 3:
        return 'Application Entry Point'
    elif dependents == 0 and deps <= 2:
        return 'Utility/Tool'
    else:
        return 'Service Component'

def generate_architecture_insights(data: Dict) -> Dict:
    """Generate architectural insights from dependency analysis"""
    dep_graph = data['internal_dependency_graph']
    reverse_deps = data['reverse_dependencies']
    
    # Calculate fan-in and fan-out metrics
    fan_metrics = {}
    for module in set(dep_graph.keys()) | set(reverse_deps.keys()):
        fan_out = len(dep_graph.get(module, []))  # Dependencies this module has
        fan_in = len(reverse_deps.get(module, []))  # Modules that depend on this
        fan_metrics[module] = {
            'fan_in': fan_in,
            'fan_out': fan_out,
            'stability': fan_in / (fan_in + fan_out) if (fan_in + fan_out) > 0 else 0,
            'abstractness': 0.5 if '.types' in module else 0.1  # Simple heuristic
        }
    
    # Identify architectural violations
    violations = []
    for module, metrics in fan_metrics.items():
        if metrics['fan_out'] > 7:  # High efferent coupling
            violations.append({
                'type': 'High Efferent Coupling',
                'module': module,
                'metric': metrics['fan_out'],
                'description': f"{module} depends on too many other modules ({metrics['fan_out']})"
            })
        
        if metrics['fan_in'] > 10:  # Very high afferent coupling
            violations.append({
                'type': 'Very High Afferent Coupling', 
                'module': module,
                'metric': metrics['fan_in'],
                'description': f"{module} is depended upon by too many modules ({metrics['fan_in']})"
            })
    
    return {
        'fan_metrics': fan_metrics,
        'architecture_violations': violations,
        'stability_analysis': {k: v['stability'] for k, v in fan_metrics.items()},
        'coupling_hotspots': sorted(fan_metrics.items(), key=lambda x: x[1]['fan_in'] + x[1]['fan_out'], reverse=True)[:10]
    }

def main():
    """Generate comprehensive dependency analysis report"""
    data = load_analysis()
    
    # Generate comprehensive analysis
    critical_analysis = analyze_critical_paths(data)
    external_analysis = analyze_external_dependencies(data)
    module_profiles = generate_module_profiles(data)
    architecture_insights = generate_architecture_insights(data)
    
    report = {
        'metadata': {
            'generated_at': '2025-01-11',
            'total_modules': data['summary']['total_internal_modules'],
            'total_external_deps': data['summary']['total_external_dependencies'],
            'circular_dependencies': data['summary']['circular_dependencies_found']
        },
        'critical_path_analysis': critical_analysis,
        'external_dependency_analysis': external_analysis,
        'key_module_profiles': module_profiles,
        'architecture_insights': architecture_insights,
        'raw_dependency_graph': data['internal_dependency_graph'],
        'raw_reverse_dependencies': data['reverse_dependencies'],
        'detailed_imports': data['detailed_imports']
    }
    
    # Save comprehensive report
    with open('/Users/ynse/projects/StyleStack/STYLESTACK_DEPENDENCY_ANALYSIS.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print executive summary
    print("StyleStack Dependency Analysis - Executive Summary")
    print("=" * 60)
    print(f"Total Modules Analyzed: {report['metadata']['total_modules']}")
    print(f"External Dependencies: {report['metadata']['total_external_deps']}")
    print(f"Circular Dependencies: {report['metadata']['circular_dependencies']}")
    print()
    
    print("CRITICAL MODULES (Infrastructure):")
    for mod in critical_analysis['critical_modules'][:5]:
        print(f"  • {mod['module']}: {mod['dependent_count']} dependents")
    print()
    
    print("ARCHITECTURE LAYERS:")
    for layer, modules in critical_analysis['dependency_layers'].items():
        print(f"  {layer.upper()}: {len(modules)} modules")
    print()
    
    print("TOP EXTERNAL DEPENDENCIES:")
    top_external = sorted(data['external_dependencies'].items(), key=lambda x: x[1], reverse=True)[:5]
    for dep, count in top_external:
        print(f"  • {dep}: {count} usages")
    print()
    
    print("ARCHITECTURE VIOLATIONS:")
    for violation in architecture_insights['architecture_violations'][:3]:
        print(f"  • {violation['type']}: {violation['module']} ({violation['metric']})")
    print()
    
    print(f"Detailed report saved to: STYLESTACK_DEPENDENCY_ANALYSIS.json")

if __name__ == "__main__":
    main()