import React, { useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { fetchResumes, deleteResume } from '../store/slices/resumesSlice';
import ResumeUpload from '../components/ResumeUpload';

const Resumes: React.FC = () => {
  const dispatch = useAppDispatch();
  const { resumes, isLoading } = useAppSelector((state) => state.resumes);
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [resumeToDelete, setResumeToDelete] = React.useState<string | null>(null);

  useEffect(() => {
    dispatch(fetchResumes());
  }, [dispatch]);

  const handleDelete = async (id: string) => {
    try {
      await dispatch(deleteResume(id)).unwrap();
      setDeleteDialogOpen(false);
      setResumeToDelete(null);
      // Refresh the list after deletion
      dispatch(fetchResumes());
    } catch (error) {
      // Error handling is done in the slice
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
      uploaded: 'default',
      parsing: 'primary',
      parsed: 'primary',
      processing: 'warning',
      processed: 'success',
      error: 'error',
    };
    return colors[status] || 'default';
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Resumes
      </Typography>

      <Box sx={{ mb: 4 }}>
        <ResumeUpload />
      </Box>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Card}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>File Name</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Uploaded</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {resumes.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      No resumes uploaded yet. Upload a resume using the drag-and-drop area above.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                resumes.map((resume) => (
                  <TableRow key={resume.id} hover>
                    <TableCell>{resume.file_name}</TableCell>
                    <TableCell>
                      <Chip label={resume.status} color={getStatusColor(resume.status)} size="small" />
                    </TableCell>
                    <TableCell>
                      {new Date(resume.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => {
                          setResumeToDelete(resume.id);
                          setDeleteDialogOpen(true);
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Resume</DialogTitle>
        <DialogContent>
          <Typography>Are you sure you want to delete this resume? This action cannot be undone.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => resumeToDelete && handleDelete(resumeToDelete)}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Resumes;

