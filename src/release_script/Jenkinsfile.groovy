echo "---build start---"
node("${NODE}") {
    properties(
        [
            [$class: 'ParametersDefinitionProperty', parameterDefinitions:
                    [
                            [$class: 'BooleanParameterDefinition', defaultValue: false, description: '테스트를 Skip 할 수 있습니다. 선택 시 테스트를 건너뛰고 체크아웃 - 빌드 - 아카이빙만 진행합니다', name: 'skipTests']
                            , [$class: 'StringParameterDefinition', defaultValue: 'development', description: 'Maven에서 Active 할 Profile 을 입력하세요. 예) production', name: 'activeProfile']
                    ]
            ]])
    )
    def shared_workspace

    stage('Preparation') { // for display purposes
        echo "Current workspace : ${workspace}"
        // Get the Maven tool.
        // ** NOTE: This 'M3' Maven tool must be configured
        // **       in the global configuration.
        shared_workspace = tool 'MapEditor_Pull'
    }
    stage('checkout'){
        checkout scm
    }

    stage(‘build’)
        {
            steps
            {
                script
                {
                    try
                    {
                        build job: ‘02_build_sim’, parameters: [ string(name: ‘RELEASE_BUILD’, value: “FALSE“),string(name: ‘NODE’, value: ${NODE}),string(name: ‘RELEASE_TYPE’, value: “SIM“),string(name: ‘Release_Version’, value: ${Release_Version}) ]
                    } catch (e)
                    {
                        echo ‘build_sim failed’
                    }
                }
            }
            
            
        }
        stage(‘build2’)
        {
            steps
            {
                 script
                {
                    try
                    {
                        build job: ‘02_build_internal’ , parameters: [ string(name: ‘RELEASE_BUILD’, value: “FALSE“),string(name: ‘NODE’, value: ${NODE}),string(name: ‘RELEASE_TYPE’, value: “INTERNAL“),string(name: ‘Release_Version’, value: ${Release_Version}) ]
                    } catch (e)
                    {
                        echo ‘build internal failed’
                    }
                }
    
            }
        }
        stage(‘build3’)
        {
            steps
            {
                 script
                {
                    try
                    {
                        build job: ‘02_build_scenario’ , parameters: [ string(name: ‘RELEASE_BUILD’, value: “FALSE“),string(name: ‘NODE’, value: ${NODE}),string(name: ‘RELEASE_TYPE’, value: “SCENARIO“),string(name: ‘Release_Version’, value: ${Release_Version}) ]
                    } catch (e)
                    {
                        echo ‘sceario build failed’
                    }
                }
            }
        }
    }
    
}

    
   
