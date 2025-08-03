"""
JSON 到 Sketch 文件转换模块
基于 JavaScript 代码的 Python 实现
"""

import json
import zipfile
import os
from pathlib import Path
import base64
import logging

logger = logging.getLogger(__name__)

class JSONToSketchConverter:
    """JSON 到 Sketch 文件转换器"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
    
    def log(self, message, level='info'):
        """记录日志"""
        if self.verbose:
            if level == 'error':
                logger.error(message)
            elif level == 'warning':
                logger.warning(message)
            else:
                logger.info(message)
    
    def to_file(self, sketch_data, output_path):
        """
        将 JSON 数据转换为 Sketch 文件
        
        Args:
            sketch_data: 包含 Sketch 数据的字典，结构如下:
                {
                    "contents": {
                        "document": {...},
                        "pages": [...],
                        "meta": {...},
                        "user": {...},
                        "workspace": {...}
                    },
                    "imageDic": {...}
                }
            output_path: 输出文件路径
        """
        
        try:
            self.log(f"开始生成 Sketch 文件: {output_path}")
            
            # 确保输出目录存在
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as sketch_zip:
                
                # 1. 首先写入页面文件并生成引用
                page_refs = []
                pages_data = sketch_data.get("contents", {}).get("pages", [])
                
                if isinstance(pages_data, list):
                    # 如果 pages 是数组，直接使用
                    for page in pages_data:
                        page_json = json.dumps(page, indent=2)
                        page_id = page.get("do_objectID")
                        
                        sketch_zip.writestr(
                            f'pages/{page_id}.json',
                            page_json.encode('utf-8')
                        )
                        
                        # 生成页面引用
                        page_ref = {
                            "_class": "MSJSONFileReference",
                            "_ref_class": "MSImmutablePage",
                            "_ref": f"pages/{page_id}"
                        }
                        page_refs.append(page_ref)
                        
                        self.log(f"写入页面文件: pages/{page_id}.json ({len(page_json)} 字符)")
                
                # 2. 写入工作空间数据
                workspace_data = sketch_data.get("contents", {}).get("workspace", {})
                
                for key, workspace_item in workspace_data.items():
                    workspace_json = json.dumps(workspace_item, indent=2)
                    sketch_zip.writestr(
                        f'workspace/{key}.json',
                        workspace_json.encode('utf-8')
                    )
                    self.log(f"写入工作空间文件: workspace/{key}.json")
                
                # 3. 准备主要文件数据
                document_data = sketch_data.get("contents", {}).get("document", {})
                # 更新文档中的页面引用
                if page_refs:
                    document_data = document_data.copy()
                    document_data["pages"] = page_refs
                
                main_files = {
                    "document.json": document_data,
                    "user.json": sketch_data.get("contents", {}).get("user", {}),
                    "meta.json": sketch_data.get("contents", {}).get("meta", {})
                }
                
                # 4. 写入主要 JSON 文件
                for filename, data in main_files.items():
                    file_json = json.dumps(data, indent=2)
                    sketch_zip.writestr(filename, file_json.encode('utf-8'))
                    self.log(f"写入主文件: {filename} ({len(file_json)} 字符)")
                
                # 5. 写入图片文件
                image_dic = sketch_data.get("imageDic", {})
                
                for image_key, image_data in image_dic.items():
                    try:
                        # 处理不同格式的图片数据
                        if isinstance(image_data, str):
                            # Base64 编码的字符串
                            if image_data.startswith('data:'):
                                # 处理 data URL
                                header, base64_data = image_data.split(',', 1)
                                image_bytes = base64.b64decode(base64_data)
                            else:
                                # 直接的 Base64 字符串
                                image_bytes = base64.b64decode(image_data)
                        elif isinstance(image_data, bytes):
                            # 直接的字节数据
                            image_bytes = image_data
                        elif isinstance(image_data, dict) and image_data.get("type") == "Buffer":
                            # 新的Buffer格式：{"type": "Buffer", "data": [byte1, byte2, ...]}
                            data_list = image_data.get("data", [])
                            if isinstance(data_list, list):
                                image_bytes = bytes(data_list)
                                self.log(f"处理Buffer格式图片: {image_key} ({len(image_bytes)} bytes)")
                            else:
                                self.log(f"Buffer格式数据无效: {image_key}", 'warning')
                                continue
                        else:
                            self.log(f"不支持的图片数据格式: {type(image_data)}", 'warning')
                            continue
                        
                        sketch_zip.writestr(image_key, image_bytes)
                        self.log(f"添加图片: {image_key} ({len(image_bytes)} bytes)")
                        
                    except Exception as img_e:
                        self.log(f"添加图片失败 {image_key}: {str(img_e)}", 'error')
                        continue
            
            self.log(f"Sketch 文件生成完成: {output_path}")
            return True
            
        except Exception as e:
            self.log(f"生成 Sketch 文件失败: {str(e)}", 'error')
            raise e
    
    def convert_from_json_file(self, json_path, output_path):
        """
        从 JSON 文件转换为 Sketch 文件
        
        Args:
            json_path: 输入的 JSON 文件路径
            output_path: 输出的 Sketch 文件路径
        """
        
        try:
            self.log(f"读取 JSON 文件: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 转换为 Sketch 文件
            return self.to_file(json_data, output_path)
            
        except Exception as e:
            self.log(f"从 JSON 文件转换失败: {str(e)}", 'error')
            raise e
    
    def convert_from_data(self, sketch_data, output_path):
        """
        从内存中的数据转换为 Sketch 文件
        
        Args:
            sketch_data: Sketch 数据字典
            output_path: 输出的 Sketch 文件路径
        """
        
        return self.to_file(sketch_data, output_path)

def json_to_sketch(input_path, output_path, verbose=False):
    """
    便捷函数：JSON 文件转 Sketch 文件
    
    Args:
        input_path: 输入 JSON 文件路径
        output_path: 输出 Sketch 文件路径
        verbose: 是否显示详细日志
    
    Returns:
        bool: 转换是否成功
    """
    
    converter = JSONToSketchConverter(verbose=verbose)
    
    try:
        return converter.convert_from_json_file(input_path, output_path)
    except Exception as e:
        if verbose:
            print(f"转换失败: {str(e)}")
        return False

def data_to_sketch(sketch_data, output_path, verbose=False):
    """
    便捷函数：内存数据转 Sketch 文件
    
    Args:
        sketch_data: Sketch 数据字典
        output_path: 输出 Sketch 文件路径
        verbose: 是否显示详细日志
    
    Returns:
        bool: 转换是否成功
    """
    
    converter = JSONToSketchConverter(verbose=verbose)
    
    try:
        return converter.convert_from_data(sketch_data, output_path)
    except Exception as e:
        if verbose:
            print(f"转换失败: {str(e)}")
        return False

# 示例使用
if __name__ == "__main__":
    # 测试用例
    test_data = {
        "contents": {
            "document": {
                "_class": "document",
                "do_objectID": "test-doc-id",
                "pages": []
            },
            "pages": [
                {
                    "_class": "page",
                    "do_objectID": "test-page-id",
                    "name": "Test Page",
                    "layers": []
                }
            ],
            "meta": {
                "_class": "meta",
                "app": "com.bohemiancoding.sketch3",
                "version": 134
            },
            "user": {},
            "workspace": {}
        },
        "imageDic": {}
    }
    
    success = data_to_sketch(test_data, "test_output.sketch", verbose=True)
    print(f"测试结果: {'成功' if success else '失败'}") 