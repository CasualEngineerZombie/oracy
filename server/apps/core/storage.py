"""
Storage utilities for the Oracy AI platform.

Provides S3-compatible storage operations with proper error handling,
configuration management, and security features.
"""

import logging
import tempfile
from contextlib import contextmanager
from typing import BinaryIO, Generator, Optional
from urllib.parse import urlparse

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class S3StorageError(Exception):
    """Base exception for S3 storage errors."""
    pass


class S3DownloadError(S3StorageError):
    """Exception raised when S3 download fails."""
    pass


class S3UploadError(S3StorageError):
    """Exception raised when S3 upload fails."""
    pass


class S3StorageService:
    """
    Service for S3-compatible storage operations.
    
    Provides secure, configured access to S3 for video/audio storage.
    Supports AWS S3, MinIO, and other S3-compatible services.
    """
    
    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        bucket: Optional[str] = None
    ):
        """
        Initialize S3 storage service.
        
        Args:
            access_key: AWS access key (defaults to settings.AWS_ACCESS_KEY_ID)
            secret_key: AWS secret key (defaults to settings.AWS_SECRET_ACCESS_KEY)
            region: AWS region (defaults to settings.AWS_S3_REGION_NAME)
            endpoint_url: Custom endpoint for S3-compatible services (e.g., MinIO)
            bucket: S3 bucket name (defaults to settings.AWS_STORAGE_BUCKET_NAME)
        """
        self.access_key = access_key or getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        self.secret_key = secret_key or getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        self.region = region or getattr(settings, 'AWS_S3_REGION_NAME', 'ap-southeast-1')
        self.endpoint_url = endpoint_url or getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        self.bucket = bucket or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
        
        if not self.bucket:
            raise ImproperlyConfigured("AWS_STORAGE_BUCKET_NAME must be configured")
        
        self._client = None
        self._resource = None
    
    @property
    def client(self):
        """Get or create boto3 S3 client."""
        if self._client is None:
            config = Config(
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'adaptive'}
            )
            
            client_kwargs = {
                'region_name': self.region,
                'config': config,
            }
            
            if self.access_key and self.secret_key:
                client_kwargs['aws_access_key_id'] = self.access_key
                client_kwargs['aws_secret_access_key'] = self.secret_key
            
            if self.endpoint_url:
                client_kwargs['endpoint_url'] = self.endpoint_url
            
            self._client = boto3.client('s3', **client_kwargs)
        
        return self._client
    
    @property
    def resource(self):
        """Get or create boto3 S3 resource."""
        if self._resource is None:
            resource_kwargs = {'region_name': self.region}
            
            if self.access_key and self.secret_key:
                resource_kwargs['aws_access_key_id'] = self.access_key
                resource_kwargs['aws_secret_access_key'] = self.secret_key
            
            if self.endpoint_url:
                resource_kwargs['endpoint_url'] = self.endpoint_url
            
            self._resource = boto3.resource('s3', **resource_kwargs)
        
        return self._resource
    
    def download_file(
        self,
        key: str,
        bucket: Optional[str] = None,
        local_path: Optional[str] = None
    ) -> str:
        """
        Download a file from S3.
        
        Args:
            key: S3 object key
            bucket: S3 bucket (defaults to configured bucket)
            local_path: Local file path (defaults to temp file)
            
        Returns:
            Path to downloaded file
            
        Raises:
            S3DownloadError: If download fails
        """
        bucket = bucket or self.bucket
        
        try:
            if local_path is None:
                # Create temp file with appropriate suffix
                suffix = self._get_suffix_from_key(key)
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    local_path = tmp.name
            
            logger.debug(f"Downloading s3://{bucket}/{key} to {local_path}")
            self.client.download_file(bucket, key, local_path)
            logger.info(f"Successfully downloaded s3://{bucket}/{key}")
            
            return local_path
            
        except NoCredentialsError as e:
            logger.error(f"AWS credentials not found: {e}")
            raise S3DownloadError(f"AWS credentials not configured: {e}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"S3 download error ({error_code}): {error_msg}")
            raise S3DownloadError(f"Failed to download {key}: {error_msg}")
        except Exception as e:
            logger.error(f"Unexpected error downloading {key}: {e}")
            raise S3DownloadError(f"Unexpected error: {e}")
    
    @contextmanager
    def download_temp(
        self,
        key: str,
        bucket: Optional[str] = None
    ) -> Generator[str, None, None]:
        """
        Context manager for temporary file download.
        
        Automatically cleans up the temp file after use.
        
        Example:
            with s3_service.download_temp('recordings/video.mp4') as local_path:
                process_video(local_path)
        """
        local_path = None
        try:
            local_path = self.download_file(key, bucket)
            yield local_path
        finally:
            if local_path:
                import os
                try:
                    os.unlink(local_path)
                    logger.debug(f"Cleaned up temp file: {local_path}")
                except OSError as e:
                    logger.warning(f"Failed to clean up temp file {local_path}: {e}")
    
    def upload_file(
        self,
        local_path: str,
        key: str,
        bucket: Optional[str] = None,
        extra_args: Optional[dict] = None
    ) -> str:
        """
        Upload a file to S3.
        
        Args:
            local_path: Path to local file
            key: S3 object key
            bucket: S3 bucket (defaults to configured bucket)
            extra_args: Additional args for upload_file (e.g., ContentType, ACL)
            
        Returns:
            S3 URI of uploaded file (s3://bucket/key)
            
        Raises:
            S3UploadError: If upload fails
        """
        bucket = bucket or self.bucket
        extra_args = extra_args or {}
        
        # Set default content type if not specified
        if 'ContentType' not in extra_args:
            content_type = self._get_content_type(key)
            if content_type:
                extra_args['ContentType'] = content_type
        
        # Never allow public ACL - always private
        if 'ACL' in extra_args:
            del extra_args['ACL']
        
        try:
            logger.debug(f"Uploading {local_path} to s3://{bucket}/{key}")
            self.client.upload_file(local_path, bucket, key, ExtraArgs=extra_args)
            logger.info(f"Successfully uploaded to s3://{bucket}/{key}")
            return f"s3://{bucket}/{key}"
            
        except NoCredentialsError as e:
            logger.error(f"AWS credentials not found: {e}")
            raise S3UploadError(f"AWS credentials not configured: {e}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"S3 upload error ({error_code}): {error_msg}")
            raise S3UploadError(f"Failed to upload {key}: {error_msg}")
        except Exception as e:
            logger.error(f"Unexpected error uploading {key}: {e}")
            raise S3UploadError(f"Unexpected error: {e}")
    
    def upload_data(
        self,
        data: BinaryIO,
        key: str,
        bucket: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload binary data to S3.
        
        Args:
            data: Binary data to upload
            key: S3 object key
            bucket: S3 bucket (defaults to configured bucket)
            content_type: MIME type of content
            
        Returns:
            S3 URI of uploaded file
        """
        bucket = bucket or self.bucket
        
        if content_type is None:
            content_type = self._get_content_type(key)
        
        try:
            extra_args = {'ContentType': content_type} if content_type else {}
            
            self.client.upload_fileobj(data, bucket, key, ExtraArgs=extra_args)
            logger.info(f"Successfully uploaded data to s3://{bucket}/{key}")
            return f"s3://{bucket}/{key}"
            
        except Exception as e:
            logger.error(f"Failed to upload data to {key}: {e}")
            raise S3UploadError(f"Failed to upload: {e}")
    
    def delete_file(self, key: str, bucket: Optional[str] = None) -> bool:
        """
        Delete a file from S3.
        
        Args:
            key: S3 object key
            bucket: S3 bucket (defaults to configured bucket)
            
        Returns:
            True if deleted, False if not found
        """
        bucket = bucket or self.bucket
        
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted s3://{bucket}/{key}")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found for deletion: s3://{bucket}/{key}")
                return False
            logger.error(f"Error deleting {key}: {e}")
            raise
    
    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        bucket: Optional[str] = None,
        http_method: str = 'get'
    ) -> str:
        """
        Generate a presigned URL for temporary access.
        
        Args:
            key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)
            bucket: S3 bucket (defaults to configured bucket)
            http_method: HTTP method ('get' or 'put')
            
        Returns:
            Presigned URL string
        """
        bucket = bucket or self.bucket
        client_method = 'get_object' if http_method == 'get' else 'put_object'
        
        try:
            url = self.client.generate_presigned_url(
                ClientMethod=client_method,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {key}: {e}")
            raise S3StorageError(f"Failed to generate URL: {e}")
    
    def file_exists(self, key: str, bucket: Optional[str] = None) -> bool:
        """
        Check if a file exists in S3.
        
        Args:
            key: S3 object key
            bucket: S3 bucket (defaults to configured bucket)
            
        Returns:
            True if file exists, False otherwise
        """
        bucket = bucket or self.bucket
        
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    def get_file_metadata(self, key: str, bucket: Optional[str] = None) -> dict:
        """
        Get metadata for an S3 object.
        
        Args:
            key: S3 object key
            bucket: S3 bucket (defaults to configured bucket)
            
        Returns:
            Dictionary with metadata (ContentType, ContentLength, LastModified, etc.)
        """
        bucket = bucket or self.bucket
        
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            logger.error(f"Failed to get metadata for {key}: {e}")
            raise S3StorageError(f"Failed to get metadata: {e}")
    
    def _get_suffix_from_key(self, key: str) -> str:
        """Extract file suffix from S3 key."""
        import os
        _, ext = os.path.splitext(key)
        return ext if ext else '.tmp'
    
    def _get_content_type(self, key: str) -> Optional[str]:
        """Determine content type from file extension."""
        import mimetypes
        content_type, _ = mimetypes.guess_type(key)
        return content_type


# Convenience functions for use in tasks and views

def get_storage_service() -> S3StorageService:
    """Get configured S3 storage service instance."""
    return S3StorageService()


def download_from_s3(key: str, bucket: Optional[str] = None) -> str:
    """
    Download file from S3 to temporary location.
    
    DEPRECATED: Use S3StorageService.download_temp() context manager instead
    for automatic cleanup.
    """
    service = get_storage_service()
    return service.download_file(key, bucket)


def upload_to_s3(local_path: str, key: str, bucket: Optional[str] = None) -> str:
    """Upload file to S3."""
    service = get_storage_service()
    return service.upload_file(local_path, key, bucket)


@contextmanager
def s3_temp_download(key: str, bucket: Optional[str] = None):
    """
    Context manager for temporary S3 file download with automatic cleanup.
    
    Example:
        with s3_temp_download('recordings/video.mp4') as local_path:
            process_video(local_path)
    """
    service = get_storage_service()
    with service.download_temp(key, bucket) as local_path:
        yield local_path
