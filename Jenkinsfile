pipeline {
    agent any
    
    parameters {
        choice(
            name: 'SECURITY_SCAN_TYPE',
            choices: ['Full Security Audit', 'Dependency Scan Only', 'Code Quality Check', 'All Checks'],
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
                    pip install --upgrade pip
                    
                    # Install project dependencies
                    pip install -r pyscript/requirements.txt
                    
                    # Verify installation
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
                    
                    # Install security scanning tools
                    pip install bandit safety pip-audit semgrep
                    
                    # Install code quality tools
                    pip install pylint flake8 black isort
                    
                    # Install Playwright and its browsers
                    pip install playwright
                    playwright install chromium
                    
                    # Show installed packages
                    echo "\\n=== Installed Security Tools ==="
                    pip list | grep -E "bandit|safety|pip-audit|semgrep|pylint|flake8|black|isort|playwright"
                '''
            }
        }
        
        stage('Dependency Vulnerability Scan') {
            when {
                expression { 
                    params.SECURITY_SCAN_TYPE in ['Dependency Scan Only', 'All Checks', 'Full Security Audit'] 
                }
            }
            steps {
                echo "🛡️ Scanning dependencies for known vulnerabilities..."
                sh '''
                    # Activate virtual environment
                    . ${VENV_DIR}/bin/activate
                    
                    echo "=== Safety Check (PyPI vulnerabilities) ==="
                    safety check --json > safety-report.json || true
                    safety check || true
                    
                    echo "\\n=== Pip Audit (comprehensive vulnerability check) ==="
                    pip-audit --desc --format json > pip-audit-report.json || true
                    pip-audit --desc || true
                '''
                
                archiveArtifacts artifacts: '*-report.json', allowEmptyArchive: true
            }
        }
        
        stage('Static Code Security Analysis') {
            when {
                expression { 
                    params.SECURITY_SCAN_TYPE in ['Full Security Audit', 'All Checks'] 
                }
            }
            steps {
                echo "🔎 Running static security analysis on code..."
                sh '''
                    # Activate virtual environment
                    . ${VENV_DIR}/bin/activate
                    
                    echo "=== Bandit Security Scan ==="
                    bandit -r pyscript/ -f json -o bandit-report.json || true
                    bandit -r pyscript/ -ll || true
                    
                    echo "\\n=== Semgrep Security Patterns ==="
                    semgrep --config=auto pyscript/ --json > semgrep-report.json || true
                    semgrep --config=auto pyscript/ || true
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
                    pylint pyscript/*.py --output-format=json > pylint-report.json || true
                    pylint pyscript/*.py || true
                    
                    echo "\\n=== Flake8 Linting ==="
                    flake8 pyscript/ --output-file=flake8-report.txt || true
                    flake8 pyscript/ || true
                    
                    echo "\\n=== Code Formatting Check ==="
                    black --check pyscript/ || true
                    isort --check-only pyscript/ || true
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
                    echo "Removing virtual environment..."
                    rm -rf ${VENV_DIR}
                fi
            '''
            archiveArtifacts artifacts: 'PY_jobs-*.json', allowEmptyArchive: true
        }
        
        success {
            echo "✅ Security testing completed successfully!"
            echo "📁 Check archived artifacts for detailed reports"
        }
        
        failure {
            echo "❌ Security testing failed. Check logs for details."
        }
    }
}