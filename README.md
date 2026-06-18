# 视频字幕自动生成与对齐系统

## 功能
- 从视频中自动提取音频
- 使用Whisper进行语音识别生成字幕（SRT/ASS/VTT）
- 可选OCR硬字幕识别（基于PaddleOCR）
- 图形界面支持字幕编辑与导出
- 支持批量处理（扩展功能）

## 安装
1. 创建Python 3.10环境
2. 安装依赖：`pip install -r requirements.txt`
3. 安装FFmpeg并添加到PATH
4. 运行：`python main.py`

## 使用说明
1. 点击“打开视频”选择MP4等文件
2. 点击“自动生成字幕”等待处理
3. 在表格中编辑字幕文本或时间
4. 点击“导出字幕”保存为SRT等格式

## 目录结构
- src/ : 源代码
- config.yaml : 配置文件（可调整模型大小、设备等）
- temp/ : 临时音频文件
- output/ : 输出字幕

## 注意事项
- 首次运行会自动下载Whisper模型（约1-3GB）
- GPU需要CUDA支持，CPU模式较慢
- OCR需要PaddlePaddle环境，请参考PaddleOCR官方文档