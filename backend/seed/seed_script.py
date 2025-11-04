import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.auth import get_password_hash


async def seed_database():
    """Seed the database with initial data"""
    
    print("🌱 Starting database seeding...")
    print(f"📡 Connecting to MongoDB Atlas...")
    print(f"   Database: {settings.MONGODB_DB_NAME}")
    
    try:
        # Connect to MongoDB Atlas
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=50
        )
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Use the configured database name
        db = client[settings.MONGODB_DB_NAME]
    except Exception as e:
        print(f"\n❌ Failed to connect to MongoDB Atlas!")
        print(f"Error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("1. Check your MONGODB_URI in .env file")
        print("2. Verify password is correct (URL encode special characters)")
        print("3. Ensure IP is whitelisted in MongoDB Atlas (0.0.0.0/0 for dev)")
        print("4. Test connection: python test_mongodb_connection.py")
        return
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    print("🗑️  Clearing existing data...")
    await db.users.delete_many({})
    await db.resources.delete_many({})
    await db.papers.delete_many({})
    await db.prompts_history.delete_many({})
    
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
    await db.users.insert_one(admin_data)
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
    result1 = await db.users.insert_one(teacher1_data)
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
    result2 = await db.users.insert_one(teacher2_data)
    teacher2_id = str(result2.inserted_id)
    print("✅ Teacher 2 created: jane.smith@university.edu / teacher123")
    
    # Create sample resources
    print("📚 Creating sample resources...")
    
    sample_resource1 = {
        "teacher_id": teacher1_id,
        "filename": "data_structures_syllabus.pdf",
        "file_type": "pdf",
        "file_size": 1024000,
        "cloudinary_url": "https://res.cloudinary.com/demo/sample.pdf",  # Demo URL
        "cloudinary_public_id": "sample/data_structures",
        "cloudinary_resource_type": "raw",
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
    await db.resources.insert_one(sample_resource1)
    
    sample_resource2 = {
        "teacher_id": teacher2_id,
        "filename": "calculus_notes.pdf",
        "file_type": "pdf",
        "file_size": 2048000,
        "cloudinary_url": "https://res.cloudinary.com/demo/sample2.pdf",  # Demo URL
        "cloudinary_public_id": "sample/calculus",
        "cloudinary_resource_type": "raw",
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
    await db.resources.insert_one(sample_resource2)
    
    print("✅ Sample resources created")
    
    # Create indexes for better performance
    print("📇 Creating database indexes...")
    await db.users.create_index("email", unique=True)
    await db.resources.create_index("teacher_id")
    await db.papers.create_index("teacher_id")
    await db.prompts_history.create_index("teacher_id")
    print("✅ Indexes created")
    
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


if __name__ == "__main__":
    asyncio.run(seed_database())
