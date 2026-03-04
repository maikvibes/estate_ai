pipeline {
    agent any
    tools {
        dockerTool 'Default'
    }
    environment {
        // Docker configuration
        DOCKER_IMAGE = 'estate-ai-app'
        DOCKER_TAG = "v${env.BUILD_NUMBER}"
        // Credentials for GitHub would typically be managed in Jenkins Web UI
        // and passed to 'checkout scm' automatically.
    }

    stages {
        stage('Checkout') {
            steps {
                // Using generic checkout scm which respects the GitHub config in Jenkins Job
                checkout scm
            }
        }

        stage('Build Image') {
            steps {
                echo 'Building Docker image...'
                script {
                    sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
                    sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest"
                }
            }
        }



        stage('Deploy') {
            steps {
                echo 'Starting service with Docker Compose...'
                script {
                    // Ensure environment variables are loaded from .env or Jenkins secrets
                    // docker-compose automatically picks up .env in the same dir
                    sh "docker compose up -d --build"
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline has finished.'
        }
        success {
            echo 'Deployment successful via Docker!'
        }
        failure {
            echo 'Pipeline failed. Check Docker logs.'
        }
    }
}
