import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { teacherAPI } from '../services/api'
import Navbar from '../components/Navbar'
import toast from 'react-hot-toast'
import { Upload, FileText, ArrowLeft } from 'lucide-react'

const UploadResource = () => {
  const [file, setFile] = useState(null)
  const [subject, setSubject] = useState('')
  const [department, setDepartment] = useState('')
  const [uploading, setUploading] = useState(false)
  const navigate = useNavigate()

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                           'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                           'image/jpeg', 'image/png']
      
      if (!allowedTypes.includes(selectedFile.type)) {
        toast.error('Invalid file type. Please upload PDF, DOCX, PPTX, or Image files.')
        return
      }
      
      if (selectedFile.size > 10 * 1024 * 1024) {
        toast.error('File size must be less than 10MB')
        return
      }
      
      setFile(selectedFile)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!file) {
      toast.error('Please select a file')
      return
    }

    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('subject', subject)
      formData.append('department', department)

      const response = await teacherAPI.uploadResource(formData)
      
      toast.success('Resource uploaded successfully!')
      
      // Show extracted topics
      if (response.data.topics && response.data.topics.length > 0) {
        toast.success(`Extracted ${response.data.topics.length} topics from the document`)
      }
      
      navigate('/teacher')
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload resource')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <button
          onClick={() => navigate('/teacher')}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Back to Dashboard
        </button>

        <div className="card">
          <div className="flex items-center mb-6">
            <Upload className="h-8 w-8 text-primary-600 mr-3" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Upload Resource</h1>
              <p className="text-gray-600">Upload syllabus, past papers, or study materials</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select File *
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-500 transition-colors">
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.pptx,.jpg,.jpeg,.png"
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-sm text-gray-600">
                    {file ? file.name : 'Click to upload or drag and drop'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    PDF, DOCX, PPTX, JPG, PNG (max 10MB)
                  </p>
                </label>
              </div>
            </div>

            {/* Subject */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Subject
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g., Data Structures and Algorithms"
                className="input-field"
              />
            </div>

            {/* Department */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Department
              </label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder="e.g., Computer Science"
                className="input-field"
              />
            </div>

            {/* Submit Button */}
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={uploading || !file}
                className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Uploading...' : 'Upload Resource'}
              </button>
              <button
                type="button"
                onClick={() => navigate('/teacher')}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>

          {/* Info Box */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-2">💡 Tips for Best Results</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Upload clear, well-structured documents</li>
              <li>• Include syllabus, past papers, and lecture notes</li>
              <li>• The AI will extract topics and content automatically</li>
              <li>• More resources = better question generation</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UploadResource
