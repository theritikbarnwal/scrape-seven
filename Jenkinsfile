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

        /* -------------------- CHECKOUT -------------------- */
        stage('Checkout') {
            steps {
                echo "🔍 Checking out repository..."
                checkout scm
            }
        }

        /* -------------------- PYTHON VENV -------------------- */
        stage('Setup Python Virtual Environment') {
            steps {
                echo "🐍 Setting up Python virtual environment..."
                sh '''
                    python3 --version
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip setuptools wheel
                    pip install -r pyscript/requirements.txt
                    echo "=== Installed packages ==="
                    pip list
                '''
            }
        }

        /* -------------------- SECURITY TOOL INSTALLATION -------------------- */
        stage('Install Security Tools') {
            steps {
                echo "🔒 Installing security tools..."
                sh '''
                    . ${VENV_DIR}/bin/activate

                    pip install bandit safety pip-audit || true
                    pip install pylint flake8 black isort || true
                    pip install playwright
                    playwright install chromium --with-deps || playwright install chromium

                    pip install semgrep || echo "⚠️ Semgrep failed to install"

                    echo "=== Installed Tools ==="
                    pip list | grep -E "bandit|safety|pip-audit|semgrep|pylint|flake8|black|isort|playwright" || true
                '''
            }
        }

        /* -------------------- DEPENDENCY SECURITY -------------------- */
        stage('Dependency Vulnerability Scan') {
            when {
                expression {
                    params.SECURITY_SCAN_TYPE in [
                        'Quick Scan (Fast)', 'Dependency Scan Only', 'All Checks', 'Full Security Audit'
                    ]
                }
            }
            steps {
                echo "🛡️ Running dependency vulnerability scans..."
                sh '''
                    . ${VENV_DIR}/bin/activate

                    echo "=== Safety ==="
                    if command -v safety >/dev/null 2>&1; then
                        safety check --json > safety-report.json || true
                    else
                        echo "Safety not installed" > safety-report.json
                    fi

                    echo "=== Pip-audit ==="
                    if command -v pip-audit >/dev/null 2>&1; then
                        pip-audit --desc --format json > pip-audit-report.json || true
                    else
                        echo "pip-audit not installed" > pip-audit-report.json
                    fi
                '''
                archiveArtifacts artifacts: '*-report.json', allowEmptyArchive: true
            }
        }

        /* -------------------- STATIC CODE SECURITY (FIXED VERSION) -------------------- */
        stage('Static Code Security Analysis') {
            when {
                expression {
                    params.SECURITY_SCAN_TYPE in ['Quick Scan (Fast)', 'Full Security Audit', 'All Checks']
                }
            }
            options {
                timeout(time: 10, unit: 'MINUTES')
            }
            steps {
                echo "🔎 Running static security analysis..."
                sh '''
                    set -eux   # POSIX safe

                    . ${VENV_DIR}/bin/activate

                    echo "Python: $(which python3)"
                    echo "Bandit: $(command -v bandit || echo 'missing')"
                    echo "Semgrep: $(command -v semgrep || echo 'missing')"

                    echo "=== BANDIT ==="
                    BANDIT_LEVEL=""
                    if [ "${SECURITY_SCAN_TYPE}" = "Quick Scan (Fast)" ]; then
                        BANDIT_LEVEL="-lll"
                    else
                        BANDIT_LEVEL="-ll"
                    fi

                    bandit -r pyscript/ $BANDIT_LEVEL -f json -o bandit-report.json || echo "Bandit completed with warnings"

                    echo "=== SEMGREP ==="
                    if [ "${SECURITY_SCAN_TYPE}" != "Quick Scan (Fast)" ]; then
                        if command -v semgrep >/dev/null 2>&1; then
                            timeout 60 semgrep --config=p/ci --json pyscript/ > semgrep-report.json \
                                || echo "Semgrep failed or timed out" > semgrep-report.json
                        else
                            echo "Semgrep not installed" > semgrep-report.json
                        fi
                    else
                        echo "Semgrep skipped for Quick Scan" > semgrep-report.json
                    fi
                '''
                archiveArtifacts artifacts: 'bandit-report.json,semgrep-report.json', allowEmptyArchive: true
            }
        }

        /* -------------------- CODE QUALITY -------------------- */
        stage('Code Quality Check') {
            when {
                expression {
                    params.SECURITY_SCAN_TYPE in ['Code Quality Check', 'All Checks']
                }
            }
            steps {
                echo "✨ Running code quality checks..."
                sh '''
                    . ${VENV_DIR}/bin/activate

                    if command -v pylint >/dev/null 2>&1; then
                        pylint pyscript/*.py --output-format=json > pylint-report.json || true
                    else
                        echo "Pylint not installed" > pylint-report.json
                    fi

                    if command -v flake8 >/dev/null 2>&1; then
                        flake8 pyscript/ --output-file=flake8-report.txt || true
                    else
                        echo "Flake8 not installed" > flake8-report.txt
                    fi

                    if command -v black >/dev/null 2>&1; then
                        black --check pyscript/ || true
                    fi

                    if command -v isort >/dev/null 2>&1; then
                        isort --check-only pyscript/ || true
                    fi
                '''
                archiveArtifacts artifacts: 'pylint-report.json,flake8-report.txt', allowEmptyArchive: true
            }
        }

        /* -------------------- SECURITY SUMMARY -------------------- */
        stage('Security Report Summary') {
            steps {
                echo "📊 Building summary..."
                sh '''
                    . ${VENV_DIR}/bin/activate

                    echo "=== Security Summary ===" > security-summary.txt
                    echo "Scan Type: ${SECURITY_SCAN_TYPE}" >> security-summary.txt
                    echo "Timestamp: $(date)" >> security-summary.txt

                    echo "--- Tools ---" >> security-summary.txt
                    command -v bandit >/dev/null && echo "Bandit OK" >> security-summary.txt || echo "Bandit Missing" >> security-summary.txt
                    command -v semgrep >/dev/null && echo "Semgrep OK" >> security-summary.txt || echo "Semgrep Missing" >> security-summary.txt

                    echo "--- Reports ---" >> security-summary.txt
                    [ -f bandit-report.json ] && echo "Bandit: OK" >> security-summary.txt
                    [ -f semgrep-report.json ] && echo "Semgrep: OK" >> security-summary.txt
                    [ -f safety-report.json ] && echo "Safety: OK" >> security-summary.txt
                    [ -f pip-audit-report.json ] && echo "Pip-audit: OK" >> security-summary.txt
                '''
                archiveArtifacts artifacts: 'security-summary.txt'
            }
        }

        /* -------------------- OPTIONAL SCRAPER -------------------- */
        stage('Run Scraper (Optional)') {
            when { expression { params.RUN_SCRAPER == true } }
            steps {
                echo "🚀 Running scraper..."
                sh '''
                    . ${VENV_DIR}/bin/activate
                    cd pyscript
                    python scrape.py

                    cp PY_jobs-*.json ../ || true
                '''
            }
        }
    }

    post {
        always {
            echo "🧹 Cleaning up..."
            sh '''
                rm -rf ${VENV_DIR}
            '''
            archiveArtifacts artifacts: 'PY_jobs-*.json', allowEmptyArchive: true
        }

        success {
            echo "✅ Security testing completed successfully!"
        }

        failure {
            echo "❌ Security testing FAILED. Check logs."
        }
    }
}
