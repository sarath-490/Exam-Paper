# 🚀 Intelligent Exam Paper Generator

A full-stack AI-powered exam paper generation system with multi-agent workflows, built with React (frontend) and FastAPI (backend).

## 🌟 Features

- **AI-Powered Question Generation** - Uses LangGraph with multiple AI agents
- **Multi-format Support** - PDF, Word, PowerPoint, and image processing
- **Duplicate Detection** - FAISS-based semantic similarity checking
- **Visual Analytics** - Bloom's taxonomy distribution charts
- **Cloud Storage** - Cloudinary integration for file uploads
- **Email Notifications** - Automated email system
- **Role-based Access** - Admin, Teacher, and Student roles

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Backend**: FastAPI + Python + MongoDB + LangGraph
- **AI**: Google Gemini + LangChain + Sentence Transformers
- **Storage**: MongoDB Atlas + Cloudinary
- **Deployment**: Render (recommended)

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- MongoDB Atlas account
- Google Gemini API key
- Cloudinary account (optional)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd exam-paper-generator
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your configuration
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   cp .env.example .env  # Create .env file with VITE_BACKEND_URL
   npm run dev
   ```

## 🌐 Deployment to Render

### 1. Backend Deployment

1. **Create a new Web Service** in Render
2. **Connect your GitHub repository**
3. **Configure the service:**
   - **Name**: `exam-paper-generator-backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --no-build-isolation -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables:**
   ```bash
   MONGODB_URL=your_mongodb_connection_string
   GEMINI_API_KEY=your_gemini_api_key
   JWT_SECRET_KEY=your_jwt_secret_key
   CLOUDINARY_CLOUD_NAME=your_cloudinary_name
   CLOUDINARY_API_KEY=your_cloudinary_key
   CLOUDINARY_API_SECRET=your_cloudinary_secret
   FRONTEND_ALLOWED_ORIGINS=https://your-frontend-app.onrender.com
   ```

### 2. Frontend Deployment

1. **Create a new Static Site** in Render
2. **Connect your GitHub repository**
3. **Configure the service:**
   - **Name**: `exam-paper-generator-frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
   - **Node Version**: `18.17.0`

4. **Add Environment Variables:**
   ```bash
   VITE_BACKEND_URL=https://your-backend-app.onrender.com
   ```

### 3. Custom Domain (Optional)

1. **Purchase a domain** from a registrar
2. **Add custom domain** in Render dashboard
3. **Configure DNS** to point to Render

## 🔧 Environment Variables

### Backend (.env)

```bash
# Database
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/exam_paper_ai

# AI API
GEMINI_API_KEY=your_gemini_api_key

# Authentication
JWT_SECRET_KEY=your_super_secret_key

# Cloud Storage
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Email
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# URLs
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
FRONTEND_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (.env)

```bash
VITE_BACKEND_URL=http://localhost:8000
```

## 📊 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user

### Papers
- `POST /teacher/papers/generate` - Generate exam paper
- `GET /teacher/papers` - List user's papers
- `GET /teacher/papers/{paper_id}` - Get specific paper

### Resources
- `POST /teacher/resources/upload` - Upload study material
- `GET /teacher/resources` - List uploaded resources

### Admin
- `GET /admin/dashboard` - Admin dashboard data
- `PUT /admin/users/{user_id}/role` - Update user role

## 🔒 Security Features

- **JWT Authentication** - Secure token-based auth
- **Role-based Access Control** - Admin/Teacher/Student roles
- **File Upload Validation** - Size and type restrictions
- **CORS Configuration** - Cross-origin resource sharing
- **Input Sanitization** - SQL injection and XSS prevention

## 🚀 Production Checklist

- [ ] Set up MongoDB Atlas cluster
- [ ] Configure Google Gemini API key
- [ ] Set up Cloudinary for file storage (optional)
- [ ] Configure email service (optional)
- [ ] Set up custom domain (optional)
- [ ] Configure environment variables in Render
- [ ] Test all API endpoints
- [ ] Verify file upload functionality
- [ ] Check email notifications
- [ ] Monitor application logs

## 🛠️ Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Database Management

The application uses MongoDB Atlas. Key collections:
- `users` - User accounts and profiles
- `papers` - Generated exam papers
- `resources` - Uploaded study materials
- `fs.files` - File storage metadata

## 📈 Monitoring

- **Application Logs**: Check Render dashboard logs
- **Database**: Monitor MongoDB Atlas metrics
- **Performance**: Use Render's built-in monitoring
- **Errors**: Implement proper error tracking

## 🚀 Deployment

**Run the deployment script:**
```cmd
deploy.bat
```

**Then follow the step-by-step guide above to complete your deployment!** 🚀📚
