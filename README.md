# PPT to Sketch 转换服务

🎨 一个基于Django的PPT到Sketch转换服务，支持高保真度转换，包含Web界面和RESTful API

## 🌿 分支选择指南

**请根据您的使用场景选择正确的分支：**

### 🔧 本地开发 ➡️ `develop` 分支
```bash
git clone -b develop https://github.com/MorningStar97/ppt_to_sketch.git
cd ppt_to_sketch
./start.sh  # 一键启动本地开发环境
```
- ✅ SQLite数据库，轻量级
- ✅ 一键启动脚本
- ✅ 调试模式开启
- ✅ 端口冲突自动处理

### 🚀 云服务器部署 ➡️ `production` 分支
```bash
# 在ECS服务器上一键部署
curl -sSL https://raw.githubusercontent.com/MorningStar97/ppt_to_sketch/production/quick_deploy.sh | bash
```
- ✅ Docker容器化部署
- ✅ PostgreSQL + Redis
- ✅ Nginx反向代理
- ✅ 生产环境优化

### 📚 查看文档 ➡️ `main` 分支（当前）
- 📋 项目概述和功能介绍
- 🌿 完整分支管理策略
- 📖 使用指南和API文档

> 💡 **重要提示**: `main` 分支是稳定基线，不包含特定环境的配置文件。请根据您的需求选择 `develop` 或 `production` 分支。

---

## ✨ 功能特性

- 🔄 **完整转换**：支持文本、图片、形状、组合等 PPT 元素
- 🎯 **高保真度**：精确保持字体、颜色、位置、旋转角度等样式
- 🌐 **Web 界面**：简洁易用的文件上传和管理界面
- 📱 **响应式设计**：支持桌面和移动端访问
- ⚡ **异步处理**：后台转换，不阻塞用户操作
- 🔗 **RESTful API**：完整的 API 接口，支持集成到其他系统
- 📦 **拖拽上传**：支持文件拖拽上传
- 📄 **任务管理**：转换历史记录和状态跟踪

## 🚀 快速开始

### 环境要求

- Python 3.8+
- macOS/Linux（推荐）
- 内存：建议 2GB 以上

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/MorningStar97/ppt_to_sketch.git
cd ppt-to-sketch-service
```

2. **自动安装与启动**
```bash
chmod +x start.sh
./start.sh
```

脚本会自动完成：
- 检查 Python 环境
- 安装依赖包
- 数据库迁移
- 创建管理员账户
- 启动开发服务器

3. **访问服务**

启动成功后，在浏览器中访问：
- 🌐 **Web 界面**：http://127.0.0.1:8000
- 🛠️ **管理后台**：http://127.0.0.1:8000/admin
- 📊 **API 文档**：http://127.0.0.1:8000/api/tasks/

### 手动安装（可选）

如果自动安装遇到问题，可以手动执行：

```bash
# 1. 安装依赖
python3 -m pip install -r requirements.txt

# 2. 数据库迁移
python3 manage.py makemigrations
python3 manage.py migrate

# 3. 创建超级用户
python3 manage.py createsuperuser

# 4. 启动服务
python3 manage.py runserver 127.0.0.1:8000
```

## 🎯 使用方法

### Web 界面使用

1. **上传文件**
   - 打开 http://127.0.0.1:8000
   - 点击选择文件或直接拖拽 PPT 文件到上传区域
   - 支持 .ppt 和 .pptx 格式

2. **监控转换**
   - 上传后自动跳转到任务详情页
   - 实时显示转换状态：等待中 → 处理中 → 已完成/失败
   - 页面会自动刷新显示最新状态

3. **下载结果**
   - 转换完成后点击"下载 Sketch 文件"
   - 可在任务列表页面查看所有转换历史

### API 接口使用

#### 1. 上传 PPT 文件
```bash
curl -X POST http://127.0.0.1:8000/api/tasks/ \
  -F "ppt_file=@your_file.pptx"
```

响应：
```json
{
  "id": "uuid-string",
  "status": "pending",
  "created_at": "2025-01-03T10:00:00Z",
  "ppt_filename": "your_file.pptx"
}
```

#### 2. 查询转换状态
```bash
curl http://127.0.0.1:8000/api/tasks/{task_id}/
```

#### 3. 下载转换结果
```bash
curl -O http://127.0.0.1:8000/api/tasks/{task_id}/download/
```

#### 4. 删除转换任务
```bash
curl -X DELETE http://127.0.0.1:8000/api/tasks/{task_id}/delete/
```

完整 API 文档请参考 [API.md](API.md)

## 📚 支持的元素

| PPT 元素 | 转换支持 | 保持属性 |
|---------|---------|---------|
| 📝 文本框 | ✅ | 字体、大小、颜色、对齐方式 |
| 🖼️ 图片 | ✅ | 位置、尺寸、旋转角度 |
| 🔷 形状 | ✅ | 位置、尺寸、填充色、旋转角度 |
| 📁 组合 | ✅ | 层级关系、相对位置 |
| 🎨 背景 | ✅ | 纯色背景 |
| 🔄 旋转 | ✅ | 精确角度转换 |

## ⚙️ 配置选项

### 文件上传限制
在 `settings.py` 中可以调整：
```python
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
```

### 图片优化设置
转换器会自动优化图片：
- 转换为 JPEG 格式（减小文件大小）
- 限制最大尺寸为 4096px
- 质量设置为 90%

## 🛠️ 开发

### 项目结构
```
ppt-to-sketch-service/
├── converter/              # 核心转换应用
│   ├── models.py          # 数据模型
│   ├── views.py           # 视图和API
│   ├── utils.py           # 转换逻辑
│   └── json_to_sketch.py  # Sketch文件生成
├── templates/             # HTML模板
├── static/               # 静态资源
├── media/                # 文件存储
├── start.sh              # 启动脚本
└── requirements.txt      # 依赖列表
```

### 运行测试
```bash
python3 manage.py test
```

### 代码风格
项目遵循 PEP 8 代码规范，建议使用：
```bash
pip install black flake8
black .
flake8 .
```

## 🔧 故障排除

### 常见问题

**Q: 启动时提示端口被占用**
```bash
# 查看占用进程
lsof -i:8000
# 或使用项目提供的脚本
./kill_port.sh 8000
```

**Q: 转换失败，提示"无法识别的文件格式"**
- 确保文件是有效的 .ppt 或 .pptx 格式
- 尝试用 PowerPoint 重新保存文件

**Q: 转换后的 Sketch 文件打不开**
- 确保使用推荐版本的 Sketch（推荐 98.2 或 98.3 版本）
- 注意：Sketch 2025等更新版本可能存在artboard属性兼容性问题，导致部分元素超出原PPT尺寸
- 检查转换日志中是否有错误信息

**Q: 图片质量下降**
- 项目会自动优化图片以减小文件大小
- 可在 `utils.py` 中调整 `optimize_image` 方法的参数

### 日志查看
```bash
# 实时查看转换日志
tail -f logs/conversion.log

# Django 调试信息
python3 manage.py runserver --verbosity=2
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [python-pptx](https://python-pptx.readthedocs.io/) - PPT 文件解析
- [Django](https://www.djangoproject.com/) - Web 框架
- [Bootstrap](https://getbootstrap.com/) - 前端样式
- [Sketch](https://www.sketch.com/) - 目标文件格式

## 📞 支持

如果您遇到问题或有建议，请：
- 🐛 提交 Issue：[GitHub Issues](https://github.com/MorningStar97/ppt_to_sketch/issues)
- 💬 讨论：[GitHub Discussions](https://github.com/MorningStar97/ppt_to_sketch/discussions)

---

⭐ 如果这个项目对您有帮助，请给个 Star 支持一下！ 