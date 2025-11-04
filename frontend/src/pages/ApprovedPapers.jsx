import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  Trash2,
  Edit,
  Download,
  Eye,
  Filter,
  ArrowLeft,
  Sparkles,
} from "lucide-react";
import Navbar from "../components/Navbar";
import { teacherAPI } from "../services/api";
import toast from "react-hot-toast";

export default function ApprovedPapers() {
  const navigate = useNavigate();
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchSubject, setSearchSubject] = useState("");
  const [searchDepartment, setSearchDepartment] = useState("");
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [availableSubjects, setAvailableSubjects] = useState([]);
  const [selectedSubjectForSummary, setSelectedSubjectForSummary] =
    useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [customPrompt, setCustomPrompt] = useState("");
  const [showCustomPrompt, setShowCustomPrompt] = useState(false);

  useEffect(() => {
    fetchApprovedPapers();
    fetchAvailableSubjects();
  }, []);

  const fetchApprovedPapers = async (subject = "", department = "") => {
    setLoading(true);
    try {
      const response = await teacherAPI.searchApprovedPapers(
        subject,
        department
      );
      if (!response.data) {
        throw new Error("No data received from server");
      }
      setPapers(Array.isArray(response.data) ? response.data : []);
      if (Array.isArray(response.data) && response.data.length === 0) {
        toast("No approved papers found", {
          icon: "📝",
        });
      }
    } catch (error) {
      console.error("Error fetching approved papers:", error);
      toast.error(
        error.response?.data?.detail || "Failed to fetch approved papers"
      );
      setPapers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchApprovedPapers(searchSubject, searchDepartment);
  };

  const handleClearFilters = () => {
    setSearchSubject("");
    setSearchDepartment("");
    fetchApprovedPapers("", "");
  };

  const downloadPDF = async (fileId, filename) => {
    try {
      const response = await teacherAPI.downloadPDF(fileId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error("Failed to download PDF");
    }
  };

  const handleViewDetails = async (paperId) => {
    try {
      const response = await teacherAPI.getApprovedPaperDetails(paperId);
      setSelectedPaper(response.data);
      setShowDetails(true);
    } catch (error) {
      toast.error("Failed to fetch paper details");
    }
  };

  const handleDelete = async (paperId) => {
    if (
      !confirm(
        "Are you sure you want to delete this approved paper? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      await teacherAPI.deleteApprovedPaper(paperId);
      toast.success("Paper deleted successfully");
      fetchApprovedPapers(searchSubject, searchDepartment);
    } catch (error) {
      toast.error("Failed to delete paper");
    }
  };

  const handleEdit = async (paper) => {
    try {
      // Create a copy of the approved paper for editing
      const response = await teacherAPI.createPaperCopyForEdit(paper.id);
      toast.success("Paper loaded for editing!");

      // Navigate to edit page with the copy
      navigate(`/edit-paper/${response.data.paper_id}`);
    } catch (error) {
      toast.error("Failed to load paper for editing");
    }
  };

  // Fetch available subjects for summary
  const fetchAvailableSubjects = async () => {
    try {
      const response = await teacherAPI.getApprovedPapersSubjects();
      setAvailableSubjects(response.data.subjects);
    } catch (error) {
      toast.error("Failed to fetch subjects");
    }
  };

  // Get summary for all papers or specific subject with optional custom prompt
  const handleGetSummary = async (subject = null, paperId = null) => {
    setSummaryLoading(true);
    try {
      const response = await teacherAPI.getApprovedPapersSummary(
        subject,
        customPrompt,
        paperId
      );
      setSummary(response.data);
      setShowSummary(true);
      setShowCustomPrompt(false); // Hide the prompt input after getting results
    } catch (error) {
      toast.error("Failed to generate summary");
    } finally {
      setSummaryLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <button
          onClick={() => navigate("/teacher")}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Back to Dashboard
        </button>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Approved Papers Repository
              </h1>
              <p className="mt-2 text-gray-600">
                Search, view, edit, and manage approved exam papers
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowCustomPrompt(true)}
                className="btn-secondary flex items-center space-x-2"
              >
                <Eye className="h-5 w-5" />
                <span>Custom Analysis</span>
              </button>
              <button
                onClick={() => handleGetSummary()}
                className="btn-primary flex items-center space-x-2"
                disabled={summaryLoading}
              >
                <Sparkles className="h-5 w-5" />
                <span>{summaryLoading ? "Analyzing..." : "View Summary"}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Search Filters */}
        <div className="card mb-6">
          <div className="flex items-center space-x-2 mb-4">
            <Filter className="h-5 w-5 text-gray-500" />
            <h2 className="text-lg font-semibold text-gray-900">
              Search Filters
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Subject
              </label>
              <input
                type="text"
                value={searchSubject}
                onChange={(e) => setSearchSubject(e.target.value)}
                placeholder="e.g., Data Structures"
                className="input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Department
              </label>
              <input
                type="text"
                value={searchDepartment}
                onChange={(e) => setSearchDepartment(e.target.value)}
                placeholder="e.g., Computer Science"
                className="input"
              />
            </div>

            <div className="flex items-end space-x-2">
              <button
                onClick={handleSearch}
                className="btn-primary flex items-center space-x-2 flex-1"
              >
                <Search className="h-4 w-4" />
                <span>Search</span>
              </button>
              <button onClick={handleClearFilters} className="btn-secondary">
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Papers List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading approved papers...</p>
          </div>
        ) : papers.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-600">No approved papers found</p>
            {(searchSubject || searchDepartment) && (
              <button
                onClick={handleClearFilters}
                className="btn-secondary mt-4"
              >
                Clear Filters
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {papers.map((paper) => (
              <div
                key={paper.id}
                className="card hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-gray-900">
                      {paper.subject}
                    </h3>
                    <p className="text-gray-600 mt-1">{paper.department}</p>

                    <div className="mt-3 flex flex-wrap gap-3 text-sm text-gray-600">
                      <span className="flex items-center">
                        <strong className="mr-1">Total Marks:</strong>{" "}
                        {paper.total_marks}
                      </span>
                      <span className="flex items-center">
                        <strong className="mr-1">Questions:</strong>{" "}
                        {paper.question_count}
                      </span>
                      {paper.section && (
                        <span className="flex items-center">
                          <strong className="mr-1">Section:</strong>{" "}
                          {paper.section}
                        </span>
                      )}
                      {paper.year && (
                        <span className="flex items-center">
                          <strong className="mr-1">Year:</strong> {paper.year}
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-gray-500 mt-2">
                      Created: {new Date(paper.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex flex-col space-y-2 ml-4">
                    <button
                      onClick={() => handleViewDetails(paper.id)}
                      className="btn-secondary flex items-center space-x-2"
                    >
                      <Eye className="h-4 w-4" />
                      <span>View</span>
                    </button>

                    <button
                      onClick={() => handleEdit(paper)}
                      className="btn-primary flex items-center space-x-2"
                    >
                      <Edit className="h-4 w-4" />
                      <span>Edit</span>
                    </button>

                    {paper.question_paper_pdf && (
                      <button
                        onClick={() =>
                          downloadPDF(
                            paper.question_paper_pdf,
                            `${paper.subject}_Question_Paper.pdf`
                          )
                        }
                        className="btn-secondary flex items-center space-x-2"
                      >
                        <Download className="h-4 w-4" />
                        <span>Q.Paper</span>
                      </button>
                    )}

                    {paper.answer_key_pdf && (
                      <button
                        onClick={() =>
                          downloadPDF(
                            paper.answer_key_pdf,
                            `${paper.subject}_Answer_Key.pdf`
                          )
                        }
                        className="btn-secondary flex items-center space-x-2"
                      >
                        <Download className="h-4 w-4" />
                        <span>Answer Key</span>
                      </button>
                    )}

                    <button
                      onClick={() => handleDelete(paper.id)}
                      className="btn-danger flex items-center space-x-2"
                    >
                      <Trash2 className="h-4 w-4" />
                      <span>Delete</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* View Details Modal */}
        {showDetails && selectedPaper && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selectedPaper.subject}
                  </h2>
                  <button
                    onClick={() => setShowDetails(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>

                <div className="mb-6">
                  <p className="text-gray-600">
                    <strong>Department:</strong> {selectedPaper.department}
                  </p>
                  <p className="text-gray-600">
                    <strong>Total Marks:</strong> {selectedPaper.total_marks}
                  </p>
                  <p className="text-gray-600">
                    <strong>Questions:</strong> {selectedPaper.questions.length}
                  </p>
                </div>

                <h3 className="text-lg font-semibold mb-4">Questions:</h3>
                <div className="space-y-6">
                  {selectedPaper.questions.map((q, index) => (
                    <div
                      key={index}
                      className="border-l-4 border-blue-500 pl-4"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className="font-semibold text-gray-900">
                          Q{index + 1}.
                        </span>
                        <div className="flex space-x-2 text-sm">
                          <span className="badge badge-blue">
                            {q.question_type}
                          </span>
                          <span className="badge badge-green">
                            {q.blooms_level}
                          </span>
                          <span className="badge badge-purple">
                            {q.marks} marks
                          </span>
                        </div>
                      </div>
                      <div className="text-gray-800 mb-3 whitespace-pre-line">
                        {q.question_text}
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <p className="text-sm font-semibold text-gray-700 mb-1">
                          Answer Key:
                        </p>
                        <div className="text-sm text-gray-600 whitespace-pre-line">
                          {q.answer_key}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 flex justify-end">
                  <button
                    onClick={() => setShowDetails(false)}
                    className="btn-secondary"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Summary Modal */}
        {showSummary && summary && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                    <Sparkles className="h-7 w-7 mr-2 text-yellow-500" />
                    Papers Summary Analytics
                  </h2>
                  <button
                    onClick={() => setShowSummary(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-6">
                  {/* Overview Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg text-center">
                      <p className="text-sm text-gray-600">Total Papers</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {summary.total_papers}
                      </p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg text-center">
                      <p className="text-sm text-gray-600">Total Questions</p>
                      <p className="text-2xl font-bold text-green-600">
                        {summary.total_questions}
                      </p>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg text-center">
                      <p className="text-sm text-gray-600">Average Marks</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {summary.average_marks}
                      </p>
                    </div>
                    <div className="bg-orange-50 p-4 rounded-lg text-center">
                      <p className="text-sm text-gray-600">Departments</p>
                      <p className="text-2xl font-bold text-orange-600">
                        {
                          Object.keys(summary.department_distribution || {})
                            .length
                        }
                      </p>
                    </div>
                  </div>

                  {/* Distribution Data */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Question Types */}
                    <div className="bg-gradient-to-br from-green-50 to-teal-50 p-4 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">
                        Question Types
                      </h3>
                      <div className="space-y-2">
                        {Object.entries(
                          summary.question_type_distribution || {}
                        ).map(([type, count]) => (
                          <div
                            key={type}
                            className="flex justify-between items-center"
                          >
                            <span className="text-gray-700">{type}:</span>
                            <span className="font-semibold">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Bloom's Levels */}
                    <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-lg">
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">
                        Bloom's Taxonomy Levels
                      </h3>
                      <div className="space-y-2">
                        {Object.entries(
                          summary.blooms_level_distribution || {}
                        ).map(([level, count]) => (
                          <div
                            key={level}
                            className="flex justify-between items-center"
                          >
                            <span className="text-gray-700">{level}:</span>
                            <span className="font-semibold">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Insights and Suggestions */}
                  <div className="space-y-6">
                    {/* AI Insights */}
                    {summary.insights && summary.insights.length > 0 && (
                      <div className="bg-blue-50 p-6 rounded-lg">
                        <h4 className="text-lg font-semibold text-blue-900 mb-4 flex items-center">
                          <Eye className="h-5 w-5 mr-2" />
                          Key Insights
                        </h4>
                        <ul className="space-y-2">
                          {summary.insights.map((insight, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-blue-500 mr-2">•</span>
                              <span className="text-blue-800">{insight}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* AI Suggestions */}
                    {summary.suggestions && summary.suggestions.length > 0 && (
                      <div className="bg-purple-50 p-6 rounded-lg">
                        <h4 className="text-lg font-semibold text-purple-900 mb-4 flex items-center">
                          <Sparkles className="h-5 w-5 mr-2" />
                          AI Recommendations
                        </h4>
                        <ul className="space-y-3">
                          {summary.suggestions.map((suggestion, index) => (
                            <li key={index} className="flex items-start">
                              <span className="text-purple-500 mr-2">→</span>
                              <span className="text-purple-800">
                                {suggestion}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-6 flex justify-end">
                  <button
                    onClick={() => setShowSummary(false)}
                    className="btn-primary"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Custom Prompt Modal */}
      {showCustomPrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg w-full max-w-2xl">
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Custom Analysis Prompt
              </h3>
              <div className="space-y-4">
                <p className="text-gray-600">
                  Enter your specific analysis request. Examples:
                </p>
                <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
                  <li>Analyze the difficulty progression across my papers</li>
                  <li>
                    How well are my papers covering different cognitive levels?
                  </li>
                  <li>
                    Compare the distribution of question types between subjects
                  </li>
                  <li>Identify gaps in topic coverage for specific subjects</li>
                </ul>
                <textarea
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Enter your analysis request..."
                  className="w-full h-32 p-3 border rounded-lg focus:ring-2 focus:ring-primary-500"
                />
                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowCustomPrompt(false)}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      if (!customPrompt.trim()) {
                        toast.error("Please enter an analysis prompt");
                        return;
                      }
                      handleGetSummary(selectedSubjectForSummary);
                    }}
                    className="btn-primary"
                  >
                    Analyze
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
