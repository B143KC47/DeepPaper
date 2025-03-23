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