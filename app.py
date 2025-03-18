from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'deeppaper_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('没有选择文件')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('没有选择文件')
        return redirect(request.url)
    
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
    return render_template('viewer.html', filename=filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/deep_paper/<filename>', methods=['POST'])
def deep_paper(filename):
    # 这里将来可以添加DeepPaper的处理逻辑
    # 例如：分析PDF内容，提取关键信息等
    flash('DeepPaper功能正在开发中...')
    return redirect(url_for('view_pdf', filename=filename))

if __name__ == '__main__':
    app.run(debug=True)