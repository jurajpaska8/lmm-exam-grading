import csv
import os
from typing import Dict

class CSVComparator:
    def __init__(self, expected_csv_path: str, actual_csv_path: str):
        """
        Initialize the comparator with paths to expected and actual CSV files.
        
        Args:
            expected_csv_path: Path to the expected (ground truth) CSV file
            actual_csv_path: Path to the actual (generated) CSV file
        """
        self.expected_csv_path = expected_csv_path
        self.actual_csv_path = actual_csv_path
        self.expected_data = {}
        self.actual_data = {}
        self.pdf_headers = []
        
    def load_csv(self, csv_path: str) -> Dict[int, Dict]:
        """Load CSV file and return dictionary with student_idx as key."""
        data = {}
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip summary rows (blank_name_pages, illegible_name_pages)
                if row.get('student_idx', '').isdigit():
                    student_idx = int(row['student_idx'])
                    data[student_idx] = row
        return data
    
    def load_data(self):
        """Load both CSV files."""
        self.expected_data = self.load_csv(self.expected_csv_path)
        self.actual_data = self.load_csv(self.actual_csv_path)
        
        # Extract PDF headers from expected data (skip student_idx and student_name)
        if self.expected_data:
            first_row = next(iter(self.expected_data.values()))
            self.pdf_headers = [k for k in first_row.keys() 
                               if k not in ['student_idx', 'student_name']]
        
        print(f"✓ Loaded {len(self.expected_data)} expected students")
        print(f"✓ Loaded {len(self.actual_data)} actual students")
        print(f"✓ Found {len(self.pdf_headers)} PDF headers: {', '.join(self.pdf_headers)}")
    
    def _page_matches(self, expected_pages: str, actual_pages: str) -> bool:
        """Return True when expected page is found in actual pages."""
        if expected_pages == '-1' or actual_pages == '-1':
            return False
        actual_values = [val.strip() for val in actual_pages.split(';') if val.strip()]
        return expected_pages in actual_values

    def compare_students(self) -> Dict:
        """
        Compare students and calculate accuracy.
        
        Returns:
            Dictionary with comparison results
        """
        results = {
            'students': [],
            'summary': {
                'total_students': 0,
                'total_matches': 0,
                'exact_total_matches': 0,
                'total_pages': 0,
                'overall_accuracy': 0.0,
                'overall_exact_accuracy': 0.0,
                'missing_in_actual': [],
                'extra_in_actual': []
            }
        }
        
        # Get all student indices from expected data
        all_student_indices = set(self.expected_data.keys()) | set(self.actual_data.keys())
        
        for student_idx in sorted(all_student_indices):
            expected_row = self.expected_data.get(student_idx)
            actual_row = self.actual_data.get(student_idx)
            
            if not expected_row:
                results['summary']['extra_in_actual'].append(student_idx)
                continue
            
            if not actual_row:
                results['summary']['missing_in_actual'].append(student_idx)
                continue
            
            student_result = {
                'student_idx': student_idx,
                'student_name': expected_row.get('student_name', 'Unknown'),
                'pages_match': 0,
                'exact_pages_match': 0,
                'total_pages': 0,
                'accuracy': 0.0,
                'mismatches': []
            }
            
            # Compare each PDF column
            for pdf_header in self.pdf_headers:
                expected_pages = expected_row.get(pdf_header, '-1')
                actual_pages = actual_row.get(pdf_header, '-1')
                if expected_pages == '-1':
                    continue

                student_result['total_pages'] += 1
                
                if expected_pages == actual_pages:
                    student_result['exact_pages_match'] += 1
                else:
                    student_result['mismatches'].append({
                        'pdf': pdf_header,
                        'expected': expected_pages,
                        'actual': actual_pages
                    })
                if self._page_matches(expected_pages, actual_pages):
                    student_result['pages_match'] += 1
            
            if student_result['total_pages'] == 0:
                continue

            student_result['accuracy'] = (student_result['pages_match'] / student_result['total_pages'] * 100)
            student_result['exact_accuracy'] = (student_result['exact_pages_match'] / student_result['total_pages'] * 100)
            results['students'].append(student_result)
            results['summary']['total_pages'] += student_result['total_pages']
            results['summary']['total_matches'] += student_result['pages_match']
            results['summary']['exact_total_matches'] += student_result['exact_pages_match']
        
        results['summary']['total_students'] = len([s for s in results['students']])
        
        if results['summary']['total_pages'] > 0:
            results['summary']['overall_accuracy'] = (
                results['summary']['total_matches'] / results['summary']['total_pages'] * 100
            )
            results['summary']['overall_exact_accuracy'] = (
                results['summary']['exact_total_matches'] / results['summary']['total_pages'] * 100
            )
        return results
    
    def print_results(self, results: Dict, verbose: bool = False):
        """Print comparison results in a readable format."""
        print("\n" + "="*80)
        print("CSV COMPARISON RESULTS")
        print("="*80)
        
        # Summary
        summary = results['summary']
        print(f"\n📊 SUMMARY:")
        print(f"  Total Students: {summary['total_students']}")
        print(f"  Overall Accuracy: {summary['overall_accuracy']:.2f}% "
              f"({summary['total_matches']}/{summary['total_pages']} pages)")
        print(f"  Overall Exact Accuracy: {summary['overall_exact_accuracy']:.2f}% "
              f"({summary['exact_total_matches']}/{summary['total_pages']} exact matches)")
        if summary['missing_in_actual']:
            print(f"  ⚠️  Missing in actual: {len(summary['missing_in_actual'])} students")
        
        if summary['extra_in_actual']:
            print(f"  ⚠️  Extra in actual: {len(summary['extra_in_actual'])} students")
        
        # Detailed results if verbose
        if verbose:
            print(f"\n{'Student':<30} {'Accuracy':<10} {'Exact%':<8} {'Matches':<15} {'Exact':<15}")
            print("-" * 90)
            for student in results['students']:
                status = "✓" if student['accuracy'] == 100 else "✗"
                print(
                    f"{status} {student['student_name'][:28]:<28} "
                    f"{student['accuracy']:>6.1f}%   "
                    f"{student['exact_accuracy']:>6.1f}%   "
                    f"{student['pages_match']:>3}/{student['total_pages']:<3}   "
                    f"{student['exact_pages_match']:>3}/{student['total_pages']:<3}"
                )
        
        # Summary by accuracy ranges
        print(f"\n📈 ACCURACY DISTRIBUTION:")
        ranges = [
            (100, 100, "Perfect (100%)"),
            (90, 99.9, "Excellent (90-99%)"),
            (70, 89.9, "Good (70-89%)"),
            (50, 69.9, "Fair (50-69%)"),
            (0, 49.9, "Poor (<50%)")
        ]
        
        for min_acc, max_acc, label in ranges:
            count = sum(1 for s in results['students'] 
                       if min_acc <= s['accuracy'] <= max_acc)
            if count > 0:
                print(f"  {label}: {count} students")
        
        print(f"\n📈 EXACT ACCURACY DISTRIBUTION:")
        for min_acc, max_acc, label in ranges:
            count = sum(1 for s in results['students'] 
                       if min_acc <= s['exact_accuracy'] <= max_acc)
            if count > 0:
                print(f"  {label}: {count} students")
        
        print("\n" + "="*80 + "\n")
    
    def run_comparison(self, verbose: bool = False):
        """Run the full comparison workflow."""
        self.load_data()
        results = self.compare_students()
        self.print_results(results, verbose=verbose)
        return results


if __name__ == "__main__":
    # Configuration
    ASSIGNMENT_FOLDER = "assignments/y2026/exam"
    RESULTS_FOLDER = f"{ASSIGNMENT_FOLDER}/results-pairing"
    EXPECTED_CSV = os.path.join(RESULTS_FOLDER, "actual_assignments.csv")
    
    # Find the most recent paired_pages_to_students_*.csv file
    ACTUAL_CSV = os.path.join(RESULTS_FOLDER, "paired_pages_to_students_qwen3.6_v1_2026-06-02_13-50-16.csv")

    if not EXPECTED_CSV:
        print("❌ Error: Could not find expected .csv file")
        exit(1)
    
    if not ACTUAL_CSV:
        print("❌ Error: Could not find paired_pages_to_students_*.csv file")
        exit(1)
    
    print(f"Comparing:\n  Expected: {EXPECTED_CSV}\n  Actual:   {ACTUAL_CSV}\n")
    
    comparator = CSVComparator(EXPECTED_CSV, ACTUAL_CSV)
    results = comparator.run_comparison(verbose=True)
    
    # Export detailed results to a summary file if needed
    summary_output = os.path.join(RESULTS_FOLDER, f"comparison_results_{os.path.basename(ACTUAL_CSV)}.txt")
    with open(summary_output, 'w', encoding='utf-8') as f:
        f.write("CSV COMPARISON RESULTS\n")
        f.write("="*80 + "\n\n")
        summary = results['summary']
        f.write(f"Overall Accuracy: {summary['overall_accuracy']:.2f}% "
                f"({summary['total_matches']}/{summary['total_pages']} pages)\n")
        f.write(f"Overall Exact Accuracy: {summary['overall_exact_accuracy']:.2f}% "
                f"({summary['exact_total_matches']}/{summary['total_pages']} exact matches)\n")
        f.write(f"Total Students Compared: {summary['total_students']}\n\n")
        
        f.write("Detailed Results:\n")
        f.write("-"*80 + "\n")
        for student in sorted(results['students'], 
                             key=lambda s: s['accuracy']):
            f.write(f"\n{student['student_name']} (idx: {student['student_idx']})\n")
            f.write(f"  Accuracy: {student['accuracy']:.1f}% "
                    f"({student['pages_match']}/{student['total_pages']})\n")
            f.write(f"  Exact Accuracy: {student['exact_accuracy']:.1f}% "
                    f"({student['exact_pages_match']}/{student['total_pages']})\n")
            if student['mismatches']:
                f.write(f"  Mismatches:\n")
                for m in student['mismatches']:
                    f.write(f"    {m['pdf']}: expected '{m['expected']}' "
                            f"got '{m['actual']}'\n")
    
    print(f"\n💾 Detailed results saved to: {summary_output}")
