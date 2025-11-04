from typing import Dict, List, Any
import json
from datetime import datetime
from collections import Counter, defaultdict
import re
from app.core.config import settings
import google.generativeai as genai
from bson import ObjectId


class SummarizerService:
    """Service for generating summaries and future suggestions for exam papers"""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    def analyze_paper_patterns(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in approved papers to identify trends"""

        if not papers:
            return {"error": "No papers available for analysis"}

        # Initialize counters and analyzers
        subject_analysis = Counter()
        department_analysis = Counter()
        blooms_analysis = Counter()
        question_type_analysis = Counter()
        difficulty_analysis = Counter()
        marks_distribution = defaultdict(list)
        question_source_analysis = Counter()

        # Analyze each paper
        for paper in papers:
            subject_analysis[paper.get('subject', 'Unknown')] += 1
            department_analysis[paper.get('department', 'Unknown')] += 1

            # Analyze Bloom's taxonomy distribution
            for level, count in paper.get('blooms_distribution', {}).items():
                blooms_analysis[level] += count

            # Analyze question types (from questions array)
            questions = paper.get('questions', [])
            for question in questions:
                question_type_analysis[question.get('question_type', 'Unknown')] += 1
                difficulty_analysis[question.get('difficulty', 'Unknown')] += 1
                marks_distribution[question.get('question_type', 'Unknown')].append(question.get('marks', 0))
                question_source_analysis[question.get('source', 'Unknown')] += 1

        # Calculate averages and trends
        total_papers = len(papers)

        # Most common subjects and departments
        top_subjects = subject_analysis.most_common(5)
        top_departments = department_analysis.most_common(5)

        # Question type distribution
        question_type_dist = {
            qtype: count/total_papers for qtype, count in question_type_analysis.items()
        }

        # Bloom's taxonomy analysis
        blooms_dist = {
            level: count/total_papers for level, count in blooms_analysis.items()
        }

        # Marks analysis per question type
        marks_analysis = {}
        for qtype, marks_list in marks_distribution.items():
            if marks_list:
                marks_analysis[qtype] = {
                    'average': sum(marks_list) / len(marks_list),
                    'min': min(marks_list),
                    'max': max(marks_list),
                    'common': Counter(marks_list).most_common(1)[0][0]
                }

        # Source analysis
        source_dist = {
            source: count/total_papers for source, count in question_source_analysis.items()
        }

        return {
            'total_papers': total_papers,
            'subject_trends': dict(top_subjects),
            'department_trends': dict(top_departments),
            'question_type_distribution': question_type_dist,
            'blooms_distribution': blooms_dist,
            'marks_analysis': marks_analysis,
            'source_distribution': source_dist,
            'difficulty_distribution': dict(difficulty_analysis)
        }

    def generate_future_suggestions(self, paper: Dict[str, Any], patterns: Dict[str, Any]) -> str:
        """Generate specific suggestions for future paper generation based on current paper"""

        # Extract paper characteristics
        subject = paper.get('subject', 'Unknown')
        department = paper.get('department', 'Unknown')
        total_marks = paper.get('total_marks', 0)
        questions = paper.get('questions', [])

        # Analyze current paper
        current_blooms = paper.get('blooms_distribution', {})
        current_question_types = Counter(q.get('question_type', 'Unknown') for q in questions)

        # Generate suggestions using AI
        prompt = f"""
        You are an expert educational consultant analyzing an exam paper to provide future improvement suggestions.

        CURRENT PAPER ANALYSIS:
        - Subject: {subject}
        - Department: {department}
        - Total Marks: {total_marks}
        - Number of Questions: {len(questions)}
        - Bloom's Taxonomy Distribution: {current_blooms}
        - Question Types: {dict(current_question_types)}

        RECENT TRENDS FROM APPROVED PAPERS:
        - Popular Subjects: {patterns.get('subject_trends', {})}
        - Popular Departments: {patterns.get('department_trends', {})}
        - Question Type Distribution: {patterns.get('question_type_distribution', {})}
        - Bloom's Distribution: {patterns.get('blooms_distribution', {})}
        - Marks Analysis: {patterns.get('marks_analysis', {})}

        Please provide specific, actionable suggestions for future paper generation including:
        1. Question type recommendations
        2. Bloom's taxonomy balance suggestions
        3. Difficulty level recommendations
        4. Marks distribution improvements
        5. Subject/department trends to follow
        6. Any other academic improvements

        Format your response as bullet points with clear, specific recommendations.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating suggestions: {str(e)}"

    def generate_dashboard_summary(self, papers: List[Dict[str, Any]], resources: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive summary of the teacher's dashboard"""

        if not papers and not resources:
            return "No data available for dashboard summary."

        # Calculate statistics
        total_papers = len(papers)
        approved_papers = len([p for p in papers if p.get('status') == 'approved'])
        draft_papers = len([p for p in papers if p.get('status') == 'draft'])
        total_resources = len(resources)

        # Subject diversity
        subjects = set(p.get('subject', 'Unknown') for p in papers)
        departments = set(p.get('department', 'Unknown') for p in papers)

        # Recent activity
        recent_papers = sorted(papers, key=lambda x: x.get('created_at', ''), reverse=True)[:5]

        # Generate summary using AI
        prompt = f"""
        You are creating a comprehensive dashboard summary for a teacher using an AI exam paper generator.

        DASHBOARD STATISTICS:
        - Total Papers Generated: {total_papers}
        - Approved Papers: {approved_papers}
        - Draft Papers: {draft_papers}
        - Total Resources Uploaded: {total_resources}
        - Unique Subjects: {len(subjects)}
        - Unique Departments: {len(departments)}

        RECENT PAPERS:
        {[
            f"- {p.get('subject', 'Unknown')} ({p.get('department', 'Unknown')}) - {p.get('total_marks', 0)} marks - Status: {p.get('status', 'Unknown')}"
            for p in recent_papers
        ]}

        Please provide a concise, professional summary of the teacher's activity and suggestions for improvement.
        Focus on:
        1. Overall productivity and paper generation trends
        2. Subject/department diversity
        3. Approval rates and quality indicators
        4. Resource utilization
        5. Specific recommendations for better exam paper generation

        Keep the summary under 300 words and make it encouraging and actionable.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating dashboard summary: {str(e)}"

    def get_paper_suggestions(self, paper_id: str, teacher_id: str, db) -> Dict[str, Any]:
        """Get suggestions for a specific paper based on historical patterns"""

        # Get the current paper
        paper = db.papers.find_one({"_id": ObjectId(paper_id), "teacher_id": teacher_id})
        if not paper:
            return {"error": "Paper not found"}

        try:
            # Get all approved papers for pattern analysis
            approved_papers = list(db.papers.find({
                "teacher_id": teacher_id,
                "status": "approved",
                "_id": {"$ne": ObjectId(paper_id)}  # Exclude current paper
            }))
        except Exception as e:
            # Handle case where collections don't exist yet
            print(f"Database collections may not exist yet: {e}")
            approved_papers = []

        # Analyze patterns
        patterns = self.analyze_paper_patterns(approved_papers)

        # Generate suggestions
        suggestions = self.generate_future_suggestions(paper, patterns)

        return {
            "paper_id": paper_id,
            "suggestions": suggestions,
            "patterns": patterns,
            "generated_at": datetime.utcnow()
        }

    def get_dashboard_summary_data(self, teacher_id: str, db) -> Dict[str, Any]:
        """Get comprehensive dashboard summary data"""

        try:
            # Get papers and resources
            papers = list(db.papers.find({"teacher_id": teacher_id}))
            resources = list(db.resources.find({"teacher_id": teacher_id}))
        except Exception as e:
            # Handle case where collections don't exist yet
            print(f"Database collections may not exist yet: {e}")
            papers = []
            resources = []

        # Generate summary
        summary = self.generate_dashboard_summary(papers, resources)

        # Get pattern analysis
        patterns = self.analyze_paper_patterns(papers)

        return {
            "summary": summary,
            "patterns": patterns,
            "statistics": {
                "total_papers": len(papers),
                "approved_papers": len([p for p in papers if p.get('status') == 'approved']),
                "draft_papers": len([p for p in papers if p.get('status') == 'draft']),
                "total_resources": len(resources),
                "unique_subjects": len(set(p.get('subject', 'Unknown') for p in papers)),
                "unique_departments": len(set(p.get('department', 'Unknown') for p in papers))
            },
            "generated_at": datetime.utcnow()
        }
