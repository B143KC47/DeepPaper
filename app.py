from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
import os
import uuid
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from pdf_analyzer import PDFAnalyzer

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
    'detail_level': 'standard'
}

# 加载设置
def load_settings():
    if os.path.exists(app.config['SETTINGS_FILE']):
        try:
            with open(app.config['SETTINGS_FILE'], 'r', encoding='utf-8') as f:
                return json.load(f)
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
    settings = {
        'model': request.form.get('model', DEFAULT_SETTINGS['model']),
        'language': request.form.get('language', DEFAULT_SETTINGS['language']),
        'detail_level': request.form.get('detail_level', DEFAULT_SETTINGS['detail_level'])
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
    
    # 获取原始文件名
    original_filename = filename.split('_', 1)[1] if '_' in filename else filename
    
    # 加载设置
    settings = load_settings()
    
    try:
        # 创建PDF分析器实例
        analyzer = PDFAnalyzer(file_path)
        
        # 步骤1：提取PDF内容
        extracted_content = analyzer.extract_text()
        
        # 步骤2：内容分块
        content_blocks = analyzer.analyze_content_blocks()
        
        # 步骤3：内容分析
        analysis_sections = analyzer.generate_analysis_sections(
            language=settings['language'],
            detail_level=settings['detail_level']
        )
        
        # 在分析完成后关闭文档
        analyzer.close()
        
        # 将分析结果存储在session中，以便在分析页面显示
        session['analysis_result'] = {
            'filename': filename,
            'original_filename': original_filename,
            'settings': settings,
            'extracted_content': extracted_content,
            'content_blocks': content_blocks,
            'analysis_sections': analysis_sections,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return redirect(url_for('analysis_result', filename=filename))
        
    except Exception as e:
        flash(f'分析过程中出错: {str(e)}')
        return redirect(url_for('view_pdf', filename=filename))

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
                           extracted_content=analysis_result.get('extracted_content'),
                           content_blocks=analysis_result.get('content_blocks'),
                           analysis_sections=analysis_result.get('analysis_sections'))

if __name__ == '__main__':
    app.run(debug=True)