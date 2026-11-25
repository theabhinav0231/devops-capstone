pipeline {
  agent any
  environment {
    APP_IMAGE = 'cloudledger-app'
    K8S_NS    = 'capstone-abhinav'
    VAULT_ADDR = 'http://127.0.0.1:8200'
  }
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Unit Test Gate') {
      steps {
        sh 'python3 -m pytest tests/test_unit.py -v --junitxml=junit-unit.xml'
      }
    }
    stage('Integration Test Gate') {
      steps {
        sh 'python3 -m pytest tests/test_integration.py -v --junitxml=junit-integration.xml'
      }
    }
    stage('Container Build') {
      steps {
        sh 'docker build --build-arg APP_VERSION=1.1.0 -t ${APP_IMAGE}:1.1.0 .'
      }
    }
    stage('DevSecOps Trivy Scan') {
      steps {
        sh 'trivy config --severity HIGH,CRITICAL k8s/'
        sh 'trivy image --severity HIGH,CRITICAL --ignore-unfixed ${APP_IMAGE}:1.1.0'
      }
    }
    stage('Vault Secret Sync') {
      steps {
        sh 'bash security/sync_vault_secret.sh'
      }
    }
    stage('Kubernetes Canary Deploy') {
      steps {
        sh 'kubectl apply -f k8s/'
        sh 'kubectl rollout status deploy/cloudledger-canary -n ${K8S_NS} --timeout=90s'
      }
    }
    stage('SLO Verification & Rollback Gate') {
      steps {
        sh 'bash ops/canary_rollout.sh --verify'
      }
    }
  }
  post {
    always { junit 'junit-*.xml' }
  }
}
