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
  return `${prefix}_${y}${mo}${da}_${h}${mi}${s}.txt`
}

const AGENT_COLORS = {
  logic: 'rgba(90, 150, 255, 0.35)',
  causality: 'rgba(90, 150, 255, 0.35)',
  tone: 'rgba(180, 120, 255, 0.35)',
  trauma: 'rgba(255, 90, 90, 0.35)',
  hate_bias: 'rgba(200, 60, 60, 0.35)',
  genre_cliche: 'rgba(255, 170, 70, 0.35)',
  spelling: 'rgba(110, 200, 120, 0.35)',
  tension: 'rgba(80, 200, 200, 0.35)'
}

function normalizeHighlights(highlights, textLength) {
  if (!Array.isArray(highlights)) return []
  const safe = []
  highlights.forEach((item) => {
    if (!item || typeof item.doc_start !== 'number' || typeof item.doc_end !== 'number') return
    const start = Math.max(0, Math.min(item.doc_start, textLength))
    const end = Math.max(0, Math.min(item.doc_end, textLength))
    if (end <= start) return
    safe.push({ ...item, start, end })
  })
  return safe.sort((a, b) => (a.start - b.start) || (a.end - b.end))
}

function buildIssueReasonMap(normalizedIssues) {
  if (!Array.isArray(normalizedIssues)) return {}
  const map = {}
  normalizedIssues.forEach((issue) => {
    const location = issue?.location || {}
    const start = location.doc_start
    const end = location.doc_end
    if (typeof start !== 'number' || typeof end !== 'number') return
    const key = `${start}:${end}:${issue.agent || ''}`
    if (!map[key]) {
      map[key] = issue.reason || issue.issue_type || ''
    }
  })
  return map
}

function renderHighlightedText(text, highlights, issueReasonMap) {
  if (!text) return ''
  if (!highlights || highlights.length === 0) return text

  const parts = []
  const boundaries = new Set([0, text.length])
  highlights.forEach((h) => {
    boundaries.add(h.start)
    boundaries.add(h.end)
  })
  const points = Array.from(boundaries).sort((a, b) => a - b)

  for (let i = 0; i < points.length - 1; i += 1) {
    const start = points[i]
    const end = points[i + 1]
    if (end <= start) continue
    const active = highlights.filter(h => h.start < end && h.end > start)
    if (active.length === 0) {
      parts.push(text.slice(start, end))
      continue
    }
    const primary = active[0]
    const agent = primary.agent
    const color = (agent && AGENT_COLORS[agent]) || 'rgba(255, 220, 120, 0.35)'
    const reasonParts = []
    const metaParts = []
    active.forEach((h) => {
      if (h.reason) reasonParts.push(h.reason)
      else {
        const key = `${h.start}:${h.end}:${h.agent || ''}`
        if (issueReasonMap?.[key]) reasonParts.push(issueReasonMap[key])
      }
      metaParts.push([h.agent, h.label, h.severity].filter(Boolean).join(' | '))
    })
    const reason = Array.from(new Set(reasonParts.filter(Boolean))).join(' | ')
    const meta = Array.from(new Set(metaParts.filter(Boolean))).join(' | ')
    const title = reason || meta
    parts.push(
      <span key={`${start}-${end}-${i}`} style={{ backgroundColor: color }} title={title}>
        {text.slice(start, end)}
      </span>
    )
  }

  return parts
}

export default function App() {
  // Auth
  const [user, setUser] = useState(null)

  // Docs/Analyses
  const [docs, setDocs] = useState([])
  const [activeDocId, setActiveDocId] = useState(null)
  const [activeDoc, setActiveDoc] = useState(null)
  const [analyses, setAnalyses] = useState([])
  const [activeAnalysis, setActiveAnalysis] = useState(null)

  // UI states
  const [loading, setLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState(null)

  //  업로드 화면 토글 (내부 저장소)
  const [showUploader, setShowUploader] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)

  const fileRef = useRef(null)
  const uploaderFileRef = useRef(null)

  // right panel view: report | json
  const [rightView, setRightView] = useState('report')

  // analyzing elapsed
  const [analysisElapsedSec, setAnalysisElapsedSec] = useState(0)
  const analysisTimerRef = useRef(null)

  // 하단 텍스트 입력 + 저장
  const [draftText, setDraftText] = useState('')
  const [isSavingDraft, setIsSavingDraft] = useState(false)

  // -----------------------------
  // Auth check and token parsing
  // -----------------------------
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

  async function onLogin() {
    window.location.href = 'http://localhost:8000/api/auth/login'
  }

  async function onLogout() {
    import('./api.js').then(api => api.logout())
    setUser(null)
  }

  // -----------------------------
  // Docs refresh
  // -----------------------------
  async function refreshDocs(pickFirstIfEmpty = true) {
    const items = await listDocuments()
    setDocs(items)
    if (pickFirstIfEmpty && !activeDocId && items.length) setActiveDocId(items[0].id)
    return items
  }

  // 앱 시작 시 문서 목록 로드 (로그인 여부와 무관)
  useEffect(() => {
    refreshDocs(true).catch(e => setError(String(e)))
    // eslint-disable-next-line
  }, [])

  // activeDocId 변경 시 문서/분석 기록 로드
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

  // -----------------------------
  // 분석 중 타이머
  // -----------------------------
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

  // -----------------------------
  //  공통 업로드 함수 (input/drag&drop 공용)
  // -----------------------------
  async function uploadOneFile(file) {
    if (!file) return
    setIsUploading(true)
    setError(null)

    try {
      const doc = await uploadDocument(file)
      await refreshDocs(false)
      setActiveDocId(doc.id)

      // 업로드 화면 닫기
      setShowUploader(false)
      setIsDragOver(false)

      // input reset
      if (fileRef.current) fileRef.current.value = ''
      if (uploaderFileRef.current) uploaderFileRef.current.value = ''

      alert('업로드가 완료되었습니다.')
    } catch (e2) {
      setError(String(e2))
    } finally {
      setIsUploading(false)
    }
  }

  // 기존 "업로드" input (혹시 남겨둘 경우를 대비)
  async function onUpload(e) {
    const f = e.target.files?.[0]
    if (!f) return
    await uploadOneFile(f)
  }

  // 업로더 화면 내 file picker
  async function onUploadFromUploader(e) {
    const f = e.target.files?.[0]
    if (!f) return
    await uploadOneFile(f)
  }

  // -----------------------------
  // Save draft as .txt document
  // -----------------------------
  async function onSaveDraft() {
    const text = (draftText ?? '').trim()
    if (!text) {
      alert('저장할 텍스트를 입력하세요.')
      return
    }

    setIsSavingDraft(true)
    setError(null)

    try {
      const filename = makeTimestampName('draft')
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
      const file = new File([blob], filename, { type: 'text/plain' })

      const doc = await uploadDocument(file)
      await refreshDocs(false)
      setActiveDocId(doc.id)

      setDraftText('')
      alert('텍스트가 .txt 원고로 저장되었습니다.')
    } catch (e2) {
      setError(String(e2))
    } finally {
      setIsSavingDraft(false)
    }
  }

  // -----------------------------
  // Run analysis
  // -----------------------------
  async function onRunAnalysis() {
    if (!activeDocId) return

    setAnalysisElapsedSec(0)
    setIsAnalyzing(true); setError(null)

    try {
      const a = await runAnalysis(activeDocId)
      const full = await getAnalysis(a.id)
      const list = await listAnalysesByDoc(activeDocId)
      setAnalyses(list)
      setActiveAnalysis(full)
      setRightView('report')
      alert('분석이 완료되었습니다.')
    } catch (e2) {
      setError(String(e2))
    } finally {
      setIsAnalyzing(false)
    }
  }

  // -----------------------------
  // Delete doc / analysis
  // -----------------------------
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

  // -----------------------------
  // Derived values
  // -----------------------------
  const readerLevel = activeAnalysis?.result?.final_metric?.reader_level
  const mode = activeAnalysis?.result?.debug?.mode || (activeAnalysis ? 'upstage_pipeline' : null)
  const reportMarkdown = activeAnalysis?.result?.report?.full_report_markdown
  const qaScores = activeAnalysis?.result?.qa_scores
  const canShowJson = !!activeAnalysis
  const rawHighlights = activeAnalysis?.result?.highlights
  const normalizedIssues = activeAnalysis?.result?.normalized_issues
  const issueReasonMap = buildIssueReasonMap(normalizedIssues)
  const highlightFilter = user ? null : new Set(['logic', 'causality'])
  const filteredHighlights = normalizeHighlights(
    (rawHighlights || []).filter(h => !highlightFilter || highlightFilter.has(h.agent)),
    (activeDoc?.extracted_text || '').length
  )

  // -----------------------------
  // Upload panel handlers
  // -----------------------------
  function openUploadPanel() {
    setShowUploader(true)
    setIsDragOver(false)
    setError(null)
  }

  function closeUploadPanel() {
    if (isUploading) return
    setShowUploader(false)
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

  return (
    <div style={{display:'grid', gridTemplateColumns:'320px 1fr 520px', height:'100vh', gap:12, padding:12}}>

      {/* QA Scores Floating Box */}
      {qaScores && Object.keys(qaScores).length > 0 && (
        <div style={{
          position: 'fixed',
          bottom: 24,
          left: 24,
          background: 'rgba(27, 27, 31, 0.9)',
          backdropFilter: 'blur(8px)',
          border: '1px solid #333',
          borderRadius: 8,
          padding: '12px 16px',
          zIndex: 1000,
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
          minWidth: 160
        }}>
          <div style={{
            fontSize: 11,
            fontWeight: 700,
            color: '#888',
            marginBottom: 8,
            textTransform: 'uppercase',
            letterSpacing: 0.5
          }}>
            Agent QA Scores
          </div>
          <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
            {Object.entries(qaScores).map(([name, score]) => (
              <div key={name} style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 20}}>
                <span style={{fontSize: 13, color: '#cfcfd6', textTransform: 'capitalize'}}>
                  {name.replace('_', ' ')}
                </span>
                <span style={{
                  fontSize: 13,
                  fontWeight: 700,
                  color: score >= 80 ? '#4caf50' : score >= 60 ? '#ffb74d' : '#f44336'
                }}>
                  {score}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Left */}
      <div className="card" style={{padding:12, overflow:'auto'}}>
        {/* User Profile Section */}
        <div style={{marginBottom: 20, paddingBottom: 12, borderBottom: '1px solid #333'}}>
          {user ? (
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <img src={user.picture} alt={user.name} style={{width: 32, height: 32, borderRadius: '50%'}} />
              <div style={{flex: 1, minWidth: 0}}>
                <div style={{fontSize: 14, fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                  {user.name}
                </div>
                <div style={{fontSize: 11, color: '#888', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                  {user.email}
                </div>
              </div>
              <button className="btn" onClick={onLogout} style={{padding: '4px 8px', fontSize: 11}}>로그아웃</button>
            </div>
          ) : (
            <button
              className="btn"
              onClick={onLogin}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                background: '#4285F4',
                color: 'white',
                border: 'none'
              }}
            >
              <svg width="18" height="18" viewBox="0 0 18 18">
                <path fill="currentColor" d="M17.64 8.2c0-.63-.06-1.25-.16-1.84H9v3.49h4.84c-.21 1.12-.84 2.07-1.79 2.7l2.85 2.21c1.67-1.54 2.63-3.81 2.63-6.56z"></path>
                <path fill="currentColor" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.85-2.21c-.79.53-1.81.85-3.11.85-2.39 0-4.41-1.61-5.14-3.78H.9v2.33C2.39 16.15 5.44 18 9 18z"></path>
                <path fill="currentColor" d="M3.86 10.68c-.19-.56-.3-1.16-.3-1.78s.11-1.22.3-1.78V4.79H.9C.33 5.93 0 7.22 0 8.6c0 1.38.33 2.67.9 3.81l2.96-2.33z"></path>
                <path fill="currentColor" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.47.89 11.43 0 9 0 5.44 0 2.39 1.85.9 4.79l2.96 2.33c.73-2.17 2.75-3.78 5.14-3.78z"></path>
              </svg>
              Google로 로그인
            </button>
          )}
        </div>

        {/* Top header + Upload button */}
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', gap:10}}>
          <div>
            <div style={{fontSize:18, fontWeight:700}}>CONTEXTOR</div>
            <div className="muted" style={{fontSize:12}}>PDF/DOCX/HWP 업로드</div>
          </div>

          {/* 업로드 버튼: 클릭하면 내부 저장소 업로드 화면으로 전환 */}
          <button
            className="btn"
            onClick={openUploadPanel}
            disabled={isUploading}
            style={{
              opacity: isUploading ? 0.7 : 1,
              cursor: isUploading ? 'not-allowed' : 'pointer',
            }}
            title={isUploading ? '업로드 중…' : '내부 저장소 업로드'}
          >
            업로드
          </button>

          {/* (기존 input 방식 유지하고 싶으면 숨김으로 남겨도 됨) */}
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.txt,.md,.hwp,.hwpx"
            onChange={onUpload}
            style={{display:'none'}}
            disabled={isUploading}
          />
        </div>

        <div style={{marginTop:12, display:'flex', gap:8, flexWrap:'wrap'}}>
          {loading ? <Badge>loading</Badge> : <Badge>ready</Badge>}
          {docs.length ? <Badge>{docs.length} docs</Badge> : <Badge>no docs</Badge>}
          {isUploading && <Badge>uploading…</Badge>}
          {isAnalyzing && <Badge>analyzing…</Badge>}
          {isSavingDraft && <Badge>saving…</Badge>}
        </div>

        {/* showUploader면: 원고목록 대신 "내부 저장소 업로드 화면" */}
        {showUploader ? (
          <div style={{marginTop:14}}>
            {/* 초록색: 내부 저장소 헤더 */}
            <div
              className="card"
              style={{
                padding: 12,
                border: '1px solid #2a2a2c',
                background: 'rgba(46, 125, 50, 0.18)', // green-ish
                marginBottom: 10
              }}
            >
              <div style={{fontWeight: 800, fontSize: 16}}>파일을 드래그 & 드랍하거나 내부 저장소를 사용하세요</div>
              <div className="muted" style={{fontSize: 12, marginTop: 4}}>

              </div>
            </div>

            {/* 파란색: Drag & Drop Zone */}
            <div
              className="card"
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
              style={{
                padding: 14,
                border: `1px dashed ${isDragOver ? '#6aa9ff' : '#2a2a2c'}`,
                background: isDragOver ? 'rgba(50, 100, 200, 0.22)' : 'rgba(50, 100, 200, 0.12)',
                minHeight: 180,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                gap: 10
              }}
            >
              <div style={{fontSize: 13, fontWeight: 700}}>
                {isDragOver ? '여기에 놓으세요' : '마우스로 파일을 드래그해서 드랍하세요'}
              </div>
              <div className="muted" style={{fontSize: 12}}>
                지원 확장자: <span className="mono">.pdf .docx .txt .md .hwp .hwpx</span>
              </div>

              <div style={{display:'flex', gap:10, alignItems:'center', marginTop: 6}}>
                <label
                  className="btn"
                  style={{
                    display:'inline-flex',
                    alignItems:'center',
                    gap:8,
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
                    style={{display:'none'}}
                    disabled={isUploading}
                  />
                </label>

                {isUploading && (
                  <div className="muted" style={{fontSize: 12}}>
                    업로드중입니다… 잠시만 기다려주세요.
                  </div>
                )}
              </div>
            </div>

            {/* 하단: 되돌아오기 */}
            <button
              className="btn"
              onClick={closeUploadPanel}
              disabled={isUploading}
              style={{
                width: '100%',
                marginTop: 12,
                opacity: isUploading ? 0.7 : 1,
                cursor: isUploading ? 'not-allowed' : 'pointer',
              }}
            >
              되돌아오기
            </button>
          </div>
        ) : (
          <>
            {/* 원고 목록 */}
            <div style={{marginTop:14}}>
              <div className="muted" style={{fontSize:12, marginBottom:8}}>원고 목록</div>
              {docs.map(d => (
                <div key={d.id} style={{display:'flex', gap:8, alignItems:'stretch', marginBottom:8}}>
                  <button
                    className="btn"
                    onClick={() => setActiveDocId(d.id)}
                    style={{
                      flex: 1,
                      textAlign:'left',
                      background: d.id===activeDocId ? '#1b1b1f' : undefined
                    }}
                  >
                    <div style={{fontWeight:650}}>{d.title}</div>
                    <div className="muted" style={{fontSize:12, marginTop:3}}>{d.filename}</div>
                  </button>

                  <button
                    className="btn"
                    title={isAnalyzing ? '분석 중에는 삭제할 수 없습니다.' : '삭제'}
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); onDeleteDoc(d.id) }}
                    disabled={loading || isAnalyzing || isSavingDraft || isUploading}
                    style={{width:56, display:'grid', placeItems:'center'}}
                  >
                    삭제
                  </button>
                </div>
              ))}
            </div>

            {/* 분석 기록 */}
            <div style={{marginTop:18}}>
              <div className="muted" style={{fontSize:12, marginBottom:8}}>분석 기록</div>
              {analyses.length === 0 && <div className="muted" style={{fontSize:13}}>아직 분석이 없습니다.</div>}
              {analyses.map(a => (
                <div key={a.id} style={{display:'flex', gap:8, alignItems:'stretch', marginBottom:8}}>
                  <button className="btn" onClick={() => openAnalysis(a.id)} style={{flex:1, textAlign:'left'}}>
                    <div style={{display:'flex', justifyContent:'space-between', gap:10}}>
                      <span className="mono" style={{fontSize:12}}>{a.id.slice(0,8)}…</span>
                      <span className="muted" style={{fontSize:12}}>{a.status}</span>
                    </div>
                    <div className="muted" style={{fontSize:12, marginTop:3}}>{a.created_at}</div>
                  </button>

                  <button
                    className="btn"
                    title={isAnalyzing ? '분석 중에는 삭제할 수 없습니다.' : '삭제'}
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); onDeleteAnalysis(a.id) }}
                    disabled={loading || isAnalyzing || isSavingDraft || isUploading}
                    style={{width:56, display:'grid', placeItems:'center'}}
                  >
                    삭제
                  </button>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Error (Left에도 표시) */}
        {error && (
          <div className="card" style={{marginTop:12, padding:12, borderColor:'#5a2a2a', background:'#1a0f10'}}>
            <div style={{fontWeight:700, marginBottom:6}}>Error</div>
            <div className="mono" style={{fontSize:12, whiteSpace:'pre-wrap'}}>{error}</div>
          </div>
        )}
      </div>

      {/* Center */}
      <div className="card" style={{padding:12, overflow:'auto', display:'flex', flexDirection:'column', gap:12}}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', gap:10}}>
          <div>
            <div style={{fontSize:16, fontWeight:700}}>원고</div>
            <div className="muted" style={{fontSize:12}}>
              {activeDoc ? `${activeDoc.title} · ${activeDoc.filename}` : '선택된 문서 없음'}
            </div>
          </div>

          <div style={{display:'flex', flexDirection:'column', alignItems:'flex-end', gap:4}}>
            <div style={{display:'flex', alignItems:'center', gap:8}}>
              {isAnalyzing && <Badge>{formatElapsed(analysisElapsedSec)}</Badge>}
              <button
                className="btn"
                onClick={onRunAnalysis}
                disabled={!activeDocId || isAnalyzing || isUploading || isSavingDraft}
                style={{
                  opacity: (!activeDocId || isAnalyzing || isUploading || isSavingDraft) ? 0.7 : 1,
                  cursor: (!activeDocId || isAnalyzing || isUploading || isSavingDraft) ? 'not-allowed' : 'pointer',
                }}
              >
                {isAnalyzing ? '분석 중…' : (user ? '분석 실행' : '분석 실행 (개연성 Only)')}
              </button>
            </div>
            {!user && <div style={{fontSize:10, color:'#ffab40'}}>* 전체 분석은 로그인 필요</div>}
          </div>
        </div>

        <div style={{flex: 1, minHeight: 0, overflow: 'auto'}}>
          {activeDoc ? (
            <pre className="mono" style={{whiteSpace:'pre-wrap', lineHeight:1.5, fontSize:12}}>
              {renderHighlightedText(activeDoc.extracted_text || '(텍스트를 추출하지 못했습니다)', filteredHighlights, issueReasonMap)}
            </pre>
          ) : (
            <div className="muted">왼쪽에서 원고를 선택하거나 업로드하세요.</div>
          )}
        </div>

        {/* 하단 텍스트 입력 */}
        <div className="card" style={{padding:12, background:'#141417', border:'1px solid #2a2a2c'}}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', gap:10, marginBottom:8}}>
            <div style={{fontWeight:700}}>텍스트 입력</div>
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
              width: '100%',
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
          <div className="muted" style={{fontSize:11, marginTop:8}}>
            저장 시 파일명은 자동으로 <span className="mono">draft_YYYYMMDD_HHMMSS.txt</span> 형태로 생성됩니다.
          </div>
        </div>
      </div>

      {/* Right */}
      <div className="card" style={{padding:12, overflow:'auto'}}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', gap:10}}>
          <div>
            <div style={{fontSize:16, fontWeight:700}}>분석 결과</div>
            <div className="muted" style={{fontSize:12}}>
              {activeAnalysis ? `mode: ${mode}` : '분석을 실행하거나 기록을 선택하세요.'}
            </div>
          </div>

          <div style={{display:'flex', gap:8, alignItems:'center'}}>
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
          <div className="muted" style={{marginTop:14, fontSize:13}}>
            오른쪽 패널에는 에이전트들의 결과(JSON)가 표시됩니다. <br/>
            UPSTAGE_API_KEY가 없으면 로컬 휴리스틱 모드로 동작합니다.
          </div>
        )}

        {activeAnalysis && (
          <div style={{marginTop:12}}>
            {rightView === 'report' && (
              <>
                {reportMarkdown ? (
                  <div className="card" style={{padding:16, background:'#202022', marginBottom:12}}>
                    <div style={{fontWeight:700, marginBottom:12, borderBottom:'1px solid #444', paddingBottom:8, fontSize:14}}>
                      📝 종합 분석 리포트 (Chief Editor)
                    </div>
                    <div className="markdown-body" style={{fontSize:14, lineHeight:1.6}}>
                      <ReactMarkdown>{reportMarkdown}</ReactMarkdown>
                    </div>
                  </div>
                ) : (
                  <div className="card" style={{padding:12, marginBottom:12}}>
                    <div style={{fontWeight:700}}>요약</div>
                    <div className="muted" style={{fontSize:13, marginTop:6}}>
                      {activeAnalysis.result?.aggregate?.summary || '—'}
                    </div>
                  </div>
                )}
              </>
            )}

            {rightView === 'json' && (
              <div className="card" style={{padding:12}}>
                <div style={{fontWeight:700, marginBottom:8}}>Raw JSON</div>
                <pre className="mono" style={{whiteSpace:'pre-wrap', fontSize:12, lineHeight:1.5}}>
                  {pretty(activeAnalysis.result)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
