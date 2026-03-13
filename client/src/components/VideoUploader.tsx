import { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { useGetUploadUrl, useUpdateAssessment } from "@/lib/api/assessments";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Label } from "@/components/ui/label";
import { 
  Upload, 
  Video, 
  X, 
  Check, 
  AlertCircle,
  FileVideo,
  Loader2
} from "lucide-react";

interface VideoUploaderProps {
  assessmentId: string;
  onUploadComplete?: () => void;
}

const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB
const ALLOWED_TYPES = ["video/mp4", "video/webm", "video/quicktime"];

export default function VideoUploader({ assessmentId, onUploadComplete }: VideoUploaderProps) {
  const navigate = useNavigate();
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const getUploadUrl = useGetUploadUrl();
  const updateAssessment = useUpdateAssessment();
  
  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `Invalid file type. Allowed: MP4, WebM, QuickTime`;
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Maximum size is 500MB`;
    }
    return null;
  };
  
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;
    
    setError(null);
    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setFile(selectedFile);
    setUploadProgress(0);
    setUploadComplete(false);
  }, []);
  
  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    const droppedFile = event.dataTransfer.files?.[0];
    if (!droppedFile) return;
    
    setError(null);
    const validationError = validateFile(droppedFile);
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setFile(droppedFile);
    setUploadProgress(0);
    setUploadComplete(false);
  }, []);
  
  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
  }, []);
  
  const handleClearFile = useCallback(() => {
    setFile(null);
    setUploadProgress(0);
    setUploadComplete(false);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);
  
  const handleUpload = async () => {
    if (!file) return;
    
    setIsUploading(true);
    setError(null);
    
    try {
      // Step 1: Get presigned URL
      const { upload_url, file_key } = await getUploadUrl.mutateAsync({
        id: assessmentId,
        data: {
          filename: file.name,
          content_type: file.type,
          file_size: file.size,
        }
      });
      
      // Step 2: Upload directly to S3 using presigned URL
      await uploadToS3(upload_url, file, (progress) => {
        setUploadProgress(progress);
      });
      
      setUploadComplete(true);
      
      // Step 3: Update assessment with file info
      await updateAssessment.mutateAsync({
        id: assessmentId,
        data: {
          status: "uploading",
        }
      });
      
      toast({
        title: "Upload Complete",
        description: "Your video has been uploaded successfully. Processing will begin shortly.",
      });
      
      onUploadComplete?.();
    } catch (err) {
      console.error("Upload error:", err);
      setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };
  
  const uploadToS3 = async (
    url: string, 
    file: File, 
    onProgress: (progress: number) => void
  ): Promise<void> => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener("progress", (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress(progress);
        }
      });
      
      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });
      
      xhr.addEventListener("error", () => {
        reject(new Error("Upload failed. Please check your connection."));
      });
      
      xhr.addEventListener("abort", () => {
        reject(new Error("Upload was cancelled"));
      });
      
      xhr.open("PUT", url);
      xhr.setRequestHeader("Content-Type", file.type);
      xhr.send(file);
    });
  };
  
  return (
    <Card className="w-full max-w-lg mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Video className="h-5 w-5" />
          Upload Recording
        </CardTitle>
        <CardDescription>
          Upload your oracy assessment video recording
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Drop Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
            transition-colors duration-200
            ${file 
              ? "border-green-500 bg-green-50 dark:bg-green-950" 
              : "border-gray-300 hover:border-gray-400 dark:border-gray-600 dark:hover:border-gray-500"
            }
            ${error ? "border-red-500 bg-red-50" : ""}
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="video/mp4,video/webm,video/quicktime"
            onChange={handleFileSelect}
            className="hidden"
            disabled={isUploading}
          />
          
          {file ? (
            <div className="flex items-center justify-center gap-3">
              <FileVideo className="h-10 w-10 text-green-600" />
              <div className="text-left">
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  {file.name}
                </p>
                <p className="text-sm text-gray-500">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
              {!isUploading && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearFile();
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          ) : (
            <>
              <Upload className="h-10 w-10 mx-auto text-gray-400 mb-3" />
              <p className="text-gray-600 dark:text-gray-300 font-medium">
                Drop your video here or click to browse
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Supports MP4, WebM, QuickTime (max 500MB)
              </p>
            </>
          )}
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="flex items-center gap-2 text-red-600 text-sm">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}
        
        {/* Upload Progress */}
        {isUploading && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Uploading...</span>
              <span className="font-medium">{uploadProgress}%</span>
            </div>
            <Progress value={uploadProgress} className="h-2" />
          </div>
        )}
        
        {/* Upload Complete */}
        {uploadComplete && (
          <div className="flex items-center gap-2 text-green-600 text-sm">
            <Check className="h-4 w-4" />
            Upload complete! Your video is being processed.
          </div>
        )}
        
        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <Button
            onClick={handleUpload}
            disabled={!file || isUploading || uploadComplete}
            className="flex-1"
          >
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Uploading...
              </>
            ) : uploadComplete ? (
              <>
                <Check className="h-4 w-4 mr-2" />
                Uploaded
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Start Upload
              </>
            )}
          </Button>
          
          {uploadComplete && (
            <Button variant="outline" onClick={() => navigate("/pupil")}>
              Continue
            </Button>
          )}
        </div>
        
        {/* Tips */}
        <div className="text-sm text-gray-500 space-y-1 pt-2">
          <p className="font-medium">Tips for a great recording:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Ensure good lighting on your face</li>
            <li>Position camera at eye level</li>
            <li>Speak clearly and at a natural pace</li>
            <li>Keep videos under 5 minutes</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
