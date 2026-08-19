pipeline {
    agent any

    environment {
        IMAGE_NAME = "ai-smart-hiring-system"
        CONTAINER_NAME = "ai-smart-hiring-container"
    }

    stages {

        stage('Build') {
            steps {
                echo 'Building AI Smart Hiring System...'

                bat '"C:\\Users\\ELCOT\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" --version'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat 'if exist requirements.txt "C:\\Users\\ELCOT\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                bat '"C:\\Users\\ELCOT\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" -m py_compile app.py'
            }
        }

        stage('Docker Build') {
            steps {
                bat 'docker build -t %IMAGE_NAME% .'
            }
        }

        stage('Docker Run') {
            steps {
                bat 'docker rm -f %CONTAINER_NAME% 2>nul || exit /b 0'
                bat 'docker run -d --name %CONTAINER_NAME% -p 5000:5000 %IMAGE_NAME%'
            }
        }
    }

    post {
        success {
            echo 'AI Smart Hiring System Docker container started successfully!'
        }
        failure {
            echo 'Build or Docker deployment failed.'
        }
    }
}

