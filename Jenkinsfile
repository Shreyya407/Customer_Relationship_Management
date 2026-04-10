def runPythonOnWindows(String args) {
    bat """
@echo off
setlocal

if not "%WINDOWS_PYTHON%"=="" (
    if not exist "%WINDOWS_PYTHON%" (
        echo ERROR: WINDOWS_PYTHON is set but file was not found: %WINDOWS_PYTHON%
        exit /b 1
    )
    "%WINDOWS_PYTHON%" ${args}
    exit /b %errorlevel%
)

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 ${args}
    exit /b %errorlevel%
)

where python >nul 2>&1
if %errorlevel%==0 (
    python ${args}
    exit /b %errorlevel%
)

for %%P in (
    "%USERPROFILE%\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
    "%USERPROFILE%\\AppData\\Local\\Programs\\Python\\Python311\\python.exe"
    "%LOCALAPPDATA%\\Programs\\Python\\Python312\\python.exe"
    "%LOCALAPPDATA%\\Programs\\Python\\Python311\\python.exe"
    "%ProgramFiles%\\Python312\\python.exe"
    "%ProgramFiles%\\Python311\\python.exe"
    "%ProgramFiles(x86)%\\Python312-32\\python.exe"
    "%ProgramFiles(x86)%\\Python311-32\\python.exe"
) do (
    if exist %%~P (
        "%%~P" ${args}
        exit /b %errorlevel%
    )
)

echo ERROR: Python was not found on this Jenkins agent.
echo Install Python 3 and restart Jenkins service, or set WINDOWS_PYTHON to the full path.
echo Example: C:\\Python312\\python.exe
echo Jenkins account: %USERNAME%
echo User profile: %USERPROFILE%
echo If Python is user-scoped, run Jenkins service under that same Windows user.
exit /b 1
"""
}

pipeline {
    agent any

    parameters {
        string(name: 'WINDOWS_PYTHON', defaultValue: 'C:\\Users\\Asus\\AppData\\Local\\Programs\\Python\\Python312\\python.exe', description: 'Optional absolute path to python.exe for Windows agents')
        booleanParam(name: 'DEPLOY_LOCAL_STAGING', defaultValue: false, description: 'Deploy backend/frontend to a local staging folder after successful build')
        string(name: 'STAGING_ROOT', defaultValue: 'C:\\JenkinsDeploy\\crm-staging', description: 'Windows staging folder used by deployment scripts')
        string(name: 'STAGING_PORT', defaultValue: '8010', description: 'Port used by staged backend service for smoke test')
    }

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Backend - Install Dependencies') {
            steps {
                dir('backend') {
                    script {
                        if (isUnix()) {
                            sh 'python3 -m pip install --upgrade pip'
                            sh 'python3 -m pip install -r requirements.txt'
                        } else {
                            runPythonOnWindows('--version')
                            runPythonOnWindows('-m pip install --upgrade pip')
                            runPythonOnWindows('-m pip install -r requirements.txt')
                        }
                    }
                }
            }
        }

        stage('Backend - Run Tests') {
            steps {
                dir('backend') {
                    script {
                        if (isUnix()) {
                            sh 'python3 -m pytest tests -q'
                        } else {
                            runPythonOnWindows('-m pytest tests -q')
                        }
                    }
                }
            }
        }

        stage('Backend - Train ML Model') {
            steps {
                dir('backend') {
                    script {
                        if (isUnix()) {
                            sh 'python3 ml/train.py'
                        } else {
                            runPythonOnWindows('ml\\train.py')
                        }
                    }
                }
            }
        }

        stage('Frontend - Install & Build') {
            steps {
                dir('frontend') {
                    script {
                        if (isUnix()) {
                            sh 'npm ci || npm install'
                            sh 'npm run build'
                        } else {
                            bat 'npm ci || npm install'
                            bat 'npm run build'
                        }
                    }
                }
            }
        }

        stage('Deploy - Local Staging') {
            when {
                expression { return !isUnix() && params.DEPLOY_LOCAL_STAGING }
            }
            steps {
                bat "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\deploy_local_staging.ps1 -WorkspacePath \"%WORKSPACE%\" -DeployRoot \"${params.STAGING_ROOT}\" -Port ${params.STAGING_PORT} -PythonExe \"${params.WINDOWS_PYTHON}\""
            }
        }

        stage('Smoke Test - Local Staging') {
            when {
                expression { return !isUnix() && params.DEPLOY_LOCAL_STAGING }
            }
            steps {
                script {
                    runPythonOnWindows("scripts\\smoke_test.py --url http://127.0.0.1:${params.STAGING_PORT}/health --timeout-seconds 120")
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'backend/ml/artifacts/*.joblib,frontend/dist/**', allowEmptyArchive: true
            script {
                if (!isUnix() && params.DEPLOY_LOCAL_STAGING) {
                    bat "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\stop_local_staging.ps1 -DeployRoot \"${params.STAGING_ROOT}\""
                }
            }
        }
    }
}
