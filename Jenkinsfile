pipeline {
    agent any

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
                            bat 'python -m pip install --upgrade pip'
                            bat 'python -m pip install -r requirements.txt'
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
                            bat 'python -m pytest tests -q'
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
                            bat 'python ml\\train.py'
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
    }

    post {
        always {
            archiveArtifacts artifacts: 'backend/ml/artifacts/*.joblib,frontend/dist/**', allowEmptyArchive: true
        }
    }
}
