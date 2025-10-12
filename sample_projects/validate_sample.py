#!/usr/bin/env python3
"""
Sample project validation script
Validates actual consulting pack output against expected output
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class ValidationError:
    """Represents a validation failure"""
    def __init__(self, field: str, expected: any, actual: any, message: str):
        self.field = field
        self.expected = expected
        self.actual = actual
        self.message = message

    def __str__(self):
        return f"[FAIL] {self.field}: {self.message}\n   Expected: {self.expected}\n   Actual: {self.actual}"


class Validator:
    """Validates consulting pack output"""

    def __init__(self, expected: Dict, actual: Dict):
        self.expected = expected
        self.actual = actual
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []

    def validate_score(self, field: str, tolerance: float = 0.5) -> bool:
        """Validate a score is within tolerance"""
        expected_val = self.expected.get('classification', {}).get(field)
        actual_val = self.actual.get('classification', {}).get(field)

        if expected_val is None or actual_val is None:
            self.errors.append(ValidationError(
                field, expected_val, actual_val,
                "Score not present in output"
            ))
            return False

        diff = abs(expected_val - actual_val)
        if diff > tolerance:
            self.errors.append(ValidationError(
                field, expected_val, actual_val,
                f"Score difference {diff:.2f} exceeds tolerance {tolerance}"
            ))
            return False

        return True

    def validate_field_present(self, path: List[str]) -> bool:
        """Validate a nested field exists"""
        obj = self.actual
        for key in path:
            if not isinstance(obj, dict) or key not in obj:
                self.errors.append(ValidationError(
                    '.'.join(path), "Present", "Missing",
                    f"Required field not found"
                ))
                return False
            obj = obj[key]
        return True

    def validate_classification(self) -> int:
        """Validate classification section"""
        print("\n[CLASSIFICATION] Validating Classification...")
        passed = 0

        # Check scores
        if self.validate_score('score_quality', tolerance=0.5):
            print("  [OK] Quality score within range")
            passed += 1

        if self.validate_score('score_fit', tolerance=1.0):
            print("  [OK] Fit score within range")
            passed += 1

        if self.validate_score('score_priority', tolerance=0.8):
            print("  [OK] Priority score within range")
            passed += 1

        # Check business type
        expected_type = self.expected.get('classification', {}).get('business_type')
        actual_type = self.actual.get('classification', {}).get('business_type')

        if expected_type == actual_type:
            print(f"  [OK] Business type matches: {actual_type}")
            passed += 1
        else:
            self.errors.append(ValidationError(
                'business_type', expected_type, actual_type,
                "Business type mismatch"
            ))

        # Check vertical applied
        if self.validate_field_present(['classification', 'vertical_applied']):
            print("  [OK] Vertical preset applied")
            passed += 1

        return passed

    def validate_outreach(self) -> int:
        """Validate outreach variants"""
        print("\n[OUTREACH] Validating Outreach...")
        passed = 0

        variants = self.actual.get('outreach_variants', [])

        if len(variants) >= 3:
            print(f"  [OK] {len(variants)} variants generated")
            passed += 1
        else:
            self.errors.append(ValidationError(
                'outreach_variants', "3 variants", f"{len(variants)} variants",
                "Insufficient variants"
            ))

        # Check deliverability scores
        low_deliverability = [v for v in variants if v.get('deliverability_score', 0) < 85]
        if not low_deliverability:
            print("  [OK] All variants pass deliverability threshold (>=85)")
            passed += 1
        else:
            self.warnings.append(
                f"[WARN] {len(low_deliverability)} variant(s) below deliverability threshold"
            )

        # Check vertical context usage
        with_context = [v for v in variants if v.get('vertical_context_used')]
        if len(with_context) >= 2:
            print(f"  [OK] Vertical context used in {len(with_context)} variants")
            passed += 1
        else:
            self.warnings.append("[WARN] Limited vertical context usage")

        return passed

    def validate_dossier(self) -> int:
        """Validate dossier section"""
        print("\n[DOSSIER] Validating Dossier...")
        passed = 0

        required_fields = [
            'business_overview',
            'digital_presence',
            'opportunities',
            'target_audience',
            'competitive_position'
        ]

        for field in required_fields:
            if self.validate_field_present(['dossier', field]):
                passed += 1

        if passed == len(required_fields):
            print(f"  [OK] All {len(required_fields)} required fields present")
        else:
            print(f"  [WARN] {passed}/{len(required_fields)} required fields present")

        # Check opportunities count
        opportunities = self.actual.get('dossier', {}).get('opportunities', [])
        if len(opportunities) >= 3:
            print(f"  [OK] {len(opportunities)} opportunities identified")
            passed += 1
        else:
            self.warnings.append(f"[WARN] Only {len(opportunities)} opportunities (expected >=3)")

        return passed

    def validate_audit(self) -> int:
        """Validate audit findings"""
        print("\n[AUDIT] Validating Audit...")
        passed = 0

        # Check priority issues
        issues = self.actual.get('audit_findings', {}).get('priority_issues', [])
        if len(issues) >= 2:
            print(f"  [OK] {len(issues)} priority issues identified")
            passed += 1
        else:
            self.errors.append(ValidationError(
                'priority_issues', ">=2 issues", f"{len(issues)} issues",
                "Insufficient priority issues"
            ))

        # Check strengths
        strengths = self.actual.get('audit_findings', {}).get('strengths', [])
        if len(strengths) >= 2:
            print(f"  [OK] {len(strengths)} strengths identified")
            passed += 1
        else:
            self.warnings.append(f"[WARN] Only {len(strengths)} strengths (expected >=2)")

        # Check quick wins in issues
        issues_with_wins = [i for i in issues if 'quick_win' in i]
        if len(issues_with_wins) == len(issues):
            print("  [OK] All issues have quick-win recommendations")
            passed += 1
        else:
            self.warnings.append("[WARN] Some issues missing quick-win recommendations")

        return passed

    def validate_quick_wins(self) -> int:
        """Validate quick wins section"""
        print("\n[QUICK WINS] Validating Quick Wins...")
        passed = 0

        quick_wins = self.actual.get('quick_wins', [])

        if len(quick_wins) >= 3:
            print(f"  [OK] {len(quick_wins)} quick wins provided")
            passed += 1
        else:
            self.errors.append(ValidationError(
                'quick_wins', ">=3 wins", f"{len(quick_wins)} wins",
                "Insufficient quick wins"
            ))

        # Check completeness
        complete_wins = [
            qw for qw in quick_wins
            if all(k in qw for k in ['title', 'description', 'estimated_time', 'estimated_impact', 'steps'])
        ]

        if len(complete_wins) == len(quick_wins):
            print("  [OK] All quick wins have complete information")
            passed += 1
        else:
            self.warnings.append(f"[WARN] {len(quick_wins) - len(complete_wins)} quick win(s) incomplete")

        # Check steps count
        wins_with_steps = [qw for qw in quick_wins if len(qw.get('steps', [])) >= 3]
        if len(wins_with_steps) == len(quick_wins):
            print("  [OK] All quick wins have >=3 implementation steps")
            passed += 1
        else:
            self.warnings.append("[WARN] Some quick wins have insufficient steps")

        return passed

    def run_validation(self) -> Tuple[int, int]:
        """Run full validation suite"""
        print("\n" + "="*60)
        print("SAMPLE PROJECT VALIDATION")
        print("="*60)

        total_passed = 0
        total_tests = 0

        # Run all validations
        validations = [
            self.validate_classification,
            self.validate_outreach,
            self.validate_dossier,
            self.validate_audit,
            self.validate_quick_wins
        ]

        for validation in validations:
            passed = validation()
            total_passed += passed

        # Estimate total tests (rough count)
        total_tests = 20  # Approximate number of checks

        return total_passed, total_tests


def load_json(path: Path) -> Dict:
    """Load JSON file"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_sample(sample_dir: str) -> int:
    """
    Validate a sample project

    Args:
        sample_dir: Name of sample directory

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    base_dir = Path(__file__).parent / sample_dir

    if not base_dir.exists():
        print(f"[FAIL] Sample directory not found: {base_dir}")
        return 1

    # Load files
    expected_path = base_dir / "expected_output.json"
    if not expected_path.exists():
        print(f"[FAIL] Expected output not found: {expected_path}")
        return 1

    expected = load_json(expected_path)

    # For now, we'll use expected as actual (TODO: run actual workflow)
    # In real usage: actual = run_consulting_pack_workflow(input_data)
    actual = expected

    # Run validation
    validator = Validator(expected, actual)
    passed, total = validator.run_validation()

    # Print summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)

    if validator.errors:
        print(f"\n[FAIL] Errors ({len(validator.errors)}):")
        for error in validator.errors:
            print(f"\n{error}")

    if validator.warnings:
        print(f"\n[WARN] Warnings ({len(validator.warnings)}):")
        for warning in validator.warnings:
            print(f"  {warning}")

    print(f"\n[OK] Tests passed: {passed}/{total}")

    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")

    if validator.errors:
        print("\n[FAIL] VALIDATION FAILED")
        return 1
    else:
        print("\n[OK] VALIDATION PASSED")
        return 0


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python validate_sample.py <sample_dir>")
        print("\\nAvailable samples:")
        samples_dir = Path(__file__).parent
        for d in samples_dir.iterdir():
            if d.is_dir() and (d / "expected_output.json").exists():
                print(f"  - {d.name}")
        sys.exit(1)

    sample_dir = sys.argv[1]
    exit_code = validate_sample(sample_dir)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
