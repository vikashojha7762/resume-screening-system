import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Chip,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { uploadResume, fetchResumes } from '../store/slices/resumesSlice';
import { toast } from 'react-toastify';

const ResumeUpload: React.FC = () => {
  const dispatch = useAppDispatch();
  const { uploadProgress } = useAppSelector((state) => state.resumes);
  const [files, setFiles] = React.useState<File[]>([]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const validFiles = acceptedFiles.filter((file) => {
        const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
        return validTypes.includes(file.type);
      });

      setFiles((prev) => [...prev, ...validFiles]);

      // Upload files sequentially to avoid conflicts
      const uploadFiles = async () => {
        const uploadedFiles: string[] = [];
        for (const file of validFiles) {
          try {
            const result = await dispatch(uploadResume(file)).unwrap();
            console.log('Upload result:', result); // Debug log
            toast.success(`${file.name} uploaded successfully`);
            uploadedFiles.push(file.name);
          } catch (error: any) {
            console.error('Upload error:', error); // Debug log
            const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to upload resume';
            toast.error(`${file.name}: ${errorMessage}`);
          }
        }
        // Remove successfully uploaded files from the local state
        if (uploadedFiles.length > 0) {
          setFiles((prev) => prev.filter((f) => !uploadedFiles.includes(f.name)));
          // Refresh the resumes list after all uploads complete
          // Use a longer delay to ensure backend has processed the upload
          setTimeout(() => {
            dispatch(fetchResumes());
          }, 500);
        }
      };
      
      uploadFiles();
    },
    [dispatch]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    multiple: true,
  });

  const removeFile = (fileName: string) => {
    setFiles((prev) => prev.filter((f) => f.name !== fileName));
  };

  return (
    <Box>
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          textAlign: 'center',
          mb: 3,
        }}
      >
        <input {...getInputProps()} />
        <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop files here' : 'Drag & drop resumes here'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          or click to select files
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Supported formats: PDF, DOC, DOCX, TXT (Max 10MB per file)
        </Typography>
      </Paper>

      {files.length > 0 && (
        <Paper>
          <List>
            {files.map((file) => (
              <ListItem
                key={file.name}
                secondaryAction={
                  <IconButton edge="end" onClick={() => removeFile(file.name)}>
                    <DeleteIcon />
                  </IconButton>
                }
              >
                <ListItemText
                  primary={file.name}
                  secondaryTypographyProps={{ component: 'div' }}
                  secondary={
                    <Box component="div">
                      <Typography component="span" variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </Typography>
                      {uploadProgress[file.name] !== undefined && (
                        <Box component="div">
                          <LinearProgress
                            variant="determinate"
                            value={uploadProgress[file.name]}
                            sx={{ mb: 0.5, mt: 1 }}
                          />
                          <Typography component="span" variant="caption" sx={{ display: 'block' }}>
                            {uploadProgress[file.name]}% uploaded
                          </Typography>
                        </Box>
                      )}
                      {uploadProgress[file.name] === 100 && (
                        <Chip
                          icon={<CheckCircleIcon />}
                          label="Uploaded"
                          color="success"
                          size="small"
                          sx={{ mt: 1, display: 'inline-block' }}
                        />
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
};

export default ResumeUpload;

