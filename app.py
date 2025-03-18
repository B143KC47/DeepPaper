from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
import os
import uuid
import json
from werkzeug.utils import secure_filename
from datetime import datetime

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
    'model': 'gpt-3.5-turbo',
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

@app.route('/settings')
def settings():
    current_settings = load_settings()
    return render_template('settings.html', current_settings=current_settings)

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
    
    # 步骤1：提取PDF内容
    extracted_content = ""
    
    # 步骤2：内容分块
    content_blocks = []
    
    # 步骤3：内容分析
    analysis_sections = []
    
    try:
        if settings['model'] in ['deepseek-chat', 'deepseek-reasoner']:
            # 使用DeepSeek API进行分析
            from openai import OpenAI
            
            # 这里应该从环境变量或配置文件中获取API密钥
            api_key = os.environ.get('DEEPSEEK_API_KEY', '')
            if not api_key:
                flash('未设置DeepSeek API密钥，请在环境变量中设置DEEPSEEK_API_KEY')
                return redirect(url_for('view_pdf', filename=filename))
            
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            
            # 步骤1：提取PDF内容（实际应用中应该使用PDF解析库）
            # 这里仅作为示例
            extracted_content = "这是从PDF中提取的内容示例。这里应该是完整的PDF文本内容，包括标题、作者、摘要、正文、图表说明和参考文献等。在实际应用中，应该使用专门的PDF解析库来提取文本内容，并保留原始格式和结构。"
            
            # 步骤2：内容分块（实际应用中应该根据文档结构进行智能分块）
            # 这里仅作为示例
            content_blocks = [
                "【标题和作者信息】这里是论文的标题和作者信息，包括作者单位、联系方式等。",
                "【摘要】这里是论文的摘要部分，简要介绍研究目的、方法、结果和结论。",
                "【引言】这里是论文的引言部分，介绍研究背景、研究意义和研究目标等。",
                "【研究方法】这里是论文的研究方法部分，详细描述研究设计、数据收集和分析方法等。",
                "【研究结果】这里是论文的研究结果部分，呈现数据分析结果和主要发现。",
                "【讨论】这里是论文的讨论部分，解释研究结果的意义、与已有研究的关系等。",
                "【结论】这里是论文的结论部分，总结主要发现和研究贡献。",
                "【参考文献】这里是论文的参考文献列表，包括引用的文献信息。"
            ]
            
            # 构建提示词
            language = "中文" if settings['language'] == 'zh' else "英文"
            detail_level_map = {
                'basic': '基础',
                'standard': '标准',
                'detailed': '详细'
            }
            detail_level = detail_level_map.get(settings['detail_level'], '标准')
            
            prompt = f"请以{language}对以下学术论文进行{detail_level}分析，包括摘要分析、研究方法评估、结论与建议以及参考文献分析：\n\n{extracted_content}"
            
            # 调用DeepSeek API
            response = client.chat.completions.create(
                model=settings['model'],
                messages=[
                    {"role": "system", "content": "你是一个专业的学术论文分析助手，擅长分析和评价学术论文的质量、方法和结论。"},
                    {"role": "user", "content": prompt},
                ],
                stream=False
            )
            
            # 处理API响应
            ai_response = response.choices[0].message.content
            
            # 简单处理返回的内容，实际应用中可能需要更复杂的解析
            analysis_sections = [
                {
                    'title': '摘要分析',
                    'content': f'<p>{ai_response}</p>'
                }
            ]
        else:
            # 模拟分析过程
            # 步骤1：提取PDF内容
            extracted_content = "这是从PDF中提取的内容示例。本研究探讨了人工智能在教育领域的应用及其对学生学习成果的影响。研究采用混合研究方法，包括问卷调查、课堂观察和半结构化访谈，收集了来自10所学校的500名学生和50名教师的数据。研究结果表明，适当整合AI技术可以显著提高学生的学习兴趣和学习效果，特别是在个性化学习和即时反馈方面。然而，研究也发现，教师的技术素养和学校的基础设施条件是影响AI教育应用效果的关键因素。本研究为教育工作者和政策制定者提供了关于如何有效利用AI技术改善教育质量的实证依据和建议。"
            
            # 步骤2：内容分块
            content_blocks = [
                "【标题和作者信息】人工智能在教育中的应用及其对学生学习成果的影响 - 张明、李华、王强 (2023)",
                "【摘要】本研究探讨了人工智能在教育领域的应用及其对学生学习成果的影响。研究采用混合研究方法，收集了来自10所学校的数据。研究结果表明，适当整合AI技术可以显著提高学生的学习兴趣和学习效果，但教师素养和基础设施条件是关键影响因素。",
                "【引言】随着人工智能技术的快速发展，其在教育领域的应用日益广泛。然而，关于AI教育应用的实际效果及影响因素的实证研究仍然不足。本研究旨在填补这一研究空白...",
                "【研究方法】本研究采用混合研究方法，包括问卷调查、课堂观察和半结构化访谈。研究对象包括来自10所不同类型学校的500名学生和50名教师。数据收集工具包括学生学习体验问卷、课堂观察量表和教师访谈提纲...",
                "【研究结果】定量分析结果显示，使用AI辅助教学的实验组学生在学习兴趣、学习投入度和学习成绩方面均显著高于对照组。定性分析发现，学生普遍认为AI提供的个性化学习路径和即时反馈最有帮助...",
                "【讨论】研究结果支持了AI技术在提升学习体验和学习效果方面的积极作用，这与Smith(2021)和Johnson(2022)的研究发现一致。然而，本研究进一步揭示了影响AI教育应用效果的关键因素...",
                "【结论】本研究证实了AI技术在教育中的应用价值，同时指出了实施过程中需要关注的关键因素。研究建议教育机构在引入AI技术时，应同步加强教师培训和基础设施建设...",
                "【参考文献】1. Smith, J. (2021). Artificial Intelligence in Education: Promises and Challenges. Educational Technology Research and Development, 69(1), 1-15.\n2. Johnson, K. (2022). The Impact of AI-Based Learning Systems on Student Achievement. Journal of Educational Psychology, 114(2), 245-260.\n..."
            ]
            
            # 步骤3：内容分析
            analysis_sections = [
                {
                    'title': '摘要分析',
                    'content': '<p>该论文摘要结构完整，清晰地概述了研究目的、方法、结果和结论。摘要指出研究探讨了AI在教育领域的应用及其对学习成果的影响，使用了混合研究方法，并简明扼要地呈现了主要发现。摘要质量较高，为读者提供了研究的整体框架。</p><p>优点：简洁明了，包含了研究的关键要素；明确指出了研究的实际意义。</p><p>建议：可以在摘要中简要提及研究的理论框架，增强学术深度。</p>'
                },
                {
                    'title': '研究方法评估',
                    'content': '<p>该研究采用的混合研究方法设计合理，结合了定量和定性数据收集技术，有助于全面理解研究问题。</p><ul><li>问卷调查：适合收集大样本数据，了解学生对AI辅助学习的整体感受</li><li>课堂观察：提供了学生实际学习行为的直接证据</li><li>半结构化访谈：深入了解教师和学生的主观体验和看法</li></ul><p>样本规模（500名学生和50名教师）足够大，来自10所不同学校的数据增强了研究的外部效度。</p><p>研究方法的局限性：文中未详细说明随机分配的过程，可能存在选择偏差；未提及研究工具的效度和信度检验情况。</p>'
                },
                {
                    'title': '结论与建议',
                    'content': '<p>研究结论与数据分析结果一致，合理地总结了AI技术在教育中的应用价值及实施条件。结论部分不仅确认了AI技术的积极作用，还指出了影响其效果的关键因素，体现了研究的平衡视角。</p><p>研究建议具有实践性，强调了教师培训和基础设施建设的重要性，为教育机构提供了可操作的指导。</p><p>对未来研究的建议：</p><ul><li>建议进行纵向研究，考察AI教育应用的长期效果</li><li>探索不同学科领域AI应用的差异性</li><li>研究AI教育应用对不同学习能力学生的影响</li></ul></p>'
                },]
    except Exception as e:
        flash(f'分析过程中出错: {str(e)}')
        return redirect(url_for('view_pdf', filename=filename))
    
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

@app.route('/analysis/<filename>')
def analysis_result(filename):
    # 从session中获取分析结果
    analysis_result = session.get('analysis_result', {})
    
    # 如果没有分析结果或者文件名不匹配，重定向到PDF查看页面
    if not analysis_result or analysis_result.get('filename') != filename:
        flash('没有找到分析结果，请重新分析')
        return redirect(url_for('view_pdf', filename=filename))
    
    return render_template('analysis.html', 
                           filename=filename,
                           original_filename=analysis_result.get('original_filename'),
                           settings=analysis_result.get('settings'),
                           extracted_content=analysis_result.get('extracted_content'),
                           content_blocks=analysis_result.get('content_blocks'),
                           analysis_sections=analysis_result.get('analysis_sections'))

if __name__ == '__main__':
    app.run(debug=True)