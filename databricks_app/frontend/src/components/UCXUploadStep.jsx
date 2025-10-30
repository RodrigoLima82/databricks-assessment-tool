import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Alert,
  CircularProgress,
  Paper,
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  InsertDriveFile as FileIcon,
} from '@mui/icons-material'
import api from '../api'

export default function UCXUploadStep({ onNext, onBack, initialData }) {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  useEffect(() => {
    loadFiles()
  }, [])

  const loadFiles = async () => {
    try {
      const response = await api.get('api/ucx/files')
      setFiles(response.data.files || [])
    } catch (error) {
      console.error('Error loading files:', error)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    // Validate file type
    const validExtensions = ['.csv', '.xlsx', '.xls']
    const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
    
    if (!validExtensions.includes(fileExtension)) {
      setError('Invalid file type. Please upload CSV or Excel files only.')
      return
    }

    setUploading(true)
    setError(null)
    setSuccess(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('api/ucx/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setSuccess(response.data.message)
      await loadFiles()
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to upload file')
    } finally {
      setUploading(false)
      // Reset file input
      event.target.value = ''
    }
  }

  const handleDeleteFile = async (filename) => {
    if (!confirm(`Delete "${filename}"?`)) return

    try {
      await api.delete(`api/ucx/delete/${filename}`)
      setSuccess(`File "${filename}" deleted successfully`)
      await loadFiles()
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to delete file')
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  const handleNext = () => {
    onNext({ files })
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        UCX Assessment Files
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Upload Unity Catalog Migration (UCX) assessment files from your clients
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Card variant="outlined" sx={{ mb: 3, p: 3, textAlign: 'center', bgcolor: 'grey.50' }}>
        <input
          accept=".csv,.xlsx,.xls"
          style={{ display: 'none' }}
          id="ucx-file-upload"
          type="file"
          onChange={handleFileUpload}
          disabled={uploading}
        />
        <label htmlFor="ucx-file-upload">
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            {uploading ? (
              <CircularProgress size={48} />
            ) : (
              <UploadIcon sx={{ fontSize: 48, color: 'primary.main' }} />
            )}
            <Typography variant="body1">
              {uploading ? 'Uploading...' : 'Click or drag files to upload'}
            </Typography>
            <Button
              variant="contained"
              component="span"
              disabled={uploading}
              startIcon={<UploadIcon />}
            >
              Select File
            </Button>
            <Typography variant="caption" color="text.secondary">
              Supported formats: CSV, XLSX, XLS
            </Typography>
          </Box>
        </label>
      </Card>

      {files.length > 0 ? (
        <Paper variant="outlined">
          <List>
            {files.map((file, index) => (
              <ListItem
                key={file.name}
                divider={index < files.length - 1}
              >
                <FileIcon color="primary" sx={{ mr: 2 }} />
                <ListItemText
                  primary={file.name}
                  secondary={`${formatFileSize(file.size)} • Uploaded ${formatDate(file.modified)}`}
                />
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    onClick={() => handleDeleteFile(file.name)}
                    color="error"
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Paper>
      ) : (
        <Alert severity="info">
          No UCX assessment files uploaded yet. Upload at least one file to continue.
        </Alert>
      )}

      <Card variant="outlined" sx={{ mt: 3, bgcolor: 'info.50', borderColor: 'info.main' }}>
        <CardContent>
          <Typography variant="subtitle2" color="info.main" gutterBottom>
            💡 About UCX Assessment Files
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Upload your Unity Catalog Migration (UCX) assessment exports. The AI agents will analyze
            migration readiness, compatibility issues, and generate recommendations for a smooth transition
            to Unity Catalog.
          </Typography>
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between', mt: 4 }}>
        <Button onClick={onBack}>
          Back
        </Button>
        <Button
          variant="contained"
          onClick={handleNext}
        >
          Next: Execute Analysis
        </Button>
      </Box>
    </Box>
  )
}

