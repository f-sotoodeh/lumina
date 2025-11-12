#!/usr/bin/env python3
"""
Automated Backend Testing Script
Tests code structure, imports, endpoints, models, and schemas
"""

import sys
import os
import importlib.util
import ast
from pathlib import Path
from typing import List, Dict, Tuple

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, msg: str):
        self.passed.append(msg)
        print(f"{GREEN}✓{RESET} {msg}")
    
    def add_fail(self, msg: str):
        self.failed.append(msg)
        print(f"{RED}✗{RESET} {msg}")
    
    def add_warning(self, msg: str):
        self.warnings.append(msg)
        print(f"{YELLOW}⚠{RESET} {msg}")
    
    def summary(self):
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test Summary{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        print(f"{GREEN}Passed: {len(self.passed)}{RESET}")
        print(f"{RED}Failed: {len(self.failed)}{RESET}")
        print(f"{YELLOW}Warnings: {len(self.warnings)}{RESET}")
        
        if self.failed:
            print(f"\n{RED}Failed Tests:{RESET}")
            for msg in self.failed:
                print(f"  - {msg}")
        
        if self.warnings:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for msg in self.warnings:
                print(f"  - {msg}")
        
        return len(self.failed) == 0

def check_syntax(file_path: Path) -> Tuple[bool, str]:
    """Check Python syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ast.parse(f.read(), filename=str(file_path))
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error: {e.msg} at line {e.lineno}"

def check_imports(file_path: Path, base_path: Path) -> Tuple[bool, List[str]]:
    """Check if imports are valid"""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        __import__(alias.name)
                    except ImportError:
                        # Check if it's a local import
                        if not alias.name.startswith('app.'):
                            errors.append(f"Cannot import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    try:
                        __import__(node.module)
                    except ImportError:
                        # Check if it's a local import
                        if not node.module.startswith('app.'):
                            errors.append(f"Cannot import: {node.module}")
    except Exception as e:
        errors.append(f"Error checking imports: {e}")
    
    return len(errors) == 0, errors

def find_endpoints(file_path: Path) -> List[Dict]:
    """Find all router endpoints"""
    endpoints = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Find @router decorators using regex
        import re
        # Match @router.get("/path") or @router.post("/path") patterns
        pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            # Find function name after the decorator
            start_pos = match.end()
            next_lines = content[start_pos:start_pos+500].split('\n')
            for line in next_lines[:10]:
                func_match = re.search(r'^(async\s+)?def\s+(\w+)', line.strip())
                if func_match:
                    endpoints.append({
                        'method': method,
                        'path': path,
                        'function': func_match.group(2),
                        'file': file_path.name
                    })
                    break
    except Exception as e:
        pass
    
    return endpoints

def check_model_indexes(file_path: Path) -> Tuple[bool, List[str]]:
    """Check if model has indexes defined"""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if Settings class exists
        if 'class Settings:' not in content:
            issues.append("No Settings class found")
        elif 'indexes' not in content:
            issues.append("No indexes defined in Settings")
    except Exception as e:
        issues.append(f"Error checking model: {e}")
    
    return len(issues) == 0, issues

def main():
    result = TestResult()
    # Get the backend directory (where this script is located)
    backend_dir = Path(__file__).parent
    base_path = backend_dir / "app"
    
    if not base_path.exists():
        result.add_fail(f"Backend app directory not found: {base_path}")
        return result.summary()
    
    print(f"{BLUE}Starting Backend Code Analysis...{RESET}\n")
    
    # 1. Syntax checking
    print(f"{BLUE}1. Syntax Checking{RESET}")
    python_files = list(base_path.rglob("*.py"))
    syntax_errors = []
    for py_file in python_files:
        if "__pycache__" in str(py_file):
            continue
        is_valid, error = check_syntax(py_file)
        if not is_valid:
            syntax_errors.append(f"{py_file.relative_to(base_path.parent)}: {error}")
    
    if syntax_errors:
        for error in syntax_errors:
            result.add_fail(error)
    else:
        result.add_pass(f"All {len(python_files)} Python files have valid syntax")
    
    # 2. Check critical files exist
    print(f"\n{BLUE}2. File Structure{RESET}")
    critical_files = [
        "main.py",
        "models/user.py",
        "models/deck.py",
        "models/step.py",
        "models/comment.py",
        "models/file.py",
        "models/share.py",
        "schemas/user.py",
        "schemas/deck.py",
        "schemas/step.py",
        "schemas/file.py",
        "schemas/response.py",
        "core/config.py",
        "core/security.py",
        "core/email.py",
        "core/i18n.py",
        "dependencies.py",
        "utils/response.py",
        "utils/minio_client.py",
        "utils/thumbnail.py",
        "utils/deck_thumbnail.py",
        "utils/export.py",
        "api/v1/router.py",
        "api/v1/endpoints/auth.py",
        "api/v1/endpoints/user.py",
        "api/v1/endpoints/decks.py",
        "api/v1/endpoints/steps.py",
        "api/v1/endpoints/comments.py",
        "api/v1/endpoints/files.py",
        "api/v1/endpoints/shares.py",
        "api/v1/endpoints/admin.py",
        "api/v1/endpoints/fonts.py",
        "api/v1/endpoints/preview.py",
        "locales/en.yaml",
        "data/fonts.json"
    ]
    
    for file_path in critical_files:
        full_path = base_path / file_path
        if full_path.exists():
            result.add_pass(f"File exists: {file_path}")
        else:
            result.add_fail(f"File missing: {file_path}")
    
    # 3. Check endpoints
    print(f"\n{BLUE}3. Endpoint Analysis{RESET}")
    endpoint_files = [
        base_path / "api/v1/endpoints/auth.py",
        base_path / "api/v1/endpoints/user.py",
        base_path / "api/v1/endpoints/decks.py",
        base_path / "api/v1/endpoints/steps.py",
        base_path / "api/v1/endpoints/comments.py",
        base_path / "api/v1/endpoints/files.py",
        base_path / "api/v1/endpoints/shares.py",
        base_path / "api/v1/endpoints/admin.py",
        base_path / "api/v1/endpoints/fonts.py",
        base_path / "api/v1/endpoints/preview.py"
    ]
    
    all_endpoints = []
    for ep_file in endpoint_files:
        if ep_file.exists():
            endpoints = find_endpoints(ep_file)
            all_endpoints.extend(endpoints)
            result.add_pass(f"{ep_file.name}: {len(endpoints)} endpoints found")
        else:
            result.add_fail(f"Endpoint file missing: {ep_file.name}")
    
    # Expected endpoints count
    expected_counts = {
        "auth.py": 6,
        "user.py": 5,
        "decks.py": 11,
        "steps.py": 7,
        "comments.py": 5,
        "files.py": 4,
        "shares.py": 3,
        "admin.py": 4,
        "fonts.py": 1,
        "preview.py": 1
    }
    
    for ep_file in endpoint_files:
        if ep_file.exists():
            endpoints = find_endpoints(ep_file)
            expected = expected_counts.get(ep_file.name, 0)
            if len(endpoints) >= expected:
                result.add_pass(f"{ep_file.name}: Expected {expected}, found {len(endpoints)}")
            else:
                result.add_warning(f"{ep_file.name}: Expected {expected}, found {len(endpoints)}")
    
    # 4. Check models have indexes
    print(f"\n{BLUE}4. Model Indexes{RESET}")
    model_files = [
        base_path / "models/user.py",
        base_path / "models/deck.py",
        base_path / "models/step.py",
        base_path / "models/comment.py",
        base_path / "models/file.py",
        base_path / "models/share.py"
    ]
    
    for model_file in model_files:
        if model_file.exists():
            is_valid, issues = check_model_indexes(model_file)
            if is_valid:
                result.add_pass(f"{model_file.name}: Indexes defined")
            else:
                for issue in issues:
                    result.add_warning(f"{model_file.name}: {issue}")
        else:
            result.add_fail(f"Model file missing: {model_file.name}")
    
    # 5. Check schemas
    print(f"\n{BLUE}5. Schema Files{RESET}")
    schema_files = [
        base_path / "schemas/user.py",
        base_path / "schemas/deck.py",
        base_path / "schemas/step.py",
        base_path / "schemas/file.py",
        base_path / "schemas/response.py"
    ]
    
    for schema_file in schema_files:
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                content = f.read()
                if 'BaseModel' in content:
                    result.add_pass(f"{schema_file.name}: Contains BaseModel")
                else:
                    result.add_warning(f"{schema_file.name}: No BaseModel found")
        else:
            result.add_fail(f"Schema file missing: {schema_file.name}")
    
    # 6. Check utilities
    print(f"\n{BLUE}6. Utility Functions{RESET}")
    utils_to_check = {
        "utils/minio_client.py": ["upload_file", "get_presigned_url", "upload_avatar", "upload_deck_file"],
        "utils/thumbnail.py": ["create_thumbnail", "is_image_type"],
        "utils/deck_thumbnail.py": ["generate_deck_thumbnail", "schedule_thumbnail_regeneration"],
        "utils/export.py": ["export_deck_to_html"],
        "utils/response.py": ["api_response"],
        "dependencies.py": ["get_current_user", "get_current_user_optional", "require_admin", "check_deck_access"]
    }
    
    for util_file, functions in utils_to_check.items():
        full_path = base_path / util_file
        if full_path.exists():
            with open(full_path, 'r') as f:
                content = f.read()
                for func in functions:
                    if f"def {func}" in content or f"async def {func}" in content:
                        result.add_pass(f"{util_file}: {func} exists")
                    else:
                        result.add_fail(f"{util_file}: {func} missing")
        else:
            result.add_fail(f"Utility file missing: {util_file}")
    
    # 7. Check core modules
    print(f"\n{BLUE}7. Core Modules{RESET}")
    core_checks = {
        "core/config.py": ["Settings", "settings"],
        "core/security.py": ["create_access_token", "create_refresh_token", "verify_password", "get_password_hash"],
        "core/email.py": ["send_otp_email"],
        "core/i18n.py": ["Translator"]
    }
    
    for core_file, items in core_checks.items():
        full_path = base_path / core_file
        if full_path.exists():
            with open(full_path, 'r') as f:
                content = f.read()
                for item in items:
                    if item in content:
                        result.add_pass(f"{core_file}: {item} exists")
                    else:
                        result.add_fail(f"{core_file}: {item} missing")
        else:
            result.add_fail(f"Core file missing: {core_file}")
    
    # 8. Check main.py
    print(f"\n{BLUE}8. Main Application{RESET}")
    main_file = base_path / "main.py"
    if main_file.exists():
        with open(main_file, 'r') as f:
            content = f.read()
        checks = {
            "FastAPI": "FastAPI app created",
            "CORSMiddleware": "CORS configured",
            "Limiter": "Rate limiting configured",
            "init_beanie": "Database initialization",
            "create_bucket_if_not_exists": "MinIO initialization",
            "api_router": "API router included"
        }
        for check, desc in checks.items():
            if check in content:
                result.add_pass(f"main.py: {desc}")
            else:
                result.add_fail(f"main.py: {desc} missing")
    else:
        result.add_fail("main.py missing")
    
    # 9. Check router includes all endpoints
    print(f"\n{BLUE}9. Router Configuration{RESET}")
    router_file = base_path / "api/v1/router.py"
    if router_file.exists():
        with open(router_file, 'r') as f:
            content = f.read()
        routers = ["auth", "user", "decks", "steps", "comments", "files", "shares", "admin", "fonts", "preview"]
        for router in routers:
            if router in content:
                result.add_pass(f"router.py: {router} router included")
            else:
                result.add_fail(f"router.py: {router} router missing")
    else:
        result.add_fail("router.py missing")
    
    # 10. Check data files
    print(f"\n{BLUE}10. Data Files{RESET}")
    data_files = {
        "locales/en.yaml": "English translations",
        "data/fonts.json": "Fonts data"
    }
    
    for data_file, desc in data_files.items():
        full_path = base_path / data_file
        if full_path.exists():
            if full_path.stat().st_size > 0:
                result.add_pass(f"{data_file}: {desc} exists and not empty")
            else:
                result.add_warning(f"{data_file}: {desc} exists but is empty")
        else:
            result.add_fail(f"{data_file}: {desc} missing")
    
    return result.summary()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

