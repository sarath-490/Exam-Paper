import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FileText, RefreshCw, CheckCircle, Download } from 'lucide-react'
import Navbar from '../components/Navbar'
import { teacherAPI } from '../services/api'
import toast from 'react-hot-toast'

export default function EditPaper() {
  const { paperId } = useParams()
  const navigate = useNavigate()
  
  const [paper, setPaper] = useState(null)
  const [loading, setLoading] = useState(true)
  const [regenerating, setRegenerating] = useState(false)
  const [approving, setApproving] = useState(false)
  
  // Editable fields
  const [subject, setSubject] = useState('')
  const [department, setDepartment] = useState('')
  const [section, setSection] = useState('')
  const [year, setYear] = useState('')
  const [totalMarks, setTotalMarks] = useState('')
  const [regeneratePrompt, setRegeneratePrompt] = useState('')

  useEffect(() => {
    fetchPaper()
  }, [paperId])

  const fetchPaper = async () => {
    setLoading(true)
    try {
      const response = await teacherAPI.getPaper(paperId)
      const paperData = response.data
      setPaper(paperData)
      
      // Populate editable fields
      setSubject(paperData.subject || '')
      setDepartment(paperData.department || '')
      setSection(paperData.section || '')
      setYear(paperData.year || '')
      setTotalMarks(paperData.total_marks || '')
      
    } catch (error) {
      toast.error('Failed to load paper')
      navigate('/approved-papers')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateMetadata = async () => {
    try {
      await teacherAPI.updatePaperMetadata(paperId, {
        subject,
        department,
        section,
        year: year ? parseInt(year) : null,
        total_marks: parseInt(totalMarks)
      })
      toast.success('Paper details updated!')
      fetchPaper()
    } catch (error) {
      toast.error('Failed to update paper details')
    }
  }

  const handleRegenerate = async () => {
    if (!regeneratePrompt.trim()) {
      toast.error('Please provide regeneration instructions')
      return
    }

    setRegenerating(true)
    try {
      const response = await teacherAPI.regeneratePaper(paperId, regeneratePrompt)
      toast.success('Paper regenerated successfully!')
      setRegeneratePrompt('')
      
      // Reload the paper
      fetchPaper()
    } catch (error) {
      toast.error('Failed to regenerate paper')
    } finally {
      setRegenerating(false)
    }
  }

  const handleApprove = async () => {
    if (!confirm('Are you sure you want to approve this paper? This will generate PDFs and mark it as approved.')) {
      return
    }

    setApproving(true)
    try {
      const response = await teacherAPI.approvePaper(paperId)
      toast.success('Paper approved successfully!')
      
      // Download PDFs
      if (response.data.question_paper_pdf) {
        await downloadPDF(response.data.question_paper_pdf, `${subject}_Question_Paper.pdf`)
      }
      if (response.data.answer_key_pdf) {
        await downloadPDF(response.data.answer_key_pdf, `${subject}_Answer_Key.pdf`)
      }
      
      // Navigate back to approved papers
      setTimeout(() => {
        navigate('/approved-papers')
      }, 2000)
    } catch (error) {
      toast.error('Failed to approve paper')
    } finally {
      setApproving(false)
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
      console.error('Failed to download PDF:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading paper...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!paper) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="card text-center py-12">
            <p className="text-gray-600">Paper not found</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Edit Paper</h1>
          <p className="mt-2 text-gray-600">
            {paper.is_edit_copy && (
              <span className="text-blue-600">
                📋 Editing copy of approved paper • Original preserved
              </span>
            )}
          </p>
        </div>

        {/* Paper Details Card */}
        <div className="card mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Paper Details</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Subject *
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="input"
                placeholder="e.g., Data Structures"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Department *
              </label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="input"
                placeholder="e.g., Computer Science"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Section
              </label>
              <input
                type="text"
                value={section}
                onChange={(e) => setSection(e.target.value)}
                className="input"
                placeholder="e.g., A"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Year
              </label>
              <input
                type="number"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className="input"
                placeholder="e.g., 2024"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Total Marks *
              </label>
              <input
                type="number"
                value={totalMarks}
                onChange={(e) => setTotalMarks(e.target.value)}
                className="input"
                placeholder="e.g., 50"
              />
            </div>
          </div>

          <div className="mt-4">
            <button
              onClick={handleUpdateMetadata}
              className="btn-secondary"
            >
              Update Details
            </button>
          </div>
        </div>

        {/* Bloom's Distribution */}
        {paper.blooms_distribution && (
          <div className="card mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Bloom's Taxonomy Distribution</h2>
            <div className="flex flex-wrap gap-3">
              {Object.entries(paper.blooms_distribution).map(([level, count]) => (
                <div key={level} className="badge badge-blue text-sm">
                  {level}: {count}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Questions */}
        <div className="card mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Questions ({paper.questions?.length || 0})
          </h2>
          
          <div className="space-y-6">
            {paper.questions?.map((q, index) => (
              <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                <div className="flex items-start justify-between mb-2">
                  <span className="font-semibold text-gray-900">Q{index + 1}.</span>
                  <div className="flex space-x-2 text-sm">
                    <span className="badge badge-blue">{q.question_type}</span>
                    <span className="badge badge-green">{q.blooms_level}</span>
                    <span className="badge badge-purple">{q.marks} marks</span>
                  </div>
                </div>
                
                <div className="text-gray-800 mb-3 whitespace-pre-line">
                  {q.question_text}
                </div>
                
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-sm font-semibold text-gray-700 mb-1">Answer Key:</p>
                  <div className="text-sm text-gray-600 whitespace-pre-line">
                    {q.answer_key}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Regenerate Section */}
        <div className="card mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <RefreshCw className="h-5 w-5 mr-2" />
            Regenerate Paper
          </h2>
          
          <p className="text-sm text-gray-600 mb-4">
            Provide instructions to regenerate the paper. The system will maintain the structure while applying your changes.
          </p>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Regeneration Instructions
            </label>
            <textarea
              value={regeneratePrompt}
              onChange={(e) => setRegeneratePrompt(e.target.value)}
              rows={6}
              className="input"
              placeholder="E.g., Make questions more difficult, Add more application-based questions, Focus on specific topics like arrays and linked lists..."
            />
          </div>

          <button
            onClick={handleRegenerate}
            disabled={regenerating || !regeneratePrompt.trim()}
            className="btn-primary flex items-center space-x-2"
          >
            {regenerating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Regenerating...</span>
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                <span>Regenerate Paper</span>
              </>
            )}
          </button>
          
          {paper.regeneration_count > 0 && (
            <p className="mt-2 text-sm text-gray-600">
              Regenerated {paper.regeneration_count} time{paper.regeneration_count !== 1 ? 's' : ''}
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Ready to approve?</h3>
              <p className="text-sm text-gray-600 mt-1">
                This will generate PDFs and mark the paper as approved.
              </p>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => navigate('/approved-papers')}
                className="btn-secondary"
              >
                Cancel
              </button>
              
              <button
                onClick={handleApprove}
                disabled={approving}
                className="btn-success flex items-center space-x-2"
              >
                {approving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Approving...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4" />
                    <span>Approve Paper</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
