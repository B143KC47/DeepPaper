<div align="center">
  <img src="static/images/logo.svg" alt="DeepPaper Logo" width="200" height="200">
  <h1>DeepPaper</h1>
  <p>Intelligent Paper Analysis System</p>
  <p>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
    <a href="#"><img src="https://img.shields.io/badge/version-1.0.0-brightgreen.svg" alt="Version"></a>
    <a href="#"><img src="https://img.shields.io/badge/python-%3E%3D3.8-blue.svg" alt="Python Version"></a>
    <a href="README_ZH.md"><img src="https://img.shields.io/badge/文档-中文版-red.svg" alt="Chinese Documentation"></a>
  </p>
</div>

> ⚠️ **Development Status Warning** ⚠️
> 
> This project is currently under active development and in beta stage. Features may be incomplete or subject to change. Use with caution in production environments.
> 
> Current Development Progress:
> - ✅ Basic PDF parsing and text extraction
> - 🚧 Research methodology analysis (In Progress)
> - 📅 Academic value assessment (Planned)
> - 📅 Knowledge graph features (Planned)

## 🎯 Project Overview
DeepPaper is an AI-powered academic paper analysis platform that automatically parses PDF documents, providing structured content extraction, research methodology evaluation, and academic value assessment.

## ✨ Key Features
- 📄 **Intelligent PDF Parsing & Content Extraction**
  - Automatic structure recognition
  - High-precision text extraction
  - Figure and table detection

- 🔍 **Research Methodology Evaluation**
  - Methodology identification
  - Experimental design analysis
  - Result validation assessment

- 📊 **Academic Value Analysis**
  - Innovation point detection
  - Research impact evaluation
  - Future direction suggestion

- 🌐 **Cross-domain Knowledge Graph**
  - Citation network analysis
  - Research trend visualization
  - Domain knowledge mapping

## 🛠️ Technology Stack
- **Backend Framework**: Flask
- **PDF Parsing**: PyMuPDF
- **NLP Processing**: spaCy + Custom Rule Engine
- **Deep Learning**: DeepSeek API Integration
- **Frontend**: HTML5 + CSS3 + JavaScript

## 🚀 Quick Start

### Prerequisites
- Python >= 3.8
- pip (Python package manager)

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/DeepPaper.git
cd DeepPaper

# Install dependencies
pip install -r requirements.txt

# Configure API Key (安全配置方式)
# 方法1: 创建.env文件（推荐）
cp .env.example .env
# 然后编辑.env文件，填入你的API密钥

# 方法2: 使用环境变量
export DEEPSEEK_API_KEY="your_api_key"  # Linux/Mac
# 或
set DEEPSEEK_API_KEY=your_api_key  # Windows

# Start service
flask run --host=0.0.0.0 --port=5000
```

## 📖 User Guide
1. Visit http://localhost:5000 in your browser
2. Upload your PDF paper
3. Select analysis parameters:
   - Language (English/Chinese)
   - Detail Level (Basic/Standard/Detailed)
4. View the structured analysis report
5. Export results in Markdown format

## ⚙️ Advanced Configuration
```python
# config.py
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ANALYSIS_MODES = ['basic', 'standard', 'detailed']
```

## 🔐 API密钥安全配置

DeepPaper使用DeepSeek API进行论文分析，需要配置API密钥。为了保护您的API密钥安全，我们提供了以下安全存储方法：

### 方法1：使用.env文件（推荐）

1. 复制项目中的`.env.example`文件并重命名为`.env`
   ```bash
   cp .env.example .env
   ```

2. 编辑`.env`文件，将您的API密钥填入`DEEPSEEK_API_KEY`变量
   ```
   DEEPSEEK_API_KEY=your_actual_api_key_here
   ```

3. `.env`文件已被添加到`.gitignore`中，确保您的API密钥不会被提交到版本控制系统

### 方法2：使用环境变量

- Linux/Mac:
  ```bash
  export DEEPSEEK_API_KEY="your_api_key"
  ```

- Windows:
  ```bash
  set DEEPSEEK_API_KEY=your_api_key
  ```

### 方法3：通过Web界面设置

1. 启动DeepPaper应用
2. 访问设置页面
3. 在"DeepSeek API密钥"字段中输入您的API密钥
4. 点击"保存设置"

> ⚠️ **安全警告**：
> - 永远不要将您的API密钥直接硬编码在代码中
> - 不要将包含API密钥的`.env`文件提交到版本控制系统
> - 定期轮换您的API密钥以提高安全性

## 🤝 Contributing
We welcome contributions from the community! Here's how you can help:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please read our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📮 Contact & Support
- Create an [Issue](https://github.com/yourusername/DeepPaper/issues) for bug reports or feature requests
- Star ⭐ the repository if you find it useful
- Follow us for updates