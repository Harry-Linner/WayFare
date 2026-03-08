"""
生成示例PDF文件的脚本

使用reportlab库生成包含文本内容的PDF文件，用于测试文档解析功能。
"""

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pathlib import Path
    
    def generate_simple_pdf():
        """生成简单的测试PDF"""
        output_path = Path(__file__).parent / "simple_test.pdf"
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # 容器
        story = []
        
        # 样式
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # 标题
        story.append(Paragraph("Simple Test Document", title_style))
        story.append(Spacer(1, 12))
        
        # 第一节
        story.append(Paragraph("Section 1: Introduction", heading_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "This is a simple test PDF document created for testing the document parser. "
            "It contains multiple sections with text content.",
            normal_style
        ))
        story.append(Spacer(1, 12))
        
        # 第二节
        story.append(Paragraph("Section 2: Content", heading_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "This section contains some sample content. The document parser should be able to "
            "extract this text along with page numbers and bounding box information.",
            normal_style
        ))
        story.append(Spacer(1, 12))
        
        # 第三节
        story.append(Paragraph("Section 3: Conclusion", heading_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "This is the conclusion of the test document. It should be parsed correctly.",
            normal_style
        ))
        
        # 构建PDF
        doc.build(story)
        print(f"Generated: {output_path}")
    
    def generate_complex_pdf():
        """生成包含中文内容的复杂PDF"""
        output_path = Path(__file__).parent / "sample_learning_material.pdf"
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # 容器
        story = []
        
        # 样式
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # 标题
        story.append(Paragraph("Learning Material: Python Basics", title_style))
        story.append(Spacer(1, 20))
        
        # 第一节
        story.append(Paragraph("Chapter 1: Variables and Data Types", heading_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "In Python, variables are used to store data values. Unlike other programming languages, "
            "Python has no command for declaring a variable. A variable is created the moment you first "
            "assign a value to it. Python has several built-in data types including integers, floats, "
            "strings, and booleans.",
            normal_style
        ))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph(
            "Example: x = 5 creates an integer variable. y = 'Hello' creates a string variable. "
            "Variables can change type after they have been set.",
            normal_style
        ))
        story.append(Spacer(1, 20))
        
        # 第二节
        story.append(Paragraph("Chapter 2: Control Flow", heading_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "Control flow statements allow you to control the execution of your code based on conditions. "
            "The most common control flow statements in Python are if, elif, and else. These statements "
            "allow you to execute different blocks of code depending on whether certain conditions are true or false.",
            normal_style
        ))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph(
            "Loops are another important control flow mechanism. Python provides two types of loops: "
            "for loops and while loops. For loops are used to iterate over a sequence, while while loops "
            "continue executing as long as a condition is true.",
            normal_style
        ))
        story.append(Spacer(1, 20))
        
        # 第三节
        story.append(Paragraph("Chapter 3: Functions", heading_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "Functions are reusable blocks of code that perform a specific task. In Python, you define "
            "a function using the def keyword, followed by the function name and parentheses. Functions "
            "can accept parameters and return values.",
            normal_style
        ))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph(
            "Functions help organize your code and make it more modular and maintainable. They allow you "
            "to avoid repeating the same code multiple times. Good function design is a key aspect of "
            "writing clean, professional Python code.",
            normal_style
        ))
        story.append(Spacer(1, 20))
        
        # 第四节
        story.append(Paragraph("Chapter 4: Data Structures", heading_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "Python provides several built-in data structures including lists, tuples, dictionaries, and sets. "
            "Lists are ordered, mutable collections. Tuples are ordered, immutable collections. Dictionaries "
            "store key-value pairs. Sets are unordered collections of unique elements.",
            normal_style
        ))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph(
            "Choosing the right data structure for your task is important for writing efficient code. "
            "Each data structure has its own strengths and use cases. Understanding when to use each one "
            "is a fundamental skill in Python programming.",
            normal_style
        ))
        
        # 构建PDF
        doc.build(story)
        print(f"Generated: {output_path}")
    
    if __name__ == "__main__":
        print("Generating sample PDF files...")
        generate_simple_pdf()
        generate_complex_pdf()
        print("Done!")

except ImportError:
    print("Warning: reportlab not installed. Cannot generate PDF files.")
    print("Install with: pip install reportlab")
    print("\nYou can still run tests without PDF files, or manually add PDF files to this directory.")
