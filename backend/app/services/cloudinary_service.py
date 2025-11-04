"""
Cloudinary service for file uploads and management
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from typing import Dict, Optional
import os

# Configure Cloudinary
try:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )
    print(f"✅ Cloudinary configured successfully")
    print(f"   Cloud name: {settings.CLOUDINARY_CLOUD_NAME}")
    print(f"   API key: {settings.CLOUDINARY_API_KEY[:10]}...")  # Only show first 10 chars
except Exception as e:
    print(f"❌ Cloudinary configuration failed: {e}")
    raise


class CloudinaryService:
    """Service for handling Cloudinary uploads and deletions"""
    
    @staticmethod
    async def upload_file(
        file: UploadFile,
        folder: str = "exam_resources",
        resource_type: str = "auto"
    ) -> Dict[str, str]:
        """
        Upload a file to Cloudinary
        
        Args:
            file: The uploaded file
            folder: Cloudinary folder name
            resource_type: 'image', 'raw', or 'auto'
        
        Returns:
            Dict containing url, public_id, format, and resource_type
        """
        try:
            # Read file content
            file_content = await file.read()
            
            # Reset file pointer
            await file.seek(0)
            
            # Determine resource type based on file type
            if file.content_type.startswith('image/'):
                resource_type = 'image'
            else:
                resource_type = 'raw'  # For PDFs, DOCX, PPTX, etc.
            
            # Upload to Cloudinary with optimizations
            # Increase timeout for large files and slow connections
            upload_result = cloudinary.uploader.upload(
                file_content,
                folder=folder,
                resource_type=resource_type,
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                chunk_size=6000000,  # 6MB chunks for large files
                timeout=600  # 10 minute timeout for slow connections
            )
            
            print(f"✅ Uploaded to Cloudinary: {upload_result['public_id']}")
            
            return {
                "url": upload_result['secure_url'],
                "public_id": upload_result['public_id'],
                "format": upload_result.get('format', ''),
                "resource_type": upload_result['resource_type'],
                "bytes": upload_result.get('bytes', 0),
                "created_at": upload_result.get('created_at', '')
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Cloudinary upload error: {error_msg}")
            
            # Provide helpful error messages
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                raise HTTPException(
                    status_code=500,
                    detail="Upload timeout - File is too large or connection is slow. Try: 1) Compress the file, 2) Use a faster internet connection, 3) Upload a smaller file (under 5MB recommended)"
                )
            elif "connection" in error_msg.lower():
                raise HTTPException(
                    status_code=500,
                    detail="Connection error - Check your internet connection and try again"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload file to Cloudinary: {error_msg}"
                )
    
    @staticmethod
    async def delete_file(public_id: str, resource_type: str = "raw") -> bool:
        """
        Delete a file from Cloudinary
        
        Args:
            public_id: The Cloudinary public ID
            resource_type: 'image', 'raw', or 'video'
        
        Returns:
            True if deleted successfully
        """
        try:
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type
            )
            
            if result.get('result') == 'ok':
                print(f"✅ Deleted from Cloudinary: {public_id}")
                return True
            else:
                print(f"⚠️ Cloudinary delete result: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Cloudinary delete error: {str(e)}")
            return False
    
    @staticmethod
    def get_file_info(public_id: str, resource_type: str = "raw") -> Optional[Dict]:
        """
        Get information about a file from Cloudinary
        
        Args:
            public_id: The Cloudinary public ID
            resource_type: 'image', 'raw', or 'video'
        
        Returns:
            Dict with file information or None
        """
        try:
            result = cloudinary.api.resource(
                public_id,
                resource_type=resource_type
            )
            return result
        except Exception as e:
            print(f"❌ Error fetching file info: {str(e)}")
            return None


# Global instance
cloudinary_service = CloudinaryService()
