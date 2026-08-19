pipeline {
    agent any

    stages {

        stage('Build') {
            steps {
                echo 'Building AI Smart Hiring System...'

                bat '"C:/Users/ELCOT/AppData/Local/Programs/Python/Python310/python.exe" --version'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '''
                if exist requirements.txt (
                    "C:/Users/ELCOT/AppData/Local/Programs/Python/Python310/python.exe" -m pip install -r requirements.txt
                ) else (
                    echo requirements.txt not found - skipping dependency installation
                )
                '''
            }
        }

        stage('Test') {
            steps {
                bat '''
                "C:/Users/ELCOT/AppData/Local/Programs/Python/Python310/python.exe" -m py_compile app.py
                '''
            }
        }
    }
}
