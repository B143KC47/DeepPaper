import requests
import os
import json
import time

class DeepSeekAPI:
    """DeepSeek API 接口封装类"""
    
    def __init__(self, model="deepseek-chat", api_key=None):
        """初始化 DeepSeek API
        
        Args:
            model: 使用的模型，可选 "deepseek-chat", "deepseek-coder", "deepseek-reasoner"
            api_key: API 密钥，如不提供则从环境变量获取
        """
        self.model = model
        # 优先从环境变量获取 API 密钥，其次使用传入的值
        self.api_key = os.environ.get('DEEPSEEK_API_KEY') or api_key
        if not self.api_key:
            print("警告: 未设置 DeepSeek API 密钥。请在.env文件中设置 DEEPSEEK_API_KEY 或在初始化时提供。")
            
        # 根据模型选择合适的 API 端点和模型 ID
        self.model_mapping = {
            "deepseek-chat": {
                "endpoint": "https://api.deepseek.com/v1/chat/completions",
                "model_id": "deepseek-chat"
            },
            "deepseek-coder": {
                "endpoint": "https://api.deepseek.com/v1/chat/completions",
                "model_id": "deepseek-coder"
            },
            "deepseek-reasoner": {
                "endpoint": "https://api.deepseek.com/v1/chat/completions",
                "model_id": "deepseek-reasoner"
            }
        }
        
        # 获取当前模型的配置
        model_config = self.model_mapping.get(model, self.model_mapping["deepseek-chat"])
        self.endpoint = model_config["endpoint"]
        self.model_id = model_config["model_id"]
        
    def analyze_text(self, prompt, language='zh', max_tokens=2000, temperature=0.7):
        """使用 DeepSeek API 解析文本
        
        Args:
            prompt: 提示词
            language: 语言，'zh' 或 'en'
            max_tokens: 最大生成令牌数
            temperature: 生成温度，越高越随机
            
        Returns:
            解析结果文本
        """
        if not self.api_key:
            return self._mock_analysis(prompt, language)
            
        # 添加语言设置到提示词
        if language == 'en' and "in English" not in prompt:
            prompt += "\nPlease respond in English."
        elif language == 'zh' and "用中文" not in prompt:
            prompt += "\n请用中文回复。"
            
        # 准备请求头和数据
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            # 发送请求到 DeepSeek API
            response = requests.post(self.endpoint, headers=headers, json=data)
            response.raise_for_status()  # 检查HTTP错误
            
            # 解析响应
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "API 返回了无效的响应格式"
                
        except requests.exceptions.RequestException as e:
            # 处理请求异常
            error_msg = f"API 请求失败: {str(e)}"
            print(error_msg)
            return error_msg
            
        except json.JSONDecodeError:
            # 处理 JSON 解析错误
            error_msg = "API 返回了无效的 JSON 响应"
            print(error_msg)
            return error_msg
            
    def _mock_analysis(self, prompt, language):
        """当没有 API 密钥时提供模拟分析结果（用于开发测试）
        
        Args:
            prompt: 提示词
            language: 语言
            
        Returns:
            模拟的分析结果
        """
        # 等待一秒，模拟 API 调用延迟
        time.sleep(1)
        
        # 根据语言返回模拟回复
        if language == 'en':
            return """
            ## Analysis Summary
            
            This document appears to be an academic paper in the field of [subject area]. The key points are:
            
            1. **Research Objective**: The paper aims to investigate [research objective].
            
            2. **Methodology**: The authors employed [research methods] to analyze the data.
            
            3. **Main Findings**: The results indicate that [key findings].
            
            4. **Significance**: This research contributes to the field by [contributions].
            
            5. **Future Directions**: The authors suggest [future research directions].
            
            Note: This is a mock analysis as the DeepSeek API key is not configured.
            """
        else:
            return """
            ## 分析摘要
            
            该文档似乎是一篇[学科领域]的学术论文。主要要点包括：
            
            1. **研究目标**：该论文旨在研究[研究目标]。
            
            2. **研究方法**：作者采用了[研究方法]来分析数据。
            
            3. **主要发现**：结果表明[关键发现]。
            
            4. **研究意义**：本研究通过[贡献]为该领域做出了贡献。
            
            5. **未来方向**：作者建议[未来研究方向]。
            
            注意：这是一个模拟分析，因为未配置 DeepSeek API 密钥。
            """