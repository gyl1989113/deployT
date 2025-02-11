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

        stage('Deploy') {
            agent { label "${params.Machine}" }  // Specify the agent for this stage
            steps {
                script {
                    // Checkout the deployment repository
                    checkout([$class: 'GitSCM',
                              branches: [[name: "main"]],
                              userRemoteConfigs: [[
                                url: 'https://github.com/gyl1989113/deployT.git',
                                credentialsId: 'github-auth'
                            ]]])

                    // Modify the docker-compose-back.yml file to replace ${Tag} with the actual value
                    sh """
                        sed -i 's/\${Tag}/${params.Tags}/g' ./deploy/docker-compose-back.yml
                    """
                }

                // Run Docker Compose commands
                sh """
                    cd deploy
                    docker-compose -p backend -f docker-compose-back.yml down
                    sleep 1
                    docker-compose -p backend -f docker-compose-back.yml up -d

                """
            }
        }
    }
    post {
        success {
            script {
                // 延迟 10 分钟触发另一个任务
                sleep time: 1, unit: 'MINUTES'
                build job: 'collectData', parameters: [string(name: 'Machine', value: params.Machine)]

            }
        }
    }
}