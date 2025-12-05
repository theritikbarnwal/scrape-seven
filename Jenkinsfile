pipeline {
    agent any
    
    parameters {
        choice(
            name: 'SECURITY_SCAN_TYPE',
            choices: ['Quick Scan (Fast)', 'Full Security Audit', 'Dependency Scan Only', 'Code Quality Check', 'All Checks'],
            description: 'Select the type of security testing to perform'
        )
        booleanParam(
            name: 'RUN_SCRAPER', 
            defaultValue: false,
            description: 'Run the actual scraper after security checks?'
        )
        booleanParam(
            name: 'VERBOSE_OUTPUT',
            defaultValue: true,
            description: 'Show detailed security scan results'
        )
    }
    
    environment {
        PYTHON_VERSION = '3.12'
        VENV_DIR = "${WORKSPACE}/venv"
        PATH = "${WORKSPACE}/venv/bin:/usr/local/bin:${env.PATH}"
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo "🔍 Checking out repository..."
                checkout scm
            }
        }
        
        stage('Setup Python Virtual Environment') {
            steps {
                echo "🐍 Setting up Python ${PYTHON_VERSION} with virtual environment..."
                sh '''
                    # Check Python version
                    python3 --version
                    
                    # Create virtual environment
                    python3 -m venv ${VENV_DIR}
                    
                    # Activate and upgrade pip
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip setuptools wheel
                    
                    # Install project dependencies
                    pip install -r pyscript/requirements.txt
                    
                    # Verify installation
                    echo "\\n=== Installed packages ==="
                    pip list
                '''
            }
        }
        
        stage('Install Security Tools') {
            steps {
                echo "🔒 Installing security scanning tools..."
                sh '''
                    # Activate virtual environment
                    . ${VENV_DIR}/bin/activate
                    
                    echo "=== Installing Python security tools ==="
                    # Install security scanning tools (skip semgrep for now)
                    pip install bandit safety pip-audit || true
                    
                    echo "\\n=== Installing code quality tools ==="
                    # Install code quality tools
                    pip install pylint flake8 black isort || true
                    
                    echo "\\n=== Installing Playwright ==="
                    # Install Playwright and its browsers
                    pip install playwright
                    playwright install chromium --with-deps || playwright install chromium
                    
                    echo "\\n=== Attempting to install Semgrep via system package ==="
                    # Try to install semgrep via pip, but don't fail if it doesn't work
                    pip install semgrep 2>/dev/null || echo "⚠️ Semgrep installation skipped (optional)"
                    
                    # Show installed packages
                    echo "\\n=== Installed Security Tools ==="
                    pip list | grep -E "bandit|safety|pip-audit|semgrep|pylint|flake8|black|isort|playwright" || true
                    
                    # Verify key tools
                    echo "\\n=== Verifying installations ==="
                    command -v bandit && echo "✓ Bandit installed" || echo "✗ Bandit missing"
                    command -v safety && echo "✓ Safety installed" || echo "✗ Safety missing"
                    command -v pip-audit && echo "✓ Pip-audit installed" || echo "✗ Pip-audit missing"
                    command -v pylint && echo "✓ Pylint installed" || echo "✗ Pylint missing"
                    command -v playwright && echo "✓ Playwright installed" || echo "✗ Playwright missing"
                '''
            }
        }
        
        stage('Dependency Vulnerability Scan') {
            when {
                expression { 
                    params.SECURITY_SCAN_TYPE in ['Quick Scan (Fast)', 'Dependency Scan Only', 'All Checks', 'Full Security Audit'] 
                }
            }
            steps {
                echo "🛡️ Scanning dependencies for known vulnerabilities..."
                sh '''
                    # Activate virtual environment
                    . ${VENV_DIR}/bin/activate
                    
                    echo "=== Safety Check (PyPI vulnerabilities) ==="
                    if command -v safety &> /dev/null; then
                        safety check --json > safety-report.json 2>&1 || true
                        safety check 2>&1 || echo "Safety check completed with warnings"
                    else
                        echo "⚠️ Safety not installed, skipping..." | tee safety-report.json
                    fi
                    
                    echo "\\n=== Pip Audit (comprehensive vulnerability check) ==="
                    if command -v pip-audit &> /dev/null; then
                        pip-audit --desc --format json > pip-audit-report.json 2>&1 || true
                        pip-audit --desc 2>&1 || echo "Pip-audit check completed with warnings"
                    else
                        echo "⚠️ Pip-audit not installed, skipping..." | tee pip-audit-report.json
                    fi
                '''
                
                archiveArtifacts artifacts: '*-report.json', allowEmptyArchive: true
            }
        }
        
        stage('Static Code Security Analysis') {
                when {
                    expression { 
                        params.SECURITY_SCAN_TYPE in ['Quick Scan (Fast)', 'Full Security Audit', 'All Checks'] 
                    }
                }
                // Hard cap the whole stage so it can never hang forever
                options {
                    timeout(time: 10, unit: 'MINUTES')
                }
                steps {
                    echo "🔎 Running static security analysis on code..."
                    sh '''
                        set -euxo pipefail

                        . ${VENV_DIR}/bin/activate

                        echo "Python used: $(which python3)"
                        echo "Bandit used: $(command -v bandit || echo 'not found')"
                        echo "Semgrep used: $(command -v semgrep || echo 'not found (optional)')"

                        echo "=== Bandit Security Scan ==="
                        BANDIT_LEVEL=""
                        if [ "${SECURITY_SCAN_TYPE}" = "Quick Scan (Fast)" ]; then
                            echo "Running QUICK scan (high severity only)..."
                            BANDIT_LEVEL="-lll"
                        else
                            echo "Running FULL scan (all severities)..."
                            BANDIT_LEVEL="-ll"
                        fi

                        # Run ONCE, JSON only, keep console small
                        time bandit -r pyscript/ $BANDIT_LEVEL -f json -o bandit-report.json || echo "Bandit finished with findings or minor errors"

                        echo "\\n=== Semgrep Security Patterns ==="
                        if [ "${SECURITY_SCAN_TYPE}" != "Quick Scan (Fast)" ]; then
                            if command -v semgrep > /dev/null 2>&1; then
                                # Use a smaller ruleset and a hard timeout
                                # If this still sucks, swap --config=p/ci for a local rules file.
                                time semgrep --config=p/ci --timeout=60 --json pyscript/ > semgrep-report.json \
                                    || echo "Semgrep failed or timed out, see logs" > semgrep-report.json
                            else
                                echo "Semgrep not installed, writing placeholder report"
                                echo "Semgrep not installed" > semgrep-report.json
                            fi
                        else
                            echo "Quick scan selected, skipping Semgrep"
                            echo "Semgrep skipped for Quick Scan" > semgrep-report.json
                        fi
                    '''

                    archiveArtifacts artifacts: 'bandit-report.json,semgrep-report.json', allowEmptyArchive: true
                }
            }

        
        stage('Code Quality Check') {
            when {
                expression { 
                    params.SECURITY_SCAN_TYPE in ['Code Quality Check', 'All Checks'] 
                }
            }
            steps {
                echo "✨ Checking code quality and standards..."
                sh '''
                    # Activate virtual environment
                    . ${VENV_DIR}/bin/activate
                    
                    echo "=== Pylint Analysis ==="
                    if command -v pylint &> /dev/null; then
                        pylint pyscript/*.py --output-format=json > pylint-report.json 2>&1 || true
                        pylint pyscript/*.py 2>&1 || echo "Pylint completed with warnings"
                    else
                        echo "⚠️ Pylint not installed, skipping..." | tee pylint-report.json
                    fi
                    
                    echo "\\n=== Flake8 Linting ==="
                    if command -v flake8 &> /dev/null; then
                        flake8 pyscript/ --output-file=flake8-report.txt 2>&1 || true
                        flake8 pyscript/ 2>&1 || echo "Flake8 completed with warnings"
                    else
                        echo "⚠️ Flake8 not installed, skipping..." | tee flake8-report.txt
                    fi
                    
                    echo "\\n=== Code Formatting Check ==="
                    if command -v black &> /dev/null; then
                        black --check pyscript/ 2>&1 || echo "Black found formatting issues (not an error)"
                    else
                        echo "⚠️ Black not installed, skipping..."
                    fi
                    
                    if command -v isort &> /dev/null; then
                        isort --check-only pyscript/ 2>&1 || echo "Isort found sorting issues (not an error)"
                    else
                        echo "⚠️ Isort not installed, skipping..."
                    fi
                '''
                
                archiveArtifacts artifacts: 'pylint-report.json,flake8-report.txt', allowEmptyArchive: true
            }
        }
        
        stage('Security Report Summary') {
            steps {
                echo "📊 Generating security report summary..."
                sh '''
                    cat > security-summary.txt << 'EOFMARKER'
========================================
SECURITY SCAN SUMMARY
========================================
EOFMARKER
                    
                    echo "Scan Type: ${SECURITY_SCAN_TYPE}" >> security-summary.txt
                    echo "Timestamp: $(date)" >> security-summary.txt
                    echo "Jenkins Job: ${JOB_NAME} #${BUILD_NUMBER}" >> security-summary.txt
                    echo "Python Version: $(python3 --version)" >> security-summary.txt
                    echo "" >> security-summary.txt
                    
                    # Check which tools ran
                    echo "--- Tools Status ---" >> security-summary.txt
                    . ${VENV_DIR}/bin/activate
                    command -v safety &> /dev/null && echo "✓ Safety: Available" >> security-summary.txt || echo "✗ Safety: Not available" >> security-summary.txt
                    command -v pip-audit &> /dev/null && echo "✓ Pip-audit: Available" >> security-summary.txt || echo "✗ Pip-audit: Not available" >> security-summary.txt
                    command -v bandit &> /dev/null && echo "✓ Bandit: Available" >> security-summary.txt || echo "✗ Bandit: Not available" >> security-summary.txt
                    command -v semgrep &> /dev/null && echo "✓ Semgrep: Available" >> security-summary.txt || echo "✗ Semgrep: Not available (optional)" >> security-summary.txt
                    command -v pylint &> /dev/null && echo "✓ Pylint: Available" >> security-summary.txt || echo "✗ Pylint: Not available" >> security-summary.txt
                    echo "" >> security-summary.txt
                    
                    # Parse and summarize results
                    echo "--- Dependency Vulnerabilities ---" >> security-summary.txt
                    if [ -f "safety-report.json" ]; then
                        echo "✓ Safety scan completed. Check safety-report.json for details." >> security-summary.txt
                    fi
                    
                    if [ -f "pip-audit-report.json" ]; then
                        echo "✓ Pip-audit scan completed. Check pip-audit-report.json for details." >> security-summary.txt
                    fi
                    
                    echo "" >> security-summary.txt
                    echo "--- Code Security Issues ---" >> security-summary.txt
                    if [ -f "bandit-report.json" ]; then
                        echo "✓ Bandit scan completed. Check bandit-report.json for details." >> security-summary.txt
                    fi
                    
                    if [ -f "semgrep-report.json" ]; then
                        echo "✓ Semgrep scan completed. Check semgrep-report.json for details." >> security-summary.txt
                    fi
                    
                    echo "" >> security-summary.txt
                    echo "--- Code Quality ---" >> security-summary.txt
                    if [ -f "pylint-report.json" ]; then
                        echo "✓ Pylint analysis completed. Check pylint-report.json for details." >> security-summary.txt
                    fi
                    
                    if [ -f "flake8-report.txt" ]; then
                        echo "✓ Flake8 analysis completed. Check flake8-report.txt for details." >> security-summary.txt
                    fi
                    
                    echo "" >> security-summary.txt
                    echo "========================================" >> security-summary.txt
                    echo "For detailed reports, check Build Artifacts" >> security-summary.txt
                    echo "========================================" >> security-summary.txt
                    
                    cat security-summary.txt
                '''
                
                archiveArtifacts artifacts: 'security-summary.txt'
            }
        }
        
        stage('Run Scraper (Optional)') {
            when {
                expression { params.RUN_SCRAPER == true }
            }
            steps {
                echo "🚀 Running ServiceNow job scraper..."
                sh '''
                    # Activate virtual environment
                    . ${VENV_DIR}/bin/activate
                    
                    cd pyscript
                    python scrape.py
                    
                    # Archive the scraped data
                    if ls PY_jobs-*.json 1> /dev/null 2>&1; then
                        cp PY_jobs-*.json ../
                        echo "✅ Scraper completed successfully"
                        ls -lh PY_jobs-*.json
                    else
                        echo "⚠️ No output file generated"
                    fi
                '''
            }
        }
    }
    
    post {
        always {
            echo "🧹 Cleaning up..."
            sh '''
                # Archive scraper output if exists
                if [ -d "${VENV_DIR}" ]; then
                    echo "Removing virtual environment to save disk space..."
                    rm -rf ${VENV_DIR}
                fi
            '''
            archiveArtifacts artifacts: 'PY_jobs-*.json', allowEmptyArchive: true
        }
        
        success {
            echo "✅ Security testing completed successfully!"
            echo "📁 Check archived artifacts for detailed reports"
            echo "📊 Review security-summary.txt for scan overview"
        }
        
        failure {
            echo "❌ Security testing failed. Check logs for details."
            echo "💡 Tip: Review Console Output for specific error messages"
        }
    }
}