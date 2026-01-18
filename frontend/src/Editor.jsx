import React, { useState, useEffect, useRef } from 'react'
import HighlightedText from './HighlightedText'

// 아이콘 (간단한 SVG)
const Icons = {
  Bold: () => <b style={{ fontFamily: 'serif' }}>B</b>,
  Italic: () => <i style={{ fontFamily: 'serif' }}>I</i>,
  Underline: () => <u style={{ fontFamily: 'serif' }}>U</u>,
  Strike: () => <span style={{ textDecoration: 'line-through' }}>S</span>,
  AlignLeft: () => <span>≡</span>, // Placeholder for icon
  AlignCenter: () => <span>≚</span>,
  AlignRight: () => <span>≡</span>,
  Check: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>,
  Close: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
  Magic: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
}

function ToolbarButton({ active, children, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? '#eee' : 'transparent',
        border: 'none',
        borderRadius: 4,
        cursor: 'pointer',
        padding: '4px 8px',
        fontSize: 14,
        color: active ? '#000' : '#666',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minWidth: 28,
        height: 28
      }}
    >
      {children}
    </button>
  )
}

function TabButton({ label, active, onClick, icon }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: 'transparent',
        border: 'none',
        borderBottom: active ? '2px solid #555' : '2px solid transparent',
        cursor: 'pointer',
        padding: '8px 16px',
        fontSize: 14,
        fontWeight: active ? 700 : 500,
        color: active ? 'var(--text-main)' : 'var(--text-muted)',
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        transition: 'all 0.2s'
      }}
    >
      {icon && <span>{icon}</span>}
      {label}
    </button>
  )
}

function EditorBlock({ text, index, onChange, onFocus, isFocused, viewMode, analysisResult, setTooltip }) {
  const textareaRef = useRef(null)

  // 높이 자동 조절
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [text, viewMode])

  const isEditMode = viewMode === 'draft';

  return (
    <div
      style={{
        background: 'var(--bg-card)',
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
        border: isFocused ? '1px solid #888' : '1px solid transparent',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        transition: 'border-color 0.2s, box-shadow 0.2s',
        position: 'relative'
      }}
    >
      {isEditMode ? (
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => onChange(index, e.target.value)}
          onFocus={() => onFocus(index)}
          style={{
            width: '100%',
            border: 'none',
            background: 'transparent',
            resize: 'none',
            outline: 'none',
            fontSize: 16,
            lineHeight: 1.6,
            fontFamily: "'MaruBuri', 'Nanum Myeongjo', serif",
            color: 'var(--text-main)',
            padding: 0,
            margin: 0,
            display: 'block'
          }}
          spellCheck={false}
        />
      ) : (
        <div style={{
            fontSize: 16,
            lineHeight: 1.6,
            fontFamily: "'MaruBuri', 'Nanum Myeongjo', serif",
            color: 'var(--text-main)',
            minHeight: '24px'
        }}>
           <HighlightedText text={text} analysisResult={analysisResult} setTooltip={setTooltip} />
        </div>
      )}
      
      {/* 하단 컨트롤 (이미지 참조) */}
      <div style={{
        marginTop: 12,
        display: 'flex',
        justifyContent: 'flex-end',
        alignItems: 'center',
        gap: 8,
        opacity: 0.6
      }}>
        {isEditMode ? (
            <span style={{ fontSize: 12 }}>{text.length}자</span>
        ) : (
             <>
                <button className="btn-icon-sm" title="확인">
                  <Icons.Check />
                </button>
                <button className="btn-icon-sm" title="취소">
                  <Icons.Close />
                </button>
                <span style={{ fontSize: 12, cursor: 'pointer', marginLeft: 8 }}>원본/코멘트 보기</span>
             </>
        )}
      </div>
    </div>
  )
}

export default function Editor({ initialText, onSave, analysisResult, setTooltip }) {
  const [blocks, setBlocks] = useState([])
  const [focusedIndex, setFocusedIndex] = useState(null)
  const [activeTab, setActiveTab] = useState('draft') // draft, feedback, plot, proof, polish, qna

  useEffect(() => {
    if (initialText) {
      const splitText = initialText.split(/\n+/).filter(t => t.trim().length > 0)
      setBlocks(splitText)
    } else {
      setBlocks([''])
    }
  }, [initialText])

  const handleBlockChange = (index, newText) => {
    const newBlocks = [...blocks]
    newBlocks[index] = newText
    setBlocks(newBlocks)
    if (onSave) onSave(newBlocks.join('\n\n'))
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg-panel)' }}>
      <style>{`
        .btn-icon-sm {
          background: transparent;
          border: none;
          cursor: pointer;
          color: inherit;
          padding: 4px;
          display: flex;
          align-items: center;
          justifyContent: center;
        }
        .btn-icon-sm:hover {
          background: rgba(0,0,0,0.05);
          border-radius: 4px;
        }
      `}</style>
      
      {/* 상단 툴바 영역 */}
      <div style={{ 
        padding: '8px 16px', 
        borderBottom: '1px solid var(--border)', 
        background: 'var(--bg-card)',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        flexShrink: 0
      }}>
        {/* 서식 툴바 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, paddingBottom: 8, borderBottom: '1px solid var(--border-light, #eee)' }}>
          <span style={{ fontSize: 13, marginRight: 8, fontWeight: 700 }}>마루부리</span>
          <ToolbarButton>-</ToolbarButton>
          <span style={{ fontSize: 13 }}>16</span>
          <ToolbarButton>+</ToolbarButton>
          <div style={{ width: 1, height: 16, background: '#ddd', margin: '0 8px' }} />
          <ToolbarButton><Icons.Bold /></ToolbarButton>
          <ToolbarButton><Icons.Italic /></ToolbarButton>
          <ToolbarButton><Icons.Underline /></ToolbarButton>
          <ToolbarButton><Icons.Strike /></ToolbarButton>
          <div style={{ width: 1, height: 16, background: '#ddd', margin: '0 8px' }} />
          <ToolbarButton><Icons.AlignLeft /></ToolbarButton>
          <ToolbarButton><Icons.AlignCenter /></ToolbarButton>
          <ToolbarButton><Icons.AlignRight /></ToolbarButton>
        </div>

        {/* 탭 메뉴 */}
        <div style={{ display: 'flex', gap: 4, overflowX: 'auto' }}>
          <TabButton label="초고쓰기" active={activeTab === 'draft'} onClick={() => setActiveTab('draft')} icon="✍️" />
          <TabButton label="피드백" active={activeTab === 'feedback'} onClick={() => setActiveTab('feedback')} icon="💬" />
          <TabButton label="전개" active={activeTab === 'plot'} onClick={() => setActiveTab('plot')} icon="💡" />
          <TabButton label="교정·교열" active={activeTab === 'proof'} onClick={() => setActiveTab('proof')} icon="✅" />
          <TabButton label="윤문" active={activeTab === 'polish'} onClick={() => setActiveTab('polish')} icon="✨" />
          <TabButton label="질문" active={activeTab === 'qna'} onClick={() => setActiveTab('qna')} icon="❓" />
        </div>
      </div>

      {/* 기능 버튼 영역 (윤문 등) */}
      {(activeTab === 'polish' || activeTab === 'proof' || activeTab === 'feedback') && (
        <div style={{ 
          padding: '8px 16px', 
          background: '#fff0f0', 
          borderBottom: '1px solid #ffd0d0',
          display: 'flex', 
          gap: 8, 
          alignItems: 'center',
          flexShrink: 0
        }}>
          <button className="btn" style={{ background: '#e57373', color: 'white', border: 'none' }}>{activeTab === 'feedback' ? 'AI 전체 분석' : '일괄 반영'}</button>
          <button className="btn" style={{ background: 'white', border: '1px solid #ddd' }}>전체 제거</button>
        </div>
      )}

      {/* 본문 에디터 영역 */}
      <div className="scroll-hide" style={{ 
        flex: 1, 
        overflowY: 'auto', 
        padding: '20px',
        background: '#f8f9fa'
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          {blocks.map((text, idx) => (
            <EditorBlock
              key={idx}
              index={idx}
              text={text}
              onChange={handleBlockChange}
              onFocus={setFocusedIndex}
              isFocused={focusedIndex === idx}
              viewMode={activeTab}
              analysisResult={analysisResult}
              setTooltip={setTooltip}
            />
          ))}
          
          <div 
            onClick={() => {
              setBlocks([...blocks, ''])
              setFocusedIndex(blocks.length)
            }}
            style={{ 
              padding: 20, 
              textAlign: 'center', 
              color: '#aaa', 
              cursor: 'pointer',
              border: '2px dashed #ddd',
              borderRadius: 8,
              marginTop: 20
            }}
          >
            + 문단 추가
          </div>
        </div>
      </div>
    </div>
  )
}