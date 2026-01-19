import React, { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import Intro from './Intro'
import Editor from './Editor'
import {
  deleteAnalysis,
  deleteDocument,
  getAnalysis,
  getDocument,
  listAnalysesByDoc,
  listDocuments,
  runAnalysis,
  runAnalysisStream,
  uploadDocument,
  updateDocument
} from './api.js'

//  docx export
// 설치: npm i docx
import { Document as DocxDocument, Packer, Paragraph, TextRun } from 'docx'

function pretty(obj) {
  try { return JSON.stringify(obj, null, 2) } catch { return String(obj) }
}

function convertRgbaToRgb(rgbaString) {
  const parts = rgbaString.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)/);
  if (parts && parts.length === 5) {
    return `rgb(${parts[1]}, ${parts[2]}, ${parts[3]})`;
  }
  return rgbaString; // Return original if not rgba
}

function Badge({ children }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      border: '1px solid var(--border)',
      background: 'var(--bg-card)',
      borderRadius: 999,
      fontSize: 12,
      color: 'var(--text-main)',
      fontWeight: 500
    }}>
      {children}
    </span>
  )
}

const ISSUE_COLORS = {
  tone: 'rgba(92, 107, 192, 0.5)',    // Indigo
  logic: 'rgba(255, 167, 38, 0.5)',   // Orange (logic/causality)
  trauma: 'rgba(211, 47, 47, 0.6)',    // Strong Red (Material Red 700)
  hate_bias: 'rgba(255, 64, 129, 0.6)', // Vibrant Rose Red (Lighter than before)
  genre_cliche: 'rgba(66, 165, 245, 0.5)',// Blue
  spelling: 'rgba(0, 188, 212, 0.6)',  // Cyan (Changed from Pink to avoid conflict with Trauma)
  tension: 'rgba(139, 195, 74, 0.5)',  // Light Green
  default: 'rgba(189, 189, 189, 0.4)'  // Grey
}

function HighlightedText({ text, analysisResult, setTooltip }) {
  const rawHighlights = Array.isArray(analysisResult?.highlights) ? analysisResult.highlights : []
  const rawNormalized = Array.isArray(analysisResult?.normalized_issues) ? analysisResult.normalized_issues : []
  const hasDocHighlights = rawHighlights.length > 0 || rawNormalized.length > 0

  const handleMouseLeave = () => {
    setTooltip(prev => ({ ...prev, visible: false }))
  }

  const handleMouseMove = (e) => {
    setTooltip(prev => ({ ...prev, x: e.clientX, y: e.clientY }))
  }

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
      return <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: 15 }}>{text}</div>
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

    const handleMouseEnter = (e, issues, borderColor) => {
      const content = (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {issues.map((issue, i) => {
            const agent = issue.agent || 'unknown'
            const reasonText = issue.reason || ''
            return (
              <div key={i}>
                <strong style={{
                  textTransform: 'capitalize',
                  color: ISSUE_COLORS[agent] ? '#fff' : '#000',
                  background: ISSUE_COLORS[agent] || 'transparent',
                  padding: '1px 4px',
                  borderRadius: 3,
                  marginRight: 4
                }}>{agent}</strong>
                <span style={{ opacity: 0.8 }}>{reasonText}</span>
              </div>
            )
          })}
        </div>
      )
      setTooltip({ visible: true, content, x: e.clientX, y: e.clientY, borderColor: convertRgbaToRgb(borderColor) })
    }

    return (
      <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontSize: 15 }}>
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

          return (
            <mark
              key={`${segment.start}-${segment.end}`}
              style={{ backgroundColor: color, color: 'var(--text-main)', padding: '0 2px', borderRadius: 6, cursor: 'help', border: 'var(--highlight-border)', fontWeight: 500 }}
              onMouseEnter={(e) => handleMouseEnter(e, sortedIssues, color)}
              onMouseLeave={handleMouseLeave}
              onMouseMove={handleMouseMove}
            >
              {segment.text}
            </mark>
          )
        })}
      </div>
    )
  }

  if (!analysisResult?.split_sentences || !analysisResult?.split_map) {
    return <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: 15 }}>{text}</div>
  }

  // ... (fallback logic, can be updated later if needed)
  const sentences = analysisResult.split_sentences
  let allIssues = []
  const collect = (source, type) => {
    if (source?.issues && Array.isArray(source.issues)) {
      source.issues.forEach(issue => {
        allIssues.push({ ...issue, type })
      })
    }
  }
  collect(analysisResult.tone, 'tone')
  collect(analysisResult.logic, 'logic')
  collect(analysisResult.trauma, 'trauma')
  collect(analysisResult.hate_bias, 'hate_bias')
  collect(analysisResult.genre_cliche, 'genre_cliche')
  collect(analysisResult.spelling, 'spelling')
  collect(analysisResult.tension_curve, 'tension')

  const handleMouseEnterSimple = (e, issue, borderColor) => {
    const content = (
      <div>
        <strong style={{
          textTransform: 'capitalize',
          color: '#fff',
          background: ISSUE_COLORS[issue.type] || ISSUE_COLORS.default,
          padding: '1px 4px',
          borderRadius: 3,
          marginRight: 4
        }}>{issue.type}</strong>
        <span>{issue.reason || issue.suggestion || 'Issue found'}</span>
      </div>
    )
    setTooltip({ visible: true, content, x: e.clientX, y: e.clientY, borderColor: convertRgbaToRgb(borderColor) })
  }

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
    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontSize: 15 }}>
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
          fragments.push(
            <mark
              key={`iss-${i}`}
              style={{ backgroundColor: color, color: 'var(--text-main)', padding: '0 2px', borderRadius: 6, cursor: 'help', border: 'var(--highlight-border)', fontWeight: 500 }}
              onMouseEnter={(e) => handleMouseEnterSimple(e, issue, color)}
              onMouseLeave={handleMouseLeave}
              onMouseMove={handleMouseMove}
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
  const baseMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?$/)

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
  return `${parts.year}년 ${parts.month}월 ${parts.day}일 ${parts.hour}:${parts.minute}:${parts.second}`
}

function scoreColor(score) {
  if (score >= 80) return '#4caf50'
  if (score >= 60) return '#ffb74d'
  return '#f44336'
}

function Tooltip({ content, position, visible, borderColor }) {
  if (!visible || !content) return null

  return (

    <div style={{

      position: 'fixed',

      top: position.y + 12,

      left: position.x + 12,

      maxWidth: 320,

      padding: '8px 12px',

      background: '#d0d0d0',

      border: `5px solid ${borderColor || '#555'}`,

      borderRadius: 8,

      color: '#000',

      fontSize: 12,

      lineHeight: 1.5,

      whiteSpace: 'pre-wrap',

      zIndex: 1500,

      pointerEvents: 'none',

      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',

      transition: 'opacity 0.1s ease, border-color 0.1s ease',

      opacity: visible ? 1 : 0,

    }}>

      {content}

    </div>

  )

}

const TOAST_STYLES = {
  success: { borderColor: '#2e7d32', background: 'rgba(46, 125, 50, 0.45)' },
  warning: { borderColor: '#ed6c02', background: 'rgba(237, 108, 2, 0.45)' },
  info: { borderColor: '#1976d2', background: 'rgba(25, 118, 210, 0.45)' },
  error: { borderColor: '#d32f2f', background: 'rgba(211, 47, 47, 0.45)' }
}



const PERSONA_LEGEND = [
  { key: 'tone', label: '어조 에이전트' },
  { key: 'logic', label: '논리/개연성 에이전트' },
  { key: 'trauma', label: '트라우마 에이전트' },
  { key: 'hate_bias', label: '혐오·편향 에이전트' },
  { key: 'genre_cliche', label: '장르 클리셰 에이전트' },
  { key: 'spelling', label: '맞춤법 에이전트' },
  { key: 'tension', label: '긴장도 에이전트' },
]

export default function App() {
  const [showIntro, setShowIntro] = useState(true)
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
  const [topic, setTopic] = useState('소설')
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme')
    return saved === 'light' ? 'light' : 'dark'
  })

  const [toasts, setToasts] = useState([])
  const [tooltip, setTooltip] = useState({ visible: false, content: null, x: 0, y: 0, borderColor: null })

  const [leftMode, setLeftMode] = useState('list')
  const [isDragOver, setIsDragOver] = useState(false)

  const fileRef = useRef(null)
  const uploaderFileRef = useRef(null)
  const toastIdRef = useRef(0)

  const [rightView, setRightView] = useState('report')

  const [analysisElapsedSec, setAnalysisElapsedSec] = useState(0)
  const analysisTimerRef = useRef(null)
  const chatEndRef = useRef(null)
  const chatContainerRef = useRef(null)

  const [draftText, setDraftText] = useState('')
  const [isSavingDraft, setIsSavingDraft] = useState(false)
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(false)
  const [isDraftInputOpen, setIsDraftInputOpen] = useState(false)
  const planLabel = ''
  const userDisplayName = user?.name || '사용자'
  const userInitial = (userDisplayName || '').trim().slice(0, 1) || 'U'

  //  download hover menu
  const [isDownloadOpen, setIsDownloadOpen] = useState(false)
  const downloadCloseTimer = useRef(null)
  const [isLegendOpen, setIsLegendOpen] = useState(false)
  const legendCloseTimer = useRef(null)
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
    document.documentElement.setAttribute('data-theme', theme)
    // document.documentElement.style.colorScheme = theme
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

  useEffect(() => {
    if (rightView === 'chat' && chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [activeAnalysis?.result?.logs, rightView])

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
    setRightView('chat')
    setIsRightPanelOpen(true)
    
    // 초기 로그 상태 설정
    const initialLog = { agent: '코디네이터', message: '저희가 왔어요! 전문가 친구들을 한 분씩 모셔오고 있으니 잠시만 기다려 주세요. 금방 시작할게요! ✨', timestamp: Date.now() / 1000 };
    setActiveAnalysis({
      result: {
        logs: [initialLog]
      }
    })

    try {
      const stream = runAnalysisStream(activeDocId)
      
      let finalData = null
      
      for await (const event of stream) {
        if (!event) continue;
        console.log("Stream event:", event); // 디버깅용 로그


        if (event.type === 'log') {
          setActiveAnalysis(prev => {
            const currentLogs = prev?.result?.logs || []
            return {
              ...prev,
              result: {
                ...(prev?.result || {}),
                logs: [...currentLogs, ...(event.logs || [])]
              }
            }
          })
        } else if (event.type === 'node_complete') {
          console.log(`Node complete: ${event.node}`)
        } else if (event.type === 'final_result') {
          finalData = event.data
          if (!finalData) continue;

          const list = await listAnalysesByDoc(activeDocId)
          setAnalyses(list)
          
          setActiveAnalysis(prev => {
            // 스트리밍 중 쌓인 로그와 최종 데이터의 로그를 병합
            const streamLogs = prev?.result?.logs || []
            const finalLogs = finalData.logs || [] // finalData는 순수 결과 객체임
            
            const combinedLogs = [...streamLogs]
            finalLogs.forEach(fLog => {
              if (!combinedLogs.find(sLog => sLog.message === fLog.message)) {
                combinedLogs.push(fLog)
              }
            })

            // UI가 기대하는 AnalysisDetail 구조로 변환
            return {
              id: event.analysis_id,
              document_id: activeDocId,
              status: 'done',
              result: {
                ...finalData,
                logs: combinedLogs.sort((a, b) => a.timestamp - b.timestamp)
              }
            }
          })
          
          setRightView('report')
          // 분석 완료 시 좌측의 점수 요약 패널도 자동으로 펼침
          setDocScoreOpenId(activeDocId)
          pushToast('분석이 완료되었습니다.', 'success')
        }
      }
    } catch (e2) {
      console.error('Analysis Stream Error:', e2)
      setError(String(e2))
      pushToast('분석 중 오류가 발생했습니다.', 'error')
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
      
      // Update main analyses list if valid
      if (activeDocId) {
        const list = await listAnalysesByDoc(activeDocId)
        setAnalyses(list)
      }

      // If deleted analysis was currently active
      if (activeAnalysis?.id === id) {
        setActiveAnalysis(null)
        setRightView('report')
      }

      // Update history modal list directly
      if (docHistoryOpenId) {
        setDocHistoryById(prev => {
          const current = prev[docHistoryOpenId] || []
          return {
            ...prev,
            [docHistoryOpenId]: current.filter(x => x.id !== id)
          }
        })
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
    setLeftMode(prev => (prev === 'upload' ? 'list' : 'upload'))
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

  async function onCreateNewDoc() {
    const filename = `새 원고_${new Date().toLocaleDateString()}_${new Date().toLocaleTimeString().slice(0,5)}.txt`
    const blob = new Blob([" "], { type: 'text/plain' })
    const file = new File([blob], filename, { type: 'text/plain' })
    await uploadOneFile(file)
  }

function SettingsIcon({ size = 28 }) {
  return (

    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M19.4 13.5a7.5 7.5 0 0 0 0-3l2-1.55-2-3.46-2.36.98a7.6 7.6 0 0 0-2.6-1.5L14 2h-4l-.44 2.97a7.6 7.6 0 0 0-2.6 1.5L4.6 5.49l-2 3.46 2 1.55a7.5 7.5 0 0 0 0 3l-2 1.55 2 3.46 2.36-.98a7.6 7.6 0 0 0 2.6 1.5L10 22h4l.44-2.97a7.6 7.6 0 0 0 2.6-1.5l2.36.98 2-3.46-2-1.55Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  )
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

  const saveTimeoutRef = useRef(null)

  return (
    <>
      {showIntro && <Intro onFinish={() => setShowIntro(false)} />}
      <Tooltip visible={tooltip.visible} content={tooltip.content} position={{ x: tooltip.x, y: tooltip.y }} borderColor={tooltip.borderColor} />
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
          border: 1px solid var(--border);
          border-radius: 12px;
          background: var(--bg-card);
          color: var(--text-main);
          cursor: pointer;
          transition: background 0.18s ease, border-color 0.18s ease;
        }
        .account-bar:hover {
          background: var(--bg-hover);
          border-color: var(--border);
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
          color: var(--text-main);
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

        .main-layout {
          grid-template-areas: "left center right";
        }
        .left-panel { grid-area: left; }
        .center-panel { grid-area: center; }
        .right-panel { grid-area: right; }

        @media (max-width: 1200px) {
          .main-layout {
            grid-template-columns: 300px 1fr;
            grid-template-areas: "left center";
          }
          .right-panel {
            display: none;
          }
        }
        @media (max-width: 768px) {
          .main-layout {
            grid-template-columns: 1fr;
            grid-template-areas: "center";
            height: auto;
            min-height: 100vh;
          }
          .left-panel {
            display: none;
          }
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
        @keyframes slideUp {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
      `}</style>
      <div className="scroll-hide main-layout" style={{
        display: 'grid',
        gridTemplateColumns: `300px 1fr ${isRightPanelOpen ? '600px' : '0px'}`,
        height: '100vh',
        gap: 8,
        background: 'var(--bg-main)',
        // filter: theme === 'light' ? 'invert(1) hue-rotate(180deg)' : 'none', // Removed filter
        transition: 'grid-template-columns 0.3s ease-in-out',
        overflow: 'hidden'
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
        <div className="card left-panel" style={{ padding: 8, overflow: 'hidden', display: 'flex', flexDirection: 'column', minHeight: 0, border: '2px solid var(--border)', background: 'var(--bg-sidebar)', position: 'relative' }}>

          {/* Header + Upload button */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 700 }}>CONTEXTOR</div>
              <div className="muted" style={{ fontSize: 12 }}>PDF/DOCX/HWP</div>
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
                  border: '3px solid var(--border)',
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
                </div>

                <div
                  className="card"
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onDrop={onDrop}
                  style={{
                    padding: 14,
                    border: `3px dashed ${isDragOver ? '#6aa9ff' : 'var(--border)'}`,
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

            {/* Settings panel - Popover style */}
            {leftMode === 'settings' && (
              <div
                className="card"
                style={{
                  position: 'absolute',
                  bottom: 70, // Account bar height + margin
                  left: 12,
                  right: 12,
                  zIndex: 100,
                  padding: 14,
                  minHeight: 200,
                  border: '3px solid var(--border)',
                  background: 'var(--bg-panel)',
                  boxShadow: '0 -4px 20px rgba(0,0,0,0.2)',
                  animation: 'slideUp 0.2s ease-out'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                   <div style={{ fontWeight: 800, fontSize: 16 }}>설정</div>
                   <button onClick={() => setLeftMode('list')} className="btn" style={{ padding: '4px 8px', fontSize: 12 }}>닫기</button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
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
            )}

            {/* List panel - Always visible if list or settings (behind settings) */}
            {(leftMode === 'list' || leftMode === 'settings') && (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div className="muted" style={{ fontSize: 12 }}>원고 목록</div>
                  <button 
                    onClick={onCreateNewDoc}
                    className="btn"
                    style={{ 
                      padding: '2px 8px', 
                      fontSize: 18, 
                      fontWeight: 800, 
                      lineHeight: 1,
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border)'
                    }}
                    title="새 원고 생성"
                  >
                    +
                  </button>
                </div>
                {docs.map(d => (
                  <div key={d.id} style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'stretch' }}>
                      <button
                        className="btn"
                        onClick={() => {
                          if (docScoreOpenId === d.id) {
                            setDocScoreOpenId(null)
                          } else {
                            setActiveDocId(d.id)
                            openLatestDocScore(d.id)
                          }
                        }}
                        style={{ 
                          flex: 1,
                          textAlign: 'left',
                          paddingTop: 20,
                          paddingBottom: 20,
                          background: d.id === activeDocId ? 'var(--bg-hover)' : undefined,
                          minHeight: 70
                        }}
                      >
                        <div style={{ fontWeight: 700, fontSize: 14 }}>{d.filename}</div>
                      </button>
                    </div>

                    {docScoreOpenId === d.id && (
                      <div className="card" style={{ marginTop: 8, padding: 10, border: '1px solid var(--border)', background: 'var(--bg-card)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-main)' }}>
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
                                padding: 0,
                                minWidth: 32,
                                height: 30,
                                display: 'grid',
                                placeItems: 'center',
                                background: 'rgba(0, 200, 83, 0.15)',
                                border: '2px solid #00C853',
                                color: '#00C853'
                              }}
                              title="문서 기록"
                              aria-label="문서 기록"
                            >
                              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
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
                                padding: 0,
                                minWidth: 32,
                                height: 30,
                                display: 'grid',
                                placeItems: 'center',
                                background: 'rgba(239, 83, 80, 0.15)',
                                border: '2px solid #ef5350',
                                color: '#ef5350'
                              }}
                              title="문서 삭제"
                              aria-label="문서 삭제"
                            >
                              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
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
                                  
                                  // 에이전트 키 매핑 (ISSUE_COLORS와 일치시키기 위해)
                                  let agentKey = name.toLowerCase();
                                  if (agentKey === 'causality') agentKey = 'logic';
                                  if (agentKey === 'cliche') agentKey = 'genre_cliche';
                                  
                                  const agentColor = convertRgbaToRgb(ISSUE_COLORS[agentKey] || ISSUE_COLORS.default);

                                  return (
                                    <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                      <div style={{ width: 80, fontSize: 11, fontWeight: 700, color: 'var(--text-main)', textTransform: 'capitalize' }}>
                                        {name.replace('_', ' ')}
                                      </div>
                                      <div style={{ flex: 1, height: 6, background: 'var(--bg-panel)', borderRadius: 999, overflow: 'hidden' }}>
                                        <div style={{ width: `${safeScore}%`, height: '100%', background: agentColor }} />
                                      </div>
                                      <div style={{ width: 40, textAlign: 'right', fontSize: 13, fontWeight: 800, color: agentColor }}>
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
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ fontWeight: 700, marginBottom: 6 }}>Error</div>
                <button
                  onClick={() => setError(null)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#aaa',
                    cursor: 'pointer',
                    fontSize: 20,
                    lineHeight: 0.8,
                    padding: '0 4px'
                  }}
                  title="오류 숨기기"
                >
                  &times;
                </button>
              </div>
              <div className="mono" style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>{error}</div>
            </div>
          )}

          {/* bottom bar */}
          <div style={{
            marginTop: 12,
            paddingTop: 10,
            borderTop: '1px solid #333'
          }}>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              {user ? (
                <div className="account-bar" style={{ flexGrow: 1 }}>
                  <div className="account-avatar">
                    {user.picture ? (
                      <img src={user.picture} alt={userDisplayName} style={{ width: '100%', height: '100%' }} />
                    ) : (
                      <span>{userInitial}</span>
                    )}
                  </div>
                  <div className="account-meta">
                    <div className="account-name">{userDisplayName}</div>
                    <div className="account-plan">{planLabel}</div>
                  </div>
                </div>
              ) : (
                <div className="account-bar" onClick={onLogin} role="button" tabIndex={0} style={{ cursor: 'pointer', flexGrow: 1 }}>
                  <div className="account-avatar">?</div>
                  <div className="account-meta">
                    <div className="account-name">Login</div>
                    <div className="account-plan">Connect account</div>
                  </div>
                  <span className="account-pill">Sign in</span>
                </div>
              )}

              {user && (
                <div style={{
                  position: 'absolute',
                  right: 0,
                  top: 0,
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  paddingRight: 8
                }}>
                                                      <button
                                                        className="btn"
                                                        type="button"
                                                        onClick={onLogout}
                                                        title="Logout"
                                                        aria-label="Logout"
                                                        disabled={!user}
                                                        style={{
                                                          width: 38,
                                                          height: 38,
                                                          display: 'flex',
                                                          justifyContent: 'center',
                                                          alignItems: 'center',
                                                          padding: 0,
                                                          opacity: user ? 1 : 0.45,
                                                          background: 'rgba(255, 87, 34, 0.1)', // Light Orange bg
                                                          color: '#ff0000',
                                                          border: '2px solid #ff0000'
                                                        }}
                                                      >                                      <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                                        <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                                        <path d="M10 17l5-5-5-5" />
                                        <path d="M15 12H3" />
                                      </svg>
                                    </button>
                  
                                                                          <button
                                                                            className="btn"
                                                                            type="button"
                                                                            onClick={openSettingsPanel}
                                                                            title="Settings"
                                                                            aria-label="Settings"
                                                                            aria-pressed={leftMode === 'settings'}
                                                                            style={{
                                                                              width: 38,
                                                                              height: 38,
                                                                              display: 'flex',
                                                                              justifyContent: 'center',
                                                                              alignItems: 'center',
                                                                              padding: 0,
                                                                              background: theme === 'light' ? '#fff' : '#27272a',
                                                                              color: theme === 'light' ? '#000' : '#fff',
                                                                              border: theme === 'light' ? '2px solid #000' : '2px solid #fff'
                                                                            }}
                                                                          >                                                                                                    <SettingsIcon size={32} />

                                                                                                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Center panel */}
        <div className="card scroll-hide center-panel" style={{ padding: 8, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 8, border: '2px solid var(--border)', background: 'var(--bg-panel)' }}>
          <div className="scroll-hide" style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
            {activeDoc ? (
              <Editor 
                initialText={activeDoc.extracted_text} 
                onSave={(newText) => {
                  if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current)
                  saveTimeoutRef.current = setTimeout(async () => {
                    try {
                      const plainText = newText.replace(/<\/p><p>/g, '\n').replace(/<[^>]+>/g, '')
                      await updateDocument(activeDocId, { extracted_text: plainText })
                      setActiveDoc(prev => ({ ...prev, extracted_text: plainText }))
                    } catch (err) {
                      console.error('Auto-save failed:', err)
                    }
                  }, 1000)
                }}
                analysisResult={activeAnalysis?.result}
                setTooltip={setTooltip}
                onRunAnalysis={onRunAnalysis}
                isAnalyzing={isAnalyzing}
                onExportTxt={exportAsTxt}
                onExportDocx={exportAsDocx}
                onToggleRightPanel={() => setIsRightPanelOpen(prev => !prev)}
              />
            ) : (
              <div className="muted" style={{ padding: 20 }}>왼쪽에서 원고를 선택하거나 업로드하세요.</div>
            )}
          </div>
        </div>

        {/* Right panel */}
        <div
          className="card right-panel"
          style={{
            padding: 8,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            opacity: isRightPanelOpen ? 1 : 0,
            transition: 'opacity 0.2s ease-in-out',
            border: '2px solid var(--border)',
            background: 'var(--bg-sidebar)'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
            <div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>분석 결과</div>
              {!activeAnalysis && (
                <div className="muted" style={{ fontSize: 12 }}>
                  분석을 실행하거나 기록을 선택하세요.
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {readerLevel && <Badge>독자 수준: {readerLevel}</Badge>}

              {canShowJson && (
                <>
                  <button 
                    className="btn" 
                    style={{ 
                      minWidth: 105, 
                      padding: '8px 12px',
                      background: rightView === 'report' ? 'var(--text-main)' : 'var(--bg-btn)',
                      color: rightView === 'report' ? 'var(--bg-main)' : 'var(--text-main)'
                    }} 
                    onClick={() => setRightView('report')} 
                    disabled={!activeAnalysis}
                  >
                    요약 보기
                  </button>
                  <button 
                    className="btn" 
                    style={{ 
                      minWidth: 105, 
                      padding: '8px 12px',
                      background: rightView === 'chat' ? 'var(--text-main)' : 'var(--bg-btn)',
                      color: rightView === 'chat' ? 'var(--bg-main)' : 'var(--text-main)'
                    }} 
                    onClick={() => setRightView('chat')} 
                    disabled={!activeAnalysis}
                  >
                    대화 보기
                  </button>
                  <button 
                    className="btn" 
                    style={{ 
                      minWidth: 105, 
                      padding: '8px 12px',
                      background: rightView === 'json' ? 'var(--text-main)' : 'var(--bg-btn)',
                      color: rightView === 'json' ? 'var(--bg-main)' : 'var(--text-main)'
                    }} 
                    onClick={() => setRightView('json')} 
                    disabled={!activeAnalysis}
                  >
                    JSON
                  </button>
                </>
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
            <div className="scroll-hide" style={{ marginTop: 12, flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
              {rightView === 'report' && (
                <div style={{ paddingBottom: 20 }}>
                  {reportMarkdown ? (
                    <div className="card" style={{ padding: 16, background: 'var(--bg-card)', marginBottom: 12 }}>
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
                </div>
              )}

              {rightView === 'json' && (
                <div className="card" style={{ padding: 12 }}>
                  <div style={{ fontWeight: 700, marginBottom: 8 }}>Raw JSON</div>
                  <pre className="mono" style={{ whiteSpace: 'pre-wrap', fontSize: 12, lineHeight: 1.5 }}>
                    {pretty(activeAnalysis.result)}
                  </pre>
                </div>
              )}

              {rightView === 'chat' && (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                  <div style={{ fontWeight: 700, marginBottom: 12, borderBottom: '1px solid var(--border)', paddingBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
                    <span>🤖 에이전트 작업 로그 (Agent Chat)</span>
                    <Badge>{activeAnalysis?.result?.logs?.length || 0} 메시지</Badge>
                  </div>
                  
                  <div 
                    ref={chatContainerRef}
                    className="scroll-hide" 
                    style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 12, paddingBottom: 20 }}
                  >
                    {activeAnalysis?.result?.logs && activeAnalysis.result.logs.length > 0 ? (
                      activeAnalysis.result.logs.map((log, i) => {
                        const isCoordinator = log.agent === 'System' || log.agent === 'Coordinator' || log.agent === 'Chief Editor';
                        
                        // 에이전트 이름별 ISSUE_COLORS 키 매핑
                        const agentMapping = {
                          '서사 분석가': 'logic',
                          '맞춤법 전문가': 'spelling',
                          '문체 전문가': 'tone',
                          '장르 전문가': 'genre_cliche',
                          '안전 관리자': 'trauma',
                          '윤리 감시자': 'hate_bias',
                          '긴장감 설계자': 'tension',
                          '코디네이터': 'tension', // 시스템 코디네이터는 기본적으로 연두색 계열
                          '수석 편집자': 'default'
                        };
                        
                        const agentKey = agentMapping[log.agent] || 'default';
                        const color = ISSUE_COLORS[agentKey] || ISSUE_COLORS.default;
                        
                        return (
                          <div key={i} style={{ 
                            alignSelf: 'flex-start',
                            maxWidth: '90%',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 4
                          }}>
                            <div style={{ fontSize: 11, fontWeight: 700, marginLeft: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                              <span style={{ 
                                width: 8, 
                                height: 8, 
                                borderRadius: '50%', 
                                background: color 
                              }} />
                              {log.agent}
                              <span className="muted" style={{ fontWeight: 400 }}>
                                {log.timestamp ? new Date(log.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : ''}
                              </span>
                            </div>
                            <div style={{ 
                              background: isCoordinator ? 'rgba(139, 195, 74, 0.05)' : 'var(--bg-panel)',
                              padding: '10px 14px',
                              borderRadius: '14px 14px 14px 4px',
                              fontSize: 13,
                              lineHeight: 1.5,
                              border: `2px solid ${color}`,
                              color: 'var(--text-main)'
                            }}>
                              {log.message}
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="muted" style={{ textAlign: 'center', marginTop: 40 }}>
                        {isAnalyzing ? '분석이 진행 중입니다. 잠시만 기다려 주세요...' : '로그 데이터가 없습니다.'}
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>
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
              width: 'min(380px, 94vw)',
              padding: 16,
              border: '2px solid var(--border)',
              background: 'var(--bg-panel)',
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
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                      {items.map(item => {
                        const labelTitle = historyDoc?.title
                          ? `${historyDoc.title} · ${item.id}`
                          : item.id
                        return (
                          <div key={item.id} style={{ display: 'flex', gap: 8, alignItems: 'center', width: '100%' }}>
                            <button
                              className="btn"
                              onClick={() => onSelectDocAnalysis(docHistoryOpenId, item.id)}
                              style={{
                                flex: 1,
                                minWidth: 0,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: 12,
                                textAlign: 'center',
                                background: activeAnalysis?.id === item.id ? 'var(--bg-hover)' : undefined
                              }}
                            >
                              <span
                                style={{
                                  fontSize: 12,
                                  color: '#000',
                                  fontWeight: 700,
                                  whiteSpace: 'nowrap'
                                }}
                              >
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
                                padding: 0,
                                minWidth: 40,
                                height: 36,
                                display: 'grid',
                                placeItems: 'center',
                                background: 'rgba(239, 83, 80, 0.15)',
                                border: '2px solid #ef5350',
                                color: '#ef5350'
                              }}
                              title="분석 삭제"
                              aria-label="분석 삭제"
                            >
                              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
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