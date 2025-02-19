pipeline {
    agent none  // No global agent; specify per stage
    parameters {
        gitParameter name: 'Tags',
                     type: 'PT_BRANCH_TAG',
                     defaultValue: 'master',
                     selectedValue: 'DEFAULT',
                     sortMode: 'DESCENDING_SMART',
                     description: 'Select the branch to build'
        choice(name: 'Machine', choices: ['master', '4090', '4080', '3080'], description: 'Select the machine to deploy')
    }
    stages {
        stage('Checkout') {
            agent { label 'master' }  // Specify the agent for this stage
            steps {
                checkout([$class: 'GitSCM',
                          branches: [[name: "${params.Tags}"]],
                          userRemoteConfigs: [[
                            url: 'https://github.com/gyl1989113/goBackendTest.git',
                            credentialsId: 'github-auth'
                        ]]])
            }
        }

        stage('编译打包') {
            agent { label 'master' }  // Specify the agent for this stage
            steps {
                sh """
                    ls -al
                    docker build -t backend:${params.Tags} .
                """
            }
        }
    }


}