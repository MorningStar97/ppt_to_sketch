# 🚀 PPT to Sketch - 生产环境部署

这是 **production** 分支，专门用于云服务器部署。

## 📋 生产环境特点

- **容器化**: Docker + docker-compose
- **数据库**: PostgreSQL (生产级数据库)
- **缓存**: Redis (高性能缓存)
- **Web服务器**: Nginx (反向代理)
- **应用服务器**: Gunicorn (WSGI服务器)
- **部署方式**: 一键部署脚本

## 🚀 快速部署

### 方式一：一键部署（推荐）

在您的ECS服务器上运行：

```bash
# SSH连接到服务器
ssh root@47.100.31.84

# 一键部署
curl -sSL https://raw.githubusercontent.com/MorningStar97/ppt_to_sketch/production/quick_deploy.sh | bash
```

### 方式二：手动部署

```bash
# 1. 连接ECS服务器
ssh root@47.100.31.84

# 2. 克隆production分支
cd /opt
git clone -b production https://github.com/MorningStar97/ppt_to_sketch.git
cd ppt_to_sketch

# 3. 按照 DOCKER_DEPLOYMENT.md 步骤部署
```

## 🐳 容器架构

```
┌─────────────────────────────────────┐
│              Nginx                  │
│         (Port 80/443)              │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│            Django                   │
│         (Port 8000)                │
└─────────────┬───────────────────────┘
              │
    ┌─────────▼─────────┐    ┌────────▼────────┐
    │   PostgreSQL      │    │     Redis       │
    │   (Port 5432)     │    │   (Port 6379)   │
    └───────────────────┘    └─────────────────┘
```

## 📊 服务管理

### 查看服务状态
```bash
cd /opt/ppt_to_sketch
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs web
docker-compose logs db
docker-compose logs redis
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart web
```

### 更新代码
```bash
cd /opt/ppt_to_sketch
git pull origin production
docker-compose up --build -d
```

## 🔧 配置文件说明

### Docker相关
- `Dockerfile` - Django应用容器配置
- `docker-compose.yml` - 多容器编排配置
- `gunicorn_docker.conf.py` - Gunicorn服务器配置

### 环境配置
- `.env` - 环境变量（密钥、密码等）
- `settings_docker.py` - Django生产环境配置

### 部署工具
- `quick_deploy.sh` - 一键部署脚本
- `DOCKER_DEPLOYMENT.md` - 详细部署指南

## 🛡️ 安全配置

### 环境变量
生产环境的敏感信息存储在 `.env` 文件中：
```bash
SECRET_KEY=生产环境密钥
DB_PASSWORD=数据库密码
```

### 访问控制
- 只开放必要端口（80, 443, 22）
- 使用强密码
- 定期更新系统和依赖

## 📈 性能优化

### 资源配置
- **CPU**: 2核（适合中小型项目）
- **内存**: 4GB（PostgreSQL + Redis + Django）
- **存储**: 50GB（系统 + 数据 + 日志）

### 数据库优化
- PostgreSQL 连接池
- Redis 缓存加速
- 静态文件CDN服务

### 监控指标
```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
df -h

# 查看内存使用
free -h
```

## 🔄 备份策略

### 数据库备份
```bash
# 手动备份
docker-compose exec db pg_dump -U ppt_user ppt_to_sketch > backup_$(date +%Y%m%d).sql

# 定时备份（添加到crontab）
0 2 * * * cd /opt/ppt_to_sketch && docker-compose exec db pg_dump -U ppt_user ppt_to_sketch > /backup/ppt_$(date +\%Y\%m\%d).sql
```

### 文件备份
```bash
# 备份用户上传的文件
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
```

## 🚨 故障排除

### 常见问题

1. **容器启动失败**
```bash
docker-compose logs web
```

2. **数据库连接错误**
```bash
docker-compose exec web python manage.py dbshell --settings=ppt_to_sketch_service.settings_docker
```

3. **静态文件不显示**
```bash
docker-compose exec web python manage.py collectstatic --noinput --settings=ppt_to_sketch_service.settings_docker
```

4. **端口冲突**
```bash
netstat -tulpn | grep :80
```

### 日志分析
```bash
# Django应用日志
docker-compose logs web

# Nginx访问日志
docker-compose exec nginx cat /var/log/nginx/access.log

# PostgreSQL日志
docker-compose logs db
```

## 🔗 相关分支

- **main**: 稳定基线版本
- **develop**: 本地开发版本（SQLite + ./start.sh）

查看完整分支策略：[BRANCH_STRATEGY.md](./BRANCH_STRATEGY.md)

## 📞 生产环境支持

如果在生产部署中遇到问题：

1. 🐛 提交 Issue：[GitHub Issues](https://github.com/MorningStar97/ppt_to_sketch/issues)
2. 📧 标注 `production` 标签
3. 🔍 提供详细的错误日志和环境信息

## 🎯 部署检查清单

- [ ] ECS服务器配置正确（2核4G）
- [ ] Docker和docker-compose已安装
- [ ] SSH访问正常
- [ ] 防火墙配置正确（开放80/443端口）
- [ ] 域名解析配置（如有）
- [ ] SSL证书配置（如需要）
- [ ] 备份策略设置
- [ ] 监控告警配置

Ready for production! 🎉 