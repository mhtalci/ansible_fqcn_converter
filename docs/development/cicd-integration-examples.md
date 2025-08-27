# CI/CD Integration Examples

## Overview

This document provides comprehensive examples and templates for integrating the FQCN Converter test suite into various CI/CD platforms, including GitHub Actions, GitLab CI, Jenkins, and Azure DevOps.

## GitHub Actions Integration

### Basic Test Workflow

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r test-requirements.txt
        pip install -e .
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ \
          --numprocesses=auto \
          --cov=src/fqcn_converter \
          --cov-report=xml \
          --cov-report=term-missing \
          --junit-xml=test-results.xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results-${{ matrix.python-version }}
        path: |
          test-results.xml
          coverage.xml
          htmlcov/
```

### Comprehensive Test Workflow

```yaml
# .github/workflows/comprehensive-tests.yml
name: Comprehensive Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  unit-tests:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.8, 3.9, "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r test-requirements.txt
        pip install -e .
    
    - name: Run unit tests with coverage
      run: |
        pytest tests/unit/ \
          --numprocesses=auto \
          --cov=src/fqcn_converter \
          --cov-report=xml \
          --cov-report=html \
          --cov-fail-under=90 \
          --junit-xml=test-results-unit.xml \
          --durations=10
    
    - name: Upload coverage artifacts
      uses: actions/upload-artifact@v3
      with:
        name: coverage-${{ matrix.os }}-${{ matrix.python-version }}
        path: |
          coverage.xml
          htmlcov/

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r test-requirements.txt
        pip install -e .
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ \
          --numprocesses=2 \
          --dist=loadfile \
          --junit-xml=test-results-integration.xml \
          --timeout=300
    
    - name: Upload integration test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: integration-test-results
        path: test-results-integration.xml

  performance-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r test-requirements.txt
        pip install -e .
    
    - name: Run performance tests
      run: |
        pytest tests/performance/ \
          --numprocesses=1 \
          --benchmark-json=benchmark-results.json \
          --junit-xml=test-results-performance.xml
    
    - name: Upload performance results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: |
          benchmark-results.json
          test-results-performance.xml

  coverage-report:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Download coverage artifacts
      uses: actions/download-artifact@v3
      with:
        pattern: coverage-*
        merge-multiple: true
    
    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install coverage tools
      run: |
        pip install coverage[toml] coverage-badge
    
    - name: Combine coverage reports
      run: |
        coverage combine
        coverage report --show-missing
        coverage html
        coverage xml
    
    - name: Generate coverage badge
      run: |
        coverage-badge -o coverage-badge.svg
    
    - name: Upload combined coverage
      uses: actions/upload-artifact@v3
      with:
        name: combined-coverage
        path: |
          htmlcov/
          coverage.xml
          coverage-badge.svg
```

### Quality Gates Workflow

```yaml
# .github/workflows/quality-gates.yml
name: Quality Gates

on:
  pull_request:
    branches: [ main ]

jobs:
  quality-checks:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Full history for better analysis
    
    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r test-requirements.txt
        pip install -e .
    
    - name: Run linting
      run: |
        flake8 src/ tests/
        black --check src/ tests/
        isort --check-only src/ tests/
    
    - name: Run type checking
      run: |
        mypy src/fqcn_converter/
    
    - name: Run security checks
      run: |
        bandit -r src/
        safety check
    
    - name: Run tests with coverage
      run: |
        pytest tests/ \
          --numprocesses=auto \
          --cov=src/fqcn_converter \
          --cov-report=xml \
          --cov-fail-under=90 \
          --junit-xml=test-results.xml
    
    - name: Check coverage diff
      run: |
        # Compare coverage with main branch
        python scripts/coverage_diff.py origin/main HEAD
    
    - name: Comment PR with results
      uses: actions/github-script@v6
      if: github.event_name == 'pull_request'
      with:
        script: |
          const fs = require('fs');
          const coverage = fs.readFileSync('coverage.xml', 'utf8');
          // Parse and comment on PR
```

## GitLab CI Integration

### Basic GitLab CI Configuration

```yaml
# .gitlab-ci.yml
stages:
  - test
  - coverage
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip/
    - venv/

before_script:
  - python -m venv venv
  - source venv/bin/activate
  - pip install --upgrade pip
  - pip install -r requirements.txt
  - pip install -r test-requirements.txt
  - pip install -e .

unit-tests:
  stage: test
  image: python:3.10
  script:
    - pytest tests/unit/ 
        --numprocesses=auto 
        --cov=src/fqcn_converter 
        --cov-report=xml 
        --cov-report=html 
        --junit-xml=test-results.xml
  artifacts:
    reports:
      junit: test-results.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - htmlcov/
    expire_in: 1 week
  coverage: '/TOTAL.*\s+(\d+%)$/'

integration-tests:
  stage: test
  image: python:3.10
  script:
    - pytest tests/integration/ 
        --numprocesses=2 
        --dist=loadfile 
        --junit-xml=integration-results.xml
  artifacts:
    reports:
      junit: integration-results.xml
    expire_in: 1 week

performance-tests:
  stage: test
  image: python:3.10
  script:
    - pytest tests/performance/ 
        --numprocesses=1 
        --benchmark-json=benchmark.json
  artifacts:
    paths:
      - benchmark.json
    expire_in: 1 week
  allow_failure: true

coverage-report:
  stage: coverage
  image: python:3.10
  dependencies:
    - unit-tests
  script:
    - coverage report --show-missing
    - coverage html
  artifacts:
    paths:
      - htmlcov/
    expire_in: 30 days
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

### Multi-Platform GitLab CI

```yaml
# .gitlab-ci.yml (multi-platform)
.test-template: &test-template
  stage: test
  script:
    - pytest tests/unit/ 
        --numprocesses=auto 
        --cov=src/fqcn_converter 
        --cov-report=xml 
        --junit-xml=test-results-$CI_JOB_NAME.xml
  artifacts:
    reports:
      junit: test-results-$CI_JOB_NAME.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

test-python38:
  <<: *test-template
  image: python:3.8

test-python39:
  <<: *test-template
  image: python:3.9

test-python310:
  <<: *test-template
  image: python:3.10

test-python311:
  <<: *test-template
  image: python:3.11
```

## Jenkins Integration

### Jenkinsfile (Declarative Pipeline)

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        PYTHONPATH = "${WORKSPACE}/src"
        PIP_CACHE_DIR = "${WORKSPACE}/.pip-cache"
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r test-requirements.txt
                    pip install -e .
                '''
            }
        }
        
        stage('Lint') {
            steps {
                sh '''
                    . venv/bin/activate
                    flake8 src/ tests/
                    black --check src/ tests/
                    isort --check-only src/ tests/
                '''
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/unit/ \
                        --numprocesses=auto \
                        --cov=src/fqcn_converter \
                        --cov-report=xml \
                        --cov-report=html \
                        --junit-xml=test-results-unit.xml
                '''
            }
            post {
                always {
                    junit 'test-results-unit.xml'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/integration/ \
                        --numprocesses=2 \
                        --dist=loadfile \
                        --junit-xml=test-results-integration.xml
                '''
            }
            post {
                always {
                    junit 'test-results-integration.xml'
                }
            }
        }
        
        stage('Performance Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/performance/ \
                        --numprocesses=1 \
                        --benchmark-json=benchmark.json \
                        --junit-xml=test-results-performance.xml
                '''
            }
            post {
                always {
                    junit 'test-results-performance.xml'
                    archiveArtifacts artifacts: 'benchmark.json', fingerprint: true
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            emailext (
                subject: "Build Success: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build completed successfully.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
        failure {
            emailext (
                subject: "Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build failed. Please check the console output.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
```

### Jenkins Multibranch Pipeline

```groovy
// Jenkinsfile (Multibranch)
pipeline {
    agent {
        docker {
            image 'python:3.10'
            args '-u root:root'
        }
    }
    
    parameters {
        choice(
            name: 'TEST_SUITE',
            choices: ['all', 'unit', 'integration', 'performance'],
            description: 'Which test suite to run'
        )
        booleanParam(
            name: 'PARALLEL_EXECUTION',
            defaultValue: true,
            description: 'Run tests in parallel'
        )
    }
    
    stages {
        stage('Setup Environment') {
            steps {
                sh '''
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r test-requirements.txt
                    pip install -e .
                '''
            }
        }
        
        stage('Run Tests') {
            parallel {
                stage('Unit Tests') {
                    when {
                        anyOf {
                            params.TEST_SUITE == 'all'
                            params.TEST_SUITE == 'unit'
                        }
                    }
                    steps {
                        script {
                            def parallelFlag = params.PARALLEL_EXECUTION ? '--numprocesses=auto' : ''
                            sh """
                                pytest tests/unit/ \
                                    ${parallelFlag} \
                                    --cov=src/fqcn_converter \
                                    --cov-report=xml:coverage-unit.xml \
                                    --junit-xml=test-results-unit.xml
                            """
                        }
                    }
                }
                
                stage('Integration Tests') {
                    when {
                        anyOf {
                            params.TEST_SUITE == 'all'
                            params.TEST_SUITE == 'integration'
                        }
                    }
                    steps {
                        sh '''
                            pytest tests/integration/ \
                                --numprocesses=2 \
                                --dist=loadfile \
                                --junit-xml=test-results-integration.xml
                        '''
                    }
                }
                
                stage('Performance Tests') {
                    when {
                        anyOf {
                            params.TEST_SUITE == 'all'
                            params.TEST_SUITE == 'performance'
                        }
                    }
                    steps {
                        sh '''
                            pytest tests/performance/ \
                                --numprocesses=1 \
                                --benchmark-json=benchmark.json
                        '''
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Collect test results
            junit testResults: 'test-results-*.xml', allowEmptyResults: true
            
            // Publish coverage
            publishCoverage adapters: [
                coberturaAdapter('coverage-*.xml')
            ], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
            
            // Archive artifacts
            archiveArtifacts artifacts: 'benchmark.json', allowEmptyArchive: true
        }
    }
}
```

## Azure DevOps Integration

### Azure Pipelines YAML

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
    - main
    - develop
  paths:
    exclude:
    - docs/*
    - README.md

pr:
  branches:
    include:
    - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  pythonVersion: '3.10'
  pipCacheDir: $(Pipeline.Workspace)/.pip

stages:
- stage: Test
  displayName: 'Run Tests'
  jobs:
  - job: UnitTests
    displayName: 'Unit Tests'
    strategy:
      matrix:
        Python38:
          pythonVersion: '3.8'
        Python39:
          pythonVersion: '3.9'
        Python310:
          pythonVersion: '3.10'
        Python311:
          pythonVersion: '3.11'
    
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
      displayName: 'Use Python $(pythonVersion)'
    
    - task: Cache@2
      inputs:
        key: 'pip | "$(Agent.OS)" | requirements.txt | test-requirements.txt'
        restoreKeys: |
          pip | "$(Agent.OS)"
        path: $(pipCacheDir)
      displayName: 'Cache pip packages'
    
    - script: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r test-requirements.txt
        pip install -e .
      displayName: 'Install dependencies'
    
    - script: |
        pytest tests/unit/ \
          --numprocesses=auto \
          --cov=src/fqcn_converter \
          --cov-report=xml \
          --cov-report=html \
          --junit-xml=test-results.xml
      displayName: 'Run unit tests'
    
    - task: PublishTestResults@2
      condition: succeededOrFailed()
      inputs:
        testResultsFiles: 'test-results.xml'
        testRunTitle: 'Unit Tests - Python $(pythonVersion)'
    
    - task: PublishCodeCoverageResults@1
      inputs:
        codeCoverageTool: Cobertura
        summaryFileLocation: 'coverage.xml'
        reportDirectory: 'htmlcov'

  - job: IntegrationTests
    displayName: 'Integration Tests'
    dependsOn: UnitTests
    
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
    
    - script: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r test-requirements.txt
        pip install -e .
      displayName: 'Install dependencies'
    
    - script: |
        pytest tests/integration/ \
          --numprocesses=2 \
          --dist=loadfile \
          --junit-xml=integration-results.xml
      displayName: 'Run integration tests'
    
    - task: PublishTestResults@2
      condition: succeededOrFailed()
      inputs:
        testResultsFiles: 'integration-results.xml'
        testRunTitle: 'Integration Tests'

- stage: QualityGates
  displayName: 'Quality Gates'
  dependsOn: Test
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  
  jobs:
  - job: QualityChecks
    displayName: 'Quality Checks'
    
    steps:
    - task: UsePythonVersion@0
      inputs:
        versionSpec: '$(pythonVersion)'
    
    - script: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r test-requirements.txt
        pip install -e .
      displayName: 'Install dependencies'
    
    - script: |
        flake8 src/ tests/
        black --check src/ tests/
        isort --check-only src/ tests/
      displayName: 'Run linting'
    
    - script: |
        mypy src/fqcn_converter/
      displayName: 'Run type checking'
    
    - script: |
        bandit -r src/
        safety check
      displayName: 'Run security checks'
```

## Docker-based CI/CD

### Multi-stage Dockerfile for Testing

```dockerfile
# Dockerfile.test
FROM python:3.10-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt test-requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r test-requirements.txt

# Copy source code
COPY . .
RUN pip install -e .

# Test stage
FROM base as test
CMD ["pytest", "tests/", "--numprocesses=auto", "--cov=src/fqcn_converter"]

# Coverage stage
FROM test as coverage
CMD ["pytest", "tests/", "--cov=src/fqcn_converter", "--cov-report=html", "--cov-report=xml"]

# Performance stage
FROM base as performance
CMD ["pytest", "tests/performance/", "--benchmark-json=benchmark.json"]
```

### Docker Compose for Testing

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  unit-tests:
    build:
      context: .
      dockerfile: Dockerfile.test
      target: test
    command: pytest tests/unit/ --numprocesses=auto --junit-xml=/app/results/unit-results.xml
    volumes:
      - ./test-results:/app/results
    environment:
      - PYTHONPATH=/app/src

  integration-tests:
    build:
      context: .
      dockerfile: Dockerfile.test
      target: test
    command: pytest tests/integration/ --numprocesses=2 --junit-xml=/app/results/integration-results.xml
    volumes:
      - ./test-results:/app/results
    depends_on:
      - unit-tests

  coverage:
    build:
      context: .
      dockerfile: Dockerfile.test
      target: coverage
    volumes:
      - ./coverage-results:/app/htmlcov
      - ./test-results:/app/results
    depends_on:
      - unit-tests
      - integration-tests

  performance:
    build:
      context: .
      dockerfile: Dockerfile.test
      target: performance
    volumes:
      - ./performance-results:/app/results
    depends_on:
      - unit-tests
```

## Configuration Templates

### pytest Configuration Templates

#### Basic pytest.ini
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

addopts = 
    --strict-markers
    --strict-config
    --cov=src/fqcn_converter
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=90
    --durations=10

markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
```

#### CI-optimized pytest.ini
```ini
# pytest-ci.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

addopts = 
    --numprocesses=auto
    --dist=loadscope
    --cov=src/fqcn_converter
    --cov-report=xml
    --cov-report=html
    --cov-fail-under=90
    --junit-xml=test-results.xml
    --maxfail=5
    --tb=short

markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow running tests
    ci_skip: Skip in CI environment
```

### Coverage Configuration Templates

#### .coveragerc for CI/CD
```ini
# .coveragerc
[run]
source = src/fqcn_converter
parallel = true
branch = true
omit = 
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*
    */conftest.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov

[xml]
output = coverage.xml
```

## Best Practices for CI/CD Integration

### 1. Test Execution Strategy
- Run unit tests in parallel for speed
- Run integration tests with limited parallelism
- Run performance tests sequentially
- Use appropriate timeouts for each test category

### 2. Artifact Management
- Collect test results in JUnit XML format
- Generate coverage reports in multiple formats (XML, HTML)
- Archive performance benchmarks
- Store test logs for debugging

### 3. Quality Gates
- Enforce minimum coverage thresholds
- Fail builds on test failures
- Run security and linting checks
- Validate performance regressions

### 4. Environment Management
- Use consistent Python versions across environments
- Cache dependencies for faster builds
- Use isolated test environments
- Clean up resources after test execution

### 5. Notification and Reporting
- Send notifications on build failures
- Generate comprehensive test reports
- Track coverage trends over time
- Monitor performance metrics

This comprehensive CI/CD integration guide provides the foundation for reliable, automated testing across multiple platforms and environments.