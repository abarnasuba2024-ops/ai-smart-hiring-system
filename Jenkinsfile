pipeline {

    agent any

    environment {
        IMAGE_NAME = "ai-smart-hiring-system"
        CONTAINER_NAME = "ai-smart-hiring-container"

        // Docker Desktop executable on your Windows machine
        DOCKER = "C:\\Users\\ELCOT\\AppData\\Local\\Programs\\Docker\\DockerDesktop\\resources\\bin\\docker.exe"

        // Python executable used by Jenkins
        PYTHON = "C:\\Users\\ELCOT\\AppData\\Local\\Programs\\Python\\Python310\\python.exe"
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing Python dependencies...'

                bat '''
                    "%PYTHON%" -m pip install --upgrade pip
                    "%PYTHON%" -m pip install -r requirements.txt
                '''
            }
        }

        stage('Python Compile Check') {
            steps {
                echo 'Checking Python files...'

                bat '''
                    "%PYTHON%" -m py_compile app.py
                    "%PYTHON%" -m py_compile database.py
                    "%PYTHON%" -m py_compile resume_parser.py
                '''
            }
        }

        stage('Test') {
            steps {
                echo 'Running tests...'

                bat '''
                    if exist tests (
                        "%PYTHON%" -m pytest tests
                    ) else (
                        echo No tests folder found.
                        echo Running basic application syntax check instead.
                        "%PYTHON%" -m py_compile app.py
                    )
                '''
            }
        }

        stage('Docker Check') {
            steps {
                echo 'Checking Docker...'

                bat '''
                    echo Docker executable:
                    "%DOCKER%" --version

                    echo.
                    echo Docker information:
                    "%DOCKER%" info
                '''
            }
        }

        stage('Docker Build') {
            steps {
                echo 'Building Docker image...'

                bat '''
                    "%DOCKER%" build -t %IMAGE_NAME% .
                '''
            }
        }

        stage('Docker Run') {
            steps {
                echo 'Starting Docker container...'

                bat '''
                    "%DOCKER%" rm -f %CONTAINER_NAME% 2>nul || exit /b 0

                    "%DOCKER%" run -d ^
                        --name %CONTAINER_NAME% ^
                        -p 5000:5000 ^
                        %IMAGE_NAME%
                '''
            }
        }

        stage('Docker Status') {
            steps {
                echo 'Checking running container...'

                bat '''
                    "%DOCKER%" ps

                    echo.
                    echo Container logs:
                    "%DOCKER%" logs %CONTAINER_NAME%
                '''
            }
        }
    }

    post {

        success {
            echo 'AI Smart Hiring System Docker container started successfully!'
            echo 'Application should be available at http://localhost:5000'
        }

        failure {
            echo 'Build or Docker deployment failed.'
            echo 'Please check the Jenkins Console Output above for the exact error.'
        }

        always {
            echo 'Jenkins pipeline completed.'
        }
    }
}
