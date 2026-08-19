pipeline {

    agent any

    environment {
        // Python
        PYTHON = 'C:\\Users\\ELCOT\\AppData\\Local\\Programs\\Python\\Python310\\python.exe'

        // Docker executable
        DOCKER = 'C:\\Users\\ELCOT\\AppData\\Local\\Programs\\Docker\\DockerDesktop\\resources\\bin\\docker.exe'

        // Docker image name
        IMAGE_NAME = 'ai-smart-hiring-system'

        // Docker container name
        CONTAINER_NAME = 'ai-smart-hiring-system-container'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Starting AI Smart Hiring System pipeline...'
                echo 'Checking workspace...'

                bat 'dir'
            }
        }

        stage('Python Check') {
            steps {
                echo 'Checking Python installation...'

                bat '"%PYTHON%" --version'
            }
        }

        stage('Compile Python') {
            steps {
                echo 'Compiling app.py...'

                bat '"%PYTHON%" -m py_compile app.py'
            }
        }

        stage('Docker Check') {
            steps {
                echo 'Checking Docker installation...'

                bat 'docker version'
                bat 'docker info'
            }
        }

        stage('Docker Build') {
            steps {
                echo 'Building Docker image...'

                bat '"%DOCKER%" build -t %IMAGE_NAME% .'
            }
        }

        stage('Docker Stop Existing Container') {
            steps {
                echo 'Stopping existing container if it exists...'

                bat '"%DOCKER%" rm -f %CONTAINER_NAME% 2>nul || exit /b 0'
            }
        }

        stage('Docker Run') {
            steps {
                echo 'Starting Docker container...'

                bat '"%DOCKER%" run -d --name %CONTAINER_NAME% -p 5000:5000 %IMAGE_NAME%'
            }
        }

        stage('Docker Status') {
            steps {
                echo 'Checking running Docker containers...'

                bat '"%DOCKER%" ps'
            }
        }
    }

    post {

        success {
            echo '=============================================='
            echo 'AI Smart Hiring System deployed successfully!'
            echo 'Docker container is running.'
            echo 'Application: http://localhost:5000'
            echo '=============================================='
        }

        failure {
            echo '=============================================='
            echo 'Build or Docker deployment failed.'
            echo 'Check the Jenkins Console Output.'
            echo '=============================================='
        }

        always {
            echo 'Jenkins pipeline completed.'
        }
    }
}

