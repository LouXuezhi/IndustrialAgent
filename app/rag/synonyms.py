"""
同义词库模块：提供查询扩展功能，通过同义词提升检索召回率。
"""
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SynonymDict:
    """
    同义词词典：管理同义词映射，支持查询扩展。
    
    支持多种同义词来源：
    1. 自定义词典（JSON 文件）
    2. LLM 生成（可选）
    3. 内置常用同义词（可选）
    """
    
    def __init__(self, dict_path: str | Path | None = None):
        """
        初始化同义词词典。
        
        Args:
            dict_path: 同义词词典文件路径（JSON 格式），如果为 None 则使用内置词典
        """
        self.synonyms: dict[str, list[str]] = {}
        self._load_dict(dict_path)
    
    def _load_dict(self, dict_path: str | Path | None):
        """加载同义词词典。"""
        if dict_path:
            try:
                path = Path(dict_path)
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 支持两种格式：
                        # 1. {"词": ["同义词1", "同义词2"]}
                        # 2. [{"word": "词", "synonyms": ["同义词1", "同义词2"]}]
                        if isinstance(data, dict):
                            self.synonyms = {k.lower(): [s.lower() for s in v] for k, v in data.items()}
                        elif isinstance(data, list):
                            for item in data:
                                word = item.get('word', '').lower()
                                syns = [s.lower() for s in item.get('synonyms', [])]
                                if word:
                                    self.synonyms[word] = syns
                    logger.info(f"✅ 加载同义词词典: {len(self.synonyms)} 个词条")
                else:
                    logger.warning(f"⚠️ 同义词词典文件不存在: {dict_path}，使用内置词典")
                    self._load_builtin_dict()
            except Exception as e:
                logger.error(f"❌ 加载同义词词典失败: {e}，使用内置词典")
                self._load_builtin_dict()
        else:
            self._load_builtin_dict()
    
    def _load_builtin_dict(self):
        """加载内置常用同义词（工业领域相关）。"""
        # 内置一些常用的工业领域同义词
        builtin_synonyms = {
            "设备": ["装置", "机器", "器械", "设施"],
            "维护": ["保养", "检修", "维修", "养护"],
            "故障": ["问题", "异常", "错误", "缺陷"],
            "检查": ["检测", "检验", "查看", "审查"],
            "操作": ["运行", "使用", "执行", "操控"],
            "安全": ["防护", "保护", "保障"],
            "温度": ["热度", "气温"],
            "压力": ["压强", "应力"],
            "系统": ["体系", "机制"],
            "流程": ["过程", "工序", "步骤"],
            "生产": ["制造", "加工"],
            "质量": ["品质", "质地"],
            "效率": ["效能", "性能"],
            "优化": ["改进", "提升", "改善"],
            "分析": ["解析", "研究", "评估"],
        }
        self.synonyms = {k.lower(): [s.lower() for s in v] for k, v in builtin_synonyms.items()}
        logger.info(f"✅ 加载内置同义词词典: {len(self.synonyms)} 个词条")
    
    def get_synonyms(self, word: str) -> list[str]:
        """
        获取指定词的同义词。
        
        Args:
            word: 查询词
        
        Returns:
            同义词列表（不包含原词）
        """
        word_lower = word.lower().strip()
        return self.synonyms.get(word_lower, [])
    
    def expand_query(self, query: str, max_expansions: int = 3) -> str:
        """
        扩展查询，添加同义词。
        
        Args:
            query: 原始查询
            max_expansions: 每个词最多扩展的同义词数量
        
        Returns:
            扩展后的查询（原查询 + 同义词）
        """
        import re
        expanded_terms = set()
        found_synonyms = []
        
        # 方法1: 检查查询中是否包含词典中的词（支持中文）
        query_lower = query.lower()
        for word, synonyms in self.synonyms.items():
            # 检查查询中是否包含这个词
            if word in query_lower:
                # 添加前 max_expansions 个同义词
                for syn in synonyms[:max_expansions]:
                    if syn not in query_lower:  # 避免添加已存在的词
                        found_synonyms.append(syn)
        
        # 方法2: 分词匹配（英文单词）
        words = re.findall(r'\b\w+\b', query)
        for word in words:
            word_lower = word.lower()
            synonyms = self.get_synonyms(word_lower)
            for syn in synonyms[:max_expansions]:
                if syn not in query_lower:
                    found_synonyms.append(syn)
        
        # 如果找到同义词，添加到查询中
        if found_synonyms:
            expanded_query = query + " " + " ".join(found_synonyms)
            logger.debug(f"查询扩展: '{query}' → '{expanded_query}'")
            return expanded_query
        
        return query
    
    def add_synonym(self, word: str, synonym: str):
        """添加同义词映射。"""
        word_lower = word.lower().strip()
        syn_lower = synonym.lower().strip()
        
        if word_lower not in self.synonyms:
            self.synonyms[word_lower] = []
        
        if syn_lower not in self.synonyms[word_lower] and syn_lower != word_lower:
            self.synonyms[word_lower].append(syn_lower)
            logger.debug(f"添加同义词: {word} → {synonym}")
    
    def save_dict(self, path: str | Path):
        """保存同义词词典到文件。"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.synonyms, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 保存同义词词典到: {path}")
        except Exception as e:
            logger.error(f"❌ 保存同义词词典失败: {e}")


class LLMQueryExpander:
    """
    使用 LLM 生成查询扩展词（同义词和相关词）。
    
    当同义词词典中没有匹配时，可以使用 LLM 生成扩展词。
    """
    
    def __init__(self, llm: Any | None = None):
        """
        初始化 LLM 查询扩展器。
        
        Args:
            llm: LangChain LLM 实例，如果为 None 则禁用 LLM 扩展
        """
        self.llm = llm
        self.enable = llm is not None
    
    async def expand(self, query: str, max_terms: int = 5) -> list[str]:
        """
        使用 LLM 生成查询扩展词。
        
        Args:
            query: 原始查询
            max_terms: 最多生成的扩展词数量
        
        Returns:
            扩展词列表
        """
        if not self.enable or not self.llm:
            return []
        
        try:
            prompt = f"""基于以下查询，生成 {max_terms} 个相关的同义词或相关词。
查询：{query}

要求：
1. 只返回同义词或相关词，用逗号分隔
2. 不要包含原查询词
3. 只返回词，不要解释

扩展词："""
            
            from langchain_core.output_parsers import StrOutputParser
            from langchain_core.prompts import ChatPromptTemplate
            
            prompt_template = ChatPromptTemplate.from_template(prompt)
            chain = prompt_template | self.llm | StrOutputParser()
            
            result = await chain.ainvoke({})
            
            # 解析结果
            expanded_terms = [
                term.strip() 
                for term in result.split(',') 
                if term.strip() and term.strip() != query
            ]
            
            logger.debug(f"LLM 查询扩展: '{query}' → {expanded_terms}")
            return expanded_terms[:max_terms]
            
        except Exception as e:
            logger.error(f"LLM 查询扩展失败: {e}", exc_info=True)
            return []


class QueryExpander:
    """
    查询扩展器：结合同义词词典和 LLM 进行查询扩展。
    """
    
    def __init__(
        self,
        synonym_dict: SynonymDict | None = None,
        llm_expander: LLMQueryExpander | None = None,
        enable: bool = True
    ):
        """
        初始化查询扩展器。
        
        Args:
            synonym_dict: 同义词词典实例
            llm_expander: LLM 扩展器实例
            enable: 是否启用查询扩展
        """
        self.enable = enable
        self.synonym_dict = synonym_dict or SynonymDict()
        self.llm_expander = llm_expander
    
    def expand(self, query: str, use_llm: bool = False) -> str:
        """
        扩展查询。
        
        Args:
            query: 原始查询
            use_llm: 是否使用 LLM 扩展（默认 False，仅使用词典）
        
        Returns:
            扩展后的查询
        """
        if not self.enable:
            return query
        
        # 首先使用同义词词典扩展
        expanded = self.synonym_dict.expand_query(query)
        
        # 如果需要，使用 LLM 进一步扩展
        if use_llm and self.llm_expander and self.llm_expander.enable:
            # 注意：LLM 扩展是异步的，这里先返回词典扩展的结果
            # 如果需要 LLM 扩展，应该在异步上下文中调用 expand_async
            pass
        
        return expanded
    
    async def expand_async(self, query: str, use_llm: bool = False) -> str:
        """
        异步扩展查询（支持 LLM 扩展）。
        
        Args:
            query: 原始查询
            use_llm: 是否使用 LLM 扩展
        
        Returns:
            扩展后的查询
        """
        if not self.enable:
            return query
        
        # 使用同义词词典扩展
        expanded = self.synonym_dict.expand_query(query)
        
        # 如果需要，使用 LLM 进一步扩展
        if use_llm and self.llm_expander and self.llm_expander.enable:
            llm_terms = await self.llm_expander.expand(query)
            if llm_terms:
                expanded = expanded + " " + " ".join(llm_terms)
                logger.debug(f"LLM 扩展后: '{expanded}'")
        
        return expanded

