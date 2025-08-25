#!/bin/bash
# Interactive FQCN Converter CLI Examples
# This script demonstrates various CLI usage patterns

set -e

echo "🚀 FQCN Converter CLI Examples"
echo "=============================="

# Function to run example with explanation
run_example() {
    local title="$1"
    local command="$2"
    local explanation="$3"
    
    echo ""
    echo "📝 $title"
    echo "Command: $command"
    echo "Explanation: $explanation"
    echo ""
    
    if [[ "$DRY_RUN" != "false" ]]; then
        echo "💡 Add DRY_RUN=false to actually run commands"
        echo "   Example: DRY_RUN=false ./cli_examples.sh"
    else
        echo "▶️  Running: $command"
        eval "$command"
    fi
    
    echo "----------------------------------------"
}

# Set default to dry run unless specified
DRY_RUN=${DRY_RUN:-true}

if [[ "$DRY_RUN" == "true" ]]; then
    echo "🔍 DRY RUN MODE - Commands will be shown but not executed"
    echo "   Set DRY_RUN=false to actually run commands"
fi


echo ""
echo "=== Basic Usage ==="

run_example "Convert Single File" \
    "fqcn-converter convert playbook.yml" \
    "Convert a single Ansible playbook to FQCN format"

run_example "Validate Conversion" \
    "fqcn-converter validate playbook.yml" \
    "Check if a file properly uses FQCN format"

echo ""
echo "=== Advanced Usage ==="

run_example "Batch Processing" \
    "fqcn-converter batch --workers 4 /ansible/projects" \
    "Process multiple projects in parallel"

run_example "Custom Configuration" \
    "fqcn-converter convert --config custom.yml --backup roles/" \
    "Use custom mappings and create backups"

echo ""
echo "=== Reporting and Analysis ==="

run_example "Detailed Reporting" \
    "fqcn-converter validate --score --report report.json --format json ." \
    "Generate comprehensive validation report"

run_example "Progress Tracking" \
    "fqcn-converter convert --progress --dry-run large_project/" \
    "Preview changes with progress indication"

echo ""
echo "✅ All examples completed!"
echo ""
echo "💡 Tips:"
echo "  - Use --help with any command for detailed information"
echo "  - Always test with --dry-run before making changes"
echo "  - Check the generated reports for detailed analysis"
echo "  - Use --verbose for debugging issues"
