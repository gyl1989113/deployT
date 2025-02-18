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
        stage('Checkout Repositories') {
            agent { label 'master' }
            steps {
                // Checkout the main project, which will be used for the COPY . /root/ directive
                checkout([$class: 'GitSCM',
                          branches: [[name: "${params.Tags}"]],
                          userRemoteConfigs: [[
                            url: 'https://github.com/6block/zkwork.git',
                            credentialsId: 'haoyang-gitauth'
                          ]]
                ])
                // Also checkout the deployT repository (which contains the Dockerfile) into a subdirectory named deployT
                dir('deployT') {
                    checkout([$class: 'GitSCM',
                              branches: [[name: "main"]], // Assumed branch for Dockerfile repository
                              userRemoteConfigs: [[
                                url: 'git@github.com:gyl1989113/deployT.git',
                                credentialsId: 'github-auth'
                              ]]
                    ])
                }
            }
        }
        stage('编译打包') {
            agent { label 'master' }
            steps {
                script {
                    def cleanTag = params.Tags.replace("origin/", "")
                    sh """
                        ls -al
                        cp deployT/deploy/run_bench.sh .

                        # Build the Docker image, using the Dockerfile from deployT/deploy/Dockerfile and the clean tag for the image
                        docker build -t cudabench:${cleanTag} -f deployT/deploy/Dockerfile .
                    """
                }
            }
        }
        stage('Deploy') {
            agent { label "${params.Machine}" }
            steps {
                script {
                    def cleanTag = params.Tags.replace("origin/", "")
                    def sharedDir = "/var/lib/jenkins/workspace"  // Define the shared directory path

                    // Trigger the collectData job once with the parameter.
                    // It is assumed that collectData is written to run continuously and check for a stop signal.
                    build job: 'collectData',
                          parameters: [string(name: 'Machine', value: params.Machine)],
                          wait: false
                    echo "Triggered collectData job..."

                    // Start the docker run command.
                    sh "docker run --gpus=all cudabench:${cleanTag}"

                    // Once docker run finishes, signal collectData to stop by creating a stop file.
                    sh "touch ${sharedDir}/stop_collectData.txt"
                    echo "Signaled collectData to stop."
                }
            }
        }
    }
}