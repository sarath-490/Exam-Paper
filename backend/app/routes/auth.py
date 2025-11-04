from fastapi import APIRouter, HTTPException, Depends
from app.schemas.auth import LoginRequest, LoginResponse, CreateUserRequest
from app.core.auth import verify_password, create_access_token, get_password_hash, get_current_user
from app.core.database import get_database
from datetime import datetime, timedelta
from bson import ObjectId
import secrets

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint"""
    db = get_database()
    
    # Find user
    user = await db.users.find_one({"email": request.email})
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if active
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is suspended")
    
    # Update last login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create token
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "role": user["role"]}
    )
    
    return LoginResponse(
        access_token=access_token,
        user={
            "id": str(user["_id"]),
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "department": user.get("department")
        }
    )


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "department": user.get("department"),
        "is_active": user.get("is_active", True)
    }


@router.post("/forgot-password")
async def forgot_password(email: str):
    """Request password reset"""
    db = get_database()
    
    # Find user
    user = await db.users.find_one({"email": email})
    if not user:
        # Don't reveal if user exists
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    reset_expires = datetime.utcnow() + timedelta(hours=1)
    
    # Store reset token
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "reset_token": reset_token,
                "reset_token_expires": reset_expires
            }
        }
    )
    
    return {
        "message": "Reset token generated",
        "token": reset_token,  # Return token directly since we can't email it
        "expires": reset_expires.isoformat()
    }


@router.post("/reset-password")
async def reset_password(token: str, new_password: str):
    """Reset password using token"""
    db = get_database()
    
    # Find user with valid token
    user = await db.users.find_one({
        "reset_token": token,
        "reset_token_expires": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Update password
    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "hashed_password": get_password_hash(new_password)
            },
            "$unset": {
                "reset_token": "",
                "reset_token_expires": ""
            }
        }
    )
    
    return {"message": "Password reset successfully"}
