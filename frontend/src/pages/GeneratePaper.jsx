import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { teacherAPI } from '../services/api'
import Navbar from '../components/Navbar'
import toast from 'react-hot-toast'
import { Sparkles, ArrowLeft, Loader } from 'lucide-react'

const GeneratePaper = () => {
  const navigate = useNavigate()
  const [generating, setGenerating] = useState(false)
  const [loading, setLoading] = useState(true)
  const [formData, setFormData] = useState({
    subject: '',
    department: '',
    section: '',
    year: new Date().getFullYear(),
    exam_type: 'Final',
    prompt: '',
    // Question categories
    mcq_count: 20,
    mcq_marks: 1,
    short_count: 5,
    short_marks: 2,
    medium_count: 3,
    medium_marks: 5,
    long_count: 1,
    long_marks: 15,
    // Source ratios
    previous_percent: 30,
    creative_percent: 40,
    new_percent: 30,
  })

  // Dynamic dropdown data
  const [dropdownData, setDropdownData] = useState({
    subjects: [],
    departments: [],
    subject_to_departments: {},
    department_to_subjects: {}
  })

  // Calculate total marks automatically
  const totalMarks = 
    (formData.mcq_count * formData.mcq_marks) +
    (formData.short_count * formData.short_marks) +
    (formData.medium_count * formData.medium_marks) +
    (formData.long_count * formData.long_marks)
  
  const totalSourcePercent = 
    formData.previous_percent + formData.creative_percent + formData.new_percent

  // Fetch subjects and departments on component mount
  useEffect(() => {
    fetchSubjectsAndDepartments()
  }, [])

  const fetchSubjectsAndDepartments = async () => {
    try {
      const response = await teacherAPI.getSubjectsAndDepartments()
      setDropdownData(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch subjects/departments:', error)
      toast.error('Failed to load subjects and departments')
      setLoading(false)
    }
  }

  // Get filtered departments based on selected subject
  const getFilteredDepartments = () => {
    if (!formData.subject) return dropdownData.departments
    return dropdownData.subject_to_departments[formData.subject] || []
  }

  // Get filtered subjects based on selected department
  const getFilteredSubjects = () => {
    if (!formData.department) return dropdownData.subjects
    return dropdownData.department_to_subjects[formData.department] || []
  }

  // Handle subject change
  const handleSubjectChange = (value) => {
    setFormData({ ...formData, subject: value })
    // Auto-select department if only one option
    const depts = dropdownData.subject_to_departments[value] || []
    if (depts.length === 1) {
      setFormData({ ...formData, subject: value, department: depts[0] })
    }
  }

  // Handle department change
  const handleDepartmentChange = (value) => {
    setFormData({ ...formData, department: value })
    // Auto-select subject if only one option
    const subjs = dropdownData.department_to_subjects[value] || []
    if (subjs.length === 1) {
      setFormData({ ...formData, department: value, subject: subjs[0] })
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!formData.subject || !formData.department) {
      toast.error('Please select subject and department')
      return
    }

    if (totalSourcePercent !== 100) {
      toast.error('Source percentages must sum to 100%')
      return
    }

    if (totalMarks === 0) {
      toast.error('Please add at least one question category')
      return
    }

    setGenerating(true)

    try {
      const requestData = {
        ...formData,
        total_marks: totalMarks,
      }

      const response = await teacherAPI.generatePaper(requestData)
      
      toast.success('Paper generated successfully!')
      navigate(`/teacher/verify/${response.data.paper_id}`)
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate paper')
    } finally {
      setGenerating(false)
    }
  }


  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <button
          onClick={() => navigate('/teacher')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Back to Dashboard
        </button>

        <div className="card">
          <div className="flex items-center mb-6">
            <Sparkles className="h-8 w-8 text-primary-600 mr-3" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Generate Exam Paper</h1>
              <p className="text-gray-600">AI-powered question paper generation</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject *
                </label>
                {loading ? (
                  <div className="input-field flex items-center justify-center">
                    <Loader className="h-5 w-5 animate-spin text-gray-400" />
                  </div>
                ) : dropdownData.subjects.length === 0 ? (
                  <div className="input-field bg-yellow-50 border-yellow-300 text-yellow-800">
                    No subjects found. Please upload resources first.
                  </div>
                ) : (
                  <select
                    required
                    value={formData.subject}
                    onChange={(e) => handleSubjectChange(e.target.value)}
                    className="input-field"
                  >
                    <option value="">Select Subject</option>
                    {getFilteredSubjects().map((subject) => (
                      <option key={subject} value={subject}>
                        {subject}
                      </option>
                    ))}
                  </select>
                )}
                {formData.department && getFilteredSubjects().length === 0 && (
                  <p className="text-sm text-red-600 mt-1">
                    No subjects found for {formData.department}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Department *
                </label>
                {loading ? (
                  <div className="input-field flex items-center justify-center">
                    <Loader className="h-5 w-5 animate-spin text-gray-400" />
                  </div>
                ) : dropdownData.departments.length === 0 ? (
                  <div className="input-field bg-yellow-50 border-yellow-300 text-yellow-800">
                    No departments found. Please upload resources first.
                  </div>
                ) : (
                  <select
                    required
                    value={formData.department}
                    onChange={(e) => handleDepartmentChange(e.target.value)}
                    className="input-field"
                  >
                    <option value="">Select Department</option>
                    {getFilteredDepartments().map((department) => (
                      <option key={department} value={department}>
                        {department}
                      </option>
                    ))}
                  </select>
                )}
                {formData.subject && getFilteredDepartments().length === 0 && (
                  <p className="text-sm text-red-600 mt-1">
                    No departments found for {formData.subject}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Section
                </label>
                <input
                  type="text"
                  value={formData.section}
                  onChange={(e) => setFormData({ ...formData, section: e.target.value })}
                  placeholder="e.g., A, B, C"
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Year
                </label>
                <input
                  type="number"
                  value={formData.year}
                  onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Exam Type *
                </label>
                <select
                  required
                  value={formData.exam_type}
                  onChange={(e) => setFormData({ ...formData, exam_type: e.target.value })}
                  className="input-field"
                >
                  <option value="Mid">Mid-Term</option>
                  <option value="Final">Final</option>
                  <option value="Internal">Internal Assessment</option>
                  <option value="Quiz">Quiz</option>
                </select>
              </div>
            </div>

            {/* Question Distribution */}
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Question Distribution</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* MCQ */}
                <div className="border rounded-lg p-4 bg-blue-50">
                  <h4 className="font-medium text-gray-900 mb-3">Multiple Choice Questions (MCQ)</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Count</label>
                      <input
                        type="number"
                        min="0"
                        value={formData.mcq_count}
                        onChange={(e) => setFormData({ ...formData, mcq_count: parseInt(e.target.value) || 0 })}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Marks Each</label>
                      <input
                        type="number"
                        min="0"
                        value={formData.mcq_marks}
                        onChange={(e) => setFormData({ ...formData, mcq_marks: parseInt(e.target.value) || 0 })}
                        className="input-field"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-gray-600 mt-2">
                    Total: {formData.mcq_count * formData.mcq_marks} marks
                  </p>
                </div>

                {/* Short Answer */}
                <div className="border rounded-lg p-4 bg-green-50">
                  <h4 className="font-medium text-gray-900 mb-3">Short Answer Questions</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Count</label>
                      <input
                        type="number"
                        min="0"
                        value={formData.short_count}
                        onChange={(e) => setFormData({ ...formData, short_count: parseInt(e.target.value) || 0 })}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Marks Each</label>
                      <input
                        type="number"
                        min="0"
                        value={formData.short_marks}
                        onChange={(e) => setFormData({ ...formData, short_marks: parseInt(e.target.value) || 0 })}
                        className="input-field"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-gray-600 mt-2">
                    Total: {formData.short_count * formData.short_marks} marks
                  </p>
                </div>

                {/* Medium Answer */}
                <div className="border rounded-lg p-4 bg-yellow-50">
                  <h4 className="font-medium text-gray-900 mb-3">Medium Answer Questions</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Count</label>
                      <input
                        type="number"
                        min="0"
                        value={formData.medium_count}
                        onChange={(e) => setFormData({ ...formData, medium_count: parseInt(e.target.value) || 0 })}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Marks Each</label>
                      <input
                        type="number"
                        min="0"
                        value={formData.medium_marks}
                        onChange={(e) => setFormData({ ...formData, medium_marks: parseInt(e.target.value) || 0 })}
                        className="input-field"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-gray-600 mt-2">
                    Total: {formData.medium_count * formData.medium_marks} marks
                  </p>
                </div>

                {/* Long Answer */}
                <div className="border rounded-lg p-4 bg-purple-50">
                  <h4 className="font-medium text-gray-900 mb-3">Long/Essay Questions</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Count</label>
                      <input
                        type="number"
                        min="0"
                        value={formData.long_count}
                        onChange={(e) => setFormData({ ...formData, long_count: parseInt(e.target.value) || 0 })}
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Marks Each</label>
                      <input
                        type="number"
                        min="0"
                        value={formData.long_marks}
                        onChange={(e) => setFormData({ ...formData, long_marks: parseInt(e.target.value) || 0 })}
                        className="input-field"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-gray-600 mt-2">
                    Total: {formData.long_count * formData.long_marks} marks
                  </p>
                </div>
              </div>

              <div className="mt-4 p-4 bg-gray-100 rounded-lg">
                <p className="text-lg font-semibold text-gray-900">
                  Total Paper Marks: {totalMarks}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  Total Questions: {formData.mcq_count + formData.short_count + formData.medium_count + formData.long_count}
                </p>
              </div>
            </div>

            {/* Question Source Ratios */}
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Question Source Distribution</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Previous Year (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.previous_percent}
                    onChange={(e) => setFormData({ ...formData, previous_percent: parseInt(e.target.value) || 0 })}
                    className="input-field"
                  />
                  <p className="text-xs text-gray-500 mt-1">Use questions from past papers</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Creative/Modified (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.creative_percent}
                    onChange={(e) => setFormData({ ...formData, creative_percent: parseInt(e.target.value) || 0 })}
                    className="input-field"
                  />
                  <p className="text-xs text-gray-500 mt-1">Modify existing questions</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    New/AI-Generated (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.new_percent}
                    onChange={(e) => setFormData({ ...formData, new_percent: parseInt(e.target.value) || 0 })}
                    className="input-field"
                  />
                  <p className="text-xs text-gray-500 mt-1">Create new questions</p>
                </div>
              </div>

              <div className={`mt-3 p-3 rounded-lg ${totalSourcePercent === 100 ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                <p className="text-sm font-medium">
                  Total: {totalSourcePercent}% {totalSourcePercent === 100 ? '✓' : '(Must equal 100%)'}
                </p>
              </div>
            </div>

            {/* Optional Topic Focus */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Optional Topic Focus
              </label>
              <textarea
                value={formData.prompt}
                onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
                rows={3}
                placeholder="E.g., Focus on Trees and Graphs, or leave blank for full syllabus coverage"
                className="input-field"
              />
              <p className="text-xs text-gray-500 mt-1">
                Specify topics to prioritize, or leave blank for balanced coverage
              </p>
            </div>

            {/* Submit Button */}
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={generating}
                className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {generating ? (
                  <>
                    <Loader className="animate-spin h-5 w-5 mr-2" />
                    Generating Paper...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-5 w-5 mr-2" />
                    Generate Paper
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => navigate('/teacher')}
                className="btn-secondary"
                disabled={generating}
              >
                Cancel
              </button>
            </div>
          </form>

          {/* Generation Status */}
          {generating && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold text-blue-900 mb-2">🤖 AI is working...</h3>
              <div className="space-y-2 text-sm text-blue-800">
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mr-2 animate-pulse"></div>
                  Reading syllabus and resources
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mr-2 animate-pulse"></div>
                  Generating questions with AI
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mr-2 animate-pulse"></div>
                  Verifying quality and uniqueness
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mr-2 animate-pulse"></div>
                  Assembling final paper
                </div>
              </div>
            </div>
          )}

          {/* Info Box */}
          {!generating && (
            <div className="mt-6 p-4 bg-green-50 rounded-lg">
              <h3 className="font-semibold text-green-900 mb-2">✨ How it works</h3>
              <ul className="text-sm text-green-800 space-y-1">
                <li>• AI analyzes your uploaded resources and syllabus</li>
                <li>• Generates questions based on your prompt and requirements</li>
                <li>• Verifies questions for quality and uniqueness</li>
                <li>• Creates balanced paper with proper Bloom's taxonomy distribution</li>
                <li>• You can review and approve before downloading</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default GeneratePaper
