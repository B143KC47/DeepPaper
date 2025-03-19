import fitz  # PyMuPDF
import re
import os
from collections import defaultdict

class PDFAnalyzer:
    """PDF 论文分析器"""
    
    def __init__(self, file_path):
        """初始化 PDF 分析器
        
        Args:
            file_path: PDF 文件路径
        """
        self.file_path = file_path
        self.doc = None
        self.text = ""
        self.sections = {}
        self.metadata = {}
        self.references = []
        self.figures = []
        self.tables = []
        
    def load_document(self):
        """加载 PDF 文档"""
        try:
            self.doc = fitz.open(self.file_path)
            return True
        except Exception as e:
            print(f"加载文档时出错: {str(e)}")
            return False
            
    def extract_text(self):
        """提取 PDF 文本内容"""
        if not self.doc:
            if not self.load_document():
                return ""
                
        full_text = ""
        for page in self.doc:
            full_text += page.get_text()
            
        self.text = full_text
        return full_text
        
    def extract_metadata(self):
        """提取元数据信息"""
        if not self.doc:
            if not self.load_document():
                return {}
                
        self.metadata = self.doc.metadata
        
        # 尝试从文本中提取标题和作者（如果元数据中不存在）
        if not self.metadata.get("title") and self.text:
            # 简单提取文档开始的第一个大文本块作为可能的标题
            lines = self.text.split("\n")
            for i, line in enumerate(lines[:10]):  # 只检查前10行
                if len(line.strip()) > 10 and len(line.strip()) < 200:  # 标题通常长度适中
                    self.metadata["title"] = line.strip()
                    break
        
        return self.metadata
        
    def detect_sections(self):
        """检测文档章节结构"""
        if not self.text:
            self.extract_text()
            
        # 常见论文章节模式
        section_patterns = [
            r"(?:^|\n)([A-Z][A-Za-z\s]+)(?:\n|\.)",  # 大写开头的章节标题
            r"(?:^|\n)(\d+\.\s*[A-Za-z\s]+)(?:\n|\.)",  # 数字编号的章节
            r"(?:^|\n)(Abstract|Introduction|Methodology|Methods|Results|Discussion|Conclusion|References)(?:\n|\.|:)"  # 常见章节名
        ]
        
        section_matches = []
        for pattern in section_patterns:
            matches = re.finditer(pattern, self.text, re.MULTILINE)
            for match in matches:
                section_title = match.group(1).strip()
                start_pos = match.start()
                section_matches.append((start_pos, section_title))
        
        # 按位置排序
        section_matches.sort()
        
        # 提取各章节内容
        sections = {}
        for i, (pos, title) in enumerate(section_matches):
            start = pos
            if i < len(section_matches) - 1:
                end = section_matches[i+1][0]
            else:
                end = len(self.text)
                
            # 跳过章节标题本身
            content_start = self.text.find('\n', start) + 1
            if content_start < end:
                sections[title] = self.text[content_start:end].strip()
            else:
                sections[title] = ""
                
        self.sections = sections
        return sections
        
    def extract_references(self):
        """提取参考文献列表"""
        if not self.sections:
            self.detect_sections()
            
        references = []
        ref_text = ""
        
        # 寻找参考文献章节
        for title, content in self.sections.items():
            if "reference" in title.lower() or "bibliography" in title.lower():
                ref_text = content
                break
                
        if ref_text:
            # 分割参考文献条目
            # 可能的分隔模式：[1], 1., 1), 等
            ref_patterns = [
                r"(?:^|\n)\[\d+\]",  # [1] 格式
                r"(?:^|\n)\d+\.",    # 1. 格式
                r"(?:^|\n)\d+\)",    # 1) 格式
                r"(?:^|\n)\(\d+\)"   # (1) 格式
            ]
            
            for pattern in ref_patterns:
                if re.search(pattern, ref_text):
                    splits = re.split(pattern, ref_text)
                    # 第一个通常是空的
                    references = [ref.strip() for ref in splits[1:] if ref.strip()]
                    break
                    
            # 如果上述模式都不匹配，尝试按行分割
            if not references:
                references = [line.strip() for line in ref_text.split('\n') if line.strip()]
                
        self.references = references
        return references
        
    def detect_figures_and_tables(self):
        """检测图表"""
        if not self.doc:
            if not self.load_document():
                return [], []
                
        figures = []
        tables = []
        
        # 通过文本检测图表引用
        fig_pattern = r"(?:Fig(?:ure)?\.?\s*(\d+))|(?:表\s*(\d+))|(?:图\s*(\d+))"
        table_pattern = r"(?:Table\s*(\d+))|(?:表\s*(\d+))"
        
        fig_matches = re.finditer(fig_pattern, self.text)
        for match in fig_matches:
            fig_num = match.group(1) or match.group(2) or match.group(3)
            if fig_num:
                fig_pos = match.start()
                # 提取图表标题（简单实现，实际可能需要更复杂的逻辑）
                context = self.text[max(0, fig_pos-50):min(len(self.text), fig_pos+200)]
                caption = re.search(r"(?:Fig(?:ure)?\.?\s*\d+[\.:]?\s*)([^\n\.]+)", context)
                caption_text = caption.group(1).strip() if caption else ""
                figures.append({
                    "number": fig_num,
                    "position": fig_pos,
                    "caption": caption_text
                })
                
        table_matches = re.finditer(table_pattern, self.text)
        for match in table_matches:
            table_num = match.group(1) or match.group(2)
            if table_num:
                table_pos = match.start()
                # 提取表格标题
                context = self.text[max(0, table_pos-50):min(len(self.text), table_pos+200)]
                caption = re.search(r"(?:Table\s*\d+[\.:]?\s*)([^\n\.]+)", context)
                caption_text = caption.group(1).strip() if caption else ""
                tables.append({
                    "number": table_num,
                    "position": table_pos,
                    "caption": caption_text
                })
                
        self.figures = figures
        self.tables = tables
        return figures, tables
        
    def analyze_content_blocks(self):
        """将文档内容分块"""
        if not self.sections:
            self.detect_sections()
            
        content_blocks = []
        
        # 添加元数据块
        metadata = self.extract_metadata()
        if metadata:
            title = metadata.get("title", "未知标题")
            author = metadata.get("author", "未知作者")
            metadata_block = f"【标题和作者信息】{title} - {author}"
            content_blocks.append(metadata_block)
            
        # 添加各章节块
        for section_title, section_content in self.sections.items():
            # 限制块大小，避免过大
            max_block_size = 1000  # 字符数
            if len(section_content) > max_block_size:
                # 按句子分割
                sentences = re.split(r'(?<=[.!?])\s+', section_content)
                current_block = ""
                for sentence in sentences:
                    if len(current_block) + len(sentence) < max_block_size:
                        current_block += sentence + " "
                    else:
                        if current_block:
                            content_blocks.append(f"【{section_title}】{current_block.strip()}")
                        current_block = sentence + " "
                
                if current_block:
                    content_blocks.append(f"【{section_title}】{current_block.strip()}")
            else:
                content_blocks.append(f"【{section_title}】{section_content}")
                
        # 如果没有检测到章节，尝试按页面分块
        if not content_blocks and self.doc:
            for page_num, page in enumerate(self.doc):
                page_text = page.get_text()
                if page_text.strip():
                    content_blocks.append(f"【页面 {page_num+1}】{page_text[:max_block_size]}")
                    
        return content_blocks
        
    def analyze_methods(self):
        """分析研究方法"""
        if not self.sections:
            self.detect_sections()
            
        methods_section = None
        for title, content in self.sections.items():
            if any(method_word in title.lower() for method_word in ["method", "methodology", "approach", "实验", "方法"]):
                methods_section = content
                break
                
        if not methods_section:
            return {
                "identified": False,
                "description": "未能识别出明确的研究方法章节。"
            }
            
        # 分析方法类型
        method_types = []
        if re.search(r"(?:survey|questionnaire|interview|focus group|问卷|调查|访谈|焦点小组)", methods_section, re.IGNORECASE):
            method_types.append("问卷调查/访谈")
            
        if re.search(r"(?:experiment|control group|随机分配|对照组|实验组|实验设计)", methods_section, re.IGNORECASE):
            method_types.append("实验研究")
            
        if re.search(r"(?:observation|ethnography|观察|民族志)", methods_section, re.IGNORECASE):
            method_types.append("观察研究")
            
        if re.search(r"(?:case study|案例研究|案例分析)", methods_section, re.IGNORECASE):
            method_types.append("案例研究")
            
        if re.search(r"(?:review|meta-analysis|综述|文献回顾|元分析)", methods_section, re.IGNORECASE):
            method_types.append("文献综述/元分析")
        
        if re.search(r"(?:model|simulation|algorithm|模型|算法|仿真)", methods_section, re.IGNORECASE):
            method_types.append("建模/算法/仿真")
            
        # 提取样本信息
        sample_info = ""
        sample_matches = re.search(r"(?:sample|participant|subject).{1,50}?(\d+)(?=\s|\.|\,|\))", methods_section, re.IGNORECASE)
        if sample_matches:
            sample_size = sample_matches.group(1)
            sample_info = f"样本量约 {sample_size}"
            
        # 分析方法部分的详细程度
        detail_level = "低"
        if len(methods_section) > 1500:
            detail_level = "高"
        elif len(methods_section) > 800:
            detail_level = "中"
            
        return {
            "identified": True,
            "method_types": method_types,
            "sample_info": sample_info,
            "detail_level": detail_level,
            "description": methods_section[:500] + "..." if len(methods_section) > 500 else methods_section
        }
        
    def analyze_academic_value(self):
        """分析学术价值"""
        if not self.text:
            self.extract_text()
            
        if not self.sections:
            self.detect_sections()
            
        # 提取摘要和结论部分
        abstract = ""
        conclusion = ""
        
        for title, content in self.sections.items():
            if "abstract" in title.lower() or "摘要" in title:
                abstract = content
            elif "conclusion" in title.lower() or "结论" in title:
                conclusion = content
                
        # 识别创新点（基于常见表达方式）
        innovation_patterns = [
            r"(?:novel|innovative|first|contribution|创新|首次|贡献).{1,100}?(?=\.|\n)",
            r"(?:propose|present|introduce|提出).{1,100}?(?:new|novel|innovative|创新).{1,100}?(?=\.|\n)",
            r"(?:improve|enhance|优化|改进).{1,100}?(?=\.|\n)",
            r"(?:outperform|better than|superior to|优于).{1,100}?(?=\.|\n)"
        ]
        
        innovation_points = []
        for pattern in innovation_patterns:
            matches = re.finditer(pattern, self.text, re.IGNORECASE)
            for match in matches:
                point = match.group(0).strip()
                if point and len(point) > 20:  # 避免过短的匹配
                    innovation_points.append(point)
                    
        # 去重
        innovation_points = list(set(innovation_points))[:5]  # 限制数量
        
        # 未来研究方向
        future_patterns = [
            r"(?:future|further|future work|未来|进一步).{1,50}?(?:research|study|work|研究).{1,100}?(?=\.|\n)",
            r"(?:suggest|recommend|建议).{1,100}?(?=\.|\n)"
        ]
        
        future_directions = []
        for pattern in future_patterns:
            matches = re.finditer(pattern, conclusion, re.IGNORECASE)
            for match in matches:
                direction = match.group(0).strip()
                if direction and len(direction) > 20:
                    future_directions.append(direction)
                    
        # 去重
        future_directions = list(set(future_directions))[:3]
        
        # 引用分析
        citation_count = len(self.references) if self.references else "未提取到参考文献"
        
        # 关键词（如果能在文本中找到）
        keywords = []
        keyword_match = re.search(r"(?:keywords|key words|关键词)[:：](.+?)(?=\n|\.|$)", self.text, re.IGNORECASE)
        if keyword_match:
            keywords_text = keyword_match.group(1).strip()
            # 尝试按不同分隔符分割
            for sep in [',', ';', '；', '，']:
                if sep in keywords_text:
                    keywords = [k.strip() for k in keywords_text.split(sep) if k.strip()]
                    break
                    
        if not keywords and abstract:
            # 从摘要中提取可能的关键词（简单实现，实际可能需要NLP支持）
            words = abstract.split()
            word_freq = defaultdict(int)
            for word in words:
                if len(word) > 4:  # 忽略过短的词
                    word_freq[word.lower()] += 1
                    
            # 按频率排序取前5个
            keywords = [word for word, freq in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]]
        
        return {
            "innovation_points": innovation_points,
            "future_directions": future_directions,
            "citation_count": citation_count,
            "keywords": keywords,
            "abstract": abstract[:300] + "..." if len(abstract) > 300 else abstract
        }
    
    def generate_analysis_sections(self, language='zh', detail_level='standard'):
        """生成分析报告章节
        
        Args:
            language: 语言，'zh' 或 'en'
            detail_level: 详细程度，'basic', 'standard', 或 'detailed'
            
        Returns:
            分析报告章节列表
        """
        # 确保数据已提取
        if not self.text:
            self.extract_text()
            
        if not self.sections:
            self.detect_sections()
            
        if not self.references:
            self.extract_references()
            
        # 研究方法分析
        methods_analysis = self.analyze_methods()
        
        # 学术价值分析
        value_analysis = self.analyze_academic_value()
        
        # 根据语言和详细程度生成分析报告
        analysis_sections = []
        
        # 摘要分析
        abstract_content = ""
        if language == 'zh':
            abstract_content = "<p>论文摘要分析：</p>"
            if value_analysis["abstract"]:
                abstract_content += f"<p>摘要内容：{value_analysis['abstract']}</p>"
                
                if detail_level in ['standard', 'detailed']:
                    abstract_content += "<p>摘要结构评价：</p>"
                    if len(value_analysis["abstract"]) < 100:
                        abstract_content += "<p>摘要篇幅较短，建议扩展以涵盖研究目的、方法、结果和结论等核心内容。</p>"
                    else:
                        abstract_content += "<p>摘要篇幅适当，能够概述研究的主要内容。</p>"
                        
                if value_analysis["keywords"]:
                    abstract_content += f"<p>关键词：{', '.join(value_analysis['keywords'])}</p>"
            else:
                abstract_content += "<p>未能从文档中提取到明确的摘要内容。</p>"
        else:  # 英文
            abstract_content = "<p>Abstract Analysis:</p>"
            if value_analysis["abstract"]:
                abstract_content += f"<p>Abstract Content: {value_analysis['abstract']}</p>"
                
                if detail_level in ['standard', 'detailed']:
                    abstract_content += "<p>Structure Evaluation:</p>"
                    if len(value_analysis["abstract"]) < 100:
                        abstract_content += "<p>The abstract is relatively short. Consider expanding it to cover key aspects like research purpose, methods, results, and conclusions.</p>"
                    else:
                        abstract_content += "<p>The abstract has appropriate length and provides an overview of the main research content.</p>"
                        
                if value_analysis["keywords"]:
                    abstract_content += f"<p>Keywords: {', '.join(value_analysis['keywords'])}</p>"
            else:
                abstract_content += "<p>Could not extract a clear abstract from the document.</p>"
                
        analysis_sections.append({
            'title': '摘要分析' if language == 'zh' else 'Abstract Analysis',
            'content': abstract_content
        })
        
        # 研究方法评估
        methods_content = ""
        if language == 'zh':
            methods_content = "<p>研究方法评估：</p>"
            if methods_analysis["identified"]:
                methods_content += f"<p>识别到的研究方法类型：{', '.join(methods_analysis['method_types']) if methods_analysis['method_types'] else '未明确识别'}</p>"
                if methods_analysis["sample_info"]:
                    methods_content += f"<p>样本信息：{methods_analysis['sample_info']}</p>"
                methods_content += f"<p>方法描述详细程度：{methods_analysis['detail_level']}</p>"
                
                if detail_level == 'detailed':
                    methods_content += f"<p>方法描述摘录：</p><p>{methods_analysis['description']}</p>"
                    
                # 评价
                if methods_analysis["detail_level"] == "低":
                    methods_content += "<p>建议：研究方法描述较为简略，建议增加更多关于研究设计、数据收集和分析过程的细节。</p>"
                elif methods_analysis["detail_level"] == "高":
                    methods_content += "<p>优点：研究方法描述详尽，清晰地说明了研究过程和技术路线。</p>"
            else:
                methods_content += "<p>未能在文档中识别出明确的研究方法章节。如果这是一篇研究论文，建议增加方法学部分的详细描述。</p>"
        else:  # 英文
            methods_content = "<p>Research Methodology Evaluation:</p>"
            if methods_analysis["identified"]:
                methods_content += f"<p>Identified research method types: {', '.join(methods_analysis['method_types']) if methods_analysis['method_types'] else 'Not clearly identified'}</p>"
                if methods_analysis["sample_info"]:
                    methods_content += f"<p>Sample information: {methods_analysis['sample_info']}</p>"
                methods_content += f"<p>Detail level of methodology description: {methods_analysis['detail_level']}</p>"
                
                if detail_level == 'detailed':
                    methods_content += f"<p>Methodology excerpt:</p><p>{methods_analysis['description']}</p>"
                    
                # 评价
                if methods_analysis["detail_level"] == "低":
                    methods_content += "<p>Suggestion: The methodology description is relatively brief. Consider adding more details about research design, data collection, and analysis procedures.</p>"
                elif methods_analysis["detail_level"] == "高":
                    methods_content += "<p>Strength: The methodology is described in detail, clearly explaining the research process and technical approach.</p>"
            else:
                methods_content += "<p>Could not identify a clear methodology section in the document. If this is a research paper, consider adding a detailed description of the methodology.</p>"
                
        analysis_sections.append({
            'title': '研究方法评估' if language == 'zh' else 'Research Methodology Evaluation',
            'content': methods_content
        })
        
        # 学术价值分析
        value_content = ""
        if language == 'zh':
            value_content = "<p>学术价值分析：</p>"
            
            # 创新点
            if value_analysis["innovation_points"]:
                value_content += "<p>识别到的创新点：</p><ul>"
                for point in value_analysis["innovation_points"]:
                    value_content += f"<li>{point}</li>"
                value_content += "</ul>"
            else:
                value_content += "<p>未能明确识别出创新点。建议在论文中更清晰地强调研究的创新性贡献。</p>"
                
            # 引用分析
            value_content += f"<p>引用文献数量：{value_analysis['citation_count']}</p>"
            
            # 未来方向
            if value_analysis["future_directions"]:
                value_content += "<p>未来研究方向建议：</p><ul>"
                for direction in value_analysis["future_directions"]:
                    value_content += f"<li>{direction}</li>"
                value_content += "</ul>"
            else:
                value_content += "<p>未能识别出明确的未来研究方向建议。考虑在结论部分增加对未来工作的展望。</p>"
                
            # 评价建议
            if detail_level == 'detailed':
                value_content += "<p>学术价值评估：</p>"
                if value_analysis["innovation_points"] and value_analysis["future_directions"]:
                    value_content += "<p>该研究在学术价值方面表现良好，既明确了创新贡献，也提出了未来研究方向。</p>"
                else:
                    value_content += "<p>建议更明确地阐述研究的学术贡献和未来研究方向，以增强论文的学术影响力。</p>"
        else:  # 英文
            value_content = "<p>Academic Value Analysis:</p>"
            
            # 创新点
            if value_analysis["innovation_points"]:
                value_content += "<p>Identified innovation points:</p><ul>"
                for point in value_analysis["innovation_points"]:
                    value_content += f"<li>{point}</li>"
                value_content += "</ul>"
            else:
                value_content += "<p>Could not clearly identify innovation points. Consider emphasizing the novel contributions of the research more clearly.</p>"
                
            # 引用分析
            value_content += f"<p>Number of citations: {value_analysis['citation_count']}</p>"
            
            # 未来方向
            if value_analysis["future_directions"]:
                value_content += "<p>Suggestions for future research:</p><ul>"
                for direction in value_analysis["future_directions"]:
                    value_content += f"<li>{direction}</li>"
                value_content += "</ul>"
            else:
                value_content += "<p>Could not identify clear suggestions for future research. Consider adding perspectives on future work in the conclusion section.</p>"
                
            # 评价建议
            if detail_level == 'detailed':
                value_content += "<p>Academic value assessment:</p>"
                if value_analysis["innovation_points"] and value_analysis["future_directions"]:
                    value_content += "<p>The research performs well in terms of academic value, both clearly stating innovative contributions and proposing future research directions.</p>"
                else:
                    value_content += "<p>It is recommended to more clearly articulate the academic contributions and future research directions to enhance the academic impact of the paper.</p>"
                    
        analysis_sections.append({
            'title': '学术价值分析' if language == 'zh' else 'Academic Value Analysis',
            'content': value_content
        })
        
        # 引用分析（仅在详细模式下）
        if detail_level == 'detailed' and self.references:
            refs_content = ""
            if language == 'zh':
                refs_content = f"<p>参考文献分析：</p><p>文献数量：{len(self.references)}</p>"
                if len(self.references) > 0:
                    refs_content += "<p>部分引用文献示例：</p><ul>"
                    for ref in self.references[:5]:  # 只显示前5条
                        refs_content += f"<li>{ref}</li>"
                    if len(self.references) > 5:
                        refs_content += f"<li>...</li>"
                    refs_content += "</ul>"
            else:
                refs_content = f"<p>Reference Analysis:</p><p>Number of references: {len(self.references)}</p>"
                if len(self.references) > 0:
                    refs_content += "<p>Sample references:</p><ul>"
                    for ref in self.references[:5]:  # 只显示前5条
                        refs_content += f"<li>{ref}</li>"
                    if len(self.references) > 5:
                        refs_content += f"<li>...</li>"
                    refs_content += "</ul>"
                    
            analysis_sections.append({
                'title': '参考文献分析' if language == 'zh' else 'Reference Analysis',
                'content': refs_content
            })
        
        return analysis_sections
        
    def close(self):
        """关闭文档"""
        if self.doc:
            self.doc.close()