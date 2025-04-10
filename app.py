from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify
from logger import logger  # 导入自定义日志模块
import os
import uuid
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from pdf_analyzer import PDFAnalyzer
from deepseek_api import DeepSeekAPI  # 引入DeepSeek API工具
import web_search  # 引入网络搜索工具
from dotenv import load_dotenv  # 引入dotenv库加载环境变量

# 加载.env文件中的环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'deeppaper_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['SETTINGS_FILE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 默认设置
DEFAULT_SETTINGS = {
    'model': 'deepseek-chat',
    'language': 'zh',
    'detail_level': 'standard',
    'custom_prompt': '',
    'enable_web_search': False,
    'test_mode': False,
    'api_key': ''
}

# 默认提示词模板
DEFAULT_PROMPTS = {
    'zh': "请对以下论文内容进行详细分析和概括，包括研究目的、方法、主要发现和结论。请用简洁的语言总结论文的核心贡献，并指出其学术价值和潜在应用。",
    'en': "Please analyze and summarize the following paper content in detail, including research objectives, methods, main findings, and conclusions. Use concise language to summarize the core contributions of the paper and point out its academic value and potential applications."
}

# 加载设置
def load_settings():
    if os.path.exists(app.config['SETTINGS_FILE']):
        try:
            with open(app.config['SETTINGS_FILE'], 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # 确保所有默认设置项都存在
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except:
            return DEFAULT_SETTINGS.copy()
    else:
        return DEFAULT_SETTINGS.copy()

# 保存设置
def save_settings_to_file(settings):
    with open(app.config['SETTINGS_FILE'], 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('ui/index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('没有选择文件')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('没有选择文件')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        # 使用UUID生成唯一文件名，避免文件名冲突
        original_filename = secure_filename(file.filename)
        filename = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        return redirect(url_for('view_pdf', filename=filename))

    flash('只允许上传PDF文件')
    return redirect(url_for('index'))

@app.route('/view/<filename>')
def view_pdf(filename):
    return render_template('viewer/viewer.html', filename=filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/settings')
def settings():
    current_settings = load_settings()
    return render_template('ui/settings.html', current_settings=current_settings)

@app.route('/save_settings', methods=['POST'])
def save_settings():
    # 获取API密钥
    api_key = request.form.get('api_key', '')

    # 如果提供了API密钥，则更新环境变量
    if api_key:
        # 将API密钥写入.env文件
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(f"# DeepSeek API密钥\nDEEPSEEK_API_KEY={api_key}")
        # 更新当前环境变量
        os.environ['DEEPSEEK_API_KEY'] = api_key

    # 保存其他设置到settings.json，但不包括API密钥
    settings = {
        'model': request.form.get('model', DEFAULT_SETTINGS['model']),
        'language': request.form.get('language', DEFAULT_SETTINGS['language']),
        'detail_level': request.form.get('detail_level', DEFAULT_SETTINGS['detail_level']),
        'custom_prompt': request.form.get('custom_prompt', ''),
        'enable_web_search': 'enable_web_search' in request.form,
        'test_mode': 'test_mode' in request.form,
        'api_key': ''  # 不保存API密钥到settings.json
    }
    save_settings_to_file(settings)
    flash('设置已保存')
    return redirect(url_for('settings'))

@app.route('/deep_paper/<filename>', methods=['POST'])
def deep_paper(filename):
    # 获取文件路径
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        flash('文件不存在')
        return redirect(url_for('index'))

    # 显示分析进度页面
    return render_template('analysis/analysis_progress.html', filename=filename)

@app.route('/api/analysis_logs')
def api_analysis_logs():
    """获取分析过程的实时日志"""
    # 获取最新的日志记录
    logs = logger.get_logs_since_last_update()
    return jsonify({
        'logs': logs,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/analyze/<filename>')
def api_analyze(filename):
    # 清除之前的分析日志
    logger.clear_analysis_logs()

    # 获取文件路径
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {filename}")
        return jsonify({'error': '文件不存在'}), 404

    # 获取原始文件名
    original_filename = filename.split('_', 1)[1] if '_' in filename else filename
    logger.info(f"开始分析文件: {original_filename}")

    # 加载设置
    settings = load_settings()
    logger.info(f"使用模型: {settings['model']}, 语言: {settings['language']}, 网络搜索: {'启用' if settings.get('enable_web_search', False) else '禁用'}")

    try:
        # 创建PDF分析器实例
        logger.info("初始化PDF分析器")
        analyzer = PDFAnalyzer(file_path)

        # 步骤1：提取PDF内容
        logger.info("步骤1: 开始提取PDF文本内容")
        extracted_content = analyzer.extract_text()
        logger.info(f"提取完成，共获取 {len(extracted_content)} 字符的文本")

        # 步骤2：提取图像和内容分块
        logger.info("步骤2: 开始分析内容结构和提取图像")
        content_blocks = analyzer.analyze_content_blocks()
        logger.info(f"内容分析完成，共识别 {len(content_blocks)} 个内容块")

        # 步骤3：创建DeepSeek API实例
        logger.info(f"步骤3: 初始化DeepSeek API，使用模型 {settings['model']}")
        deepseek = DeepSeekAPI(model=settings['model'], api_key=settings.get('api_key', ''))

        # 步骤4：准备解读提示词
        logger.info("步骤4: 准备解读提示词")
        prompt = settings.get('custom_prompt', '')
        if not prompt:
            # 使用默认提示词
            prompt = DEFAULT_PROMPTS.get(settings['language'], DEFAULT_PROMPTS['zh'])
            logger.info("使用默认提示词模板")
        else:
            logger.info("使用自定义提示词")

        # 步骤5：处理网络搜索（如果启用）
        web_search_results = []
        if settings.get('enable_web_search', False):
            logger.info("步骤5: 开始网络搜索相关参考资料")
            # 提取关键信息以用于搜索
            metadata = analyzer.extract_metadata()
            title = metadata.get('title', '')
            # 使用论文标题进行网络搜索
            if title:
                logger.info(f"使用论文标题进行搜索: {title}")
                web_search_results = web_search.search_for_references(title)
                logger.info(f"搜索完成，获取 {len(web_search_results)} 条参考资料")
            else:
                logger.warning("未能提取到论文标题，跳过网络搜索")

        # 步骤6：生成分析结果
        logger.info("步骤6: 开始生成分析结果")
        analysis_sections = []

        # 检查是否启用测试模式
        test_mode = settings.get('test_mode', False)
        if test_mode:
            logger.info("测试模式已启用，只处理第一个内容分块")
            # 在测试模式下，只保留第一个非图像内容块
            filtered_blocks = []
            for block in content_blocks:
                if block.get('type') != 'image':
                    filtered_blocks.append(block)
                    break
            # 如果没有找到文本块，则保留第一个图像块（如果有）
            if not filtered_blocks and content_blocks:
                filtered_blocks = [content_blocks[0]]
            content_blocks = filtered_blocks
            logger.info(f"测试模式：将只处理 {len(content_blocks)} 个内容块")

        # 处理每个内容块
        for i, block in enumerate(content_blocks):
            logger.info(f"处理内容块 {i+1}/{len(content_blocks)}")
            # 跳过图像块直接添加，不需要解读
            if block.get('type') == 'image':
                logger.info(f"识别到图像块，标题: {block.get('title', f'图像 {i+1}')}")
                analysis_sections.append({
                    'type': 'image',
                    'title': block.get('title', f'图像 {i+1}'),
                    'content': block.get('content', '')
                })
                continue

            # 处理文本块
            block_content = block.get('content', '')
            if not block_content:
                logger.info(f"跳过空内容块 {i+1}")
                continue

            # 构建完整提示词
            logger.info(f"处理文本块 {i+1}，标题: {block.get('title', f'段落 {i+1}')}")
            full_prompt = f"{prompt}\n\n文本内容：{block_content}"

            # 如果有网络搜索结果，添加到提示词中
            if web_search_results and i == 0:  # 只在第一个块添加参考资料
                logger.info("添加网络搜索参考资料到提示词")
                full_prompt += "\n\n参考资料：\n" + "\n".join(web_search_results)

            # 调用DeepSeek API进行解读
            logger.info(f"开始使用DeepSeek API解读文本块 {i+1}")
            analysis = deepseek.analyze_text(full_prompt, language=settings['language'])
            logger.info(f"文本块 {i+1} 解读完成，生成 {len(analysis)} 字符的分析结果")

            # 添加到分析结果中
            analysis_sections.append({
                'type': 'text',
                'title': block.get('title', f'段落 {i+1}'),
                'original_content': block_content,
                'analysis': analysis
            })

        # 在分析完成后关闭文档
        analyzer.close()

        # 将分析结果存储在session中，以便在分析页面显示
        session['analysis_result'] = {
            'filename': filename,
            'original_filename': original_filename,
            'settings': settings,
            'content_blocks': content_blocks,
            'analysis_sections': analysis_sections,
            'web_search_results': web_search_results,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return jsonify({'success': True, 'redirect': url_for('analysis_with_preview', filename=filename)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analysis/<filename>')
def analysis_result(filename):
    # 从session中获取分析结果
    analysis_result = session.get('analysis_result', {})

    # 如果没有分析结果或者文件名不匹配，重定向到PDF查看页面
    if not analysis_result or analysis_result.get('filename') != filename:
        flash('没有找到分析结果，请重新分析')
        return redirect(url_for('view_pdf', filename=filename))

    return render_template('analysis/analysis.html',
                           filename=filename,
                           original_filename=analysis_result.get('original_filename'),
                           settings=analysis_result.get('settings'),
                           content_blocks=analysis_result.get('content_blocks'),
                           analysis_sections=analysis_result.get('analysis_sections'),
                           web_search_results=analysis_result.get('web_search_results'))

@app.route('/analysis_with_preview/<filename>')
def analysis_with_preview(filename):
    # 从session中获取分析结果
    analysis_result = session.get('analysis_result', {})

    # 如果没有分析结果或者文件名不匹配，重定向到PDF查看页面
    if not analysis_result or analysis_result.get('filename') != filename:
        flash('没有找到分析结果，请重新分析')
        return redirect(url_for('view_pdf', filename=filename))

    return render_template('analysis/analysis_with_preview.html',
                           filename=filename,
                           original_filename=analysis_result.get('original_filename'),
                           settings=analysis_result.get('settings'),
                           content_blocks=analysis_result.get('content_blocks'),
                           analysis_sections=analysis_result.get('analysis_sections'),
                           web_search_results=analysis_result.get('web_search_results'))

@app.route('/process_analysis/<filename>')
def process_analysis(filename):
    # 获取文件路径
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        flash('文件不存在')
        return redirect(url_for('index'))

    # 获取原始文件名
    original_filename = filename.split('_', 1)[1] if '_' in filename else filename

    # 加载设置
    settings = load_settings()

    try:
        # 创建PDF分析器实例
        logger.info("初始化PDF分析器")
        analyzer = PDFAnalyzer(file_path)

        # 步骤1：提取PDF内容
        logger.info("步骤1: 开始提取PDF文本内容")
        extracted_content = analyzer.extract_text()
        logger.info(f"提取完成，共获取 {len(extracted_content)} 字符的文本")

        # 步骤2：提取图像和内容分块
        logger.info("步骤2: 开始分析内容结构和提取图像")
        content_blocks = analyzer.analyze_content_blocks()
        logger.info(f"内容分析完成，共识别 {len(content_blocks)} 个内容块")

        # 步骤3：创建DeepSeek API实例
        logger.info(f"步骤3: 初始化DeepSeek API，使用模型 {settings['model']}")
        deepseek = DeepSeekAPI(model=settings['model'], api_key=settings.get('api_key', ''))

        # 步骤4：准备解读提示词
        logger.info("步骤4: 准备解读提示词")
        prompt = settings.get('custom_prompt', '')
        if not prompt:
            # 使用默认提示词
            prompt = DEFAULT_PROMPTS.get(settings['language'], DEFAULT_PROMPTS['zh'])
            logger.info("使用默认提示词模板")
        else:
            logger.info("使用自定义提示词")

        # 步骤5：处理网络搜索（如果启用）
        web_search_results = []
        if settings.get('enable_web_search', False):
            logger.info("步骤5: 开始网络搜索相关参考资料")
            # 提取关键信息以用于搜索
            metadata = analyzer.extract_metadata()
            title = metadata.get('title', '')
            # 使用论文标题进行网络搜索
            if title:
                logger.info(f"使用论文标题进行搜索: {title}")
                web_search_results = web_search.search_for_references(title)
                logger.info(f"搜索完成，获取 {len(web_search_results)} 条参考资料")
            else:
                logger.warning("未能提取到论文标题，跳过网络搜索")

        # 步骤6：生成分析结果
        logger.info("步骤6: 开始生成分析结果")
        analysis_sections = []

        # 检查是否启用测试模式
        test_mode = settings.get('test_mode', False)
        if test_mode:
            logger.info("测试模式已启用，只处理第一个内容分块")
            # 在测试模式下，只保留第一个非图像内容块
            filtered_blocks = []
            for block in content_blocks:
                if block.get('type') != 'image':
                    filtered_blocks.append(block)
                    break
            # 如果没有找到文本块，则保留第一个图像块（如果有）
            if not filtered_blocks and content_blocks:
                filtered_blocks = [content_blocks[0]]
            content_blocks = filtered_blocks
            logger.info(f"测试模式：将只处理 {len(content_blocks)} 个内容块")

        # 处理每个内容块
        for i, block in enumerate(content_blocks):
            logger.info(f"处理内容块 {i+1}/{len(content_blocks)}")
            # 跳过图像块直接添加，不需要解读
            if block.get('type') == 'image':
                logger.info(f"识别到图像块，标题: {block.get('title', f'图像 {i+1}')}")
                analysis_sections.append({
                    'type': 'image',
                    'title': block.get('title', f'图像 {i+1}'),
                    'content': block.get('content', '')
                })
                continue

            # 处理文本块
            block_content = block.get('content', '')
            if not block_content:
                logger.info(f"跳过空内容块 {i+1}")
                continue

            # 构建完整提示词
            logger.info(f"处理文本块 {i+1}，标题: {block.get('title', f'段落 {i+1}')}")
            full_prompt = f"{prompt}\n\n文本内容：{block_content}"

            # 如果有网络搜索结果，添加到提示词中
            if web_search_results and i == 0:  # 只在第一个块添加参考资料
                logger.info("添加网络搜索参考资料到提示词")
                full_prompt += "\n\n参考资料：\n" + "\n".join(web_search_results)

            # 调用DeepSeek API进行解读
            logger.info(f"开始使用DeepSeek API解读文本块 {i+1}")
            analysis = deepseek.analyze_text(full_prompt, language=settings['language'])
            logger.info(f"文本块 {i+1} 解读完成，生成 {len(analysis)} 字符的分析结果")

            # 添加到分析结果中
            analysis_sections.append({
                'type': 'text',
                'title': block.get('title', f'段落 {i+1}'),
                'original_content': block_content,
                'analysis': analysis
            })

        # 在分析完成后关闭文档
        analyzer.close()

        # 将分析结果存储在session中，以便在分析页面显示
        session['analysis_result'] = {
            'filename': filename,
            'original_filename': original_filename,
            'settings': settings,
            'content_blocks': content_blocks,
            'analysis_sections': analysis_sections,
            'web_search_results': web_search_results,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 返回JSON响应，包含重定向URL，供前端JavaScript使用
        return jsonify({'success': True, 'redirect': url_for('analysis_with_preview', filename=filename)})

    except Exception as e:
        flash(f'分析过程中出错: {str(e)}')
        return redirect(url_for('view_pdf', filename=filename))

if __name__ == '__main__':
    app.run(debug=True)