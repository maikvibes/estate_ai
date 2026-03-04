pipeline {
    agent any
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
        stage('Environment Setup') {
            steps {
                echo 'Generating .env file...'
                sh """
                    cat <<EOF > .env
KAFKA_BOOTSTRAP_SERVERS=192.168.1.80:9092
KAFKA_REQUESTS_TOPIC=agent.requests
KAFKA_LISTINGS_TOPIC=listings.new
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=estate_ai
LISTING_REVIEW_WEBHOOK_URL=https://api.estate.maik.io.vn/reporting/review
LISTING_REVIEW_SECRET=your_webhook_secret_here
CHROMA_PERSIST_DIR=.chroma
EOF
                """
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
                    sh "docker-compose up -d --build"
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
