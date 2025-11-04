import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { teacherAPI } from '../services/api'
import Navbar from '../components/Navbar'
import toast from 'react-hot-toast'
import { ArrowLeft, Clock, CheckCircle, XCircle, AlertCircle, Trash2 } from 'lucide-react'

const History = () => {
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      const response = await teacherAPI.getHistory()
      setHistory(response.data)
    } catch (error) {
      toast.error('Failed to fetch history')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteItem = async (historyId) => {
    if (!confirm('Are you sure you want to delete this history item?')) {
      return
    }

    try {
      await teacherAPI.deleteHistoryItem(historyId)
      toast.success('History item deleted')
      fetchHistory()
    } catch (error) {
      toast.error('Failed to delete history item')
    }
  }

  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to clear ALL history? This action cannot be undone.')) {
      return
    }

    try {
      const response = await teacherAPI.clearAllHistory()
      toast.success(response.data.message)
      fetchHistory()
    } catch (error) {
      toast.error('Failed to clear history')
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />
      case 'in_progress':
        return <Clock className="h-5 w-5 text-yellow-600 animate-spin" />
      default:
        return <AlertCircle className="h-5 w-5 text-gray-600" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

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

        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Generation History</h1>
            {history.length > 0 && (
              <button
                onClick={handleClearAll}
                className="btn-danger flex items-center space-x-2"
              >
                <Trash2 className="h-4 w-4" />
                <span>Clear All</span>
              </button>
            )}
          </div>

          {history.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Clock className="h-16 w-16 mx-auto mb-4 text-gray-400" />
              <p>No generation history yet</p>
              <button
                onClick={() => navigate('/generate')}
                className="btn-primary mt-4"
              >
                Generate Your First Paper
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {history.map((item) => (
                <div key={item.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        {getStatusIcon(item.status)}
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(item.status)}`}>
                          {item.status}
                        </span>
                        <span className="text-sm text-gray-500">
                          {new Date(item.created_at).toLocaleString()}
                        </span>
                      </div>

                      <div className="mb-3">
                        <h3 className="font-semibold text-gray-900 mb-1">Prompt:</h3>
                        <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                          {item.prompt}
                        </p>
                      </div>

                      {item.parameters && Object.keys(item.parameters).length > 0 && (
                        <div className="mb-3">
                          <h3 className="font-semibold text-gray-900 mb-1">Parameters:</h3>
                          <div className="flex flex-wrap gap-2">
                            {item.parameters.subject && (
                              <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                                Subject: {item.parameters.subject}
                              </span>
                            )}
                            {item.parameters.department && (
                              <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded">
                                Dept: {item.parameters.department}
                              </span>
                            )}
                            {item.parameters.total_marks && (
                              <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                                {item.parameters.total_marks} marks
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {item.error_message && (
                        <div className="bg-red-50 border border-red-200 rounded p-3">
                          <p className="text-sm text-red-800">
                            <strong>Error:</strong> {item.error_message}
                          </p>
                        </div>
                      )}

                      {item.completed_at && (
                        <p className="text-xs text-gray-500 mt-2">
                          Completed: {new Date(item.completed_at).toLocaleString()}
                        </p>
                      )}
                    </div>

                    <div className="flex flex-col space-y-2 ml-4">
                      {item.paper_id && item.status === 'success' && (
                        <button
                          onClick={() => navigate(`/teacher/verify/${item.paper_id}`)}
                          className="btn-primary"
                        >
                          View Paper
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteItem(item.id)}
                        className="btn-danger flex items-center justify-center space-x-2"
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
        </div>
      </div>
    </div>
  )
}

export default History
