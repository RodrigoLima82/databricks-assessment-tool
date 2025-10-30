import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  PictureAsPdf as PdfIcon,
  Refresh as RefreshIcon,
  Article as ArticleIcon,
  Html as HtmlIcon,
} from '@mui/icons-material'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import api from '../api'

export default function ResultsStep({ onBack, onReset }) {
  const [reports, setReports] = useState([])
  const [selectedReport, setSelectedReport] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [exportingPdf, setExportingPdf] = useState(false)
  const [exportingHtml, setExportingHtml] = useState(false)

  useEffect(() => {
    loadReportsList()
  }, [])

  const loadReportsList = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await api.get('api/results/list')
      const availableReports = response.data.reports.filter(r => r.exists)
      setReports(availableReports)
      
      // Select consolidated report by default
      const consolidatedReport = availableReports.find(r => r.agent === 'report_generator')
      if (consolidatedReport) {
        setSelectedReport(consolidatedReport)
        await loadReport(consolidatedReport.filename)
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to load reports list')
    } finally {
      setLoading(false)
    }
  }

  const loadReport = async (filename) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await api.get(`api/results/report/${filename}`)
      setReport(response.data)
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to load report')
    } finally {
      setLoading(false)
    }
  }

  const handleReportSelect = (reportConfig) => {
    setSelectedReport(reportConfig)
    loadReport(reportConfig.filename)
  }

  const handleExportPdf = async () => {
    if (!selectedReport) return
    
    setExportingPdf(true)
    try {
      // For now, only consolidated report supports PDF export
      const response = await api.get('api/results/export-pdf', {
        responseType: 'blob',
      })
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'Databricks_Assessment_Report.pdf')
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
    } catch (error) {
      if (error.response?.status === 500) {
        setError('PDF export requires WeasyPrint to be installed on the server')
      } else {
      setError('Failed to export PDF')
    }
  } finally {
    setExportingPdf(false)
  }
}

  const handleExportHtml = async () => {
    if (!selectedReport) return
    
    setExportingHtml(true)
    try {
      const response = await api.get('api/results/export-html', {
        responseType: 'blob',
      })
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/html' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'Databricks_Assessment_Report.html')
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
    } catch (error) {
      setError('Failed to export HTML: ' + (error.response?.data?.detail || error.message))
    } finally {
      setExportingHtml(false)
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading assessment report...
        </Typography>
      </Box>
    )
  }

  if (error && !report) {
    return (
      <Box>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={loadReport}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box>
          <Typography variant="h6">
            Assessment Results
          </Typography>
          <Typography variant="body2" color="text.secondary">
            View and export Databricks infrastructure assessment reports
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh">
            <IconButton onClick={loadReportsList} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Export HTML (Interactive Report)">
            <IconButton
              onClick={handleExportHtml}
              disabled={exportingHtml || !selectedReport || selectedReport.agent !== 'report_generator'}
              color="primary"
            >
              {exportingHtml ? <CircularProgress size={24} /> : <HtmlIcon />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Export PDF (Consolidated Report Only)">
            <IconButton
              onClick={handleExportPdf}
              disabled={exportingPdf || !selectedReport || selectedReport.agent !== 'report_generator'}
              color="secondary"
            >
              {exportingPdf ? <CircularProgress size={24} /> : <PdfIcon />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="warning" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {reports.length > 0 && (
        <Card variant="outlined" sx={{ mb: 2, bgcolor: 'success.50', borderColor: 'success.main' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ArticleIcon color="success" />
              <Box>
                <Typography variant="subtitle2" color="success.main">
                  {reports.length} Report(s) Generated Successfully
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Select a report below to view details
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Reports Navigation */}
      {reports.length > 1 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Available Reports:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {reports.map((reportConfig) => (
              <Card
                key={reportConfig.filename}
                variant="outlined"
                sx={{
                  cursor: 'pointer',
                  minWidth: 200,
                  bgcolor: selectedReport?.filename === reportConfig.filename ? 'primary.50' : 'inherit',
                  borderColor: selectedReport?.filename === reportConfig.filename ? 'primary.main' : 'divider',
                  borderWidth: selectedReport?.filename === reportConfig.filename ? 2 : 1,
                  transition: 'all 0.2s',
                  '&:hover': {
                    bgcolor: 'action.hover',
                    transform: 'translateY(-2px)',
                    boxShadow: 2,
                  }
                }}
                onClick={() => handleReportSelect(reportConfig)}
              >
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Typography variant="h6">{reportConfig.icon}</Typography>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      {reportConfig.title}
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {reportConfig.description}
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 0.5 }}>
                    {(reportConfig.size / 1024).toFixed(1)} KB
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Box>
        </Box>
      )}

      <Card variant="outlined">
        <CardContent sx={{ maxHeight: '600px', overflow: 'auto', p: 3 }}>
          {report?.format === 'html' ? (
            // Render HTML directly with styling already included
            <Box
              dangerouslySetInnerHTML={{ __html: report?.content || '' }}
              sx={{
                // Override some MUI defaults to match the HTML styles
                '& table': {
                  marginTop: 2,
                  marginBottom: 2,
                },
              }}
            />
          ) : (
            // Render Markdown using ReactMarkdown
            <Box
              sx={{
                '& h1': {
                  fontSize: '2rem',
                  fontWeight: 600,
                  mt: 3,
                  mb: 2,
                  color: 'primary.main',
                },
                '& h2': {
                  fontSize: '1.5rem',
                  fontWeight: 600,
                  mt: 3,
                  mb: 1.5,
                  color: 'primary.dark',
                },
                '& h3': {
                  fontSize: '1.25rem',
                  fontWeight: 600,
                  mt: 2,
                  mb: 1,
                },
                '& p': {
                  lineHeight: 1.7,
                  mb: 2,
                },
                '& ul, & ol': {
                  pl: 3,
                  mb: 2,
                },
                '& li': {
                  mb: 0.5,
                },
                '& table': {
                  width: '100%',
                  borderCollapse: 'collapse',
                  mb: 2,
                  '& th': {
                    bgcolor: 'grey.100',
                    p: 1,
                    border: '1px solid',
                    borderColor: 'divider',
                    fontWeight: 600,
                  },
                  '& td': {
                    p: 1,
                    border: '1px solid',
                    borderColor: 'divider',
                  },
                },
                '& code': {
                  bgcolor: 'grey.100',
                  px: 0.5,
                  py: 0.25,
                  borderRadius: 0.5,
                  fontFamily: 'monospace',
                },
                '& pre': {
                  bgcolor: 'grey.900',
                  p: 2,
                  borderRadius: 1,
                  overflow: 'auto',
                },
                '& blockquote': {
                  borderLeft: '4px solid',
                  borderColor: 'primary.main',
                  pl: 2,
                  py: 0.5,
                  my: 2,
                  bgcolor: 'grey.50',
                },
              }}
            >
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    )
                  },
                }}
              >
                {report?.content || ''}
              </ReactMarkdown>
            </Box>
          )}
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between', mt: 4 }}>
        <Button onClick={onBack}>
          Back to Execution
        </Button>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button variant="outlined" onClick={handleExportPdf} startIcon={<PdfIcon />}>
            Export PDF
          </Button>
          <Button variant="contained" onClick={onReset}>
            Start New Assessment
          </Button>
        </Box>
      </Box>
    </Box>
  )
}

