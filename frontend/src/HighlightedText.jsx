import React from 'react'

function convertRgbaToRgb(rgbaString) {
  const parts = rgbaString.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)/);
  if (parts && parts.length === 5) {
    return `rgb(${parts[1]}, ${parts[2]}, ${parts[3]})`;
  }
  return rgbaString; // Return original if not rgba
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

export default function HighlightedText({ text: propText, analysisResult, setTooltip }) {
  // 줄바꿈 정규화: CRLF -> LF (윈도우 환경 등에서 좌표 밀림 방지)
  // 유니코드 정규화: NFC (맥/리눅스 간 자모 분리 차이 방지)
  const text = typeof propText === 'string' 
    ? propText.replace(/\r\n/g, '\n').normalize('NFC') 
    : propText
  
  const rawHighlights = Array.isArray(analysisResult?.highlights) ? analysisResult.highlights : []
  const rawNormalized = Array.isArray(analysisResult?.normalized_issues) ? analysisResult.normalized_issues : []
  const hasDocHighlights = rawHighlights.length > 0 || rawNormalized.length > 0

  const handleMouseLeave = () => {
    setTooltip(prev => ({ ...prev, visible: false }))
  }

  const handleMouseMove = (e) => {
    setTooltip(prev => ({ ...prev, x: e.clientX, y: e.clientY }))
  }

  // 1. 문서 전체 범위 기반 하이라이트 (legacy or specific logic)
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

  // 2. 문장 단위 분석 결과 기반 하이라이트 (split_sentences 사용)
  if (!analysisResult?.split_sentences || !analysisResult?.split_map) {
    return <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: 15 }}>{text}</div>
  }

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

  // 에디터의 문단(Block) 텍스트와 분석된 문장들을 매칭해야 함.
  // 여기서는 단순히 전체 텍스트를 문장 단위로 렌더링하는 기존 로직을 그대로 사용하되,
  // EditorBlock에서 전달받은 'text' (문단)가 전체 텍스트의 일부분일 수 있음을 고려해야 함.
  
  // 하지만, 현재 구조상 analysisResult는 "전체 문서" 기준의 인덱스(sentence_index)를 가지고 있음.
  // EditorBlock은 "문단" 단위로 잘려있음.
  // 이 매핑을 정확히 하려면 복잡한 계산이 필요함.
  // 간단한 해결책: 
  // 1. HighlightedText 컴포넌트는 "전체 텍스트" 기준 렌더링용이므로, Editor 내에서 전체 텍스트 뷰를 보여줄 때 사용하거나,
  // 2. EditorBlock 내에서 "해당 문단에 속하는 문장들"만 필터링해서 보여줘야 함.
  
  // 여기서는 2번 방식을 위해, 문단 텍스트 자체를 입력받아
  // 그 문단 텍스트 내에서 분석 결과를 찾아 매핑하는 로직이 필요하지만,
  // analysisResult의 sentence_index는 전체 문서 기준이므로 매칭이 어려움.
  
  // 따라서 타협안:
  // EditorBlock 내부에서 HighlightedText를 쓸 때는, 
  // analysisResult를 통째로 넘기되, 현재 문단 텍스트와 일치하는 문장만 찾아내거나,
  // 혹은 단순히 "편집 모드"가 아닌 "전체 보기 모드"에서만 하이라이트를 제공하는 것이 안전함.
  
  // 그러나 사용자는 "문단별 피드백"을 원함.
  // 문단별 매칭을 위해: 문단 텍스트가 analysisResult.split_sentences의 어느 부분에 해당하는지 찾아야 함.
  
  // 이 파일은 일단 기존 로직을 그대로 보존하여 export함.
  
  return (
    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontSize: 15 }}>
      {sentences.map((sent, idx) => {
        // 문단 텍스트(text) 내에 이 문장(sent)이 포함되어 있는지 확인
        if (!text.includes(sent)) return null;

        const sentIssues = issuesBySentence[idx] || []
        
        let content = null;

        if (sentIssues.length === 0) {
            content = <span key={idx}>{sent} </span>
        } else {
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
            content = <span key={idx} style={{ marginRight: 4 }}>{fragments}</span>
        }
        
        return content
      })}
    </div>
  )
}
