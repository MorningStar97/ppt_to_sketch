from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404, HttpResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ConversionTask
from .serializers import ConversionTaskSerializer, ConversionTaskCreateSerializer
from .utils import convert_ppt_to_sketch_async
import threading
import logging

logger = logging.getLogger(__name__)

class ConversionTaskListCreateView(generics.ListCreateAPIView):
    """转换任务列表和创建视图"""
    queryset = ConversionTask.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ConversionTaskCreateSerializer
        return ConversionTaskSerializer
    
    def perform_create(self, serializer):
        """创建任务后启动异步转换"""
        task = serializer.save()
        
        # 启动异步转换任务
        def start_conversion():
            convert_ppt_to_sketch_async(task.id)
        
        conversion_thread = threading.Thread(target=start_conversion)
        conversion_thread.daemon = True
        conversion_thread.start()
        
        return task

class ConversionTaskDetailView(generics.RetrieveAPIView):
    """转换任务详情视图"""
    queryset = ConversionTask.objects.all()
    serializer_class = ConversionTaskSerializer
    lookup_field = 'id'

@api_view(['GET'])
def download_sketch_file(request, task_id):
    """下载转换后的 Sketch 文件"""
    try:
        task = get_object_or_404(ConversionTask, id=task_id)
        
        if not task.sketch_file:
            return Response({'error': 'Sketch 文件不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        if task.status != 'completed':
            return Response({'error': '转换尚未完成'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 构建文件下载响应
        response = HttpResponse(
            task.sketch_file.read(),
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{task.sketch_filename}"'
        return response
        
    except Exception as e:
        logger.error(f"下载文件时发生错误: {str(e)}")
        return Response({'error': '下载失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def delete_conversion_task(request, task_id):
    """删除转换任务"""
    try:
        task = get_object_or_404(ConversionTask, id=task_id)
        task.delete()
        return Response({'message': '任务删除成功'}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"删除任务时发生错误: {str(e)}")
        return Response({'error': '删除失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 前端视图
def index_view(request):
    """主页视图"""
    return render(request, 'converter/index.html')

def task_list_view(request):
    """任务列表页面"""
    tasks = ConversionTask.objects.all()
    return render(request, 'converter/task_list.html', {'tasks': tasks})

def task_detail_view(request, task_id):
    """任务详情页面"""
    task = get_object_or_404(ConversionTask, id=task_id)
    return render(request, 'converter/task_detail.html', {'task': task})
