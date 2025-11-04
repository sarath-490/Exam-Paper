import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { teacherAPI } from "../services/api";
import Navbar from "../components/Navbar";
import toast from "react-hot-toast";
import {
  Upload,
  FileText,
  PlusCircle,
  History,
  BarChart3,
  Trash2,
  Sparkles,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

const TeacherDashboard = () => {
  const [papers, setPapers] = useState([]);
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showSummary, setShowSummary] = useState(false);
  const [dashboardSummary, setDashboardSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [papersRes, resourcesRes] = await Promise.all([
        teacherAPI.listPapers(),
        teacherAPI.listResources(),
      ]);
      setPapers(papersRes.data);
      setResources(resourcesRes.data);
    } catch (error) {
      toast.error("Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  const handleGetDashboardSummary = async () => {
    setSummaryLoading(true);
    try {
      const response = await teacherAPI.getDashboardSummary();
      setDashboardSummary(response.data);
      setShowSummary(true);
    } catch (error) {
      toast.error("Failed to generate dashboard summary");
    } finally {
      setSummaryLoading(false);
    }
  };

  const recentPapers = papers.slice(0, 5);

  // Calculate Bloom's distribution across all papers
  const bloomsData = papers.reduce((acc, paper) => {
    Object.entries(paper.blooms_distribution || {}).forEach(
      ([level, count]) => {
        acc[level] = (acc[level] || 0) + count;
      }
    );
    return acc;
  }, {});

  const chartData = Object.entries(bloomsData).map(([name, value]) => ({
    name,
    value,
  }));

  const COLORS = [
    "#0088FE",
    "#00C49F",
    "#FFBB28",
    "#FF8042",
    "#8884D8",
    "#82CA9D",
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Teacher Dashboard
              </h1>
              <p className="text-gray-600 mt-2">
                Generate and manage exam papers with AI
              </p>
            </div>
            <button
              onClick={handleGetDashboardSummary}
              disabled={summaryLoading}
              className="btn-primary flex items-center space-x-2"
            >
              <Sparkles className="h-5 w-5" />
              <span>{summaryLoading ? "Generating..." : "AI Summary"}</span>
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Link
            to="/upload"
            className="card hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-primary-100 p-3 rounded-lg">
                <Upload className="h-8 w-8 text-primary-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">
                  Upload Resources
                </h3>
                <p className="text-sm text-gray-600">
                  Add syllabus & materials
                </p>
              </div>
            </div>
          </Link>

          <Link
            to="/generate"
            className="card hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-green-100 p-3 rounded-lg">
                <PlusCircle className="h-8 w-8 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Generate Paper</h3>
                <p className="text-sm text-gray-600">Create new exam paper</p>
              </div>
            </div>
          </Link>

          <Link
            to="/history"
            className="card hover:shadow-lg transition-shadow cursor-pointer"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-purple-100 p-3 rounded-lg">
                <History className="h-8 w-8 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">View History</h3>
                <p className="text-sm text-gray-600">Past generations</p>
              </div>
            </div>
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Papers */}
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <FileText className="h-6 w-6 mr-2 text-primary-600" />
              Recent Papers
            </h2>

            {recentPapers.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No papers generated yet</p>
                <Link
                  to="/generate"
                  className="text-primary-600 hover:underline mt-2 inline-block"
                >
                  Generate your first paper
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {recentPapers.map((paper) => (
                  <Link
                    key={paper.id}
                    to={`/teacher/verify/${paper.id}`}
                    className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {paper.subject}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {paper.department}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(paper.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            paper.status === "approved"
                              ? "bg-green-100 text-green-800"
                              : "bg-yellow-100 text-yellow-800"
                          }`}
                        >
                          {paper.status}
                        </span>
                        <p className="text-sm text-gray-600 mt-1">
                          {paper.total_marks} marks
                        </p>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Bloom's Taxonomy Distribution */}
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <BarChart3 className="h-6 w-6 mr-2 text-primary-600" />
              Bloom's Taxonomy Distribution
            </h2>

            {chartData.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No data available yet</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Statistics */}
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Statistics</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-primary-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Total Papers</p>
                <p className="text-3xl font-bold text-primary-600">
                  {papers.length}
                </p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Approved</p>
                <p className="text-3xl font-bold text-green-600">
                  {papers.filter((p) => p.status === "approved").length}
                </p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Resources</p>
                <p className="text-3xl font-bold text-purple-600">
                  {resources.length}
                </p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Draft Papers</p>
                <p className="text-3xl font-bold text-orange-600">
                  {papers.filter((p) => p.status === "draft").length}
                </p>
              </div>
            </div>
          </div>

          {/* Uploaded Resources */}
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
              <Upload className="h-6 w-6 mr-2 text-primary-600" />
              Uploaded Resources
            </h2>

            {resources.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No resources uploaded yet</p>
                <Link
                  to="/upload"
                  className="text-primary-600 hover:underline mt-2 inline-block"
                >
                  Upload your first resource
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {resources.slice(0, 5).map((resource) => (
                  <div
                    key={resource.id}
                    className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <p className="font-medium text-gray-900">
                            {resource.filename}
                          </p>
                          {resource.cloudinary_url && (
                            <a
                              href={resource.cloudinary_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-blue-600 hover:text-blue-800"
                              title="View on Cloudinary"
                            >
                              ☁️
                            </a>
                          )}
                        </div>
                        <p className="text-xs text-gray-500">
                          {resource.subject || "No subject"} •{" "}
                          {(resource.file_size / 1024).toFixed(0)} KB
                          {resource.uploaded_by &&
                            ` • by ${resource.uploaded_by}`}
                        </p>
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className="text-xs text-gray-500">
                          {new Date(resource.uploaded_at).toLocaleDateString()}
                        </span>
                        <button
                          onClick={() =>
                            handleDeleteResource(resource.id, resource.filename)
                          }
                          className="text-red-600 hover:text-red-800 transition-colors"
                          title="Delete resource"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dashboard Summary Modal */}
      {showSummary && dashboardSummary && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <Sparkles className="h-7 w-7 mr-2 text-yellow-500" />
                  Dashboard Summary & Insights
                </h2>
                <button
                  onClick={() => setShowSummary(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>

              {/* Statistics Overview */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Total Papers</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {dashboardSummary.total_papers}
                  </p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Total Questions</p>
                  <p className="text-2xl font-bold text-green-600">
                    {dashboardSummary.total_questions}
                  </p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Average Marks</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {dashboardSummary.average_marks}
                  </p>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Departments</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {
                      Object.keys(
                        dashboardSummary.department_distribution || {}
                      ).length
                    }
                  </p>
                </div>
              </div>

              {/* Distribution Sections */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">
                    Subject Distribution
                  </h4>
                  <div className="space-y-1">
                    {Object.entries(
                      dashboardSummary.subject_distribution || {}
                    ).map(([subject, count]) => (
                      <div
                        key={subject}
                        className="flex justify-between text-sm"
                      >
                        <span>{subject}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">
                    Question Types
                  </h4>
                  <div className="space-y-1">
                    {Object.entries(
                      dashboardSummary.question_type_distribution || {}
                    ).map(([type, count]) => (
                      <div key={type} className="flex justify-between text-sm">
                        <span>{type}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Bloom's Taxonomy Levels */}
              <div className="bg-gray-50 p-4 rounded-lg mb-6">
                <h4 className="font-medium text-gray-900 mb-2">
                  Bloom's Taxonomy Distribution
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(
                    dashboardSummary.blooms_level_distribution || {}
                  ).map(([level, count]) => (
                    <div key={level} className="flex justify-between text-sm">
                      <span>{level}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={() => setShowSummary(false)}
                  className="btn-primary"
                >
                  Close Summary
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeacherDashboard;
