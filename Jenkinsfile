// =====================================================================
// 小树成长岛 (studentStudy) Jenkins 部署流水线
// 参考 akshare-docker 部署目录改造：
//   - 原项目前后端为两个独立仓库；本项目为单仓库 monorepo
//   - 服务器上 git clone 整个仓库到 $DEPLOY_PATH/src，再 docker compose 构建部署
// 架构: backend(FastAPI) + frontend(Vue 构建产物 volume) + nginx(反向代理)
// =====================================================================
pipeline {
    agent any

    environment {
        PROJECT_NAME = 'studentstudy'
        WORKSPACE_DIR = "${WORKSPACE}"

        // 部署服务器（参考 akshare-docker: sos@192.168.3.53，可在构建参数覆盖）
        DEPLOY_SERVER = 'sos@192.168.3.53'
        DEPLOY_PATH = '/home/sos/apps/studentstudy'
        SSH_CREDENTIALS_ID = 'sos'

        // 仓库与端口
        GIT_REPO = 'git@github.com:lwyx2000/studentStudy.git'
        NGINX_PORT = '8061'
        BACKEND_PORT = '3001'
        // 服务器上仓库克隆到 $DEPLOY_PATH/src，compose 构建上下文前缀
        SRC_DIR = './src'
        COMPOSE_PROJECT_NAME = 'studentstudy'
    }

    parameters {
        string(name: 'GIT_BRANCH', defaultValue: 'main', description: 'Git 分支名称')
        string(name: 'DEPLOY_SERVER', defaultValue: '', description: '部署服务器 user@host（留空使用环境变量）')
        string(name: 'DEPLOY_PATH', defaultValue: '', description: '服务器部署目录（留空使用环境变量）')
        booleanParam(name: 'SKIP_TESTS', defaultValue: false, description: '跳过健康检查')
        booleanParam(name: 'FORCE_REBUILD', defaultValue: false, description: '强制重新构建镜像 (--no-cache)')
        booleanParam(name: 'FORCE_PULL', defaultValue: true, description: '强制重新拉取最新 Git 代码（清空 src 重新 clone）')

        choice(name: 'DEPLOY_TARGET', choices: ['all', 'backend', 'frontend'], description: '部署目标: all=前后端都部署, backend=仅后端, frontend=仅前端')
        choice(name: 'DEPLOY_ACTION', choices: ['deploy', 'build-only', 'stop', 'restart'], description: '部署动作')
    }

    stages {
        // ==================== 环境检查 ====================
        stage('环境检查') {
            steps {
                script {
                    def server = params.DEPLOY_SERVER ?: env.DEPLOY_SERVER
                    def deployPath = params.DEPLOY_PATH ?: env.DEPLOY_PATH

                    echo "========================================"
                    echo "${env.PROJECT_NAME} 多容器部署流水线"
                    echo "========================================"
                    echo "部署目标: ${server}:${deployPath}"
                    echo "分支: ${params.GIT_BRANCH}"
                    echo "远程仓库: ${env.GIT_REPO}"
                    echo "访问端口: ${env.NGINX_PORT}"

                    withCredentials([sshUserPrivateKey(credentialsId: env.SSH_CREDENTIALS_ID, keyFileVariable: 'SSH_KEY')]) {
                        sh """
                            chmod 600 ${SSH_KEY}
                            ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${server} '
                                echo "--- Docker 环境 ---"
                                docker --version
                                (docker compose version || docker-compose version) 2>&1 | head -1
                                echo "--- GitHub 连通性（服务器需配置 GitHub 部署密钥）---"
                                ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null || true
                                git ls-remote ${env.GIT_REPO} HEAD >/dev/null 2>&1 && echo "GitHub 连通 OK" || echo "警告: 无法连接 GitHub，请检查服务器 ~/.ssh 部署密钥"
                            '
                        """
                        // 探测 compose 命令：优先 docker compose (v2)，兼容 docker-compose (v1)
                        def composeDetect = sh(
                            script: """
                                chmod 600 ${SSH_KEY}
                                ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${server} '
                                    if docker compose version >/dev/null 2>&1; then echo dc2; elif docker-compose version >/dev/null 2>&1; then echo dc1; else echo none; fi
                                '
                            """,
                            returnStdout: true
                        ).trim()
                        env.COMPOSE_CMD = (composeDetect == 'dc1') ? 'docker-compose' : 'docker compose'
                        if (composeDetect == 'none') {
                            error '服务器上未检测到 Docker Compose，请先安装 docker compose v2 或 docker-compose v1'
                        }
                        echo "Compose 命令: ${env.COMPOSE_CMD}"
                    }
                }
            }
        }

        // ==================== 验证基础镜像 ====================
        stage('验证基础镜像') {
            when {
                expression { params.DEPLOY_ACTION in ['deploy', 'build-only'] }
            }
            steps {
                script {
                    def server = params.DEPLOY_SERVER ?: env.DEPLOY_SERVER
                    def targetImages = []
                    if (params.DEPLOY_TARGET in ['all', 'backend']) {
                        targetImages << 'python:3.12-slim'
                    }
                    if (params.DEPLOY_TARGET in ['all', 'frontend']) {
                        targetImages << 'node:22-alpine'
                        targetImages << 'alpine:3.20'
                    }
                    if (!targetImages.contains('nginx:alpine')) {
                        targetImages << 'nginx:alpine'
                    }
                    def imagesStr = targetImages.join(' ')

                    withCredentials([sshUserPrivateKey(credentialsId: env.SSH_CREDENTIALS_ID, keyFileVariable: 'SSH_KEY')]) {
                        sh """
                            chmod 600 ${SSH_KEY}
                            ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${server} '
                                MISSING=""
                                for img in ${imagesStr}; do
                                    if docker image inspect \$img > /dev/null 2>&1; then
                                        echo "[OK] \$img"
                                    else
                                        echo "[缺失] \$img"
                                        MISSING="\$MISSING \$img"
                                    fi
                                done
                                if [ -n "\$MISSING" ]; then
                                    echo ""
                                    echo "错误: 以下基础镜像不存在:\$MISSING"
                                    echo "请先手动拉取: docker pull <镜像名>"
                                    exit 1
                                fi
                                echo ""
                                echo "所有基础镜像验证通过"
                            '
                        """
                    }
                }
            }
        }

        // ==================== 宿主机拉取代码 ====================
        stage('宿主机拉取代码') {
            when {
                expression { params.DEPLOY_ACTION in ['deploy', 'build-only'] }
            }
            steps {
                script {
                    def server = params.DEPLOY_SERVER ?: env.DEPLOY_SERVER
                    def deployPath = params.DEPLOY_PATH ?: env.DEPLOY_PATH

                    // 单仓库 monorepo：整仓 clone 到 $DEPLOY_PATH/src
                    def cloneCmd
                    if (params.FORCE_PULL) {
                        cloneCmd = "rm -rf ${deployPath}/src && git clone --depth 1 -b ${params.GIT_BRANCH} ${env.GIT_REPO} ${deployPath}/src"
                    } else {
                        cloneCmd = "if [ ! -d ${deployPath}/src/.git ]; then git clone --depth 1 -b ${params.GIT_BRANCH} ${env.GIT_REPO} ${deployPath}/src; else git -C ${deployPath}/src fetch origin && git -C ${deployPath}/src reset --hard origin/${params.GIT_BRANCH}; fi"
                    }

                    withCredentials([sshUserPrivateKey(credentialsId: env.SSH_CREDENTIALS_ID, keyFileVariable: 'SSH_KEY')]) {
                        sh """
                            chmod 600 ${SSH_KEY}
                            ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${server} 'mkdir -p ${deployPath}/nginx'

                            ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${server} '
                                export GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no"
                                echo "--- 拉取代码到 ${deployPath}/src ---"
                                ${cloneCmd}

                                echo "--- 同步部署配置文件 ---"
                                cp -f ${deployPath}/src/docker-compose.yml ${deployPath}/docker-compose.yml
                                cp -f ${deployPath}/src/nginx/nginx.conf ${deployPath}/nginx/nginx.conf
                                cp -f ${deployPath}/src/.env.example ${deployPath}/.env.example

                                echo "--- 初始化 .env ---"
                                if [ ! -f ${deployPath}/.env ]; then
                                    cp ${deployPath}/.env.example ${deployPath}/.env
                                    echo "已从 .env.example 创建 .env 文件"
                                fi

                                echo "--- 初始化非敏感配置 (仅缺失时追加，不覆盖服务器自定义) ---"
                                # 注意: 不覆盖 JWT_SECRET / LLM_API_KEY 等敏感变量
                                # 注意: 不覆盖已存在的 SRC_DIR/NGINX_PORT/BACKEND_PORT（保留服务器自定义）
                                if ! grep -q "^SRC_DIR=" ${deployPath}/.env 2>/dev/null; then
                                    echo "SRC_DIR=${env.SRC_DIR}" >> ${deployPath}/.env
                                    echo "已添加 .env: SRC_DIR=${env.SRC_DIR}"
                                fi
                                if ! grep -q "^NGINX_PORT=" ${deployPath}/.env 2>/dev/null; then
                                    echo "NGINX_PORT=${env.NGINX_PORT}" >> ${deployPath}/.env
                                    echo "已添加 .env: NGINX_PORT=${env.NGINX_PORT}"
                                fi
                                if ! grep -q "^BACKEND_PORT=" ${deployPath}/.env 2>/dev/null; then
                                    echo "BACKEND_PORT=${env.BACKEND_PORT}" >> ${deployPath}/.env
                                    echo "已添加 .env: BACKEND_PORT=${env.BACKEND_PORT}"
                                fi
                            '
                        """
                    }
                }
            }
        }

        // ==================== 构建 Docker 镜像 ====================
        stage('构建 Docker 镜像') {
            when {
                expression { params.DEPLOY_ACTION in ['deploy', 'build-only'] }
            }
            steps {
                script {
                    def server = params.DEPLOY_SERVER ?: env.DEPLOY_SERVER
                    def deployPath = params.DEPLOY_PATH ?: env.DEPLOY_PATH
                    def buildArgs = params.FORCE_REBUILD ? '--no-cache' : ''
                    def buildTargets = (params.DEPLOY_TARGET == 'backend') ? 'backend' : (params.DEPLOY_TARGET == 'frontend') ? 'frontend' : ''

                    withCredentials([sshUserPrivateKey(credentialsId: env.SSH_CREDENTIALS_ID, keyFileVariable: 'SSH_KEY')]) {
                        sh """
                            chmod 600 ${SSH_KEY}
                            ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${server} '
                                echo ">>> 构建 Docker 镜像"
                                cd ${deployPath}
                                ${env.COMPOSE_CMD} -p ${env.COMPOSE_PROJECT_NAME} build ${buildArgs} ${buildTargets}
                            '
                        """
                    }
                }
            }
        }

        // ==================== 启动服务 ====================
        stage('启动服务') {
            when {
                expression { params.DEPLOY_ACTION == 'deploy' }
            }
            steps {
                script {
                    def server = params.DEPLOY_SERVER ?: env.DEPLOY_SERVER
                    def deployPath = params.DEPLOY_PATH ?: env.DEPLOY_PATH

                    withCredentials([sshUserPrivateKey(credentialsId: env.SSH_CREDENTIALS_ID, keyFileVariable: 'SSH_KEY')]) {
                        sh """
                            chmod 600 ${SSH_KEY}
                            ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${server} '
                                echo ">>> 启动 Docker 服务"
                                cd ${deployPath}
                                if [ "${params.DEPLOY_TARGET}" = "all" ] || [ "${params.DEPLOY_TARGET}" = "frontend" ]; then
                                    echo "清理旧前端/nginx 容器与前端构建产物 volume..."
                                    ${env.COMPOSE_CMD} stop frontend nginx 2>/dev/null || true
                                    ${env.COMPOSE_CMD} rm -f frontend nginx 2>/dev/null || true
                                    docker volume rm studentstudy-frontend-dist 2>/dev/null && echo "Volume 清理成功" || echo "Volume 清理跳过"
                                    if [ "${params.DEPLOY_TARGET}" = "all" ]; then
                                        ${env.COMPOSE_CMD} up -d --force-recreate
                                    else
                                        ${env.COMPOSE_CMD} up -d --force-recreate frontend nginx
                                    fi
                                else
                                    echo "仅更新后端服务..."
                                    ${env.COMPOSE_CMD} up -d --force-recreate backend nginx
                                fi
                                sleep 10
                                ${env.COMPOSE_CMD} ps
                            '
                        """
                    }
                }
            }
        }

        // ==================== 健康检查 ====================
        stage('健康检查') {
            when {
                expression { params.DEPLOY_ACTION == 'deploy' && !params.SKIP_TESTS }
            }
            steps {
                script {
                    def server = params.DEPLOY_SERVER ?: env.DEPLOY_SERVER

                    withCredentials([sshUserPrivateKey(credentialsId: env.SSH_CREDENTIALS_ID, keyFileVariable: 'SSH_KEY')]) {
                        sh """
                            chmod 600 ${SSH_KEY}
                            ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${server} '
                                echo ">>> 等待 Nginx/前端就绪..."
                                for i in {1..30}; do
                                    if curl -sf http://localhost:${env.NGINX_PORT}/health > /dev/null 2>&1; then
                                        echo "Nginx 健康检查通过"
                                        break
                                    fi
                                    echo "等待 Nginx 就绪... (\$i/30)"
                                    sleep 2
                                    if [ "\$i" -eq 30 ]; then
                                        echo "Nginx 健康检查超时"
                                        exit 1
                                    fi
                                done

                                echo ">>> 检查后端容器健康状态..."
                                for i in {1..30}; do
                                    status=\$(docker inspect --format "{{.State.Health.Status}}" studentstudy-backend 2>/dev/null)
                                    echo "后端状态: \$status (\$i/30)"
                                    if [ "\$status" = "healthy" ]; then
                                        echo "后端健康检查通过"
                                        break
                                    fi
                                    if [ "\$status" = "unhealthy" ]; then
                                        echo "后端健康检查失败"
                                        exit 1
                                    fi
                                    sleep 2
                                    if [ "\$i" -eq 30 ]; then
                                        echo "后端健康检查超时"
                                        exit 1
                                    fi
                                done

                                echo ">>> 验证 API 经 Nginx 可达 (401/200=后端连通) ..."
                                code=\$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${env.NGINX_PORT}/api/v1/auth/session)
                                echo "API 返回码: \$code"
                                if [ "\$code" = "401" ] || [ "\$code" = "200" ]; then
                                    echo "API 连通性验证通过"
                                else
                                    echo "API 连通性验证失败 (HTTP \$code)"
                                    exit 1
                                fi
                            '
                        """
                    }
                }
            }
        }

        // ==================== 停止服务 ====================
        stage('停止服务') {
            when {
                expression { params.DEPLOY_ACTION == 'stop' }
            }
            steps {
                script {
                    def server = params.DEPLOY_SERVER ?: env.DEPLOY_SERVER
                    def deployPath = params.DEPLOY_PATH ?: env.DEPLOY_PATH

                    withCredentials([sshUserPrivateKey(credentialsId: env.SSH_CREDENTIALS_ID, keyFileVariable: 'SSH_KEY')]) {
                        sh """
                            chmod 600 ${SSH_KEY}
                            ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${server} '
                                echo ">>> 停止 Docker 服务"
                                cd ${deployPath}
                                ${env.COMPOSE_CMD} -p ${env.COMPOSE_PROJECT_NAME} down --remove-orphans
                            '
                        """
                    }
                }
            }
        }

        // ==================== 重启服务 ====================
        stage('重启服务') {
            when {
                expression { params.DEPLOY_ACTION == 'restart' }
            }
            steps {
                script {
                    def server = params.DEPLOY_SERVER ?: env.DEPLOY_SERVER
                    def deployPath = params.DEPLOY_PATH ?: env.DEPLOY_PATH
                    def restartTargets = (params.DEPLOY_TARGET == 'backend') ? 'backend nginx' : (params.DEPLOY_TARGET == 'frontend') ? 'frontend nginx' : ''

                    withCredentials([sshUserPrivateKey(credentialsId: env.SSH_CREDENTIALS_ID, keyFileVariable: 'SSH_KEY')]) {
                        sh """
                            chmod 600 ${SSH_KEY}
                            ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${server} '
                                echo ">>> 重启 Docker 服务"
                                cd ${deployPath}
                                ${env.COMPOSE_CMD} -p ${env.COMPOSE_PROJECT_NAME} restart ${restartTargets}
                                sleep 10
                                ${env.COMPOSE_CMD} ps
                            '
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                def server = params.DEPLOY_SERVER ?: env.DEPLOY_SERVER
                def host = server.contains('@') ? server.split('@')[1] : server
                echo "========================================"
                echo "部署成功! 访问地址: http://${host}:${env.NGINX_PORT}"
                echo "API 文档: http://${host}:${env.NGINX_PORT}/docs"
                echo "========================================"
            }
        }
        failure {
            script {
                def server = params.DEPLOY_SERVER ?: env.DEPLOY_SERVER
                def deployPath = params.DEPLOY_PATH ?: env.DEPLOY_PATH
                // 若失败发生在环境检查（compose 探测前），COMPOSE_CMD 可能未定义，使用默认值兜底
                def composeCmd = env.COMPOSE_CMD ?: 'docker compose'
                echo "部署失败! 查看日志..."
                withCredentials([sshUserPrivateKey(credentialsId: env.SSH_CREDENTIALS_ID, keyFileVariable: 'SSH_KEY')]) {
                    sh """
                        chmod 600 ${SSH_KEY}
                        ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${server} '
                            if [ -d "${deployPath}" ]; then
                                cd ${deployPath} && ${composeCmd} -p ${env.COMPOSE_PROJECT_NAME} logs --tail=50
                            else
                                echo "部署目录 ${deployPath} 不存在，跳过日志查看"
                            fi
                        ' || true
                    """
                }
            }
        }
        always {
            deleteDir()
        }
    }
}
