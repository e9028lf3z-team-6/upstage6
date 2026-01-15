import React, { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import {
  deleteAnalysis,
  deleteDocument,
  getAnalysis,
  getDocument,
  listAnalysesByDoc,
  listDocuments,
  runAnalysis,
  uploadDocument
} from './api.js'

//  docx export
// 설치: npm i docx
import { Document as DocxDocument, Packer, Paragraph, TextRun } from 'docx'

function pretty(obj) {
  try { return JSON.stringify(obj, null, 2) } catch { return String(obj) }
}

function Badge({ children }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      border: '1px solid #2a2a2c',
      borderRadius: 999,
      fontSize: 12,
      color: '#cfcfd6'
    }}>
      {children}
    </span>
  )
}

const ISSUE_COLORS = {
  tone: 'rgba(0, 150, 136, 0.4)',
  logic: 'rgba(255, 202, 40, 0.4)',
  causality: 'rgba(255, 202, 40, 0.4)',
  trauma: 'rgba(239, 83, 80, 0.45)',
  hate_bias: 'rgba(171, 71, 188, 0.4)',
  genre_cliche: 'rgba(66, 165, 245, 0.4)',
  cliche: 'rgba(66, 165, 245, 0.4)',
  spelling: 'rgba(239, 83, 80, 0.3)',
  tension: 'rgba(255, 112, 67, 0.4)',
  default: 'rgba(158, 158, 158, 0.35)'
}

function HighlightedText({ text, analysisResult }) {
  const rawHighlights = Array.isArray(analysisResult?.highlights) ? analysisResult.highlights : []
  const rawNormalized = Array.isArray(analysisResult?.normalized_issues) ? analysisResult.normalized_issues : []
  const hasDocHighlights = rawHighlights.length > 0 || rawNormalized.length > 0

  if (hasDocHighlights && typeof text === 'string') {
    const textLen = text.length
    const severityRank = { high: 3, medium: 2, low: 1 }

    const highlightItems = []
    const sourceItems = rawHighlights.length > 0
      ? rawHighlights.map(item => ({
        agent: item.agent,
        severity: item.severity,
        label: item.label || item.issue_type,
        reason: item.reason,
        doc_start: item.doc_start,
        doc_end: item.doc_end
      }))
      : rawNormalized.map(item => ({
        agent: item.agent,
        severity: item.severity,
        label: item.issue_type,
        reason: item.reason,
        doc_start: item.location?.doc_start,
        doc_end: item.location?.doc_end
      }))

    sourceItems.forEach(item => {
      const start = Number.isFinite(item.doc_start)
        ? Math.max(0, Math.min(textLen, Math.floor(item.doc_start)))
        : null
      const end = Number.isFinite(item.doc_end)
        ? Math.max(0, Math.min(textLen, Math.floor(item.doc_end)))
        : null
      if (start === null || end === null || end <= start) return
      highlightItems.push({ ...item, start, end })
    })

    if (highlightItems.length === 0) {
      return <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{text}</div>
    }

    const boundaries = new Set([0, textLen])
    highlightItems.forEach(item => {
      boundaries.add(item.start)
      boundaries.add(item.end)
    })
    const points = Array.from(boundaries).sort((a, b) => a - b)

    const segments = []
    for (let i = 0; i < points.length - 1; i += 1) {
      const start = points[i]
      const end = points[i + 1]
      if (end <= start) continue
      const segmentText = text.slice(start, end)
      const issues = highlightItems.filter(item => item.start < end && item.end > start)
      segments.push({ start, end, text: segmentText, issues })
    }

    return (
      <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontSize: 13 }}>
        {segments.map(segment => {
          if (!segment.issues.length) {
            return <span key={`${segment.start}-${segment.end}`}>{segment.text}</span>
          }

          const sortedIssues = [...segment.issues].sort((a, b) => {
            const rankDiff = (severityRank[b.severity] || 0) - (severityRank[a.severity] || 0)
            if (rankDiff !== 0) return rankDiff
            return String(a.agent || '').localeCompare(String(b.agent || ''))
          })
          const primary = sortedIssues[0]
          const color = ISSUE_COLORS[primary.agent] || ISSUE_COLORS.default
          const title = sortedIssues.map(issue => {
            const agent = issue.agent || 'unknown'
            const severity = issue.severity ? ` (${issue.severity})` : ''
            const label = issue.label || 'issue'
            const reason = issue.reason ? ` - ${issue.reason}` : ''
            return `${agent}${severity}: ${label}${reason}`
          }).join('\n')

          return (
            <mark
              key={`${segment.start}-${segment.end}`}
              style={{ backgroundColor: color, color: '#fff', padding: '0 2px', borderRadius: 2 }}
              title={title}
            >
              {segment.text}
            </mark>
          )
        })}
      </div>
    )
  }

  if (!analysisResult?.split_sentences || !analysisResult?.split_map) {
    return <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{text}</div>
  }

  const sentences = analysisResult.split_sentences
  // Aggregate all issues from different agents
  let allIssues = []

  // Helper to collect issues
  const collect = (source, type) => {
    if (source?.issues && Array.isArray(source.issues)) {
      source.issues.forEach(issue => {
        allIssues.push({ ...issue, type })
      })
    }
  }

  collect(analysisResult.tone, 'tone')
  // ✅ logic / causality 분리 (기존엔 둘 중 하나를 logic으로만 묶어서 causality 색상/표시가 깨짐)
  collect(analysisResult.logic, 'logic')
  collect(analysisResult.causality, 'causality')
  collect(analysisResult.trauma, 'trauma')
  collect(analysisResult.hate_bias, 'hate_bias')
  collect(analysisResult.genre_cliche, 'genre_cliche')
  collect(analysisResult.spelling, 'spelling')
  collect(analysisResult.tension_curve, 'tension')

  const issuesBySentence = {}
  allIssues.forEach(issue => {
    if (typeof issue.sentence_index === 'number') {
      if (!issuesBySentence[issue.sentence_index]) {
        issuesBySentence[issue.sentence_index] = []
      }
      issuesBySentence[issue.sentence_index].push(issue)
    }
  })

  return (
    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontSize: 13 }}>
      {sentences.map((sent, idx) => {
        const sentIssues = issuesBySentence[idx] || []
        if (sentIssues.length === 0) {
          return <span key={idx}>{sent} </span>
        }

        sentIssues.sort((a, b) => (a.char_start || 0) - (b.char_start || 0))

        let lastIndex = 0
        const fragments = []

        sentIssues.forEach((issue, i) => {
          const start = issue.char_start || 0
          const end = issue.char_end || sent.length

          if (start > lastIndex) {
            fragments.push(<span key={`txt-${i}`}>{sent.slice(lastIndex, start)}</span>)
          }

          const color = ISSUE_COLORS[issue.type] || ISSUE_COLORS.default
          const title = `${issue.type.toUpperCase()}: ${issue.reason || issue.suggestion || 'Issue found'}`

          fragments.push(
            <mark
              key={`iss-${i}`}
              style={{ backgroundColor: color, color: '#fff', padding: '0 2px', borderRadius: 2 }}
              title={title}
            >
              {sent.slice(start, end)}
            </mark>
          )

          lastIndex = end
        })

        if (lastIndex < sent.length) {
          fragments.push(<span key="end">{sent.slice(lastIndex)}</span>)
        }

        return (
          <span key={idx} style={{ marginRight: 4 }}>
            {fragments}
          </span>
        )
      })}
    </div>
  )
}

function formatElapsed(sec) {
  const s = Math.max(0, Math.floor(sec || 0))
  const m = Math.floor(s / 60)
  const r = s % 60
  if (m <= 0) return `${r}s`
  return `${m}m ${r}s`
}

function pad2(n) {
  return String(n).padStart(2, '0')
}

function makeTimestampName(prefix = 'note') {
  const d = new Date()
  const y = d.getFullYear()
  const mo = pad2(d.getMonth() + 1)
  const da = pad2(d.getDate())
  const h = pad2(d.getHours())
  const mi = pad2(d.getMinutes())
  const s = pad2(d.getSeconds())
  return `${prefix}_${y}${mo}${da}_${h}${mi}${s}`
}

function formatDisplayTimestamp(value) {
  if (!value) return ''
  const raw = String(value).trim()
  const tzPattern = /([zZ]|[+\-]\d{2}:?\d{2})$/
  const baseMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?/)

  let dateStringToParse = raw
  if (baseMatch && !tzPattern.test(raw)) {
    // 타임존 정보가 없는 timestamp는 UTC로 간주 (ISO 8601 형식)
    dateStringToParse = raw.replace(' ', 'T') + 'Z'
  }

  const parsed = new Date(dateStringToParse)
  if (Number.isNaN(parsed.getTime())) return raw
  const parts = new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).formatToParts(parsed).reduce((acc, part) => {
    if (part.type !== 'literal') acc[part.type] = part.value
    return acc
  }, {})
  if (!parts.year) return raw
  return `${parts.year}-${parts.month}-${parts.day}   ${parts.hour}:${parts.minute}:${parts.second}`
}

function scoreColor(score) {
  if (score >= 80) return '#4caf50'
  if (score >= 60) return '#ffb74d'
  return '#f44336'
}

const TOAST_STYLES = {
  success: { borderColor: '#2e7d32', background: 'rgba(46, 125, 50, 0.45)' },
  warning: { borderColor: '#ed6c02', background: 'rgba(237, 108, 2, 0.45)' },
  info: { borderColor: '#1976d2', background: 'rgba(25, 118, 210, 0.45)' },
  error: { borderColor: '#d32f2f', background: 'rgba(211, 47, 47, 0.45)' }
}

const PERSONA_LEGEND = [
  { key: 'spelling', label: '맞춤법 에이전트' },
  { key: 'causality', label: '개연성 에이전트' },
  { key: 'hate_bias', label: '혐오·편향 에이전트' },
  { key: 'cliche', label: '장르 클리셰 에이전트' },
  { key: 'tension', label: '긴장도 에이전트' }
]

export default function App() {
  const [user, setUser] = useState(null)

  const [docs, setDocs] = useState([])
  const [activeDocId, setActiveDocId] = useState(null)
  const [activeDoc, setActiveDoc] = useState(null)
  const [analyses, setAnalyses] = useState([])
  const [activeAnalysis, setActiveAnalysis] = useState(null)

  const [loading, setLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState(null)

  // settings
  const [personaCount, setPersonaCount] = useState(3)
  const [creativeFocus, setCreativeFocus] = useState(true)
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme')
    return saved === 'light' ? 'light' : 'dark'
  })

  const [toasts, setToasts] = useState([])

  const [leftMode, setLeftMode] = useState('list')
  const [isDragOver, setIsDragOver] = useState(false)

  const fileRef = useRef(null)
  const uploaderFileRef = useRef(null)
  const toastIdRef = useRef(0)

  const [rightView, setRightView] = useState('report')

  const [analysisElapsedSec, setAnalysisElapsedSec] = useState(0)
  const analysisTimerRef = useRef(null)

  const [draftText, setDraftText] = useState('')
  const [isSavingDraft, setIsSavingDraft] = useState(false)
  const planLabel = 'Plus'
  const userDisplayName = user?.name || '사용자'
  const userInitial = (userDisplayName || '').trim().slice(0, 1) || 'U'

  //  download hover menu
  const [isDownloadOpen, setIsDownloadOpen] = useState(false)
  const downloadCloseTimer = useRef(null)
  const [isLegendOpen, setIsLegendOpen] = useState(false)
  const legendCloseTimer = useRef(null)
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false)
  const accountMenuRef = useRef(null)
  const [docScoreOpenId, setDocScoreOpenId] = useState(null)
  const [docScoreById, setDocScoreById] = useState({})
  const [docScoreLoadingId, setDocScoreLoadingId] = useState(null)
  const [docHistoryOpenId, setDocHistoryOpenId] = useState(null)
  const [docHistoryById, setDocHistoryById] = useState({})
  const [docHistoryLoadingId, setDocHistoryLoadingId] = useState(null)

  function pushToast(message, variant = 'info') {
    const id = (toastIdRef.current += 1)
    setToasts(prev => [...prev, { id, message, variant }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 2400)
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    if (token) {
      localStorage.setItem('token', token)
      window.history.replaceState({}, document.title, "/")
    }

    const savedToken = localStorage.getItem('token')
    if (savedToken) {
      import('./api.js').then(api => {
        api.getMe()
          .then(u => setUser(u))
          .catch(() => localStorage.removeItem('token'))
      })
    }
  }, [])

  useEffect(() => {
    if (!isAccountMenuOpen) return
    const handleClick = (event) => {
      if (accountMenuRef.current && !accountMenuRef.current.contains(event.target)) {
        setIsAccountMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [isAccountMenuOpen])

  useEffect(() => {
    document.documentElement.style.colorScheme = theme
    localStorage.setItem('theme', theme)
  }, [theme])

  async function onLogin() {
    window.location.href = 'http://localhost:8000/api/auth/login'
  }

  async function onLogout() {
    import('./api.js').then(api => api.logout())
    setUser(null)
  }

  async function refreshDocs(pickFirstIfEmpty = true) {
    const items = await listDocuments()
    setDocs(items)
    if (pickFirstIfEmpty && !activeDocId && items.length) setActiveDocId(items[0].id)
    return items
  }

  useEffect(() => {
    refreshDocs(true).catch(e => setError(String(e)))
    // eslint-disable-next-line
  }, [])

  useEffect(() => {
    if (!activeDocId) return
    setLoading(true); setError(null)
    Promise.all([
      getDocument(activeDocId),
      listAnalysesByDoc(activeDocId),
    ]).then(([d, a]) => {
      setActiveDoc(d)
      setAnalyses(a)
      setActiveAnalysis(null)
      setRightView('report')
    }).catch(e => setError(String(e))).finally(() => setLoading(false))
  }, [activeDocId])

  useEffect(() => {
    if (!activeAnalysis?.document_id) return
    const scores = activeAnalysis?.result?.qa_scores
    if (!scores) return
    setDocScoreById(prev => ({ ...prev, [activeAnalysis.document_id]: scores }))
  }, [activeAnalysis])

  useEffect(() => {
    if (!isAnalyzing) {
      if (analysisTimerRef.current) {
        clearInterval(analysisTimerRef.current)
        analysisTimerRef.current = null
      }
      return
    }

    analysisTimerRef.current = setInterval(() => {
      setAnalysisElapsedSec(prev => prev + 1)
    }, 1000)

    return () => {
      if (analysisTimerRef.current) {
        clearInterval(analysisTimerRef.current)
        analysisTimerRef.current = null
      }
    }
  }, [isAnalyzing])

  async function uploadOneFile(file) {
    if (!file) return
    setIsUploading(true)
    setError(null)

    try {
      const doc = await uploadDocument(file)
      await refreshDocs(false)
      setActiveDocId(doc.id)

      setLeftMode('list')
      setIsDragOver(false)

      if (fileRef.current) fileRef.current.value = ''
      if (uploaderFileRef.current) uploaderFileRef.current.value = ''

      pushToast('업로드가 완료되었습니다.', 'success')
    } catch (e2) {
      setError(String(e2))
    } finally {
      setIsUploading(false)
    }
  }

  async function onUpload(e) {
    const f = e.target.files?.[0]
    if (!f) return
    await uploadOneFile(f)
  }

  async function onUploadFromUploader(e) {
    const f = e.target.files?.[0]
    if (!f) return
    await uploadOneFile(f)
  }

  async function onSaveDraft() {
    const text = (draftText ?? '').trim()
    if (!text) {
      pushToast('저장할 텍스트를 입력하세요.', 'warning')
      return
    }

    setIsSavingDraft(true)
    setError(null)

    try {
      const filename = makeTimestampName('draft')
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
      const file = new File([blob], `${filename}.txt`, { type: 'text/plain' })

      const doc = await uploadDocument(file)
      await refreshDocs(false)
      setActiveDocId(doc.id)

      setDraftText('')
      pushToast('텍스트가 .txt 원고로 저장되었습니다.', 'success')
    } catch (e2) {
      setError(String(e2))
    } finally {
      setIsSavingDraft(false)
    }
  }

  async function onRunAnalysis() {
    if (!activeDocId) return

    setAnalysisElapsedSec(0)
    setIsAnalyzing(true); setError(null)

    try {
      const a = await runAnalysis(activeDocId, { personaCount, creativeFocus })
      const full = await getAnalysis(a.id)
      const list = await listAnalysesByDoc(activeDocId)
      setAnalyses(list)
      setActiveAnalysis(full)
      setRightView('report')
      pushToast('분석이 완료되었습니다.', 'success')
    } catch (e2) {
      setError(String(e2))
    } finally {
      setIsAnalyzing(false)
    }
  }

  async function onDeleteDoc(id) {
    if (!id) return
    const target = docs.find(x => x.id === id)
    const label = target ? `${target.title} (${target.filename})` : id
    if (!window.confirm(`원고를 삭제할까요?\n\n${label}\n\n※ 연결된 분석 기록도 함께 삭제됩니다.`)) return

    setLoading(true); setError(null)
    try {
      await deleteDocument(id)
      const items = await listDocuments()
      setDocs(items)

      if (id === activeDocId) {
        const nextId = items[0]?.id || null
        setActiveDocId(nextId)
        if (!nextId) {
          setActiveDoc(null)
          setAnalyses([])
          setActiveAnalysis(null)
          setRightView('report')
        }
      }
    } catch (e2) {
      setError(String(e2))
    } finally {
      setLoading(false)
    }
  }

  async function onOpenDocScore(docId) {
    if (!docId) return
    if (docScoreOpenId === docId) {
      setDocScoreOpenId(null)
      return
    }

    setDocScoreOpenId(docId)
    if (docScoreById[docId]) return

    setDocScoreLoadingId(docId)
    try {
      const list = await listAnalysesByDoc(docId)
      if (!list.length) {
        pushToast('분석 기록이 없습니다.', 'warning')
        return
      }
      const latestId = list[0].id
      const full = await getAnalysis(latestId)
      const qaScores = full?.result?.qa_scores || {}
      setDocScoreById(prev => ({ ...prev, [docId]: qaScores }))
    } catch (err) {
      pushToast('점수 정보를 불러오지 못했습니다.', 'error')
    } finally {
      setDocScoreLoadingId(null)
    }
  }

  async function onToggleDocHistory(docId) {
    if (!docId) return
    if (docHistoryOpenId === docId) {
      setDocHistoryOpenId(null)
      return
    }

    setDocHistoryOpenId(docId)
    setDocHistoryLoadingId(docId)
    try {
      const list = await listAnalysesByDoc(docId)
      setDocHistoryById(prev => ({ ...prev, [docId]: list }))
    } catch (err) {
      pushToast('문서 기록을 불러오지 못했습니다.', 'error')
    } finally {
      setDocHistoryLoadingId(null)
    }
  }

  async function onSelectDocAnalysis(docId, analysisId) {
    if (!docId || !analysisId) return
    setDocHistoryOpenId(null)
    setDocScoreOpenId(docId)
    await openAnalysis(analysisId)
    setRightView('report')
  }

  async function onDeleteAnalysis(id) {
    if (!id) return
    if (!window.confirm(`분석 결과를 삭제할까요?\n\n${id}`)) return

    setLoading(true); setError(null)
    try {
      await deleteAnalysis(id)
      const list = await listAnalysesByDoc(activeDocId)
      setAnalyses(list)
      if (activeAnalysis?.id === id) {
        setActiveAnalysis(null)
        setRightView('report')
      }
    } catch (e2) {
      setError(String(e2))
    } finally {
      setLoading(false)
    }
  }

  async function openAnalysis(id) {
    setLoading(true); setError(null)
    try {
      const full = await getAnalysis(id)
      setActiveAnalysis(full)
      setRightView('report')
    } catch (e2) {
      setError(String(e2))
    } finally {
      setLoading(false)
    }
  }

  async function openLatestDocScore(docId) {
    if (!docId) return
    setDocScoreOpenId(docId)
    setDocScoreLoadingId(docId)
    try {
      const list = await listAnalysesByDoc(docId)
      if (!list.length) {
        pushToast('분석 기록이 없습니다.', 'warning')
        return
      }
      const latestId = list[0].id
      await openAnalysis(latestId)
    } catch (err) {
      pushToast('점수 정보를 불러오지 못했습니다.', 'error')
    } finally {
      setDocScoreLoadingId(null)
    }
  }

  const readerLevel = activeAnalysis?.result?.final_metric?.reader_level
  const mode = activeAnalysis?.result?.debug?.mode || (activeAnalysis ? 'upstage_pipeline' : null)
  const reportMarkdown = activeAnalysis?.result?.report?.full_report_markdown
  const canShowJson = !!activeAnalysis
  const historyDoc = docHistoryOpenId ? docs.find(doc => doc.id === docHistoryOpenId) : null

  function openUploadPanel() {
    setLeftMode('upload')
    setIsDragOver(false)
    setError(null)
  }

  function openSettingsPanel() {
    setLeftMode(prev => (prev === 'settings' ? 'list' : 'settings'))
    setIsDragOver(false)
    setError(null)
  }

  function closeLeftPanelToList() {
    if (isUploading) return
    setLeftMode('list')
    setIsDragOver(false)
  }

  function onDragOver(e) {
    e.preventDefault()
    e.stopPropagation()
    if (!isDragOver) setIsDragOver(true)
  }

  function onDragLeave(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  async function onDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    if (isUploading) return
    const file = e.dataTransfer?.files?.[0]
    if (!file) return
    await uploadOneFile(file)
  }

  // toggle sizes
  const SWITCH_W = 44
  const SWITCH_H = 24
  const SWITCH_PAD = 3
  const KNOB = SWITCH_H - SWITCH_PAD * 2
  const KNOB_TRAVEL = SWITCH_W - SWITCH_PAD * 2 - KNOB

  // -----------------------------
  //  Front-only download helpers
  // -----------------------------
  const docTitleBase =
    (activeDoc?.title || activeDoc?.filename || 'document')
      .replace(/[\\/:*?"<>|]/g, '_')
      .slice(0, 80)

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1200)
  }

  function exportAsTxt() {
    const text = (activeDoc?.extracted_text || '').trim()
    if (!text) {
      pushToast('내보낼 텍스트가 없습니다.', 'warning')
      return
    }
    const filename = `${docTitleBase}_${makeTimestampName('export')}.txt`
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    downloadBlob(blob, filename)
    pushToast('txt로 저장했습니다.', 'success')
  }

  async function exportAsDocx() {
    const text = (activeDoc?.extracted_text || '').trim()
    if (!text) {
      pushToast('내보낼 텍스트가 없습니다.', 'warning')
      return
    }

    const lines = text.split(/\r?\n/)
    const paragraphs = lines.map(line =>
      new Paragraph({
        children: [new TextRun({ text: line || ' ' })]
      })
    )

    const doc = new DocxDocument({
      sections: [{ children: paragraphs }]
    })

    const blob = await Packer.toBlob(doc)
    const filename = `${docTitleBase}_${makeTimestampName('export')}.docx`
    downloadBlob(blob, filename)
    pushToast('docx로 저장했습니다.', 'success')
  }

  function onDownloadEnter() {
    if (downloadCloseTimer.current) {
      clearTimeout(downloadCloseTimer.current)
      downloadCloseTimer.current = null
    }
    setIsDownloadOpen(true)
  }

  function onDownloadLeave() {
    downloadCloseTimer.current = setTimeout(() => {
      setIsDownloadOpen(false)
    }, 180)
  }

  function onLegendEnter() {
    if (legendCloseTimer.current) {
      clearTimeout(legendCloseTimer.current)
      legendCloseTimer.current = null
    }
    setIsLegendOpen(true)
  }

  function onLegendLeave() {
    legendCloseTimer.current = setTimeout(() => {
      setIsLegendOpen(false)
    }, 180)
  }

  return (
    <>
      <style>{`
        body {
          scrollbar-width: none;
          -ms-overflow-style: none;
        }
        body::-webkit-scrollbar {
          width: 0;
          height: 0;
        }
        .scroll-hide {
          scrollbar-width: none;
          -ms-overflow-style: none;
        }
        .scroll-hide::-webkit-scrollbar {
          width: 0;
          height: 0;
        }
        .account-bar {
          width: 100%;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 8px 10px;
          border: 1px solid #2a2a2c;
          border-radius: 12px;
          background: #141417;
          color: #e6e6ea;
          cursor: pointer;
          transition: background 0.18s ease, border-color 0.18s ease;
        }
        .account-bar:hover {
          background: #1b1b1f;
          border-color: #3a3a3f;
        }
        .account-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: #2a2a2c;
          display: grid;
          place-items: center;
          overflow: hidden;
          color: #cfcfd6;
          font-weight: 700;
          font-size: 12px;
          flex: 0 0 auto;
        }
        .account-meta {
          display: flex;
          flex-direction: column;
          gap: 2px;
          min-width: 0;
          flex: 1;
        }
        .account-name {
          font-size: 13px;
          font-weight: 700;
          color: #e6e6ea;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .account-plan {
          font-size: 11px;
          color: #9aa0a6;
        }
        .account-pill {
          font-size: 10px;
          font-weight: 700;
          padding: 2px 8px;
          border-radius: 999px;
          border: 1px solid #2a2a2c;
          background: #101014;
          color: #cfcfd6;
          flex: 0 0 auto;
        }
        @media (max-width: 640px) {
          .account-bar {
            padding: 6px 8px;
            gap: 8px;
          }
          .account-plan {
            display: none;
          }
        }
      `}</style>
      <div className="scroll-hide" style={{
        display: 'grid',
        gridTemplateColumns: '300px 1fr 480px',
        height: '100vh',
        gap: 8,
        background: '#0f0f12',
        filter: theme === 'light' ? 'invert(1) hue-rotate(180deg)' : 'none',
        transition: 'filter 0.2s ease'
      }}>
        {/* Toast notifications */}
        {toasts.length > 0 && (
          <div style={{
            position: 'fixed',
            top: 24,
            right: 24,
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            zIndex: 1200,
            pointerEvents: 'none'
          }}>
            {toasts.map(t => {
              const style = TOAST_STYLES[t.variant] || TOAST_STYLES.info
              return (
                <div
                  key={t.id}
                  style={{
                    border: `1px solid ${style.borderColor}`,
                    background: style.background,
                    color: '#e6e6ea',
                    padding: '10px 12px',
                    borderRadius: 8,
                    minWidth: 220,
                    fontSize: 13,
                    boxShadow: '0 6px 16px rgba(0,0,0,0.35)'
                  }}
                >
                  {t.message}
                </div>
              )
            })}
          </div>
        )}

        {/* Left panel */}
        <div className="card" style={{ padding: 8, overflow: 'hidden', display: 'flex', flexDirection: 'column', minHeight: 0 }}>

          {/* Header + Upload button */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 700 }}>CONTEXTOR</div>
              <div className="muted" style={{ fontSize: 12 }}>PDF/DOCX/HWP 업로드</div>
            </div>

            <button
              className="btn"
              onClick={openUploadPanel}
              disabled={isUploading}
              style={{ opacity: isUploading ? 0.7 : 1, cursor: isUploading ? 'not-allowed' : 'pointer' }}
              title={isUploading ? '업로드 중…' : '내부 저장소 업로드'}
            >
              업로드
            </button>

            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.docx,.txt,.md,.hwp,.hwpx"
              onChange={onUpload}
              style={{ display: 'none' }}
              disabled={isUploading}
            />
          </div>

          <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {loading ? <Badge>loading</Badge> : <Badge>ready</Badge>}
            {docs.length ? <Badge>{docs.length} docs</Badge> : <Badge>no docs</Badge>}
            {isUploading && <Badge>uploading…</Badge>}
            {isAnalyzing && <Badge>analyzing…</Badge>}
            {isSavingDraft && <Badge>saving…</Badge>}
          </div>

          {/* scroll area */}
          <div className="scroll-hide" style={{ marginTop: 14, flex: 1, minHeight: 0, overflow: 'auto', paddingBottom: 12 }}>
            {/* Upload panel */}
            {leftMode === 'upload' && (
              <div>
                <div className="card" style={{
                  padding: 12,
                  border: '3px solid #2a2a2c',
                  background: 'rgba(46, 125, 50, 0.18)',
                  marginBottom: 10,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 10
                }}>
                  <div>
                    <div style={{ fontWeight: 800, fontSize: 16 }}>내부저장소</div>
                    <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                      파일을 업로드하거나 드래그 앤 드롭하세요.
                    </div>
                  </div>

                  <button
                    className="btn"
                    onClick={closeLeftPanelToList}
                    disabled={isUploading}
                    style={{
                      opacity: isUploading ? 0.7 : 1,
                      cursor: isUploading ? 'not-allowed' : 'pointer',
                      width: 100,
                      height: 42,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                    title="되돌아오기"
                  >
                    돌아가기
                  </button>
                </div>

                <div
                  className="card"
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onDrop={onDrop}
                  style={{
                    padding: 14,
                    border: `3px dashed ${isDragOver ? '#6aa9ff' : '#2a2a2c'}`,
                    background: isDragOver ? 'rgba(50, 100, 200, 0.22)' : 'rgba(50, 100, 200, 0.12)',
                    minHeight: 220,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    gap: 10
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 700 }}>
                    {isDragOver ? '여기에 놓으세요' : '마우스로 파일을 드래그해서 드랍하세요'}
                  </div>
                  <div className="muted" style={{ fontSize: 12 }}>
                    지원 확장자: <span className="mono">.pdf .docx .txt .md .hwp .hwpx</span>
                  </div>

                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 6 }}>
                    <label
                      className="btn"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 8,
                        opacity: isUploading ? 0.7 : 1,
                        cursor: isUploading ? 'not-allowed' : 'pointer',
                        pointerEvents: isUploading ? 'none' : 'auto',
                      }}
                      title={isUploading ? '업로드 중…' : '파일 선택'}
                    >
                      <span>{isUploading ? '업로드 중…' : '파일 선택'}</span>
                      <input
                        ref={uploaderFileRef}
                        type="file"
                        accept=".pdf,.docx,.txt,.md,.hwp,.hwpx"
                        onChange={onUploadFromUploader}
                        style={{ display: 'none' }}
                        disabled={isUploading}
                      />
                    </label>

                    {isUploading && (
                      <div className="muted" style={{ fontSize: 12 }}>
                        업로드중입니다… 잠시만 기다려주세요.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Settings panel */}
            {leftMode === 'settings' && (
              <div>
                <div className="card" style={{
                  padding: 12,
                  border: '3px solid #2a2a2c',
                  background: '#141417',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 10
                }}>
                  <div>
                    <div style={{ fontWeight: 800, fontSize: 16 }}>설정</div>
                    <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                      설정 내용은 나중에 추가할 것
                    </div>
                  </div>
                </div>

                <div className="card" style={{
                  marginTop: 10,
                  padding: 14,
                  minHeight: 320,
                  border: '3px solid #2a2a2c',
                  background: '#0f0f12'
                }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 10 }}>
                        <div>
                          <div style={{ fontWeight: 800, fontSize: 16 }}>페르소나 갯수</div>
                          <div className="muted" style={{ fontSize: 12 }}>1(디폴트 3) 최대 5</div>
                        </div>
                        <span className="mono" style={{
                          padding: '4px 10px',
                          borderRadius: 10,
                          border: '1px solid #2a2a2c',
                          background: '#141417',
                          fontSize: 13,
                          fontWeight: 900,
                          color: '#e6e6ea',
                          minWidth: 44,
                          textAlign: 'center'
                        }}>
                          {personaCount}명
                        </span>
                      </div>

                      <div>
                        <input
                          type="range"
                          min={1}
                          max={5}
                          step={1}
                          value={personaCount}
                          onChange={(e) => setPersonaCount(Number(e.target.value))}
                          style={{ width: '100%', boxSizing: 'border-box', padding: 0 }}
                        />
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
                          <span className="muted" style={{ fontSize: 11 }}>1</span>
                          <span className="muted" style={{ fontSize: 11 }}>5</span>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 16 }}>집중 모드</div>
                        <div className="muted" style={{ fontSize: 12 }}>창의성 ↔ 직관성</div>
                      </div>

                      <button
                        className="btn"
                        type="button"
                        onClick={() => setCreativeFocus(prev => !prev)}
                        aria-pressed={creativeFocus}
                        style={{
                          minWidth: 150,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: 10,
                          padding: '6px 10px'
                        }}
                      >
                        <span style={{ fontSize: 12, fontWeight: 800 }}>
                          {creativeFocus ? '창의성 중심' : '직관성'}
                        </span>

                        <span aria-hidden="true" style={{
                          width: SWITCH_W,
                          height: SWITCH_H,
                          borderRadius: 999,
                          background: creativeFocus ? '#66bb6a' : '#555',
                          position: 'relative',
                          display: 'inline-block',
                          padding: SWITCH_PAD,
                          boxSizing: 'border-box',
                          transition: 'background 0.18s ease',
                          border: '1px solid #2a2a2c'
                        }}>
                          <span style={{
                            width: KNOB,
                            height: KNOB,
                            borderRadius: '50%',
                            background: '#0f0f12',
                            display: 'block',
                            transform: creativeFocus ? `translateX(${KNOB_TRAVEL}px)` : 'translateX(0px)',
                            transition: 'transform 0.18s ease',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.45)'
                          }} />
                        </span>
                      </button>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 16 }}>테마</div>
                        <div className="muted" style={{ fontSize: 12 }}>Light / Dark</div>
                      </div>

                      <button
                        className="btn"
                        type="button"
                        onClick={() => setTheme(prev => (prev === 'light' ? 'dark' : 'light'))}
                        aria-pressed={theme === 'light'}
                        style={{
                          minWidth: 150,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: 10,
                          padding: '6px 10px'
                        }}
                      >
                        <span style={{ fontSize: 12, fontWeight: 800 }}>
                          {theme === 'light' ? 'Light' : 'Dark'}
                        </span>

                        <span aria-hidden="true" style={{
                          width: SWITCH_W,
                          height: SWITCH_H,
                          borderRadius: 999,
                          background: theme === 'light' ? '#66bb6a' : '#555',
                          position: 'relative',
                          display: 'inline-block',
                          padding: SWITCH_PAD,
                          boxSizing: 'border-box',
                          transition: 'background 0.18s ease',
                          border: '1px solid #2a2a2c'
                        }}>
                          <span style={{
                            width: KNOB,
                            height: KNOB,
                            borderRadius: '50%',
                            background: '#0f0f12',
                            display: 'block',
                            transform: theme === 'light' ? `translateX(${KNOB_TRAVEL}px)` : 'translateX(0px)',
                            transition: 'transform 0.18s ease',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.45)'
                          }} />
                        </span>
                      </button>
                    </div>

                  </div>
                </div>
              </div>
            )}

            {/* List panel */}
            {leftMode === 'list' && (
              <>
                <div className="muted" style={{ fontSize: 12, marginBottom: 8 }}>원고 목록</div>
                {docs.map(d => (
                  <div key={d.id} style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'stretch' }}>
                      <button
                        className="btn"
                        onClick={() => {
                          setActiveDocId(d.id)
                          openLatestDocScore(d.id)
                        }}
                        style={{
                          flex: 1,
                          textAlign: 'left',
                          background: d.id === activeDocId ? '#1b1b1f' : undefined
                        }}
                      >
                        <div style={{ fontWeight: 650 }}>{d.title}</div>
                        <div className="muted" style={{ fontSize: 12, marginTop: 3 }}>{d.filename}</div>
                      </button>
                    </div>

                    {docScoreOpenId === d.id && (
                      <div className="card" style={{ marginTop: 8, padding: 10, border: '1px solid #2a2a2c', background: '#141417' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <div style={{ fontSize: 11, fontWeight: 700, color: '#9aa0a6' }}>
                            문서 점수 요약
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <button
                              className="btn"
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                                onToggleDocHistory(d.id)
                              }}
                              disabled={loading || isAnalyzing || isSavingDraft || isUploading}
                              style={{
                                padding: '2px 6px',
                                minWidth: 28,
                                height: 24,
                                display: 'grid',
                                placeItems: 'center',
                                background: 'rgba(46, 125, 50, 0.12)',
                                border: '1px solid rgba(76, 175, 80, 0.55)',
                                color: '#4caf50'
                              }}
                              title="문서 기록"
                              aria-label="문서 기록"
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path
                                  d="M4 7c0-2 4-3 8-3s8 1 8 3-4 3-8 3-8-1-8-3Z"
                                  stroke="currentColor"
                                  strokeWidth="1.5"
                                />
                                <path
                                  d="M4 7v6c0 2 4 3 8 3s8-1 8-3V7"
                                  stroke="currentColor"
                                  strokeWidth="1.5"
                                  strokeLinecap="round"
                                />
                                <path
                                  d="M4 13v4c0 2 4 3 8 3s8-1 8-3v-4"
                                  stroke="currentColor"
                                  strokeWidth="1.5"
                                  strokeLinecap="round"
                                />
                              </svg>
                            </button>
                            <button
                              className="btn"
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                                onDeleteDoc(d.id)
                              }}
                              disabled={loading || isAnalyzing || isSavingDraft || isUploading}
                              style={{
                                padding: '2px 6px',
                                minWidth: 28,
                                height: 24,
                                display: 'grid',
                                placeItems: 'center',
                                background: '#1a0f10',
                                border: '1px solid rgba(239, 83, 80, 0.55)',
                                color: '#ef5350'
                              }}
                              title="문서 삭제"
                              aria-label="문서 삭제"
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path
                                  d="M4 7h16M9 7v-2.2c0-.7.6-1.3 1.3-1.3h3.4c.7 0 1.3.6 1.3 1.3V7M9.5 11.5v6M14.5 11.5v6M6.5 7l1 13.2c.1 1 1 1.8 2 1.8h5c1 0 1.9-.8 2-1.8L17.5 7"
                                  stroke="currentColor"
                                  strokeWidth="1.5"
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                />
                              </svg>
                            </button>
                          </div>
                        </div>
                        {docScoreLoadingId === d.id && (
                          <div className="muted" style={{ fontSize: 12 }}>불러오는 중...</div>
                        )}
                        {docScoreLoadingId !== d.id && (
                          (() => {
                            const scores = docScoreById[d.id] || {}
                            const entries = Object.entries(scores).filter(([, value]) => typeof value === 'number')
                            if (!entries.length) {
                              return <div className="muted" style={{ fontSize: 12 }}>점수 데이터가 없습니다.</div>
                            }
                            return (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                {entries.map(([name, value]) => {
                                  const safeScore = Math.max(0, Math.min(100, Math.round(value)))
                                  const color = scoreColor(safeScore)
                                  return (
                                    <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                      <div style={{ width: 70, fontSize: 11, color: '#cfcfd6', textTransform: 'capitalize' }}>
                                        {name.replace('_', ' ')}
                                      </div>
                                      <div style={{ flex: 1, height: 6, background: '#1b1b1f', borderRadius: 999, overflow: 'hidden' }}>
                                        <div style={{ width: `${safeScore}%`, height: '100%', background: color }} />
                                      </div>
                                      <div style={{ width: 30, textAlign: 'right', fontSize: 11, color }}>
                                        {safeScore}
                                      </div>
                                    </div>
                                  )
                                })}
                              </div>
                            )
                          })()
                        )}
                      </div>
                    )}

                  </div>
                ))}
              </>
            )}
          </div>

          {/* Error banner */}
          {error && (
            <div className="card" style={{ marginTop: 12, padding: 12, borderColor: '#5a2a2a', background: '#1a0f10' }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Error</div>
              <div className="mono" style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>{error}</div>
            </div>
          )}

          {/* bottom bar */}
          <div style={{
            marginTop: 12,
            paddingTop: 10,
            borderTop: '1px solid #333'
          }}>
            <div ref={accountMenuRef} style={{ position: 'relative' }}>
              {user ? (
                <>
                  <div
                    className="account-bar"
                    onClick={() => setIsAccountMenuOpen(prev => !prev)}
                    role="button"
                    tabIndex={0}
                  >
                    <div className="account-avatar">
                      {user.picture ? (
                        <img src={user.picture} alt={userDisplayName} style={{ width: '100%', height: '100%' }} />
                      ) : (
                        <span>{userInitial}</span>
                      )}
                    </div>
                    <div className="account-meta">
                      <div className="account-name">{userDisplayName}</div>
                      <div className="account-plan">Plan: {planLabel}</div>
                    </div>
                    <span className="account-pill">{planLabel}</span>
                  </div>

                  {isAccountMenuOpen && (
                    <div
                      className="card"
                      style={{
                        position: 'absolute',
                        bottom: 'calc(100% + 8px)',
                        right: 0,
                        minWidth: 220,
                        padding: 8,
                        border: '2px solid #2a2a2c',
                        background: '#0f0f12',
                        zIndex: 60,
                        boxShadow: '0 10px 30px rgba(0,0,0,0.45)'
                      }}
                    >
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <button
                          className="btn"
                          onClick={() => {
                            setIsAccountMenuOpen(false)
                            pushToast('기능 준비 중입니다.', 'info')
                          }}
                          style={{ width: '100%', justifyContent: 'flex-start', textAlign: 'left' }}
                        >
                          계정 관리
                        </button>
                        <button
                          className="btn"
                          onClick={() => {
                            setIsAccountMenuOpen(false)
                            pushToast('기능 준비 중입니다.', 'info')
                          }}
                          style={{ width: '100%', justifyContent: 'flex-start', textAlign: 'left' }}
                        >
                          개인 설정
                        </button>
                        <button
                          className="btn"
                          onClick={() => {
                            setIsAccountMenuOpen(false)
                            openSettingsPanel()
                          }}
                          style={{ width: '100%', justifyContent: 'flex-start', textAlign: 'left' }}
                        >
                          설정
                        </button>
                        <button
                          className="btn"
                          onClick={() => {
                            setIsAccountMenuOpen(false)
                            pushToast('기능 준비 중입니다.', 'info')
                          }}
                          style={{ width: '100%', justifyContent: 'flex-start', textAlign: 'left' }}
                        >
                          도움말
                        </button>
                        <button
                          className="btn"
                          onClick={() => {
                            setIsAccountMenuOpen(false)
                            onLogout()
                          }}
                          style={{ width: '100%', justifyContent: 'flex-start', textAlign: 'left' }}
                        >
                          로그아웃
                        </button>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="account-bar" onClick={onLogin} role="button" tabIndex={0}>
                  <div className="account-avatar">?</div>
                  <div className="account-meta">
                    <div className="account-name">로그인</div>
                    <div className="account-plan">계정을 연결하세요</div>
                  </div>
                  <span className="account-pill">Sign in</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Center panel */}
        <div className="card scroll-hide" style={{ padding: 8, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ fontSize: 16, fontWeight: 700, lineHeight: 1 }}>
                  {activeDoc ? `${activeDoc.title} · ${activeDoc.filename}` : '선택된 문서 없음'}
                </div>
              </div>
              <div
                onMouseEnter={onLegendEnter}
                onMouseLeave={onLegendLeave}
                style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}
              >
                <span style={{
                  fontSize: 12,
                  fontWeight: 700,
                  color: '#cfcfd6',
                  padding: '3px 8px',
                  borderRadius: 8,
                  border: '1px solid #2a2a2c',
                  background: '#16161a'
                }}>
                  페르소나 구성
                </span>

                {isLegendOpen && (
                  <div
                    className="card"
                    style={{
                      position: 'absolute',
                      top: 'calc(100% + 6px)',
                      left: 0,
                      minWidth: 180,
                      padding: 10,
                      border: '2px solid #2a2a2c',
                      background: '#0f0f12',
                      zIndex: 60,
                      boxShadow: '0 10px 28px rgba(0,0,0,0.45)'
                    }}
                  >
                    <div style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: '#888',
                      marginBottom: 8,
                      textTransform: 'uppercase',
                      letterSpacing: 0.5
                    }}>
                      Agents by Color
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {PERSONA_LEGEND.map(item => (
                        <div key={item.key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{
                            width: 10,
                            height: 10,
                            borderRadius: 3,
                            background: ISSUE_COLORS[item.key] || ISSUE_COLORS.default,
                            border: '1px solid #444'
                          }} />
                          <span className="mono" style={{ fontSize: 12, color: '#cfcfd6' }}>
                            {item.label}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 실행 버튼 + 내보내기 hover 메뉴 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginRight: 8 }}>
              {isAnalyzing && <Badge>{formatElapsed(analysisElapsedSec)}</Badge>}

              <button
                className="btn"
                onClick={onRunAnalysis}
                disabled={!activeDocId || isAnalyzing || isUploading || isSavingDraft}
                style={{
                  opacity: (!activeDocId || isAnalyzing || isUploading || isSavingDraft) ? 0.7 : 1,
                  cursor: (!activeDocId || isAnalyzing || isUploading || isSavingDraft) ? 'not-allowed' : 'pointer',
                  marginRight: 6
                }}
              >
                {isAnalyzing ? '분석 중…' : (user ? '분석 실행' : '분석 실행 (개연성 Only)')}
              </button>

              <div
                onMouseEnter={onDownloadEnter}
                onMouseLeave={onDownloadLeave}
                style={{ position: 'relative' }}
              >
                <button
                  className="btn"
                  type="button"
                  disabled={!activeDoc}
                  style={{
                    opacity: !activeDoc ? 0.6 : 1,
                    cursor: !activeDoc ? 'not-allowed' : 'pointer',
                    paddingLeft: 12,
                    paddingRight: 12
                  }}
                  title="내보내기"
                >
                  내보내기
                </button>

                {isDownloadOpen && activeDoc && (
                  <div
                    className="card"
                    style={{
                      position: 'absolute',
                      top: 'calc(100% + 8px)',
                      right: 0,
                      minWidth: 180,
                      padding: 8,
                      border: '2px solid #2a2a2c',
                      background: '#0f0f12',
                      zIndex: 50,
                      boxShadow: '0 10px 30px rgba(0,0,0,0.45)'
                    }}
                  >
                    <button
                      className="btn"
                      type="button"
                      onClick={() => { setIsDownloadOpen(false); exportAsTxt() }}
                      style={{
                        width: '100%',
                        justifyContent: 'flex-start',
                        textAlign: 'left',
                        marginBottom: 6
                      }}
                    >
                      txt로 내보내기
                    </button>

                    <button
                      className="btn"
                      type="button"
                      onClick={() => { setIsDownloadOpen(false); exportAsDocx() }}
                      style={{
                        width: '100%',
                        justifyContent: 'flex-start',
                        textAlign: 'left'
                      }}
                    >
                      docx로 내보내기
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {!user && <div style={{ fontSize: 10, color: '#ffab40' }}>* 전체 분석은 로그인 필요</div>}

          <div className="scroll-hide" style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
            {activeDoc ? (
              activeAnalysis?.result?.split_sentences ? (
                <div className="mono" style={{ paddingBottom: 40 }}>
                  <HighlightedText text={activeDoc.extracted_text} analysisResult={activeAnalysis.result} />
                </div>
              ) : (
                <pre className="mono" style={{ whiteSpace: 'pre-wrap', lineHeight: 1.5, fontSize: 12 }}>
                  {activeDoc.extracted_text || '(텍스트를 추출하지 못했습니다)'}
                </pre>
              )
            ) : (
              <div className="muted">왼쪽에서 원고를 선택하거나 업로드하세요.</div>
            )}
          </div>

          {/* Draft input */}
          <div className="card" style={{ padding: 12, background: '#141417', border: '3px solid #2a2a2c' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <div style={{ fontWeight: 700 }}>텍스트 입력</div>
              <button
                className="btn"
                onClick={onSaveDraft}
                disabled={isSavingDraft || isUploading || isAnalyzing}
                style={{
                  opacity: (isSavingDraft || isUploading || isAnalyzing) ? 0.7 : 1,
                  cursor: (isSavingDraft || isUploading || isAnalyzing) ? 'not-allowed' : 'pointer',
                }}
                title={isSavingDraft ? '저장 중…' : '입력한 텍스트를 .txt로 저장'}
              >
                {isSavingDraft ? '저장 중…' : '저장'}
              </button>
            </div>

            <textarea
              value={draftText}
              onChange={(e) => setDraftText(e.target.value)}
              placeholder="여기에 텍스트를 입력하고 [저장]을 누르면 .txt 원고로 저장됩니다."
              className="mono"
              style={{
                width: '96%',
                height: 140,
                resize: 'vertical',
                borderRadius: 8,
                border: '1px solid #2a2a2c',
                background: '#0f0f12',
                color: '#e6e6ea',
                padding: 10,
                outline: 'none',
                lineHeight: 1.5,
                fontSize: 12
              }}
            />
            <div className="muted" style={{ fontSize: 11, marginTop: 8 }}>
              저장 시 파일명은 자동으로 <span className="mono">draft_YYYYMMDD_HHMMSS.txt</span> 형태로 생성됩니다.
            </div>
          </div>
        </div>

        {/* Right panel */}
        <div className="card scroll-hide" style={{ padding: 8, overflow: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
            <div>
              <div style={{ fontSize: 16, fontWeight: 700 }}>분석 결과</div>
              <div className="muted" style={{ fontSize: 12 }}>
                {activeAnalysis ? `mode: ${mode}` : '분석을 실행하거나 기록을 선택하세요.'}
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {readerLevel && <Badge>독자 수준: {readerLevel}</Badge>}

              {canShowJson && rightView === 'report' && (
                <button className="btn" onClick={() => setRightView('json')} disabled={!activeAnalysis}>
                  JSON 파일로 보기
                </button>
              )}

              {canShowJson && rightView === 'json' && (
                <button className="btn" onClick={() => setRightView('report')}>
                  돌아오기
                </button>
              )}
            </div>
          </div>

          {!activeAnalysis && (
            <div className="muted" style={{ marginTop: 14, fontSize: 13 }}>
              오른쪽 패널에는 에이전트들의 결과(JSON)가 표시됩니다. <br />
              UPSTAGE_API_KEY가 없으면 로컬 휴리스틱 모드로 동작합니다.
            </div>
          )}

          {activeAnalysis && (
            <div style={{ marginTop: 12 }}>
              {rightView === 'report' && (
                <>
                  {reportMarkdown ? (
                    <div className="card" style={{ padding: 16, background: '#202022', marginBottom: 12 }}>
                      <div style={{ fontWeight: 700, marginBottom: 12, borderBottom: '1px solid #444', paddingBottom: 8, fontSize: 14 }}>
                        📝 종합 분석 리포트 (Chief Editor)
                      </div>
                      <div className="markdown-body" style={{ fontSize: 14, lineHeight: 1.6 }}>
                        <ReactMarkdown>{reportMarkdown}</ReactMarkdown>
                      </div>
                    </div>
                  ) : (
                    <div className="card" style={{ padding: 12, marginBottom: 12 }}>
                      <div style={{ fontWeight: 700 }}>요약</div>
                      <div className="muted" style={{ fontSize: 13, marginTop: 6 }}>
                        {activeAnalysis.result?.aggregate?.summary || '—'}
                      </div>
                    </div>
                  )}
                </>
              )}

              {rightView === 'json' && (
                <div className="card" style={{ padding: 12 }}>
                  <div style={{ fontWeight: 700, marginBottom: 8 }}>Raw JSON</div>
                  <pre className="mono" style={{ whiteSpace: 'pre-wrap', fontSize: 12, lineHeight: 1.5 }}>
                    {pretty(activeAnalysis.result)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {docHistoryOpenId && (
        <div
          onClick={() => setDocHistoryOpenId(null)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(10, 10, 12, 0.7)',
            zIndex: 1400,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 16
          }}
        >
          <div
            className="card"
            onClick={(e) => e.stopPropagation()}
            style={{
              width: 'min(520px, 94vw)',
              padding: 16,
              border: '2px solid #2a2a2c',
              background: '#0f0f12',
              boxShadow: '0 20px 40px rgba(0,0,0,0.5)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
              <div>
                <div style={{ fontSize: 16, fontWeight: 700 }}>문서 기록</div>
                <div className="muted" style={{ fontSize: 12 }}>
                  {historyDoc ? `${historyDoc.title} · ${historyDoc.filename}` : '선택된 문서'}
                </div>
              </div>
              <button className="btn" onClick={() => setDocHistoryOpenId(null)}>닫기</button>
            </div>

            <div style={{ marginTop: 12 }}>
              {docHistoryLoadingId === docHistoryOpenId && (
                <div className="muted" style={{ fontSize: 12 }}>불러오는 중...</div>
              )}

              {docHistoryLoadingId !== docHistoryOpenId && (
                (() => {
                  const items = docHistoryById[docHistoryOpenId] || []
                  if (!items.length) {
                    return <div className="muted" style={{ fontSize: 12 }}>분석 기록이 없습니다.</div>
                  }
                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {items.map(item => {
                        const labelTitle = historyDoc?.title
                          ? `${historyDoc.title} · ${item.id}`
                          : item.id
                        return (
                          <div key={item.id} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <button
                              className="btn"
                              onClick={() => onSelectDocAnalysis(docHistoryOpenId, item.id)}
                              style={{
                                flex: 1,
                                minWidth: 0,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'flex-start',
                                gap: 12,
                                textAlign: 'left',
                                background: activeAnalysis?.id === item.id ? '#1b1b1f' : undefined
                              }}
                            >
                              {/* ✅ historyLabel 미정의 버그 수정: item.id 표시 */}
                              <span
                                title={labelTitle}
                                style={{
                                  fontSize: 12,
                                  flex: '0 0 50%',
                                  maxWidth: '50%',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }}
                              >
                                {item.id}
                              </span>
                              <span className="muted" style={{ fontSize: 12, marginLeft: 'auto', whiteSpace: 'nowrap', textAlign: 'right' }}>
                                {formatDisplayTimestamp(item.created_at)}
                              </span>
                            </button>

                            <button
                              className="btn"
                              onClick={(e) => {
                                e.preventDefault()
                                e.stopPropagation()
                                onDeleteAnalysis(item.id)
                              }}
                              disabled={loading || isAnalyzing || isSavingDraft || isUploading}
                              style={{
                                padding: '2px 6px',
                                minWidth: 28,
                                height: 28,
                                display: 'grid',
                                placeItems: 'center',
                                background: '#1a0f10',
                                border: '1px solid rgba(239, 83, 80, 0.55)',
                                color: '#ef5350'
                              }}
                              title="분석 삭제"
                              aria-label="분석 삭제"
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                                <path
                                  d="M4 7h16M9 7v-2.2c0-.7.6-1.3 1.3-1.3h3.4c.7 0 1.3.6 1.3 1.3V7M9.5 11.5v6M14.5 11.5v6M6.5 7l1 13.2c.1 1 1 1.8 2 1.8h5c1 0 1.9-.8 2-1.8L17.5 7"
                                  stroke="currentColor"
                                  strokeWidth="1.5"
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                />
                              </svg>
                            </button>
                          </div>
                        )
                      })}
                    </div>
                  )
                })()
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
