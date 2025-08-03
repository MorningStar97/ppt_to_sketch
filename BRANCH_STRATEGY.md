# 🌿 分支管理策略

本项目采用多分支开发策略，以区分不同的开发和部署环境。

## 📋 分支说明

### 🎯 **main** (主分支)
- **用途**: 稳定版本，经过充分测试
- **特点**: 保持项目的稳定性，可随时用于生产部署
- **保护**: 只接受来自 `develop` 和 `production` 的合并请求
- **部署**: 可用于生产环境部署的基准版本

### 🔧 **develop** (开发分支)
- **用途**: 本地开发和功能测试
- **特点**: 
  - 包含最新的开发功能
  - 使用SQLite数据库
  - 适合本地开发调试
  - 包含开发工具和调试配置
- **启动方式**: `./start.sh`
- **数据库**: SQLite (开发环境)

### 🚀 **production** (生产分支)
- **用途**: 云服务器部署
- **特点**:
  - 包含Docker配置
  - 使用PostgreSQL + Redis
  - 生产环境优化配置
  - 包含部署脚本和文档
- **部署方式**: Docker + docker-compose
- **数据库**: PostgreSQL (生产环境)

## 🔄 工作流程

### 本地开发流程
```bash
# 1. 切换到开发分支
git checkout develop

# 2. 拉取最新代码
git pull origin develop

# 3. 进行开发工作
# ... 编码、测试 ...

# 4. 提交代码
git add .
git commit -m "✨ Add new feature"

# 5. 推送到开发分支
git push origin develop

# 6. 本地启动服务
./start.sh
```

### 生产部署流程
```bash
# 1. 将开发完成的功能合并到main
git checkout main
git merge develop
git push origin main

# 2. 切换到生产分支
git checkout production

# 3. 合并main分支的稳定代码
git merge main

# 4. 推送生产分支
git push origin production

# 5. 在云服务器上部署
# SSH到服务器后执行：
cd /opt/ppt_to_sketch
git checkout production
git pull origin production
docker-compose up --build -d
```

### 热修复流程
```bash
# 1. 从main分支创建hotfix分支
git checkout main
git checkout -b hotfix/urgent-fix

# 2. 修复问题
# ... 修复代码 ...

# 3. 测试验证
./start.sh  # 本地测试

# 4. 合并到main和production
git checkout main
git merge hotfix/urgent-fix
git push origin main

git checkout production
git merge main
git push origin production

# 5. 删除hotfix分支
git branch -d hotfix/urgent-fix
```

## 📁 分支特定文件

### develop 分支特有文件
- `start.sh` - 本地启动脚本
- `kill_port.sh` - 端口管理脚本
- 开发环境配置

### production 分支特有文件
- `Dockerfile` - Docker镜像配置
- `docker-compose.yml` - 容器编排配置
- `quick_deploy.sh` - 一键部署脚本
- `DOCKER_DEPLOYMENT.md` - Docker部署指南
- `gunicorn_docker.conf.py` - 生产环境Gunicorn配置
- `settings_docker.py` - Docker环境Django配置

## 🔧 分支切换指南

### 本地开发 ➡️ 云服务器部署
```bash
# 当前在develop分支，想要部署到云服务器
git checkout production
git merge develop  # 将开发的功能合并到生产分支
git push origin production

# 然后在服务器上：
ssh root@47.100.31.84
cd /opt/ppt_to_sketch
git checkout production
git pull origin production
docker-compose up --build -d
```

### 云服务器 ➡️ 本地开发
```bash
# 在本地切换到开发环境
git checkout develop
git pull origin develop

# 启动本地开发服务
./start.sh
```

## 🚨 注意事项

1. **永远不要直接在main分支开发**
2. **develop分支用于日常开发和功能测试**
3. **production分支专门用于生产环境部署**
4. **合并到main前务必经过充分测试**
5. **生产部署前建议先在本地测试Docker配置**

## 📋 快速命令参考

```bash
# 查看当前分支
git branch

# 查看所有分支（包括远程）
git branch -a

# 切换分支
git checkout <branch-name>

# 创建并切换到新分支
git checkout -b <new-branch>

# 合并分支
git merge <source-branch>

# 删除本地分支
git branch -d <branch-name>

# 删除远程分支
git push origin --delete <branch-name>
```

## 🎯 版本标签管理

对于重要的发布版本，建议使用Git标签：

```bash
# 创建标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签
git push origin v1.0.0

# 列出所有标签
git tag -l

# 基于标签创建分支
git checkout -b release-1.0.0 v1.0.0
```

这样的分支策略可以确保开发和部署环境的清晰分离，同时保持代码的稳定性和可维护性。 