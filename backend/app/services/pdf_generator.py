from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io
from typing import List, Dict


class PDFGenerator:
    """Generate exam paper and answer key PDFs"""
    
    @staticmethod
    def generate_question_paper(
        subject: str,
        department: str,
        section: str,
        year: int,
        exam_date: datetime,
        total_marks: int,
        questions: List[Dict]
    ) -> bytes:
        """Generate question paper PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            alignment=TA_CENTER
        )
        
        question_style = ParagraphStyle(
            'Question',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            leftIndent=20
        )
        
        option_style = ParagraphStyle(
            'Option',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leftIndent=40
        )
        
        # Header
        story.append(Paragraph("UNIVERSITY EXAMINATION", title_style))
        story.append(Paragraph(f"Department of {department}", subtitle_style))
        story.append(Paragraph(f"{subject}", subtitle_style))
        if section:
            story.append(Paragraph(f"Section: {section}", subtitle_style))
        if year:
            story.append(Paragraph(f"Year: {year}", subtitle_style))
        if exam_date:
            story.append(Paragraph(f"Date: {exam_date.strftime('%B %d, %Y')}", subtitle_style))
        story.append(Paragraph(f"Total Marks: {total_marks}", subtitle_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Instructions
        story.append(Paragraph("<b>Instructions:</b>", styles['Heading3']))
        instructions = [
            "Answer all questions.",
            "Each question carries marks as indicated.",
            "Write clearly and legibly.",
            "Use of calculators is permitted unless otherwise stated."
        ]
        for inst in instructions:
            story.append(Paragraph(f"• {inst}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Questions
        story.append(Paragraph("<b>QUESTIONS</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        for idx, q in enumerate(questions, 1):
            # Question number and marks
            q_header = f"<b>Q{idx}.</b> [{q['marks']} marks] [{q['blooms_level']}] [{q['question_type']}]"
            story.append(Paragraph(q_header, question_style))
            
            # Question text - handle MCQ formatting
            question_text = q['question_text']
            
            # Check if it's an MCQ with options
            if q.get('question_type') == 'MCQ' and '\n' in question_text:
                # Split question and options
                lines = question_text.split('\n')
                
                # First line is the question
                story.append(Paragraph(lines[0], question_style))
                story.append(Spacer(1, 0.05*inch))
                
                # Remaining lines are options
                for line in lines[1:]:
                    if line.strip():  # Skip empty lines
                        story.append(Paragraph(line, option_style))
            else:
                # Regular question - replace \n with <br/> for HTML rendering
                formatted_text = question_text.replace('\n', '<br/>')
                story.append(Paragraph(formatted_text, question_style))
            
            story.append(Spacer(1, 0.15*inch))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def generate_answer_key(
        subject: str,
        department: str,
        questions: List[Dict]
    ) -> bytes:
        """Generate answer key PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        answer_style = ParagraphStyle(
            'Answer',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=10,
            leftIndent=20,
            textColor=colors.HexColor('#0066cc')
        )
        
        question_text_style = ParagraphStyle(
            'QuestionText',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leftIndent=20
        )
        
        option_style = ParagraphStyle(
            'Option',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=3,
            leftIndent=40
        )
        
        # Header
        story.append(Paragraph("ANSWER KEY", title_style))
        story.append(Paragraph(f"Department of {department}", styles['Normal']))
        story.append(Paragraph(f"{subject}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Answers
        for idx, q in enumerate(questions, 1):
            # Question header
            story.append(Paragraph(f"<b>Q{idx}.</b> [{q['marks']} marks] [{q['blooms_level']}] [{q['question_type']}]", styles['Heading4']))
            
            # Question text - handle MCQ formatting
            question_text = q['question_text']
            
            if q.get('question_type') == 'MCQ' and '\n' in question_text:
                # Split question and options
                lines = question_text.split('\n')
                
                # First line is the question
                story.append(Paragraph(f"<b>Question:</b> {lines[0]}", question_text_style))
                story.append(Spacer(1, 0.05*inch))
                
                # Options
                for line in lines[1:]:
                    if line.strip():
                        story.append(Paragraph(line, option_style))
            else:
                # Regular question
                formatted_text = question_text.replace('\n', '<br/>')
                story.append(Paragraph(f"<b>Question:</b> {formatted_text}", question_text_style))
            
            story.append(Spacer(1, 0.05*inch))
            
            # Answer
            answer_text = q['answer_key'].replace('\n', '<br/>')
            story.append(Paragraph(f"<b>Answer:</b> {answer_text}", answer_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
