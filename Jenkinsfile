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
                    docker.image('cuda:1.0').inside('--user root -e HOST_HOSTNAME=$(hostname) -v /etc/localtime:/etc/localtime:ro --privileged --gpus all') {
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
                                sh 'cd deploy/hardware && rm -f task1_completed* && rm -f gpu_metrics*.txt'
                                sh 'cd rust&& cargo bench|grep -vi "Warning" > test_result'
//                                 sh 'sleep 60 && echo "hello" > test_result'
                                sh "cd deploy/hardware && touch task1_completed"
                            },
                            "task2": {
                                sh 'cd deploy/hardware && gcc -o gpu_monitor gpu_monitor.c -I/usr/local/cuda/include/ -L/usr/lib/ -lnvidia-ml -pthread'
                                sh 'cd deploy/hardware && ./gpu_monitor'
                            }
                        )

                        def generatedFile = 'deploy/hardware/gpu_metrics0.txt'
                        if (fileExists(generatedFile)) {
                            echo "文件 ${generatedFile} 已成功生成。"
                            // 传递 Jenkins 作业名称和构建编号作为参数
                            def jobNameWithBuildNumber = "${env.JOB_NAME}_${env.BUILD_NUMBER}"
                            sh "cd deploy/hardware && pip3 install -r requirements.txt && python3 cuda_influxdb.py ${jobNameWithBuildNumber}"
                        } else {
                            error "文件 ${generatedFile} 未生成，构建失败。"
                        }
                    }
                }
            }
        }
    }

}