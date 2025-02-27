pipeline {
    agent none
    parameters {
        gitParameter name: 'BRANCH_TAG',
                     type: 'PT_BRANCH_TAG',
                     defaultValue: 'master',
                     selectedValue: 'DEFAULT',
                     sortMode: 'DESCENDING_SMART',
                     description: 'Select the branch to build'
        choice(name: 'NODE_LABEL', choices: ['master'], description: '选择要使用的机器节点')
    }
  
    stages {
        stage("select node and run in docker"){
            agent {
                node {
                    label "${params.NODE_LABEL}"
                }
            }
            steps {
                script {
                    sh 'rm -rf task1_completed*'
                    docker.image('cuda:1.0').inside('--user root -v /etc/localtime:/etc/localtime:ro --privileged --gpus all') {
                        // 提取到外面统一处理步骤
                        checkout([
                            $class: 'GitSCM', 
                            branches: [[name: "${params.BRANCH_TAG}"]],
                            userRemoteConfigs: [[
                                url: 'https://github.com/6block/zkwork.git',
                                credentialsId: 'ee3ca30d-4d1c-4c0d-a72f-9fb5a903e172' 
                            ]]
                        ])
                        
                        checkout([
                            $class: 'GitSCM', 
                            branches: [[name: 'main']],
                            userRemoteConfigs: [[
                                url: 'https://github.com/gyl1989113/deployT.git',
                                credentialsId: 'github-auth' 
                            ]],
                            extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'deploy']]
                        ])


                        parallel (
                            "task1": {
                                sh 'cd rust&& cargo bench|grep -vi "Warning" > test_result'
                                //sh "touch task1_completed_${currentTime}"
                                sh "cd deploy/hardware && touch task1_completed"
                            },
                            "task2": {
                                sh 'cd deploy/hardware && gcc -o gpu_monitor gpu_monitor.c -I/usr/local/cuda/include/ -L/usr/lib/ -lnvidia-ml -pthread'
                                sh 'cd deploy/hardware && ./gpu_monitor'
                            }
                        )

                        def generatedFile = 'gpu_metrics0.txt'
                        if (fileExists(generatedFile)) {
                            echo "文件 ${generatedFile} 已成功生成。"
                            sh 'cd deploy/hardware && python3 cuda_influxdb.py'
                        } else {
                            error "文件 ${generatedFile} 未生成，构建失败。"
                        }
                    }
                }
            }
        }
    }
    post {
        success {
            node("${params.NODE_LABEL}") {
                script {    
                    def testResult
                    try {
                        testResult = readFile('rust/test_result')
                    } catch (FileNotFoundException e) {
                        testResult = "Test result file 'rust/test.txt' not found."
                    }
                    emailext(
                        subject: '${ENV, var="JOB_NAME"} - Build # ${BUILD_NUMBER} - SUCCESS',
                        body: """
                        <p>Build Status: SUCCESS</p>
                        <p>Build Number: ${BUILD_NUMBER}</p>
                        <p>Build URL: <a href="${BUILD_URL}">${BUILD_URL}</a></p>
                        <p>Test Results:</p>
                        <pre>${testResult}</pre>
                        """,
                        to: 'wangmao2009@sina.com', '1476642362@qq.com',
                        replyTo: '229681868@qq.com',
                        mimeType: 'text/html'
                    )
                    echo 'c and Python script executed successfully.check grafana'
                }
            }
        }
    }
}