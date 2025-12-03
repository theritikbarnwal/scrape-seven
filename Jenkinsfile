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
        PYTHON_VERSION = '3.11'
        WORKSPACE_CLEAN = 'true'
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo "🔍 Checking out repository..."
                checkout scm
            }
        }
        
        stage('Setup Python Environment') {
            steps {
                echo "🐍 Setting up Python ${PYTHON_VERSION}..."
                sh '''
                    python3 --version
                    python3 -m pip install --upgrade pip
                    pip install -r pyscript/requirements.txt
                '''
            }
        }
        
        stage('Install Security Tools') {
            steps {
                echo "🔒 Installing security scanning tools..."
                sh '''
                    # Install security scanning tools
                    pip install bandit safety pip-audit semgrep
                    
                    # Install code quality tools
                    pip install pylint flake8 black isort
                    
                    # Install Playwright for testing
                    playwright install chromium
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
                        echo "Safety scan completed. Check safety-report.json for details." >> security-summary.txt
                    fi
                    
                    if [ -f "pip-audit-report.json" ]; then
                        echo "Pip-audit scan completed. Check pip-audit-report.json for details." >> security-summary.txt
                    fi
                    
                    echo "" >> security-summary.txt
                    echo "--- Code Security Issues ---" >> security-summary.txt
                    if [ -f "bandit-report.json" ]; then
                        echo "Bandit scan completed. Check bandit-report.json for details." >> security-summary.txt
                    fi
                    
                    echo "" >> security-summary.txt
                    echo "--- Code Quality ---" >> security-summary.txt
                    if [ -f "pylint-report.json" ]; then
                        echo "Pylint analysis completed. Check pylint-report.json for details." >> security-summary.txt
                    fi
                    
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
                    cd pyscript
                    python scrape.py
                    
                    # Archive the scraped data
                    if ls PY_jobs-*.json 1> /dev/null 2>&1; then
                        cp PY_jobs-*.json ../
                        echo "✅ Scraper completed successfully"
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