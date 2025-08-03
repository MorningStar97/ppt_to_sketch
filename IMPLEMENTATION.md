# PPT to Sketch 转换服务 - 实现原理

📋 本文档详细介绍了 PPT to Sketch 转换服务的技术架构、核心算法和实现原理。

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面       │    │   Django后端     │    │   转换引擎       │
│                │    │                │    │                │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │文件上传界面  │ │◄──►│ │REST API     │ │◄──►│ │PPT解析器    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │任务状态监控  │ │◄──►│ │异步任务管理  │ │◄──►│ │坐标转换器    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │文件下载     │ │◄──►│ │文件存储管理  │ │◄──►│ │Sketch生成器  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 技术栈选择

| 层级 | 技术 | 选择原因 |
|------|------|----------|
| **Web框架** | Django 4.2 | 成熟稳定、ORM强大、生态丰富 |
| **API框架** | Django REST Framework | 与Django深度集成、文档完善 |
| **前端框架** | Bootstrap 5 + Vanilla JS | 轻量级、响应式、无复杂依赖 |
| **PPT解析** | python-pptx | 官方推荐、API完整、文档详细 |
| **图像处理** | Pillow (PIL) | Python标准图像库、功能全面 |
| **异步任务** | Threading | 简单有效、可扩展为Celery |
| **数据库** | SQLite/PostgreSQL | 开发简单、生产稳定 |

## 🔄 转换流程详解

### 1. 文件上传与验证

```python
# converter/views.py
class ConversionTaskListCreateView(generics.ListCreateAPIView):
    def perform_create(self, serializer):
        # 1. 文件格式验证
        ppt_file = self.request.FILES['ppt_file']
        if not ppt_file.name.lower().endswith(('.ppt', '.pptx')):
            raise ValidationError("不支持的文件格式")
        
        # 2. 文件大小检查
        if ppt_file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            raise ValidationError("文件过大")
        
        # 3. 创建转换任务
        task = serializer.save()
        
        # 4. 启动异步转换
        threading.Thread(
            target=convert_ppt_to_sketch_async,
            args=(task.id,),
            daemon=True
        ).start()
```

### 2. PPT 结构解析

```python
# converter/utils.py
def convert_ppt_to_sketch(self, ppt_file_path, output_dir):
    # 1. 加载PPT文件
    presentation = Presentation(ppt_file_path)
    
    # 2. 提取画板尺寸（直接使用点单位）
    self.artboard_width = presentation.slide_width.pt
    self.artboard_height = presentation.slide_height.pt
    
    # 3. 逐页转换幻灯片
    artboards = []
    for i, slide in enumerate(presentation.slides):
        artboard = self.convert_slide_to_artboard(slide, i)
        if artboard:
            artboards.append(artboard)
```

### 3. 元素分类与处理

```python
def process_shape(self, shape, layer_name):
    """根据形状类型分派到不同的处理方法"""
    shape_type = shape.shape_type
    
    if shape_type == MSO_SHAPE_TYPE.GROUP:
        return self.create_group_layer(shape, layer_name)
    elif shape_type == MSO_SHAPE_TYPE.PICTURE:
        return self.create_image_layer(shape, layer_name)
    elif hasattr(shape, 'text_frame') and shape.text_frame.text.strip():
        return self.create_text_layer(shape, layer_name)
    else:
        return self.create_shape_layer(shape, layer_name)
```

## 🎨 核心转换算法

### 坐标系统转换

PPT 和 Sketch 使用不同的坐标系统和单位，需要精确转换：

```python
# PPT 使用 EMU (English Metric Units)
# 1 inch = 914,400 EMU
# 1 point = 12,700 EMU

# Sketch 使用 Points
# 1 inch = 72 points

# 转换策略：直接使用 python-pptx 的 .pt 属性
left = shape.left.pt   # 自动转换为点
top = shape.top.pt     # 自动转换为点
width = shape.width.pt # 自动转换为点
height = shape.height.pt # 自动转换为点
```

### 颜色转换算法

```python
def extract_color(self, color_obj):
    """将PPT颜色转换为Sketch格式"""
    try:
        if isinstance(color_obj, RGBColor):
            # 直接从RGBColor对象提取
            return {
                "_class": "color",
                "alpha": 1,
                "red": color_obj[0] / 255.0,    # 0-255 → 0-1
                "green": color_obj[1] / 255.0,  # 0-255 → 0-1
                "blue": color_obj[2] / 255.0    # 0-255 → 0-1
            }
        elif hasattr(color_obj, 'rgb'):
            # 从color对象的rgb属性提取
            rgb = color_obj.rgb
            return {
                "_class": "color",
                "alpha": 1,
                "red": rgb[0] / 255.0,
                "green": rgb[1] / 255.0,
                "blue": rgb[2] / 255.0
            }
    except Exception as e:
        # 默认返回黑色
        return {"_class": "color", "alpha": 1, "red": 0, "green": 0, "blue": 0}
```

### 旋转角度转换

```python
# PPT: 顺时针为正
# Sketch: 逆时针为正
# 转换公式：sketch_rotation = -ppt_rotation

rotation = -shape.rotation if hasattr(shape, 'rotation') else 0
```

## 📝 文本处理算法

### 智能字体样式提取

```python
def create_text_layer(self, shape, layer_name):
    # 统计不同字体样式的字符数量
    style_counts = {}
    for paragraph in text_frame.paragraphs:
        for run in paragraph.runs:
            if run.font.size and run.font.name:
                size = run.font.size.pt
                name = run.font.name
                color = self.extract_color(run.font.color.rgb)
                
                # 使用字符数作为权重
                style_key = (size, name, json.dumps(color))
                style_counts[style_key] = style_counts.get(style_key, 0) + len(run.text)
    
    # 选择应用范围最广的样式
    if style_counts:
        dominant_style = max(style_counts, key=style_counts.get)
        font_size, font_name, text_color = dominant_style
```

### 段落对齐方式映射

```python
# PPT对齐方式到Sketch的映射
align_map = {
    PP_ALIGN.LEFT: 0,      # 左对齐
    PP_ALIGN.CENTER: 2,    # 居中
    PP_ALIGN.RIGHT: 1,     # 右对齐
    PP_ALIGN.JUSTIFY: 3    # 两端对齐
}
alignment = align_map.get(paragraph.alignment, 0)
```

## 🖼️ 图像处理算法

### 图像优化策略

```python
def optimize_image(self, image_blob, max_size=4096):
    """优化图片：格式转换 + 尺寸压缩 + 质量控制"""
    image = Image.open(io.BytesIO(image_blob))
    
    # 1. 格式标准化：统一转为RGB
    if image.mode == 'RGBA':
        # 透明背景转为白色背景
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 2. 尺寸优化：大图片缩放
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    # 3. 质量控制：高质量JPEG输出
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=90, optimize=True)
    return output.getvalue()
```

### 图像数据格式

```python
# 使用 Buffer 格式存储图像数据，兼容Sketch
image_ref = f"images/{str(uuid.uuid4())}.png"
self.image_dict[image_ref] = {
    "type": "Buffer", 
    "data": list(image_data)  # 字节数组
}
```

## 🏗️ 组合图层处理

### 递归层级处理

```python
def create_group_layer(self, shape, layer_name):
    """处理PPT组合，保持层级关系"""
    group_left = shape.left.pt
    group_top = shape.top.pt
    
    sub_layers = []
    for i, sub_shape in enumerate(shape.shapes):
        sub_layer = self.process_shape(sub_shape, f"{layer_name}_child_{i}")
        if sub_layer:
            # 关键：子图层坐标转为相对于父组的坐标
            sub_layer['frame']['x'] -= group_left
            sub_layer['frame']['y'] -= group_top
            sub_layers.append(sub_layer)
    
    return {
        "_class": "group",
        "frame": {"x": group_left, "y": group_top, "width": width, "height": height},
        "layers": sub_layers
    }
```

## 📄 Sketch 文件格式

### Sketch 文件结构

```
.sketch 文件 (ZIP压缩包)
├── document.json          # 主文档信息
├── meta.json             # 元数据和版本信息  
├── user.json             # 用户设置（缩放、滚动位置等）
├── pages/                # 页面数据目录
│   └── {page-id}.json    # 每个页面的图层数据
├── workspace/            # 工作空间数据（符号、样式等）
└── images/               # 图片资源
    ├── {image-id}.png
    └── {image-id}.jpg
```

### JSON 结构设计

```python
def _create_sketch_document(self, artboards):
    """创建符合Sketch标准的JSON结构"""
    
    # 1. 页面数据和引用分离
    pages_data = []
    page_refs = []
    
    for artboard in artboards:
        page_id = str(uuid.uuid4())
        
        # 完整的页面数据
        page_data = {
            "_class": "page",
            "do_objectID": page_id,
            "name": artboard.get("name", "Page 1"),
            "layers": [artboard],  # artboard作为页面的子图层
            # ... 其他标准属性
        }
        pages_data.append(page_data)
        
        # 文档中只存储引用
        page_refs.append({
            "_class": "MSJSONFileReference",
            "_ref_class": "MSImmutablePage", 
            "_ref": f"pages/{page_id}"
        })
    
    # 2. 主文档结构
    document = {
        "_class": "document",
        "pages": page_refs,  # 引用而非完整数据
        "currentPageIndex": 0,
        # ... 其他文档属性
    }
    
    return {
        "contents": {
            "document": document,
            "pages": pages_data,    # 完整页面数据
            "meta": meta_data,      # 元数据
            "user": user_data,      # 用户设置
            "workspace": {}         # 工作空间
        },
        "imageDic": self.image_dict  # 图片数据
    }
```

## 🎨 Artboard 裁剪机制

### 标准属性配置

```python
artboard = {
    "_class": "artboard",
    "hasClippingMask": True,        # 启用裁剪
    "clippingMaskMode": 0,          # 默认裁剪模式
    "isVisible": True,              # 确保可见
    "isLocked": False,              # 允许编辑
    # 完整的图层属性
    "booleanOperation": -1,
    "resizingConstraint": 63,
    "style": {
        "_class": "style",
        "endMarkerType": 0,
        "miterLimit": 10,
        "windingRule": 1,
        "borders": [], "fills": [], "shadows": []
    },
    "exportOptions": {
        "_class": "exportOptions",
        "includedLayerIds": [],
        "layerOptions": 0,
        "shouldTrim": False,
        "exportFormats": []
    }
}
```

## 🔄 异步任务管理

### 任务状态流转

```python
def convert_ppt_to_sketch_async(task_id):
    """异步转换任务"""
    task = ConversionTask.objects.get(id=task_id)
    
    try:
        # 1. 更新状态为处理中
        task.status = 'processing'
        task.save()
        
        # 2. 执行转换
        converter = PPTToSketchConverter(verbose=True)
        sketch_file_path = converter.convert_ppt_to_sketch(
            task.ppt_file.path, 
            output_dir
        )
        
        # 3. 保存结果文件
        with open(sketch_file_path, 'rb') as f:
            task.sketch_file.save(filename, File(f), save=True)
        
        # 4. 更新状态为完成
        task.status = 'completed'
        task.error_message = None
        task.save()
        
    except Exception as e:
        # 5. 错误处理
        task.status = 'failed'
        task.error_message = str(e)
        task.save()
        logger.error(f"转换失败: {e}", exc_info=True)
```

## 🎯 关键设计决策

### 1. 坐标转换策略

**问题**：PPT和Sketch使用不同的单位系统
- PPT: EMU (English Metric Units) 
- Sketch: Points

**解决方案**：直接使用 `python-pptx` 的 `.pt` 属性
```python
# 避免手动EMU转换，减少精度损失
left = shape.left.pt    # 而不是 shape.left / 914400
```

**优势**：
- 精度更高
- 代码更简洁
- 减少转换错误

### 2. 图层裁剪机制

**问题**：PPT中的元素可能超出幻灯片边界

**方案对比**：
- ❌ 手动计算裁剪：复杂且容易出错
- ✅ 依赖Sketch的 `hasClippingMask`：标准且可靠

**实现**：
```python
artboard = {
    "hasClippingMask": True,  # 让Sketch处理裁剪
    "clippingMaskMode": 0,    # 标准裁剪模式
    # 补全所有标准属性确保裁剪生效
}
```

### 3. 图像处理策略

**目标**：平衡文件大小和图像质量

**策略**：
- 格式统一：转换为JPEG（减小体积）
- 尺寸限制：最大4096px（适合多数场景）
- 质量控制：90%质量（高质量且体积合理）

### 4. 字体样式提取

**挑战**：PPT文本可能包含多种字体样式

**解决方案**：基于字符数量的加权选择
```python
# 统计每种样式的字符数
style_counts[style_key] = style_counts.get(style_key, 0) + len(run.text)

# 选择覆盖字符最多的样式作为主样式
dominant_style = max(style_counts, key=style_counts.get)
```

**优势**：
- 自动选择主要样式
- 避免样式混乱
- 提高转换质量

## 🚀 性能优化

### 1. 内存管理

```python
# 图像流式处理，避免大量内存占用
def optimize_image(self, image_blob, max_size=4096):
    with io.BytesIO(image_blob) as input_stream:
        image = Image.open(input_stream)
        # ... 处理
        with io.BytesIO() as output_stream:
            image.save(output_stream, format='JPEG')
            return output_stream.getvalue()
```

### 2. 异步处理

```python
# 使用线程池避免阻塞主进程
conversion_thread = threading.Thread(
    target=convert_ppt_to_sketch_async,
    args=(task.id,),
    daemon=True  # 主进程结束时自动清理
)
conversion_thread.start()
```

### 3. 错误恢复

```python
# 多层异常捕获确保系统稳定
try:
    # 转换逻辑
except SpecificException as e:
    # 特定错误处理
except Exception as e:
    # 通用错误处理
    logger.error(f"未预期的错误: {e}", exc_info=True)
finally:
    # 清理资源
    cleanup_temp_files()
```

## 🔍 调试与监控

### 日志系统

```python
# 分级日志记录
def log(self, message, level='info'):
    if self.verbose:
        if level == 'error':
            logger.error(message)
        elif level == 'warning':
            logger.warning(message)
        else:
            logger.info(message)
```

### 详细错误信息

```python
# 记录转换过程中的关键信息
self.log(f"开始转换: {ppt_file_path}")
self.log(f"画板尺寸: {self.artboard_width:.2f} x {self.artboard_height:.2f} 点")
self.log(f"转换 {len(artboards)} 个画板")
self.log(f"Sketch 文件生成完成: {sketch_file_path}")
```

## 🔮 扩展能力

### 1. 支持更多PPT元素

```python
# 可扩展的形状处理器
shape_processors = {
    MSO_SHAPE_TYPE.GROUP: self.create_group_layer,
    MSO_SHAPE_TYPE.PICTURE: self.create_image_layer,
    MSO_SHAPE_TYPE.TEXT_BOX: self.create_text_layer,
    MSO_SHAPE_TYPE.AUTO_SHAPE: self.create_shape_layer,
    # 可继续添加新的形状类型
}

processor = shape_processors.get(shape_type, self.create_shape_layer)
return processor(shape, layer_name)
```

### 2. 转换质量配置

```python
class ConversionConfig:
    """转换配置类"""
    MAX_IMAGE_SIZE = 4096
    IMAGE_QUALITY = 90
    ENABLE_IMAGE_OPTIMIZATION = True
    VERBOSE_LOGGING = False
    
    # 可通过环境变量或配置文件动态调整
```

### 3. 输出格式扩展

```python
# 可扩展到其他设计工具格式
class ConverterFactory:
    converters = {
        'sketch': PPTToSketchConverter,
        'figma': PPTToFigmaConverter,    # 未来支持
        'adobe_xd': PPTToXDConverter,    # 未来支持
    }
    
    @classmethod
    def get_converter(cls, format_type):
        return cls.converters.get(format_type, PPTToSketchConverter)
```

## 📚 总结

本项目实现了从PPT到Sketch的高质量转换，关键技术要点包括：

1. **精确的坐标系统转换**：避免手动计算，使用库提供的标准转换
2. **智能的样式提取算法**：基于字符数量加权选择主要样式
3. **标准的Sketch文件格式**：严格遵循Sketch的JSON结构规范
4. **可靠的图层裁剪机制**：使用Sketch原生的裁剪功能
5. **高效的异步处理**：不阻塞用户操作，提供实时状态反馈
6. **完善的错误处理**：多层异常捕获，确保系统稳定性

通过这些技术方案，项目实现了高保真度的PPT到Sketch转换，为设计师提供了便捷的工具链。 