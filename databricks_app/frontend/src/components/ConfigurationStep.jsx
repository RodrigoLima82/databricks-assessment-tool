import React, { useState, useEffect } from 'react'
import {
  Box,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Typography,
  Grid,
  InputAdornment,
  IconButton,
} from '@mui/material'
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material'
import api from '../api'

export default function ConfigurationStep({ onNext, initialData }) {
  const [config, setConfig] = useState({
    databricks_host: initialData?.databricks_host || '',
    databricks_token: initialData?.databricks_token || '',
    terraform_path: initialData?.terraform_path || '',
  })
  
  const [validation, setValidation] = useState({
    databricks: null,
    terraform: null,
    message: '',
  })
  
  const [loading, setLoading] = useState(false)
  const [showToken, setShowToken] = useState(false)

  useEffect(() => {
    // Load existing configuration on mount
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const response = await api.get('api/config/load')
      if (response.data.exists) {
        setConfig(response.data.config)
      }
    } catch (error) {
      console.error('Error loading config:', error)
    }
  }

  const handleValidate = async () => {
    setLoading(true)
    setValidation({ databricks: null, terraform: null, message: '' })
    
    try {
      const response = await api.post('api/config/validate', config)
      setValidation(response.data)
      
      if (response.data.databricks && response.data.terraform) {
        // Auto-save if validation succeeds
        await handleSave()
      }
    } catch (error) {
      setValidation({
        databricks: false,
        terraform: false,
        message: error.response?.data?.detail || 'Validation failed',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      await axios.post('/api/config/save', config)
    } catch (error) {
      console.error('Error saving config:', error)
    }
  }

  const handleNext = () => {
    onNext(config)
  }

  const isValid = validation.databricks && validation.terraform

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Database Configuration
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure your Databricks workspace credentials and Terraform settings
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Databricks Host"
            placeholder="https://your-workspace.cloud.databricks.com"
            value={config.databricks_host}
            onChange={(e) =>
              setConfig({ ...config, databricks_host: e.target.value })
            }
            variant="outlined"
            helperText="Your Databricks workspace URL"
            InputProps={{
              endAdornment: validation.databricks !== null && (
                <InputAdornment position="end">
                  {validation.databricks ? (
                    <CheckIcon color="success" />
                  ) : (
                    <ErrorIcon color="error" />
                  )}
                </InputAdornment>
              ),
            }}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Databricks Token"
            type={showToken ? 'text' : 'password'}
            value={config.databricks_token}
            onChange={(e) =>
              setConfig({ ...config, databricks_token: e.target.value })
            }
            variant="outlined"
            helperText="Personal Access Token or Service Principal token"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowToken(!showToken)}
                    edge="end"
                  >
                    {showToken ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                  {validation.databricks !== null && (
                    validation.databricks ? (
                      <CheckIcon color="success" sx={{ ml: 1 }} />
                    ) : (
                      <ErrorIcon color="error" sx={{ ml: 1 }} />
                    )
                  )}
                </InputAdornment>
              ),
            }}
          />
        </Grid>

        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Terraform Path (Optional)"
            placeholder="/usr/local/bin/terraform"
            value={config.terraform_path}
            onChange={(e) =>
              setConfig({ ...config, terraform_path: e.target.value })
            }
            variant="outlined"
            helperText="Leave empty to use Terraform from PATH"
            InputProps={{
              endAdornment: validation.terraform !== null && (
                <InputAdornment position="end">
                  {validation.terraform ? (
                    <CheckIcon color="success" />
                  ) : (
                    <ErrorIcon color="error" />
                  )}
                </InputAdornment>
              ),
            }}
          />
        </Grid>

        {validation.message && (
          <Grid item xs={12}>
            <Alert
              severity={isValid ? 'success' : 'error'}
              icon={isValid ? <CheckIcon /> : <ErrorIcon />}
            >
              {validation.message}
            </Alert>
          </Grid>
        )}

        <Grid item xs={12}>
          <Card variant="outlined" sx={{ bgcolor: 'grey.50' }}>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>
                📋 Configuration Checklist
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2 }}>
                <Typography component="li" variant="body2">
                  ✓ Databricks workspace URL (e.g., https://xxxxx.cloud.databricks.com)
                </Typography>
                <Typography component="li" variant="body2">
                  ✓ Valid access token with appropriate permissions
                </Typography>
                <Typography component="li" variant="body2">
                  ✓ Terraform installed (run <code>terraform --version</code> to verify)
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              onClick={handleValidate}
              disabled={loading || !config.databricks_host || !config.databricks_token}
              startIcon={loading && <CircularProgress size={16} />}
            >
              {loading ? 'Validating...' : 'Test Connection'}
            </Button>
            <Button
              variant="contained"
              onClick={handleNext}
              disabled={!isValid}
            >
              Next: Upload UCX (Optional)
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  )
}

