from fastapi import APIRouter, HTTPException, Depends
from app.schemas.auth import CreateUserRequest, UpdateUserRequest, ResetPasswordRequest
from app.core.auth import require_admin, get_password_hash
from app.core.database import get_database
from bson import ObjectId
from datetime import datetime
import secrets
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/users")
async def create_user(
    request: CreateUserRequest,
    current_user: dict = Depends(require_admin)
):
    """Create a new user (admin or teacher)"""
    db = get_database()
    
    # Check if user already exists
    existing = await db.users.find_one({"email": request.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Validate role
    if request.role not in ["admin", "teacher"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    # Create user
    user_data = {
        "email": request.email,
        "hashed_password": get_password_hash(request.password),
        "full_name": request.full_name,
        "role": request.role,
        "department": request.department,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    result = await db.users.insert_one(user_data)
    
    return {
        "id": str(result.inserted_id),
        "message": "User created successfully"
    }


@router.get("/users")
async def list_users(
    current_user: dict = Depends(require_admin)
):
    """List all users"""
    db = get_database()
    
    users = await db.users.find().to_list(length=1000)
    
    return [
        {
            "id": str(user["_id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "department": user.get("department"),
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login")
        }
        for user in users
    ]


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    current_user: dict = Depends(require_admin)
):
    """Update user information"""
    db = get_database()
    
    # Build update data
    update_data = {}
    if request.full_name is not None:
        update_data["full_name"] = request.full_name
    if request.department is not None:
        update_data["department"] = request.department
    if request.is_active is not None:
        update_data["is_active"] = request.is_active
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User updated successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete a user and all their data (cascade delete)"""
    db = get_database()
    from app.core.database import get_gridfs
    
    # Check if user exists
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cascade delete all user data
    try:
        # 1. Delete all papers
        papers_result = await db.papers.delete_many({"teacher_id": user_id})
        
        # 2. Delete all resources and their GridFS files
        resources = await db.resources.find({"teacher_id": user_id}).to_list(length=1000)
        fs = get_gridfs()
        for resource in resources:
            # Delete GridFS file if exists
            if "gridfs_id" in resource:
                try:
                    await fs.delete(ObjectId(resource["gridfs_id"]))
                except Exception as e:
                    print(f"Failed to delete GridFS file: {e}")
        
        resources_result = await db.resources.delete_many({"teacher_id": user_id})
        
        # 3. Delete all prompt history
        history_result = await db.prompts_history.delete_many({"teacher_id": user_id})
        
        # 4. Delete user account
        user_result = await db.users.delete_one({"_id": ObjectId(user_id)})
        
        return {
            "message": "User and all associated data deleted successfully",
            "deleted": {
                "user": user_result.deleted_count,
                "papers": papers_result.deleted_count,
                "resources": resources_result.deleted_count,
                "history": history_result.deleted_count
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cascade delete: {str(e)}")


@router.post("/users/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    current_user: dict = Depends(require_admin)
):
    """Reset user password"""
    db = get_database()
    
    # Find user
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new password
    new_password = secrets.token_urlsafe(12)
    
    # Update password
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"hashed_password": get_password_hash(new_password)}}
    )
    
    return {
        "message": "Password reset successfully",
        "new_password": new_password  # Return new password since we can't email it
    }


@router.get("/analytics")
async def get_analytics(
    current_user: dict = Depends(require_admin)
):
    """Get system analytics"""
    db = get_database()
    
    # Count statistics
    total_users = await db.users.count_documents({})
    total_teachers = await db.users.count_documents({"role": "teacher"})
    total_papers = await db.papers.count_documents({})
    total_resources = await db.resources.count_documents({})
    
    # Recent activity
    recent_papers = await db.papers.find().sort("created_at", -1).limit(10).to_list(length=10)
    
    return {
        "total_users": total_users,
        "total_teachers": total_teachers,
        "total_papers": total_papers,
        "total_resources": total_resources,
        "recent_papers": [
            {
                "id": str(p["_id"]),
                "subject": p["subject"],
                "department": p["department"],
                "total_marks": p["total_marks"],
                "status": p["status"],
                "created_at": p["created_at"]
            }
            for p in recent_papers
        ]
    }
