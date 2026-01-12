import React, { useEffect, useRef, useState } from 'react'
import { deleteAnalysis, deleteDocument, getAnalysis, getDocument, listAnalysesByDoc, listDocuments, runAnalysis, uploadDocument } from './api.js'

function pretty(obj) {
  try { return JSON.stringify(obj, null, 2) } catch { return String(obj) }
}

function Badge({ children }) {
  return <span style={{display:'inline-block', padding:'2px 8px', border:'1px solid #2a2a2c', borderRadius:999, fontSize:12, color:'#cfcfd6'}}>{children}</span>
}

export default function App() {
  const [docs, setDocs] = useState([])
  const [activeDocId, setActiveDocId] = useState(null)
  const [activeDoc, setActiveDoc] = useState(null)
  const [analyses, setAnalyses] = useState([])
  const [activeAnalysis, setActiveAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const fileRef = useRef(null)

  async function refreshDocs() {
    const items = await listDocuments()
    setDocs(items)
    if (!activeDocId && items.length) setActiveDocId(items[0].id)
  }

  useEffect(() => {
    refreshDocs().catch(e => setError(String(e)))
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
    }).catch(e => setError(String(e))).finally(() => setLoading(false))
  }, [activeDocId])

  async function onUpload(e) {
    const f = e.target.files?.[0]
    if (!f) return
    setLoading(true); setError(null)
    try {
      const doc = await uploadDocument(f)
      await refreshDocs()
      setActiveDocId(doc.id)
      if (fileRef.current) fileRef.current.value = ''
    } catch (e2) {
      setError(String(e2))
    } finally {
      setLoading(false)
    }
  }

  async function onRunAnalysis() {
    if (!activeDocId) return
    setLoading(true); setError(null)
    try {
      const a = await runAnalysis(activeDocId)
      const full = await getAnalysis(a.id)
      const list = await listAnalysesByDoc(activeDocId)
      setAnalyses(list)
      setActiveAnalysis(full)
    } catch (e2) {
      setError(String(e2))
    } finally {
      setLoading(false)
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
      // refresh list and pick next doc
      const items = await listDocuments()
      setDocs(items)
      if (id === activeDocId) {
        const nextId = items[0]?.id || null
        setActiveDocId(nextId)
        if (!nextId) {
          setActiveDoc(null)
          setAnalyses([])
          setActiveAnalysis(null)
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
      if (activeAnalysis?.id === id) setActiveAnalysis(null)
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
    } catch (e2) {
      setError(String(e2))
    } finally {
      setLoading(false)
    }
  }

  const readerLevel = activeAnalysis?.result?.final_metric?.reader_level
  const mode = activeAnalysis?.result?.debug?.mode || (activeAnalysis ? 'upstage_pipeline' : null)

  return (
    <div style={{display:'grid', gridTemplateColumns:'320px 1fr 520px', height:'100vh', gap:12, padding:12}}>
      {/* Left: history */}
      <div className="card" style={{padding:12, overflow:'auto'}}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', gap:10}}>
          <div>
            <div style={{fontSize:18, fontWeight:700}}>CONTEXTOR</div>
            <div className="muted" style={{fontSize:12}}>로컬 문서 분석 (PDF/DOCX 업로드)</div>
          </div>
          <label className="btn" style={{display:'inline-flex', alignItems:'center', gap:8}}>
            <span>업로드</span>
            <input ref={fileRef} type="file" accept=".pdf,.docx,.txt,.md" onChange={onUpload} style={{display:'none'}} />
          </label>
        </div>

        <div style={{marginTop:12, display:'flex', gap:8, flexWrap:'wrap'}}>
          {loading ? <Badge>loading</Badge> : <Badge>ready</Badge>}
          {docs.length ? <Badge>{docs.length} docs</Badge> : <Badge>no docs</Badge>}
        </div>

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
                title="삭제"
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); onDeleteDoc(d.id) }}
                disabled={loading}
                style={{width:56, display:'grid', placeItems:'center'}}
              >
                삭제
              </button>
            </div>
          ))}
        </div>

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
                title="삭제"
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); onDeleteAnalysis(a.id) }}
                disabled={loading}
                style={{width:56, display:'grid', placeItems:'center'}}
              >
                삭제
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Center: document viewer */}
      <div className="card" style={{padding:12, overflow:'auto'}}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', gap:10}}>
          <div>
            <div style={{fontSize:16, fontWeight:700}}>원고</div>
            <div className="muted" style={{fontSize:12}}>
              {activeDoc ? `${activeDoc.title} · ${activeDoc.filename}` : '선택된 문서 없음'}
            </div>
          </div>
          <button className="btn" onClick={onRunAnalysis} disabled={!activeDocId || loading}>
            분석 실행
          </button>
        </div>

        {error && (
          <div className="card" style={{marginTop:12, padding:12, borderColor:'#5a2a2a', background:'#1a0f10'}}>
            <div style={{fontWeight:700, marginBottom:6}}>Error</div>
            <div className="mono" style={{fontSize:12, whiteSpace:'pre-wrap'}}>{error}</div>
          </div>
        )}

        <div style={{marginTop:12}}>
          {activeDoc ? (
            <pre className="mono" style={{whiteSpace:'pre-wrap', lineHeight:1.5, fontSize:12}}>
              {activeDoc.extracted_text || '(텍스트를 추출하지 못했습니다)'}
            </pre>
          ) : (
            <div className="muted">왼쪽에서 원고를 선택하거나 업로드하세요.</div>
          )}
        </div>
      </div>

      {/* Right: results */}
      <div className="card" style={{padding:12, overflow:'auto'}}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', gap:10}}>
          <div>
            <div style={{fontSize:16, fontWeight:700}}>분석 결과</div>
            <div className="muted" style={{fontSize:12}}>
              {activeAnalysis ? `mode: ${mode}` : '분석을 실행하거나 기록을 선택하세요.'}
            </div>
          </div>
          {readerLevel && <Badge>독자 수준: {readerLevel}</Badge>}
        </div>

        {!activeAnalysis && (
          <div className="muted" style={{marginTop:14, fontSize:13}}>
            오른쪽 패널에는 에이전트들의 결과(JSON)가 표시됩니다. <br/>
            UPSTAGE_API_KEY가 없으면 로컬 휴리스틱 모드로 동작합니다.
          </div>
        )}

        {activeAnalysis && (
          <div style={{marginTop:12}}>
            <div className="card" style={{padding:12}}>
              <div style={{fontWeight:700}}>요약</div>
              <div className="muted" style={{fontSize:13, marginTop:6}}>
                {activeAnalysis.result?.aggregate?.summary || '—'}
              </div>
            </div>

            <div style={{height:12}} />

            <div className="card" style={{padding:12}}>
              <div style={{fontWeight:700, marginBottom:8}}>Raw JSON</div>
              <pre className="mono" style={{whiteSpace:'pre-wrap', fontSize:12, lineHeight:1.5}}>
                {pretty(activeAnalysis.result)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
