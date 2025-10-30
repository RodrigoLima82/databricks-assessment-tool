import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Checkbox,
  FormControlLabel,
  LinearProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Chip,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import {
  PlayArrow as PlayIcon,
  CheckCircle as CheckIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as WaitingIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import api, { createWebSocket } from '../api'

export default function ExecutionStep({ onNext, onBack, config }) {
  const [options, setOptions] = useState({
    runTerraform: true,
    runAgents: true,
    terraformServices: ['groups', 'users', 'compute', 'jobs', 'notebooks', 'repos', 'access', 'secrets', 'storage', 'sql-endpoints', 'dashboards'],
    terraformListing: ['compute', 'jobs', 'notebooks', 'sql-endpoints'],
    terraformDebug: false,
    selectedAgents: ['terraform_reader', 'ucx_analyst', 'report_generator'],
    reportLanguage: 'pt-BR',
  })
  
  const [executing, setExecuting] = useState(false)
  const [executionSteps, setExecutionSteps] = useState([])
  const [error, setError] = useState(null)
  const [ws, setWs] = useState(null)
  const [showLogs, setShowLogs] = useState(true)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [startTime, setStartTime] = useState(null)
  const [hasExistingReports, setHasExistingReports] = useState(false)

  // Check for existing reports on mount
  useEffect(() => {
    const checkExistingReports = async () => {
      try {
        const response = await api.get('api/results/list')
        const existingReports = response.data.reports.filter(r => r.exists)
        if (existingReports.length > 0) {
          setHasExistingReports(true)
          console.log(`Found ${existingReports.length} existing reports`)
        }
      } catch (error) {
        console.log('No existing reports found')
      }
    }
    checkExistingReports()
  }, [])

  useEffect(() => {
    return () => {
      if (ws) {
        ws.close()
      }
    }
  }, [ws])

  const connectWebSocket = () => {
    const socket = createWebSocket('ws/execution')

    socket.onopen = () => {
      console.log('WebSocket connected')
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    }

    socket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    socket.onclose = () => {
      console.log('WebSocket disconnected')
    }

    setWs(socket)
    return socket
  }

  const handleWebSocketMessage = (data) => {
    if (data.type === 'status') {
      setExecutionSteps((prev) => {
        const updated = [...prev]
        // Find the step by name instead of fixed index
        const stepIndex = updated.findIndex(step => 
          (data.step === 'terraform' && step.name === 'Terraform Export') ||
          (data.step === 'agents' && step.name === 'AI Agents Analysis')
        )
        
        if (stepIndex !== -1) {
          updated[stepIndex] = {
            ...updated[stepIndex],
            status: data.status,
            message: data.message,
            logs: data.log ? [...updated[stepIndex].logs, data.log] : updated[stepIndex].logs,
          }
        }
        return updated
      })
    } else if (data.type === 'log') {
      // Add log message to the appropriate step
      setExecutionSteps((prev) => {
        const updated = [...prev]
        // Find the step by name instead of fixed index
        const stepIndex = updated.findIndex(step => 
          (data.step === 'terraform' && step.name === 'Terraform Export') ||
          (data.step === 'agents' && step.name === 'AI Agents Analysis')
        )
        
        if (stepIndex !== -1) {
          updated[stepIndex] = {
            ...updated[stepIndex],
            logs: [...updated[stepIndex].logs, data.message],
          }
        }
        return updated
      })
    } else if (data.type === 'completed') {
      setExecuting(false)
      setHasExistingReports(true) // Mark that reports now exist
      // Wait a bit before proceeding to results
      setTimeout(() => {
        onNext({ success: true })
      }, 1500)
    } else if (data.type === 'error') {
      setError(data.message)
      setExecuting(false)
    } else if (data.type === 'stopped') {
      setExecuting(false)
      setError('Execution stopped by user.')
    }
  }

  const handleExecute = async () => {
    setExecuting(true)
    setError(null)
    setStartTime(Date.now())
    setElapsedTime(0)
    setHasExistingReports(false) // Reset on new execution
    
    // Build execution steps based on selected options
    const steps = []
    if (options.runTerraform) {
      steps.push({ name: 'Terraform Export', status: 'pending', message: '', logs: [] })
    }
    if (options.runAgents) {
      steps.push({ name: 'AI Agents Analysis', status: 'pending', message: '', logs: [] })
    }
    
    setExecutionSteps(steps)

    // Connect WebSocket
    connectWebSocket()

    // Start timer
    const timer = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - Date.now()) / 1000))
    }, 1000)

    try {
      // Ensure report_generator is always included
      const agentsToRun = options.selectedAgents.includes('report_generator') 
        ? options.selectedAgents 
        : [...options.selectedAgents, 'report_generator']
      
      await api.post('api/execute/start', {
        run_terraform: options.runTerraform,
        run_agents: options.runAgents,
        terraform_services: options.terraformServices.join(','),
        terraform_listing: options.terraformListing.join(','),
        terraform_debug: options.terraformDebug,
        selected_agents: agentsToRun.join(','),
        report_language: options.reportLanguage,
      })
    } catch (error) {
      clearInterval(timer)
      setError(error.response?.data?.detail || 'Failed to start execution')
      setExecuting(false)
    }
  }
  
  // Update elapsed time
  useEffect(() => {
    if (executing && startTime) {
      const timer = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000))
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [executing, startTime])

  const getStepIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckIcon color="success" />
      case 'running':
        return <WaitingIcon color="primary" />
      case 'error':
        return <ErrorIcon color="error" />
      default:
        return <WaitingIcon color="disabled" />
    }
  }

  const getStepColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'running':
        return 'primary'
      case 'error':
        return 'error'
      default:
        return 'default'
    }
  }

  // Show "View Results" and "Run Again" if:
  // 1. Execution just completed (executionSteps has completed steps)
  // 2. OR there are existing reports from a previous execution
  const allCompleted = 
    (executionSteps.length > 0 && executionSteps.every((step) => step.status === 'completed')) ||
    hasExistingReports

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Execute Analysis
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Run the Terraform export and AI analysis pipeline
      </Typography>

      {error && (
        <Alert 
          severity="error" 
          onClose={() => setError(null)} 
          sx={{ mb: 2 }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              startIcon={<RefreshIcon />}
              onClick={() => {
                setError(null)
                handleExecute()
              }}
            >
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      )}

      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            Execution Options
          </Typography>
          
          <FormControlLabel
            control={
              <Checkbox
                checked={options.runTerraform}
                onChange={(e) => setOptions({ ...options, runTerraform: e.target.checked })}
                disabled={executing}
              />
            }
            label="Run Terraform Export"
          />
          
          <FormControlLabel
            control={
              <Checkbox
                checked={options.runAgents}
                onChange={(e) => setOptions({ ...options, runAgents: e.target.checked })}
                disabled={executing}
              />
            }
            label="Run AI Agents Analysis"
          />
        </CardContent>
      </Card>

      {/* Terraform Export Options */}
      {options.runTerraform && (
        <Card variant="outlined" sx={{ mb: 3, bgcolor: 'grey.50' }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              Terraform Export Configuration
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Select which services and options to export
            </Typography>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Services to Export
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {['groups', 'users', 'compute', 'jobs', 'notebooks', 'repos', 'access', 'secrets', 'storage', 'sql-endpoints', 'dashboards', 'alerts', 'queries', 'policies', 'mounts', 'wsconf', 'directories', 'dlt', 'model-serving', 'vector-search', 'uc-catalogs', 'uc-schemas', 'uc-tables', 'uc-volumes', 'uc-external-locations', 'uc-storage-credentials'].map((service) => (
                  <FormControlLabel
                    key={service}
                    control={
                      <Checkbox
                        checked={options.terraformServices.includes(service)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setOptions({
                              ...options,
                              terraformServices: [...options.terraformServices, service]
                            })
                          } else {
                            setOptions({
                              ...options,
                              terraformServices: options.terraformServices.filter(s => s !== service)
                            })
                          }
                        }}
                        disabled={executing}
                        size="small"
                      />
                    }
                    label={service.charAt(0).toUpperCase() + service.slice(1)}
                  />
                ))}
              </Box>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Listing Options (resources to list and import dependencies)
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {['compute', 'jobs', 'notebooks', 'sql-endpoints', 'dashboards', 'repos', 'queries', 'alerts', 'directories', 'dlt', 'model-serving', 'vector-search', 'uc-catalogs', 'uc-schemas', 'uc-tables', 'uc-volumes'].map((listing) => (
                  <FormControlLabel
                    key={listing}
                    control={
                      <Checkbox
                        checked={options.terraformListing.includes(listing)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setOptions({
                              ...options,
                              terraformListing: [...options.terraformListing, listing]
                            })
                          } else {
                            setOptions({
                              ...options,
                              terraformListing: options.terraformListing.filter(l => l !== listing)
                            })
                          }
                        }}
                        disabled={executing}
                        size="small"
                      />
                    }
                    label={listing.charAt(0).toUpperCase() + listing.slice(1)}
                  />
                ))}
              </Box>
            </Box>

            <FormControlLabel
              control={
                <Checkbox
                  checked={options.terraformDebug}
                  onChange={(e) => setOptions({ ...options, terraformDebug: e.target.checked })}
                  disabled={executing}
                  size="small"
                />
              }
              label="Enable Debug Mode (verbose output)"
            />
          </CardContent>
        </Card>
      )}

      {/* Report Language Selection */}
      {options.runAgents && (
        <Card variant="outlined" sx={{ mb: 3, bgcolor: 'success.50' }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              🌐 Report Language
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Select the language for the assessment report
            </Typography>

            <FormControl fullWidth size="small">
              <InputLabel id="report-language-label">Language</InputLabel>
              <Select
                labelId="report-language-label"
                value={options.reportLanguage}
                label="Language"
                onChange={(e) => setOptions({ ...options, reportLanguage: e.target.value })}
                disabled={executing}
              >
                <MenuItem value="pt-BR">🇧🇷 Português (Brasil)</MenuItem>
                <MenuItem value="en-US">🇺🇸 English (United States)</MenuItem>
                <MenuItem value="es-ES">🇪🇸 Español (España)</MenuItem>
              </Select>
            </FormControl>

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="caption">
                💡 <strong>Tip:</strong> All prompts, titles, and LLM responses will be in the selected language.
              </Typography>
            </Alert>
          </CardContent>
        </Card>
      )}

      {/* AI Agents Selection */}
      {options.runAgents && (
        <Card variant="outlined" sx={{ mb: 3, bgcolor: 'info.50' }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              AI Analysis Phases
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Select which analysis phases to run
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {[
                { id: 'terraform_reader', name: '🔍 Terraform Analysis', desc: 'Analyzes Terraform files and extracts infrastructure details' },
                { id: 'ucx_analyst', name: '🔄 UCX Assessment', desc: 'Analyzes Unity Catalog migration readiness (if UCX files available)' },
                { id: 'report_generator', name: '📝 Consolidated Report', desc: 'Generates final consolidated assessment report', locked: true },
              ].map((agent) => (
                <Box key={agent.id}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={options.selectedAgents.includes(agent.id) || agent.locked}
                        onChange={(e) => {
                          if (!agent.locked) {
                            if (e.target.checked) {
                              setOptions({
                                ...options,
                                selectedAgents: [...options.selectedAgents, agent.id]
                              })
                            } else {
                              setOptions({
                                ...options,
                                selectedAgents: options.selectedAgents.filter(a => a !== agent.id)
                              })
                            }
                          }
                        }}
                        disabled={executing || agent.locked}
                        size="small"
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {agent.name}
                          {agent.locked && <Chip label="Always Enabled" size="small" color="success" sx={{ ml: 1 }} />}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {agent.desc}
                        </Typography>
                      </Box>
                    }
                  />
                </Box>
              ))}
            </Box>

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="caption">
                💡 <strong>Info:</strong> Select which analysis phases to run. The Consolidated Report always runs and combines results from all selected analyses.
              </Typography>
            </Alert>
          </CardContent>
        </Card>
      )}

      {executing && (
        <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle1">
              Execution Progress
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip 
                label={`${Math.floor(elapsedTime / 60)}:${(elapsedTime % 60).toString().padStart(2, '0')}`}
                size="small"
                color="primary"
              />
              <Button
                size="small"
                onClick={() => setShowLogs(!showLogs)}
              >
                {showLogs ? 'Hide Logs' : 'Show Logs'}
              </Button>
            </Box>
          </Box>
          
          {executionSteps.map((step, index) => (
            <Box key={step.name} sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                {getStepIcon(step.status)}
                <Typography variant="body1">
                  {step.name}
                </Typography>
                <Chip
                  label={step.status.toUpperCase()}
                  size="small"
                  color={getStepColor(step.status)}
                />
              </Box>
              {step.message && (
                <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mb: 1 }}>
                  {step.message}
                </Typography>
              )}
              {step.status === 'running' && (
                <LinearProgress sx={{ ml: 4, mr: 4, mt: 1, mb: 2 }} />
              )}
              
              {/* Real-time logs */}
              {showLogs && step.logs.length > 0 && (
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    ml: 4, 
                    p: 2, 
                    bgcolor: 'grey.900', 
                    color: 'grey.100',
                    maxHeight: 200,
                    overflow: 'auto',
                    fontFamily: 'monospace',
                    fontSize: '0.75rem'
                  }}
                >
                  {step.logs.slice(-20).map((log, idx) => (
                    <Box key={idx} sx={{ mb: 0.5 }}>
                      {log}
                    </Box>
                  ))}
                </Paper>
              )}
            </Box>
          ))}
        </Paper>
      )}

      <Card variant="outlined" sx={{ bgcolor: 'warning.50', borderColor: 'warning.main' }}>
        <CardContent>
          <Typography variant="subtitle2" color="warning.main" gutterBottom>
            ⏱️ Estimated Execution Time
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • Terraform Export: ~5 minutes<br />
            • AI Agents Analysis: ~2 minutes<br />
            • <strong>Total: ~7 minutes</strong><br />
            <em style={{ fontSize: '0.85em' }}>(measured in production workspace with 34 TF files and 3 UCX files)</em>
          </Typography>
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between', mt: 4 }}>
        <Button onClick={onBack} disabled={executing}>
          Back
        </Button>
        <Box sx={{ display: 'flex', gap: 2 }}>
          {allCompleted && (
            <Button
              variant="outlined"
              onClick={handleExecute}
              startIcon={<RefreshIcon />}
            >
              Run Again
            </Button>
          )}
          <Button
            variant="contained"
            onClick={allCompleted ? onNext : handleExecute}
            disabled={executing || (!options.runTerraform && !options.runAgents)}
            startIcon={executing ? <WaitingIcon /> : (allCompleted ? <CheckCircleIcon /> : <PlayIcon />)}
          >
            {executing ? 'Executing...' : allCompleted ? 'View Results' : 'Start Execution'}
          </Button>
        </Box>
      </Box>
    </Box>
  )
}

