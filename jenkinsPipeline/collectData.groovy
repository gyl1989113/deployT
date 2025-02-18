pipeline {
    agent none  // No global agent; specify per stage
    parameters {
        choice(name: 'Machine', choices: ['master', '4090', '4080', '3080'], description: 'Select the machine to deploy')
    }
    stages {
        stage('Checkout') {
            agent { label "${params.Machine}" }
            steps {
                script {
                    checkout([$class: 'GitSCM',
                              branches: [[name: "main"]],
                              userRemoteConfigs: [[
                                  url: 'https://github.com/gyl1989113/deployT.git',
                                  credentialsId: 'github-auth'
                              ]]
                    ])

                    def sharedDir = "/var/lib/jenkins/workspace"  // Define the shared directory path

                    // Install requirements, then enter a loop to run the data gathering script repeatedly.
                    // The loop will exit when a "stop" file (stop_collectData.txt) is detected.
                    sh """
                        /usr/bin/pip3 install -r requirements.txt
                        cd hardware
                        while [ ! -f ${sharedDir}/stop_collectData.txt ]; do
                            /usr/bin/python3 gatherdata.py
                            sleep 10
                        done
                    """
                }
            }
        }
    }
}