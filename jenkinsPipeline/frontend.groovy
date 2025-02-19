timestamps {
    node('master') {
        stage('Checkout') {
            // No 'steps' block needed in a scripted pipeline
            // checkout([$class: 'GitSCM', branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[url: 'git@github.com:gyl1989113/webTest.git']]])
            checkout([$class: 'GitSCM',
                          branches: [[name: "*/main"]],
                          userRemoteConfigs: [[
                            url: 'git@github.com:gyl1989113/webTest.git',
                            credentialsId: 'github-auth' // 替换为你添加的凭据的 ID
                    ]]])
        }

        stage('编译打包') {
            // Use a Docker container for this stage


            sh """
                ls -al
                docker build -t frontT:v1 .

            """

        }

    }
    // 多台机器可以改成 '4090'等
    node('master') {
        stage('Deploy') {
            sh """
                echo "Deploying to node labeled 4090"
                sudo cp /home/ps/deploy/frontend/docker-compose-front.yml .
                docker-compose -f docker-compose-front.yml up -d
            """
        }
    }
}