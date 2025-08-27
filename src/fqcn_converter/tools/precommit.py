"""Pre-commit hook system for FQCN validation and conversion."""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import tempfile
import shutil

from ..core.validator import FQCNValidator
from ..core.converter import FQCNConverter
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PreCommitHook:
    """Pre-commit hook for FQCN validation and conversion."""
    
    def __init__(self, auto_fix: bool = False, strict_mode: bool = False):
        """Initialize pre-commit hook.
        
        Args:
            auto_fix: Whether to automatically fix FQCN issues
            strict_mode: Whether to fail on any FQCN issues
        """
        self.auto_fix = auto_fix
        self.strict_mode = strict_mode
        self.validator = FQCNValidator()
        self.converter = FQCNConverter() if auto_fix else None
        
    def run_hook(self, files: List[Path]) -> Tuple[bool, List[str]]:
        """Run the pre-commit hook on specified files.
        
        Args:
            files: List of files to check
            
        Returns:
            Tuple of (success, messages)
        """
        messages = []
        overall_success = True
        
        # Filter for YAML files
        yaml_files = [f for f in files if f.suffix.lower() in ['.yml', '.yaml']]
        
        if not yaml_files:
            messages.append("No YAML files to check")
            return True, messages
        
        messages.append(f"Checking {len(yaml_files)} YAML files for FQCN compliance...")
        
        for file_path in yaml_files:
            try:
                success, file_messages = self._check_file(file_path)
                messages.extend(file_messages)
                
                if not success:
                    overall_success = False
                    
            except Exception as e:
                messages.append(f"Error checking {file_path}: {e}")
                overall_success = False
        
        return overall_success, messages   
 
    def _check_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Check a single file for FQCN compliance.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            Tuple of (success, messages)
        """
        messages = []
        
        try:
            # Validate file
            validation_result = self.validator.validate_file(file_path)
            
            if validation_result.is_valid:
                messages.append(f"✓ {file_path}: FQCN compliant")
                return True, messages
            
            # File has FQCN issues
            messages.append(f"⚠ {file_path}: FQCN issues found")
            for issue in validation_result.issues:
                messages.append(f"  - {issue}")
            
            if self.auto_fix:
                return self._attempt_auto_fix(file_path, messages)
            elif self.strict_mode:
                messages.append(f"✗ {file_path}: Failing due to strict mode")
                return False, messages
            else:
                messages.append(f"⚠ {file_path}: Issues found but not failing")
                return True, messages
                
        except Exception as e:
            messages.append(f"✗ {file_path}: Error during validation - {e}")
            return False, messages
    
    def _attempt_auto_fix(self, file_path: Path, messages: List[str]) -> Tuple[bool, List[str]]:
        """Attempt to automatically fix FQCN issues.
        
        Args:
            file_path: Path to the file to fix
            messages: List to append messages to
            
        Returns:
            Tuple of (success, messages)
        """
        try:
            # Create backup
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            shutil.copy2(file_path, backup_path)
            
            # Attempt conversion
            result = self.converter.convert_file(file_path)
            
            if result.success:
                messages.append(f"✓ {file_path}: Auto-fixed {len(result.conversions)} FQCN issues")
                
                # Stage the fixed file
                self._stage_file(file_path)
                
                # Remove backup
                backup_path.unlink()
                
                return True, messages
            else:
                # Restore backup
                shutil.move(backup_path, file_path)
                messages.append(f"✗ {file_path}: Auto-fix failed - {result.error}")
                return False, messages
                
        except Exception as e:
            messages.append(f"✗ {file_path}: Auto-fix error - {e}")
            return False, messages
    
    def _stage_file(self, file_path: Path) -> None:
        """Stage a file in git.
        
        Args:
            file_path: Path to the file to stage
        """
        try:
            subprocess.run(['git', 'add', str(file_path)], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to stage {file_path}: {e}")
    
    @classmethod
    def install_hook(cls, repo_path: Path, hook_config: Dict[str, Any] = None) -> bool:
        """Install the pre-commit hook in a git repository.
        
        Args:
            repo_path: Path to the git repository
            hook_config: Hook configuration options
            
        Returns:
            True if installation successful
        """
        try:
            hooks_dir = repo_path / '.git' / 'hooks'
            if not hooks_dir.exists():
                logger.error(f"Git hooks directory not found: {hooks_dir}")
                return False
            
            hook_script = cls._generate_hook_script(hook_config or {})
            hook_path = hooks_dir / 'pre-commit'
            
            # Write hook script
            hook_path.write_text(hook_script, encoding='utf-8')
            hook_path.chmod(0o755)  # Make executable
            
            logger.info(f"Installed FQCN pre-commit hook at {hook_path}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to install pre-commit hook: {e}")
            return False
    
    @classmethod
    def _generate_hook_script(cls, config: Dict[str, Any]) -> str:
        """Generate the pre-commit hook script.
        
        Args:
            config: Hook configuration
            
        Returns:
            Hook script content
        """
        auto_fix = config.get('auto_fix', False)
        strict_mode = config.get('strict_mode', False)
        
        script = f'''#!/usr/bin/env python3
"""FQCN Converter Pre-commit Hook"""

import sys
import subprocess
from pathlib import Path

def get_staged_files():
    """Get list of staged YAML files."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
            capture_output=True, text=True, check=True
        )
        files = result.stdout.strip().split('\\n') if result.stdout.strip() else []
        return [Path(f) for f in files if f.endswith(('.yml', '.yaml'))]
    except subprocess.CalledProcessError:
        return []

def main():
    """Main hook function."""
    staged_files = get_staged_files()
    
    if not staged_files:
        sys.exit(0)  # No YAML files to check
    
    try:
        # Import and run FQCN hook
        from fqcn_converter.tools.precommit import PreCommitHook
        
        hook = PreCommitHook(auto_fix={auto_fix}, strict_mode={strict_mode})
        success, messages = hook.run_hook(staged_files)
        
        for message in messages:
            print(message)
        
        if not success:
            print("\\nPre-commit hook failed. Fix FQCN issues before committing.")
            sys.exit(1)
        
        sys.exit(0)
        
    except ImportError:
        print("FQCN Converter not found. Please install it first.")
        sys.exit(1)
    except Exception as e:
        print(f"Pre-commit hook error: {{e}}")
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
        return script
    
    @classmethod
    def uninstall_hook(cls, repo_path: Path) -> bool:
        """Uninstall the pre-commit hook from a git repository.
        
        Args:
            repo_path: Path to the git repository
            
        Returns:
            True if uninstallation successful
        """
        try:
            hook_path = repo_path / '.git' / 'hooks' / 'pre-commit'
            
            if hook_path.exists():
                # Check if it's our hook
                content = hook_path.read_text(encoding='utf-8')
                if 'FQCN Converter Pre-commit Hook' in content:
                    hook_path.unlink()
                    logger.info(f"Uninstalled FQCN pre-commit hook from {repo_path}")
                    return True
                else:
                    logger.warning(f"Pre-commit hook exists but is not FQCN hook: {hook_path}")
                    return False
            else:
                logger.info(f"No pre-commit hook found at {hook_path}")
                return True
                
        except Exception as e:
            logger.exception(f"Failed to uninstall pre-commit hook: {e}")
            return False


def main():
    """CLI entry point for pre-commit hook."""
    import argparse
    
    parser = argparse.ArgumentParser(description='FQCN Pre-commit Hook')
    parser.add_argument('files', nargs='*', help='Files to check')
    parser.add_argument('--auto-fix', action='store_true', help='Automatically fix issues')
    parser.add_argument('--strict', action='store_true', help='Strict mode - fail on any issues')
    parser.add_argument('--install', metavar='REPO_PATH', help='Install hook in repository')
    parser.add_argument('--uninstall', metavar='REPO_PATH', help='Uninstall hook from repository')
    
    args = parser.parse_args()
    
    if args.install:
        repo_path = Path(args.install)
        config = {'auto_fix': args.auto_fix, 'strict_mode': args.strict}
        success = PreCommitHook.install_hook(repo_path, config)
        sys.exit(0 if success else 1)
    
    if args.uninstall:
        repo_path = Path(args.uninstall)
        success = PreCommitHook.uninstall_hook(repo_path)
        sys.exit(0 if success else 1)
    
    if not args.files:
        print("No files specified")
        sys.exit(0)
    
    # Run hook on specified files
    hook = PreCommitHook(auto_fix=args.auto_fix, strict_mode=args.strict)
    files = [Path(f) for f in args.files]
    success, messages = hook.run_hook(files)
    
    for message in messages:
        print(message)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()