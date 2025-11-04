import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { teacherAPI } from '../services/api'
import Navbar from '../components/Navbar'
import toast from 'react-hot-toast'
import { ArrowLeft, Download, CheckCircle, FileText, RefreshCw, X } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'

const VerifyPaper = () => {
  const { paperId } = useParams()
  const navigate = useNavigate()
  const [paper, setPaper] = useState(null)
  const [loading, setLoading] = useState(true)
  const [approving, setApproving] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [feedbackPrompt, setFeedbackPrompt] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    // Reset states when paperId changes
    setLoading(true)
    setRegenerating(false)
    setShowFeedbackModal(false)
    setFeedbackPrompt('')
    fetchPaper()
  }, [paperId])

  const fetchPaper = async () => {
    try {
      setError(null)
      const response = await teacherAPI.getPaper(paperId)
      console.log('Paper data:', response.data) // Debug log
      
      // Validate paper data
      if (!response.data) {
        throw new Error('No paper data received')
      }
      
      // Ensure required fields exist
      const paperData = {
        ...response.data,
        questions: response.data.questions || [],
        blooms_distribution: response.data.blooms_distribution || {},
        regeneration_count: response.data.regeneration_count || 0
      }
      
      setPaper(paperData)
    } catch (error) {
      console.error('Error fetching paper:', error) // Debug log
      setError(error.response?.data?.detail || error.message || 'Failed to fetch paper')
      toast.error(error.response?.data?.detail || 'Failed to fetch paper')
      
      // Don't navigate away immediately, show error state
      setTimeout(() => {
        navigate('/teacher')
      }, 3000)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    setApproving(true)
    try {
      const response = await teacherAPI.approvePaper(paperId)
      toast.success('Paper approved successfully!')
      
      // Show download progress
      toast.loading('Downloading Question Paper...', { id: 'download-progress' })
      
      // Download Question Paper (questions only)
      await downloadPDF(
        response.data.question_paper_id, 
        `${paper.subject}_Question_Paper.pdf`
      )
      
      toast.loading('Downloading Answer Key...', { id: 'download-progress' })
      
      // Download Answer Key (questions with answers)
      await downloadPDF(
        response.data.answer_key_id, 
        `${paper.subject}_Answer_Key.pdf`
      )
      
      toast.success('Both PDFs downloaded successfully!', { id: 'download-progress' })
      
      // Navigate after a short delay to ensure downloads complete
      setTimeout(() => {
        navigate('/teacher')
      }, 1500)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve paper', { id: 'download-progress' })
    } finally {
      setApproving(false)
    }
  }

  const handleRegenerate = async () => {
    setRegenerating(true)
    try {
      const response = await teacherAPI.regeneratePaper(paperId, feedbackPrompt || null)
      
      // Close modal and reset feedback
      setShowFeedbackModal(false)
      setFeedbackPrompt('')
      
      // Show success message
      toast.success('Paper regenerated! Review the new version.')
      
      // Navigate to the new paper (useEffect will fetch it automatically)
      navigate(`/teacher/verify/${response.data.paper_id}`, { replace: true })
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to regenerate paper')
      setRegenerating(false)
    }
  }

  const downloadPDF = async (fileId, filename) => {
    try {
      const response = await teacherAPI.downloadPDF(fileId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      toast.error(`Failed to download ${filename}`)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-600">Loading paper...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6 max-w-md">
            <h2 className="text-xl font-bold text-red-900 mb-2">Error Loading Paper</h2>
            <p className="text-red-700 mb-4">{error}</p>
            <button
              onClick={() => navigate('/teacher')}
              className="btn-primary w-full"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!paper) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <p className="text-gray-600 mb-4">Paper not found</p>
          <button
            onClick={() => navigate('/teacher')}
            className="btn-primary"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    )
  }

  // Wrap entire render in try-catch
  try {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <button
          onClick={() => navigate('/teacher')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Back to Dashboard
        </button>

        {/* Paper Header */}
        <div className="card mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{paper.subject}</h1>
              <p className="text-gray-600 mt-1">{paper.department}</p>
              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                {paper.section && <span>Section: {paper.section}</span>}
                {paper.year && <span>Year: {paper.year}</span>}
                <span>Total Marks: {paper.total_marks}</span>
                {paper.regeneration_count > 0 && (
                  <span className="flex items-center text-blue-600 font-medium">
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Regenerated {paper.regeneration_count}x
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                paper.status === 'approved' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {paper.status}
              </span>
            </div>
          </div>
        </div>

        {/* Regeneration Info */}
        {paper.regeneration_count > 0 && paper.status === 'draft' && (
          <div className="card mb-6 bg-blue-50 border-2 border-blue-200">
            <div className="flex items-start space-x-3">
              <RefreshCw className="h-6 w-6 text-blue-600 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-blue-900">Regenerated Paper</h3>
                <p className="text-sm text-blue-700 mt-1">
                  This paper has been regenerated {paper.regeneration_count} time{paper.regeneration_count > 1 ? 's' : ''}. 
                  Review the new questions and either approve or regenerate again with more feedback.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Paper Summary */}
        {paper.summary && (
          <div className="card mb-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Paper Summary</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Question Distribution */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Question Types</h3>
                <div className="space-y-2">
                  {paper.summary.question_distribution && Object.entries(paper.summary.question_distribution).map(([type, count]) => (
                    count > 0 && (
                      <div key={type} className="flex justify-between items-center bg-blue-50 p-2 rounded">
                        <span className="text-sm text-gray-700">{type}</span>
                        <span className="text-sm font-bold text-blue-600">{count}</span>
                      </div>
                    )
                  ))}
                </div>
              </div>

              {/* Source Distribution */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Question Sources</h3>
                <div className="space-y-2">
                  {paper.summary.source_distribution && Object.entries(paper.summary.source_distribution).map(([source, count]) => (
                    count > 0 && (
                      <div key={source} className="flex justify-between items-center bg-green-50 p-2 rounded">
                        <span className="text-sm text-gray-700">{source}</span>
                        <span className="text-sm font-bold text-green-600">{count}</span>
                      </div>
                    )
                  ))}
                </div>
              </div>

              {/* Bloom's Distribution */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Bloom's Taxonomy</h3>
                <div className="space-y-2">
                  {paper.summary.blooms_distribution && Object.entries(paper.summary.blooms_distribution).map(([level, count]) => (
                    count > 0 && (
                      <div key={level} className="bg-purple-50 p-2 rounded">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-700">{level}</span>
                          <span className="text-sm font-bold text-purple-600">{count}</span>
                        </div>
                        {/* Show source breakdown if available */}
                        {paper.summary.blooms_with_sources && paper.summary.blooms_with_sources[level] && (
                          <div className="flex gap-2 mt-1 text-xs text-gray-600">
                            {paper.summary.blooms_with_sources[level].previous > 0 && (
                              <span className="bg-yellow-100 px-1 rounded">📚 {paper.summary.blooms_with_sources[level].previous}</span>
                            )}
                            {paper.summary.blooms_with_sources[level].creative > 0 && (
                              <span className="bg-orange-100 px-1 rounded">✨ {paper.summary.blooms_with_sources[level].creative}</span>
                            )}
                            {paper.summary.blooms_with_sources[level].new > 0 && (
                              <span className="bg-teal-100 px-1 rounded">🆕 {paper.summary.blooms_with_sources[level].new}</span>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  ))}
                </div>
              </div>
            </div>

            {/* Totals */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-gray-700">Total Questions:</span>
                <span className="text-lg font-bold text-gray-900">{paper.summary.total_questions}</span>
              </div>
              <div className="flex justify-between items-center mt-2">
                <span className="text-sm font-semibold text-gray-700">Total Marks:</span>
                <span className="text-lg font-bold text-primary-600">{paper.summary.total_marks}</span>
              </div>
            </div>
          </div>
        )}

        {/* Bloom's Taxonomy Pie Charts */}
        {paper.summary && paper.summary.blooms_with_sources && Object.keys(paper.summary.blooms_with_sources).length > 0 ? (
          <div className="card mb-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Bloom's Taxonomy Distribution (Source Breakdown)</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(paper.summary.blooms_with_sources).map(([level, data]) => {
                if (data.total === 0) return null;
                
                // Prepare data for pie chart
                const pieData = [
                  { name: 'Previous', value: data.previous, color: '#FCD34D' },
                  { name: 'Creative', value: data.creative, color: '#FB923C' },
                  { name: 'New', value: data.new, color: '#2DD4BF' }
                ].filter(item => item.value > 0);
                
                return (
                  <div key={level} className="bg-white border rounded-lg p-4 shadow-sm">
                    <h3 className="text-center font-semibold text-gray-900 mb-2">
                      {level}
                      <span className="ml-2 text-sm text-gray-600">({data.total} questions)</span>
                    </h3>
                    
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={60}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {pieData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                    
                    {/* Legend with counts */}
                    <div className="mt-2 space-y-1">
                      {data.previous > 0 && (
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center">
                            <div className="w-3 h-3 bg-yellow-400 rounded mr-2"></div>
                            <span>📚 Previous</span>
                          </div>
                          <span className="font-semibold">{data.previous}</span>
                        </div>
                      )}
                      {data.creative > 0 && (
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center">
                            <div className="w-3 h-3 bg-orange-400 rounded mr-2"></div>
                            <span>✨ Creative</span>
                          </div>
                          <span className="font-semibold">{data.creative}</span>
                        </div>
                      )}
                      {data.new > 0 && (
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center">
                            <div className="w-3 h-3 bg-teal-400 rounded mr-2"></div>
                            <span>🆕 New</span>
                          </div>
                          <span className="font-semibold">{data.new}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Overall Source Distribution Bar Chart */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
                Overall Question Source Distribution
              </h3>
              
              {(() => {
                // Calculate overall distribution across all Bloom's levels
                const overallData = Object.entries(paper.summary.blooms_with_sources).reduce((acc, [level, data]) => {
                  acc.previous += data.previous;
                  acc.creative += data.creative;
                  acc.new += data.new;
                  return acc;
                }, { previous: 0, creative: 0, new: 0 });

                const barData = [
                  {
                    name: '📚 Previous',
                    count: overallData.previous,
                    percentage: ((overallData.previous / paper.summary.total_questions) * 100).toFixed(1),
                    fill: '#FCD34D'
                  },
                  {
                    name: '✨ Creative',
                    count: overallData.creative,
                    percentage: ((overallData.creative / paper.summary.total_questions) * 100).toFixed(1),
                    fill: '#FB923C'
                  },
                  {
                    name: '🆕 New',
                    count: overallData.new,
                    percentage: ((overallData.new / paper.summary.total_questions) * 100).toFixed(1),
                    fill: '#2DD4BF'
                  }
                ];

                return (
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis label={{ value: 'Number of Questions', angle: -90, position: 'insideLeft' }} />
                        <Tooltip 
                          content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                              return (
                                <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
                                  <p className="font-semibold">{payload[0].payload.name}</p>
                                  <p className="text-sm">Count: <span className="font-bold">{payload[0].payload.count}</span></p>
                                  <p className="text-sm">Percentage: <span className="font-bold">{payload[0].payload.percentage}%</span></p>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Bar dataKey="count" fill="#8884d8" radius={[8, 8, 0, 0]}>
                          {barData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>

                    {/* Summary Stats */}
                    <div className="grid grid-cols-3 gap-4 mt-6">
                      <div className="bg-yellow-50 p-4 rounded-lg text-center border border-yellow-200">
                        <div className="text-2xl font-bold text-yellow-700">{overallData.previous}</div>
                        <div className="text-sm text-yellow-600 mt-1">📚 Previous Questions</div>
                        <div className="text-xs text-yellow-500 mt-1">
                          {((overallData.previous / paper.summary.total_questions) * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="bg-orange-50 p-4 rounded-lg text-center border border-orange-200">
                        <div className="text-2xl font-bold text-orange-700">{overallData.creative}</div>
                        <div className="text-sm text-orange-600 mt-1">✨ Creative Questions</div>
                        <div className="text-xs text-orange-500 mt-1">
                          {((overallData.creative / paper.summary.total_questions) * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="bg-teal-50 p-4 rounded-lg text-center border border-teal-200">
                        <div className="text-2xl font-bold text-teal-700">{overallData.new}</div>
                        <div className="text-sm text-teal-600 mt-1">🆕 New Questions</div>
                        <div className="text-xs text-teal-500 mt-1">
                          {((overallData.new / paper.summary.total_questions) * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        ) : (
          // Show message if blooms_with_sources is not available
          paper.summary && (
            <div className="card mb-6 bg-blue-50 border-2 border-blue-200">
              <div className="flex items-start space-x-3">
                <div className="text-blue-600 text-2xl">ℹ️</div>
                <div>
                  <h3 className="font-semibold text-blue-900">Source Breakdown Not Available</h3>
                  <p className="text-sm text-blue-700 mt-1">
                    This paper was generated before the source tracking feature was implemented.
                    Please regenerate the paper to see detailed source breakdown (Previous/Creative/New) for each Bloom's level.
                  </p>
                </div>
              </div>
            </div>
          )
        )}

        {/* Bloom's Distribution (Legacy fallback) */}
        {!paper.summary && paper.blooms_distribution && Object.keys(paper.blooms_distribution).length > 0 && (
          <div className="card mb-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Bloom's Taxonomy Distribution</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(paper.blooms_distribution).map(([level, count]) => (
                <div key={level} className="bg-primary-50 p-4 rounded-lg text-center">
                  <p className="text-sm text-gray-600">{level}</p>
                  <p className="text-2xl font-bold text-primary-600">{count}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Questions */}
        <div className="card mb-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">
            Questions ({paper.questions?.length || 0})
          </h2>
          
          <div className="space-y-6">
            {paper.questions && paper.questions.length > 0 ? (
              paper.questions.map((question, index) => {
                // Parse MCQ options if question text contains them
                const isMCQ = question.question_type === 'MCQ' || question.question_text?.includes('\nA)');
                let questionText = question.question_text;
                let options = [];
                
                if (isMCQ && question.question_text?.includes('\n')) {
                  const parts = question.question_text.split('\n');
                  questionText = parts[0];
                  options = parts.slice(1).filter(opt => opt.trim());
                }
                
                return (
                  <div key={index} className="border-l-4 border-primary-500 pl-4 py-2 bg-white rounded-r-lg shadow-sm">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-gray-900">Question {index + 1}</h3>
                      <div className="flex flex-wrap gap-2">
                        <span className="px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded">
                          {question.blooms_level}
                        </span>
                        <span className="px-2 py-1 text-xs font-semibold bg-purple-100 text-purple-800 rounded">
                          {question.question_type}
                        </span>
                        <span className="px-2 py-1 text-xs font-semibold bg-green-100 text-green-800 rounded">
                          {question.marks} marks
                        </span>
                        {question.source && (
                          <span className={`px-2 py-1 text-xs font-semibold rounded ${
                            question.source === 'previous' ? 'bg-yellow-100 text-yellow-800' :
                            question.source === 'creative' ? 'bg-orange-100 text-orange-800' :
                            'bg-teal-100 text-teal-800'
                          }`}>
                            {question.source === 'previous' ? '📚 Previous' :
                             question.source === 'creative' ? '✨ Creative' :
                             '🆕 New'}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Question Text */}
                    <div className="text-gray-800 mb-3">
                      <p className="font-medium">{questionText}</p>
                      
                      {/* MCQ Options */}
                      {isMCQ && options.length > 0 && (
                        <div className="mt-3 space-y-1 ml-4">
                          {options.map((option, optIndex) => (
                            <div key={optIndex} className="text-gray-700">
                              {option}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    {/* Answer Key */}
                    <div className="bg-gray-50 p-3 rounded">
                      <p className="text-sm font-semibold text-gray-700 mb-1">Answer Key:</p>
                      <div className="text-sm text-gray-600 whitespace-pre-line">
                        {question.answer_key}
                      </div>
                    </div>
                    
                    {/* Explanation */}
                    {question.explanation && question.explanation !== question.answer_key && (
                      <div className="bg-blue-50 p-3 rounded mt-2">
                        <p className="text-sm font-semibold text-blue-700 mb-1">Explanation:</p>
                        <div className="text-sm text-blue-600 whitespace-pre-line">
                          {question.explanation}
                        </div>
                      </div>
                    )}
                    
                    {/* Unit */}
                    {question.unit && (
                      <p className="text-xs text-gray-500 mt-2">📖 Unit: {question.unit}</p>
                    )}
                  </div>
                );
              })
            ) : (
              <p className="text-gray-500 text-center py-8">No questions available</p>
            )}
          </div>
        </div>

        {/* Actions */}
        {(paper.status === 'draft' || paper.status === 'pending') && (
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-gray-900">Review Paper</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Approve to download 2 PDFs: Question Paper (questions only) & Answer Key (with solutions)
                </p>
                {paper.regeneration_count > 0 && (
                  <p className="text-xs text-blue-600 mt-1">
                    🔄 Regenerated {paper.regeneration_count} time(s)
                  </p>
                )}
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowFeedbackModal(true)}
                  disabled={regenerating || approving}
                  className="btn-secondary flex items-center space-x-2 disabled:opacity-50"
                >
                  <RefreshCw className="h-5 w-5" />
                  <span>Regenerate</span>
                </button>
                <button
                  onClick={handleApprove}
                  disabled={approving || regenerating}
                  className="btn-primary flex items-center space-x-2 disabled:opacity-50"
                >
                  {approving ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      <span>Approving...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-5 w-5" />
                      <span>Approve & Download PDFs</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {paper.status === 'approved' && (
          <div className="card bg-green-50 border-2 border-green-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-8 w-8 text-green-600" />
                <div>
                  <h3 className="font-semibold text-green-900">Paper Approved</h3>
                  <p className="text-sm text-green-700 mt-1">
                    PDFs have been generated and downloaded
                  </p>
                </div>
              </div>
              {paper.question_paper_pdf && paper.answer_key_pdf && (
                <div className="flex space-x-3">
                  <button
                    onClick={() => downloadPDF(paper.question_paper_pdf, `${paper.subject}_Question_Paper.pdf`)}
                    className="btn-secondary flex items-center space-x-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>Question Paper</span>
                  </button>
                  <button
                    onClick={() => downloadPDF(paper.answer_key_pdf, `${paper.subject}_Answer_Key.pdf`)}
                    className="btn-secondary flex items-center space-x-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>Answer Key</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Regenerate Paper</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Provide feedback to improve the paper or leave empty for a fresh generation
                </p>
              </div>
              <button
                onClick={() => setShowFeedbackModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Feedback (Optional)
              </label>
              <textarea
                value={feedbackPrompt}
                onChange={(e) => setFeedbackPrompt(e.target.value)}
                placeholder="e.g., Make questions more challenging, add more application-based questions, focus on specific topics..."
                rows={6}
                className="input-field w-full"
              />
              <p className="text-xs text-gray-500 mt-2">
                💡 Tip: Be specific about what you want to improve. Leave empty to generate completely new questions.
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">Context Preserved:</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Subject: {paper.subject}</li>
                <li>• Total Marks: {paper.total_marks}</li>
                <li>• Previous questions count: {paper.questions.length}</li>
                <li>• Bloom's levels: {Object.keys(paper.blooms_distribution).join(', ')}</li>
              </ul>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowFeedbackModal(false)}
                disabled={regenerating}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleRegenerate}
                disabled={regenerating}
                className="btn-primary flex items-center space-x-2 disabled:opacity-50"
              >
                {regenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Regenerating...</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-5 w-5" />
                    <span>Regenerate Paper</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    )
  } catch (renderError) {
    console.error('Render error:', renderError)
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6 max-w-md">
            <h2 className="text-xl font-bold text-red-900 mb-2">Rendering Error</h2>
            <p className="text-red-700 mb-4">{renderError.message}</p>
            <button
              onClick={() => navigate('/teacher')}
              className="btn-primary w-full"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }
}

export default VerifyPaper
