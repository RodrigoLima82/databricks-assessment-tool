import React, { useState, useEffect } from 'react'
import {
  Box,
  Container,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Typography,
  AppBar,
  Toolbar,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  Settings as SettingsIcon,
  SmartToy as AgentIcon,
  Upload as UploadIcon,
  PlayArrow as ExecuteIcon,
  Assessment as ResultsIcon,
} from '@mui/icons-material'
import axios from 'axios'

// Step components
import ConfigurationStep from './components/ConfigurationStep'
import AgentsStep from './components/AgentsStep'
import UCXUploadStep from './components/UCXUploadStep'
import ExecutionStep from './components/ExecutionStep'
import ResultsStep from './components/ResultsStep'

const steps = [
  {
    label: 'Configuration',
    description: 'Configure Databricks credentials and Terraform',
    icon: <SettingsIcon />,
  },
  {
    label: 'Agents Setup',
    description: 'Configure AI agents and tasks',
    icon: <AgentIcon />,
  },
  {
    label: 'UCX Assessment',
    description: 'Upload UCX assessment files',
    icon: <UploadIcon />,
  },
  {
    label: 'Execute',
    description: 'Run Terraform export and AI analysis',
    icon: <ExecuteIcon />,
  },
  {
    label: 'Results',
    description: 'View and export assessment reports',
    icon: <ResultsIcon />,
  },
]

function App() {
  const [activeStep, setActiveStep] = useState(0)
  const [stepData, setStepData] = useState({
    configuration: null,
    agents: null,
    ucx: null,
    execution: null,
  })
  const [checkingReports, setCheckingReports] = useState(true)

  // Check for existing reports on mount
  useEffect(() => {
    const checkExistingReports = async () => {
      try {
        const response = await axios.get('/api/results/list')
        const existingReports = response.data.reports.filter(r => r.exists)
        
        if (existingReports.length > 0) {
          console.log(`Found ${existingReports.length} existing reports, jumping to Results step`)
          
          // Mark all previous steps as completed
          setStepData({
            configuration: { completed: true },
            agents: { completed: true },
            ucx: { completed: true },
            execution: { completed: true },
          })
          
          setActiveStep(4) // Jump to Results step (index 4)
        }
      } catch (error) {
        console.log('No existing reports found or error checking:', error)
      } finally {
        setCheckingReports(false)
      }
    }
    
    checkExistingReports()
  }, [])

  const handleNext = (data) => {
    // Save step data
    const stepKeys = ['configuration', 'agents', 'ucx', 'execution', 'results']
    if (stepKeys[activeStep]) {
      setStepData((prev) => ({
        ...prev,
        [stepKeys[activeStep]]: data,
      }))
    }
    setActiveStep((prevActiveStep) => prevActiveStep + 1)
  }

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1)
  }

  const handleReset = () => {
    setActiveStep(0)
    setStepData({
      configuration: null,
      agents: null,
      ucx: null,
      execution: null,
    })
  }

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <ConfigurationStep
            onNext={handleNext}
            initialData={stepData.configuration}
          />
        )
      case 1:
        return (
          <AgentsStep
            onNext={handleNext}
            onBack={handleBack}
            initialData={stepData.agents}
          />
        )
      case 2:
        return (
          <UCXUploadStep
            onNext={handleNext}
            onBack={handleBack}
            initialData={stepData.ucx}
          />
        )
      case 3:
        return (
          <ExecutionStep
            onNext={handleNext}
            onBack={handleBack}
            config={stepData.configuration}
          />
        )
      case 4:
        return (
          <ResultsStep
            onBack={handleBack}
            onReset={handleReset}
          />
        )
      default:
        return null
    }
  }

  // Show loading screen while checking for existing reports
  if (checkingReports) {
    return (
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center', 
        justifyContent: 'center',
        minHeight: '100vh',
        bgcolor: 'grey.50'
      }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 3, color: 'text.secondary' }}>
          Checking for existing reports...
        </Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar position="static" elevation={0} sx={{ bgcolor: 'primary.main' }}>
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <img
              src="/databricks-logo-white.svg"
              alt="Databricks"
              style={{ height: 32 }}
              onError={(e) => {
                e.target.style.display = 'none'
              }}
            />
            <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
              Databricks Assessment Tool
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, flex: 1 }}>
        <Paper elevation={2} sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
            Infrastructure Assessment Workflow
          </Typography>
          
          <Stepper activeStep={activeStep} orientation="vertical">
            {steps.map((step, index) => (
              <Step key={step.label}>
                <StepLabel
                  optional={
                    index === steps.length - 1 ? (
                      <Typography variant="caption">Last step</Typography>
                    ) : null
                  }
                  StepIconComponent={() => (
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: 40,
                        height: 40,
                        borderRadius: '50%',
                        bgcolor:
                          activeStep === index
                            ? 'primary.main'
                            : activeStep > index
                            ? 'secondary.main'
                            : 'grey.300',
                        color: 'white',
                      }}
                    >
                      {step.icon}
                    </Box>
                  )}
                >
                  <Typography variant="h6">{step.label}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {step.description}
                  </Typography>
                </StepLabel>
                <StepContent>
                  <Box sx={{ mt: 2 }}>{getStepContent(index)}</Box>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </Paper>
      </Container>

      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 2,
          px: 2,
          mt: 'auto',
          backgroundColor: 'grey.100',
          borderTop: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary" align="center">
            Databricks Assessment Tool
          </Typography>
        </Container>
      </Box>
    </Box>
  )
}

export default App

