---
name: Quality Gate Failure
about: Report a quality gate failure in CI/CD
title: '[QG] Quality Gate Failure - '
labels: ['quality-gate', 'ci/cd', 'bug']
assignees: []
---

## Quality Gate Failure Report

### Failed Check(s)
<!-- Check all that apply -->
- [ ] Code Coverage (< 95%)
- [ ] Code Formatting (Black/isort)
- [ ] Linting (Flake8)
- [ ] Type Checking (MyPy)
- [ ] Security Scan (Bandit)
- [ ] Dependency Vulnerabilities (Safety)
- [ ] Code Complexity (> 10)
- [ ] Tests
- [ ] Documentation Build

### Build Information
- **Branch:** 
- **Commit SHA:** 
- **PR Number (if applicable):** 
- **Workflow Run:** [Link to failed workflow run]

### Error Details
```
<!-- Paste the error output here -->
```

### Expected Behavior
<!-- Describe what should happen -->

### Actual Behavior
<!-- Describe what actually happened -->

### Steps to Reproduce
1. 
2. 
3. 

### Additional Context
<!-- Add any other context about the problem here -->

### Checklist
- [ ] I have checked that this issue hasn't been reported before
- [ ] I have provided all the necessary information
- [ ] I have included the full error output
- [ ] I have linked to the failed workflow run