# PDF 转文本实现说明

## 项目中的实现

项目使用 **`pypdf`** 库来提取 PDF 文本，这是一个纯 Python 的 PDF 处理库。

### 代码位置

`app/rag/ingestion.py` 中的 `_extract_text_from_file()` 函数：

```python
def _extract_text_from_file(path: Path) -> str:
    """Extract text from various file formats."""
    suffix = path.suffix.lower()
    
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            return "\n".join(page.extract_text() for page in reader.pages)
        except Exception:
            return ""
```

## 实现原理

### 1. 使用 pypdf 库

```python
from pypdf import PdfReader

# 创建 PDF 读取器
reader = PdfReader("document.pdf")

# 遍历每一页
for page in reader.pages:
    # 提取页面文本
    text = page.extract_text()
    print(text)
```

### 2. 逐页提取

```python
# 将所有页面的文本合并
text = "\n".join(page.extract_text() for page in reader.pages)
```

### 3. 错误处理

```python
try:
    # PDF 提取逻辑
    text = extract_pdf_text(path)
except Exception:
    return ""  # 失败时返回空字符串，不影响其他文件处理
```

## 详细步骤

### 步骤 1：读取 PDF 文件

```python
from pypdf import PdfReader

# 打开 PDF 文件
reader = PdfReader("manual.pdf")

# 获取页数
num_pages = len(reader.pages)
print(f"PDF 有 {num_pages} 页")
```

### 步骤 2：提取每一页的文本

```python
# 方法 1：逐页提取
all_text = []
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    all_text.append(f"=== 第 {i+1} 页 ===\n{text}")

result = "\n".join(all_text)
```

```python
# 方法 2：列表推导式（项目中使用的方法）
text = "\n".join(page.extract_text() for page in reader.pages)
```

### 步骤 3：处理特殊情况

```python
# 处理空页面
text = page.extract_text()
if not text.strip():
    continue  # 跳过空页面

# 处理编码问题
text = text.encode('utf-8', errors='ignore').decode('utf-8')
```

## 完整示例

### 基础示例

```python
from pathlib import Path
from pypdf import PdfReader

def extract_pdf_text(pdf_path: Path) -> str:
    """提取 PDF 文本"""
    reader = PdfReader(pdf_path)
    
    # 提取所有页面的文本
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text.strip():  # 跳过空页面
            pages_text.append(text)
    
    return "\n".join(pages_text)

# 使用
pdf_file = Path("manual.pdf")
text = extract_pdf_text(pdf_file)
print(text)
```

### 项目中的实际使用

```python
# 在向量化流程中
def _extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            # 逐页提取并合并
            return "\n".join(page.extract_text() for page in reader.pages)
        except Exception:
            return ""  # 失败返回空字符串

# 调用
text = _extract_text_from_file(Path("document.pdf"))
if text.strip():
    # 继续处理文本（分块、向量化等）
    chunks = chunk_text(text, chunk_size=800)
```

## 支持的 PDF 类型

### ✅ 支持的格式

- **文本型 PDF**：包含可提取文本的 PDF（最常见）
- **扫描型 PDF**：如果包含文本层，也可以提取
- **加密 PDF**：如果知道密码，可以解密后提取

### ⚠️ 限制

- **纯图片 PDF**：如果 PDF 是扫描图片，没有文本层，无法提取文本
  - 解决方案：需要使用 OCR（光学字符识别）技术
- **复杂布局**：表格、多栏布局可能提取不准确
- **特殊字体**：某些特殊字体可能无法正确识别

## 其他 PDF 处理库对比

### 1. pypdf（项目使用）

**优点**：
- ✅ 纯 Python，无需外部依赖
- ✅ 轻量级，安装简单
- ✅ 支持基本文本提取
- ✅ 跨平台

**缺点**：
- ❌ 不支持 OCR（图片转文字）
- ❌ 复杂布局提取可能不准确

### 2. PyMuPDF (fitz)

```python
import fitz  # PyMuPDF

doc = fitz.open("document.pdf")
text = ""
for page in doc:
    text += page.get_text()
```

**优点**：
- ✅ 速度快
- ✅ 支持图片提取
- ✅ 支持 OCR（需额外配置）

**缺点**：
- ❌ 需要系统依赖（C 库）

### 3. pdfplumber

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    text = ""
    for page in pdf.pages:
        text += page.extract_text()
```

**优点**：
- ✅ 表格提取能力强
- ✅ 布局分析准确

**缺点**：
- ❌ 速度较慢
- ❌ 依赖较多

## OCR 处理（图片 PDF）

如果 PDF 是扫描图片，需要使用 OCR：

### 使用 Tesseract OCR

```python
from pdf2image import convert_from_path
import pytesseract

def extract_text_from_scanned_pdf(pdf_path: Path) -> str:
    """从扫描型 PDF 提取文本（OCR）"""
    # 将 PDF 转为图片
    images = convert_from_path(pdf_path)
    
    # OCR 识别每张图片
    text_parts = []
    for img in images:
        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        text_parts.append(text)
    
    return "\n".join(text_parts)
```

### 使用 EasyOCR

```python
import easyocr

reader = easyocr.Reader(['ch_sim', 'en'])

def extract_text_with_easyocr(pdf_path: Path) -> str:
    images = convert_from_path(pdf_path)
    text_parts = []
    for img in images:
        results = reader.readtext(img)
        text = "\n".join([result[1] for result in results])
        text_parts.append(text)
    return "\n".join(text_parts)
```

## 项目中的完整流程

```
用户上传 PDF
    ↓
保存到磁盘 (data/uploads/{uuid}_file.pdf)
    ↓
调用 _extract_text_from_file()
    ↓
使用 pypdf.PdfReader 读取
    ↓
逐页提取文本: page.extract_text()
    ↓
合并所有页面文本: "\n".join(...)
    ↓
返回文本字符串
    ↓
文本分块 (chunk_size=800)
    ↓
生成向量并存储
```

## 依赖安装

项目已在 `pyproject.toml` 中配置：

```toml
dependencies = [
    "pypdf>=4.0.0",
    # ...
]
```

安装：
```bash
uv sync
# 或
pip install pypdf>=4.0.0
```

## 总结

- **当前实现**：使用 `pypdf` 库，适合文本型 PDF
- **提取方式**：逐页提取文本，用换行符连接
- **错误处理**：失败时返回空字符串，不影响其他文件
- **未来扩展**：如需支持扫描 PDF，可集成 OCR 库（如 Tesseract、EasyOCR）

