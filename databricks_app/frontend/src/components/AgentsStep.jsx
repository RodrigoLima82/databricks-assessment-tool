import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Chip,
  Alert,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  SmartToy as AgentIcon,
} from '@mui/icons-material'
import axios from 'axios'
import AceEditor from 'react-ace'
import 'ace-builds/src-noconflict/mode-yaml'
import 'ace-builds/src-noconflict/theme-github'

export default function AgentsStep({ onNext, onBack, initialData }) {
  const [agents, setAgents] = useState({})
  const [tasks, setTasks] = useState({})
  const [openDialog, setOpenDialog] = useState(false)
  const [editingAgent, setEditingAgent] = useState(null)
  const [agentForm, setAgentForm] = useState({
    name: '',
    role: '',
    goal: '',
    backstory: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadAgents()
    loadTasks()
  }, [])

  const loadAgents = async () => {
    try {
      const response = await axios.get('/api/agents/list')
      setAgents(response.data.agents || {})
    } catch (error) {
      setError('Failed to load agents')
      console.error('Error loading agents:', error)
    }
  }

  const loadTasks = async () => {
    try {
      const response = await axios.get('/api/tasks/list')
      setTasks(response.data.tasks || {})
    } catch (error) {
      console.error('Error loading tasks:', error)
    }
  }

  const handleEditAgent = (agentName) => {
    const agent = agents[agentName]
    setAgentForm({
      name: agentName,
      role: agent.role,
      goal: agent.goal,
      backstory: agent.backstory,
    })
    setEditingAgent(agentName)
    setOpenDialog(true)
  }

  const handleCreateAgent = () => {
    setAgentForm({
      name: '',
      role: '',
      goal: '',
      backstory: '',
    })
    setEditingAgent(null)
    setOpenDialog(true)
  }

  const handleSaveAgent = async () => {
    setLoading(true)
    setError(null)
    
    try {
      if (editingAgent) {
        // Update existing agent
        await axios.put(`/api/agents/update/${editingAgent}`, {
          name: agentForm.name,
          role: agentForm.role,
          goal: agentForm.goal,
          backstory: agentForm.backstory,
        })
      } else {
        // Create new agent
        await axios.post('/api/agents/create', agentForm)
      }
      
      setOpenDialog(false)
      await loadAgents()
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to save agent')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAgent = async (agentName) => {
    if (!confirm(`Are you sure you want to delete agent "${agentName}"?`)) {
      return
    }
    
    try {
      await axios.delete(`/api/agents/delete/${agentName}`)
      await loadAgents()
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to delete agent')
    }
  }

  const handleNext = () => {
    onNext({ agents, tasks })
  }

  const agentCount = Object.keys(agents).length

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h6">
            AI Agents Configuration
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configure and customize your AI analysis agents
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateAgent}
        >
          Create New Agent
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2}>
        {Object.entries(agents).map(([agentName, agent]) => (
          <Grid item xs={12} md={6} key={agentName}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AgentIcon color="primary" />
                    <Typography variant="h6" component="div">
                      {agentName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Typography>
                  </Box>
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => handleEditAgent(agentName)}
                      color="primary"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteAgent(agentName)}
                      color="error"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </Box>
                
                <Chip label={agent.role} size="small" color="primary" sx={{ mb: 1 }} />
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  <strong>Goal:</strong> {agent.goal.substring(0, 100)}...
                </Typography>
                
                <Typography variant="body2" color="text.secondary">
                  <strong>Backstory:</strong> {agent.backstory.substring(0, 100)}...
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {agentCount === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No agents configured yet. Create your first agent to get started.
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between', mt: 4 }}>
        <Button onClick={onBack}>
          Back
        </Button>
        <Button
          variant="contained"
          onClick={handleNext}
          disabled={agentCount === 0}
        >
          Next: Upload UCX Files
        </Button>
      </Box>

      {/* Agent Dialog */}
      <Dialog
        open={openDialog}
        onClose={() => setOpenDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingAgent ? 'Edit Agent' : 'Create New Agent'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              fullWidth
              label="Agent Name"
              value={agentForm.name}
              onChange={(e) => setAgentForm({ ...agentForm, name: e.target.value })}
              disabled={!!editingAgent}
              helperText="Unique identifier for the agent (e.g., terraform_reader)"
            />
            
            <TextField
              fullWidth
              label="Role"
              value={agentForm.role}
              onChange={(e) => setAgentForm({ ...agentForm, role: e.target.value })}
              helperText="The role or title of the agent"
            />
            
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Goal"
              value={agentForm.goal}
              onChange={(e) => setAgentForm({ ...agentForm, goal: e.target.value })}
              helperText="What should this agent accomplish?"
            />
            
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Backstory"
              value={agentForm.backstory}
              onChange={(e) => setAgentForm({ ...agentForm, backstory: e.target.value })}
              helperText="Background and expertise of the agent"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSaveAgent}
            disabled={loading || !agentForm.name || !agentForm.role || !agentForm.goal}
          >
            {loading ? 'Saving...' : 'Save Agent'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

