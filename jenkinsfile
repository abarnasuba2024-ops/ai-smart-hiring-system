pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Building AI Smart Hiring System...'
                bat 'python --version'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat 'if exist requirements.txt pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                bat 'python -m py_compile app.py'
            }
        }
    }

    post {
        success {
            echo 'Build completed successfully!'
        }
        failure {
            echo 'Build failed!'
        }
    }
}
