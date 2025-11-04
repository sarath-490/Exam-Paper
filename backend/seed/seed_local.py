"""
Simple synchronous seed script for local MongoDB (MongoDB Compass)
Works better with local MongoDB installations
"""

from pymongo import MongoClient
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.auth import get_password_hash


def seed_database():
    """Seed the database with initial data using synchronous pymongo"""
    
    print("🌱 Starting database seeding (Local MongoDB)...")
    
    # MongoDB connection string for local
    MONGO_URI = "mongodb://localhost:27017/"
    
    print(f"📡 Connecting to MongoDB at: {MONGO_URI}")
    
    try:
        # Connect to MongoDB
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        
        # Get database
        db = client.exam_generator
        
    except Exception as e:
        print(f"\n❌ Failed to connect to MongoDB!")
        print(f"Error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("1. Make sure MongoDB is installed and running")
        print("2. Start MongoDB service:")
        print("   Windows (Run as Administrator):")
        print("   > net start MongoDB")
        print("\n3. Or start MongoDB manually:")
        print("   > mongod --dbpath C:\\data\\db")
        print("\n4. Or use MongoDB Compass:")
        print("   - Open MongoDB Compass")
        print("   - Connect to: mongodb://localhost:27017")
        print("\nIf MongoDB is not installed:")
        print("- Download from: https://www.mongodb.com/try/download/community")
        return
    
    # Clear existing data
    print("🗑️  Clearing existing data...")
    db.users.delete_many({})
    db.resources.delete_many({})
    db.papers.delete_many({})
    db.prompts_history.delete_many({})
    
    # Create admin user
    print("👤 Creating admin user...")
    admin_data = {
        "email": "admin@university.edu",
        "hashed_password": get_password_hash("admin123"),
        "full_name": "System Administrator",
        "role": "admin",
        "department": "Administration",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    db.users.insert_one(admin_data)
    print("✅ Admin created: admin@university.edu / admin123")
    
    # Create demo teachers
    print("👨‍🏫 Creating demo teachers...")
    
    teacher1_data = {
        "email": "john.doe@university.edu",
        "hashed_password": get_password_hash("teacher123"),
        "full_name": "Dr. John Doe",
        "role": "teacher",
        "department": "Computer Science",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    result1 = db.users.insert_one(teacher1_data)
    teacher1_id = str(result1.inserted_id)
    print("✅ Teacher 1 created: john.doe@university.edu / teacher123")
    
    teacher2_data = {
        "email": "jane.smith@university.edu",
        "hashed_password": get_password_hash("teacher123"),
        "full_name": "Dr. Jane Smith",
        "role": "teacher",
        "department": "Mathematics",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    result2 = db.users.insert_one(teacher2_data)
    teacher2_id = str(result2.inserted_id)
    print("✅ Teacher 2 created: jane.smith@university.edu / teacher123")
    
    # Create sample resources
    print("📚 Creating sample resources...")
    
    sample_resource1 = {
        "teacher_id": teacher1_id,
        "filename": "data_structures_syllabus.pdf",
        "file_type": "pdf",
        "file_path": "/uploads/sample1.pdf",
        "file_size": 1024000,
        "extracted_text": """
        Data Structures and Algorithms - Course Syllabus
        
        Unit 1: Introduction to Data Structures
        - Arrays and Linked Lists
        - Stacks and Queues
        - Time and Space Complexity
        
        Unit 2: Trees and Graphs
        - Binary Trees and BST
        - AVL Trees and Red-Black Trees
        - Graph Representations and Traversals
        
        Unit 3: Sorting and Searching
        - Bubble Sort, Merge Sort, Quick Sort
        - Binary Search and Hashing
        - Heap Sort
        
        Unit 4: Advanced Topics
        - Dynamic Programming
        - Greedy Algorithms
        - Graph Algorithms (Dijkstra, Prim, Kruskal)
        """,
        "topics": [
            "Arrays and Linked Lists",
            "Stacks and Queues",
            "Binary Trees",
            "Graph Algorithms",
            "Sorting Algorithms",
            "Dynamic Programming"
        ],
        "subject": "Data Structures",
        "department": "Computer Science",
        "uploaded_at": datetime.utcnow(),
        "processed": True
    }
    db.resources.insert_one(sample_resource1)
    
    sample_resource2 = {
        "teacher_id": teacher2_id,
        "filename": "calculus_notes.pdf",
        "file_type": "pdf",
        "file_path": "/uploads/sample2.pdf",
        "file_size": 2048000,
        "extracted_text": """
        Advanced Calculus - Course Notes
        
        Unit 1: Limits and Continuity
        - Definition of Limits
        - Continuity and Differentiability
        - L'Hôpital's Rule
        
        Unit 2: Differentiation
        - Derivatives of Elementary Functions
        - Chain Rule and Product Rule
        - Implicit Differentiation
        
        Unit 3: Integration
        - Definite and Indefinite Integrals
        - Integration by Parts
        - Substitution Method
        
        Unit 4: Applications
        - Area Under Curves
        - Volume of Solids of Revolution
        - Differential Equations
        """,
        "topics": [
            "Limits and Continuity",
            "Differentiation",
            "Integration",
            "Differential Equations",
            "Applications of Calculus"
        ],
        "subject": "Advanced Calculus",
        "department": "Mathematics",
        "uploaded_at": datetime.utcnow(),
        "processed": True
    }
    db.resources.insert_one(sample_resource2)
    
    print("✅ Sample resources created")
    
    # Create indexes for better performance
    print("📇 Creating database indexes...")
    try:
        db.users.create_index("email", unique=True)
        db.resources.create_index("teacher_id")
        db.papers.create_index("teacher_id")
        db.prompts_history.create_index("teacher_id")
        print("✅ Indexes created")
    except Exception as e:
        print(f"⚠️  Index creation warning: {e}")
    
    # Close connection
    client.close()
    
    print("\n" + "="*60)
    print("🎉 Database seeding completed successfully!")
    print("="*60)
    print("\n📋 Login Credentials:")
    print("\n👨‍💼 Admin:")
    print("   Email: admin@university.edu")
    print("   Password: admin123")
    print("\n👨‍🏫 Teacher 1 (Computer Science):")
    print("   Email: john.doe@university.edu")
    print("   Password: teacher123")
    print("\n👨‍🏫 Teacher 2 (Mathematics):")
    print("   Email: jane.smith@university.edu")
    print("   Password: teacher123")
    print("\n" + "="*60)
    print("\n✅ You can now start the backend server:")
    print("   uvicorn app.main:app --reload")


if __name__ == "__main__":
    seed_database()
