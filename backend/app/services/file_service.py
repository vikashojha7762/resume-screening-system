"""
File upload and storage service
"""
import os
import uuid
from typing import Optional, BinaryIO
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class FileService:
    """Service for handling file uploads and storage"""
    
    def __init__(self):
        self.s3_client = None
        self.use_s3 = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.AWS_S3_BUCKET)
        
        if self.use_s3:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                logger.info("S3 client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {str(e)}")
                self.use_s3 = False
        else:
            # Use local storage
            self.upload_dir = Path(settings.UPLOAD_DIR)
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using local storage: {self.upload_dir}")
    
    def validate_file(self, file_content: bytes, filename: str) -> tuple[bool, Optional[str]]:
        """
        Validate uploaded file
        Returns: (is_valid, error_message)
        """
        # Check file size
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            return False, f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes"
        
        # Check file extension
        file_ext = Path(filename).suffix.lower().lstrip('.')
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            return False, f"File type {file_ext} not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        
        # Basic file type validation (check magic bytes)
        if file_ext == 'pdf' and not file_content.startswith(b'%PDF'):
            return False, "Invalid PDF file"
        
        return True, None
    
    def upload_file(self, file_content: bytes, filename: str, user_id: str) -> str:
        """
        Upload file to S3 or local storage
        Returns: file path/URL
        """
        # Validate file
        is_valid, error = self.validate_file(file_content, filename)
        if not is_valid:
            raise ValueError(error)
        
        # Generate unique filename
        file_ext = Path(filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        if self.use_s3:
            # Upload to S3
            s3_key = f"{settings.AWS_S3_RESUME_PREFIX}{user_id}/{unique_filename}"
            try:
                self.s3_client.put_object(
                    Bucket=settings.AWS_S3_BUCKET,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=self._get_content_type(file_ext)
                )
                file_path = f"s3://{settings.AWS_S3_BUCKET}/{s3_key}"
                logger.info(f"File uploaded to S3: {s3_key}")
                return file_path
            except ClientError as e:
                logger.error(f"S3 upload error: {str(e)}")
                raise Exception(f"Failed to upload file to S3: {str(e)}")
        else:
            # Save locally
            user_dir = self.upload_dir / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = user_dir / unique_filename
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"File saved locally: {file_path}")
            return str(file_path)
    
    def read_file(self, file_path: str) -> Optional[bytes]:
        """
        Read file content from S3 or local storage
        Returns: file content as bytes, or None if error
        """
        try:
            if file_path.startswith('s3://'):
                # Read from S3
                bucket, key = file_path.replace('s3://', '').split('/', 1)
                response = self.s3_client.get_object(Bucket=bucket, Key=key)
                file_content = response['Body'].read()
                logger.info(f"File read from S3: {key} ({len(file_content)} bytes)")
                return file_content
            else:
                # Read local file
                file_path_obj = Path(file_path)
                if file_path_obj.exists():
                    with open(file_path_obj, 'rb') as f:
                        file_content = f.read()
                    logger.info(f"File read locally: {file_path} ({len(file_content)} bytes)")
                    return file_content
                else:
                    logger.error(f"Local file not found: {file_path}")
                    return None
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}", exc_info=True)
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from S3 or local storage
        Returns: success status
        """
        if file_path.startswith('s3://'):
            # Delete from S3
            try:
                bucket, key = file_path.replace('s3://', '').split('/', 1)
                self.s3_client.delete_object(Bucket=bucket, Key=key)
                logger.info(f"File deleted from S3: {key}")
                return True
            except ClientError as e:
                logger.error(f"S3 delete error: {str(e)}")
                return False
        else:
            # Delete local file
            try:
                file_path_obj = Path(file_path)
                if file_path_obj.exists():
                    file_path_obj.unlink()
                    logger.info(f"File deleted locally: {file_path}")
                    return True
                return False
            except Exception as e:
                logger.error(f"Local delete error: {str(e)}")
                return False
    
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get presigned URL for S3 file or local file path
        """
        if file_path.startswith('s3://'):
            try:
                bucket, key = file_path.replace('s3://', '').split('/', 1)
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': key},
                    ExpiresIn=expires_in
                )
                return url
            except ClientError as e:
                logger.error(f"Failed to generate presigned URL: {str(e)}")
                return None
        else:
            # For local files, return the path (in production, serve via static file endpoint)
            return file_path
    
    def _get_content_type(self, file_ext: str) -> str:
        """Get content type from file extension"""
        content_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain'
        }
        return content_types.get(file_ext.lower(), 'application/octet-stream')


# Singleton instance
file_service = FileService()

