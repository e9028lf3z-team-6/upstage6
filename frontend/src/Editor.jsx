import React, { useState, useEffect } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Placeholder from '@tiptap/extension-placeholder'
import { TextStyle } from '@tiptap/extension-text-style'
import { FontFamily } from '@tiptap/extension-font-family'
import HighlightedText from './HighlightedText'

// 아이콘 (간단한 SVG)
const Icons = {
  Bold: () => <b style={{ fontFamily: 'serif' }}>B</b>,
  Italic: () => <i style={{ fontFamily: 'serif' }}>I</i>,
  Underline: () => <u style={{ fontFamily: 'serif' }}>U</u>,
  Strike: () => <span style={{ textDecoration: 'line-through' }}>S</span>,
  AlignLeft: () => <span>≡</span>,
  AlignCenter: () => <span>≚</span>,
  AlignRight: () => <span>≡</span>,
  Check: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>,
  Close: () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
}

// 글자 크기 조절을 위한 커스텀 익스텐션
const FontSize = TextStyle.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      fontSize: {
        default: null,
        parseHTML: element => element.style.fontSize,
        renderHTML: attributes => {
          if (!attributes.fontSize) return {}
          return { style: `font-size: ${attributes.fontSize}` }
        },
      },
    }
  },
})

function ToolbarButton({ active, children, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        background: active ? '#eee' : 'transparent',
        border: 'none',
        borderRadius: 4,
        cursor: disabled ? 'not-allowed' : 'pointer',
        padding: '4px 8px',
        fontSize: 14,
        color: active ? '#000' : (disabled ? '#ccc' : '#666'),
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minWidth: 28,
        height: 28,
        opacity: disabled ? 0.5 : 1
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

export default function Editor({ initialText, onSave, analysisResult, setTooltip, onRunAnalysis, isAnalyzing, onExportTxt, onExportDocx, onToggleRightPanel }) {
  const [activeTab, setActiveTab] = useState('draft') // draft, highlight, run_analysis
  const [fontFamily, setFontFamily] = useState("'MaruBuri', 'Nanum Myeongjo', serif")
  const [fontSize, setFontSize] = useState(16)
  const [isLegendOpen, setIsLegendOpen] = useState(false)
  const [isExportOpen, setIsExportOpen] = useState(false)
  
  // 페르소나 설정 상태
  const [personaName, setPersonaName] = useState('')
  const [personaDesc, setPersonaDesc] = useState('')

  const fonts = [
    { name: '마루부리', value: "'MaruBuri', serif" },
    { name: '나눔명조', value: "'Nanum Myeongjo', serif" },
    { name: '바탕체', value: "'Batang', serif" },
    { name: 'Pretendard', value: "'Pretendard', sans-serif" },
    { name: '나눔고딕', value: "'Nanum Gothic', sans-serif" },
    { name: '나눔손글씨', value: "'Nanum Pen Script', cursive" },
    { name: '시스템 명조', value: "serif" },
    { name: '시스템 고딕', value: "sans-serif" }
  ]

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      TextStyle,
      FontFamily,
      FontSize,
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Placeholder.configure({
        placeholder: '당신의 이야기를 들려주세요...',
      }),
    ],
    content: initialText ? initialText.split('\n').map(line => `<p>${line}</p>`).join('') : '',
    onUpdate: ({ editor }) => {
      if (onSave) {
        onSave(editor.getHTML())
      }
    },
    editable: activeTab === 'draft' // 초고쓰기 탭에서만 편집 가능
  })

  // 문서 이동 시 에디터 콘텐츠 업데이트
  useEffect(() => {
    if (editor && initialText) {
      const htmlContent = initialText.split('\n').map(line => `<p>${line}</p>`).join('')
      if (editor.getHTML() !== htmlContent) {
        editor.commands.setContent(htmlContent)
      }
    }
  }, [initialText, editor])

  // 분석이 시작되면 자동으로 '분석 실행' 탭으로 이동
  useEffect(() => {
    if (isAnalyzing) {
      setActiveTab('run_analysis')
    }
  }, [isAnalyzing])

  // 분석이 완료되면 자동으로 하이라이트 탭으로 이동
  useEffect(() => {
    if (!isAnalyzing && analysisResult) {
      setActiveTab('highlight')
    }
  }, [isAnalyzing, analysisResult])

  // 탭 변경 시 에디터 편집 가능 여부 업데이트
  useEffect(() => {
    if (editor) {
      editor.setEditable(activeTab === 'draft')
    }
  }, [activeTab, editor])

  // 폰트 변경 시 에디터에 적용
  useEffect(() => {
    if (editor && fontFamily) {
      editor.chain().focus().setFontFamily(fontFamily).run()
    }
  }, [fontFamily, editor])

  // 글자 크기 조절
  const handleFontSize = (delta) => {
    const newSize = Math.min(Math.max(fontSize + delta, 12), 32)
    setFontSize(newSize)
    if (editor) {
      editor.chain().focus().setMark('textStyle', { fontSize: `${newSize}px` }).run()
    }
  }

  if (!editor) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--bg-panel)' }}>
      <style>{`
        .ProseMirror {
          min-height: 500px;
          outline: none;
          padding: 40px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.05);
          font-size: ${fontSize}px;
          line-height: 1.8;
          font-family: ${fontFamily};
        }
        .ProseMirror p { margin-bottom: 1em; }
        .ProseMirror p.is-editor-empty:first-child::before {
          content: attr(data-placeholder);
          float: left;
          color: #adb5bd;
          pointer-events: none;
          height: 0;
        }
        .font-select {
          border: 1px solid transparent;
          background: transparent;
          padding: 2px 4px;
          border-radius: 4px;
          font-size: 13px;
          font-weight: 700;
          cursor: pointer;
        }
        .font-select:hover { background: #f0f0f0; }
        
        .analysis-screen {
          display: flex;
          flex-direction: column;
          align-items: center;
          justifyContent: center;
          height: 500px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.05);
          text-align: center;
          padding: 40px;
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
        {/* 서식 툴바 + 액션 버튼 통합 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid var(--border-light, #eee)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <select 
              className="font-select"
              value={fontFamily}
              onChange={(e) => setFontFamily(e.target.value)}
            >
              {fonts.map(f => (
                <option key={f.value} value={f.value}>{f.name}</option>
              ))}
            </select>
            <div style={{ width: 1, height: 16, background: '#ddd', margin: '0 8px' }} />
            
            <ToolbarButton onClick={() => handleFontSize(-1)}>-</ToolbarButton>
            <span style={{ fontSize: 13, minWidth: 20, textAlign: 'center' }}>{fontSize}</span>
            <ToolbarButton onClick={() => handleFontSize(1)}>+</ToolbarButton>
            
            <div style={{ width: 1, height: 16, background: '#ddd', margin: '0 8px' }} />
            
            <ToolbarButton 
              onClick={() => editor.chain().focus().toggleBold().run()}
              active={editor.isActive('bold')}
              disabled={activeTab !== 'draft'}
            >
              <Icons.Bold />
            </ToolbarButton>
            <ToolbarButton 
              onClick={() => editor.chain().focus().toggleItalic().run()}
              active={editor.isActive('italic')}
              disabled={activeTab !== 'draft'}
            >
              <Icons.Italic />
            </ToolbarButton>
            <ToolbarButton 
              onClick={() => editor.chain().focus().toggleUnderline().run()}
              active={editor.isActive('underline')}
              disabled={activeTab !== 'draft'}
            >
              <Icons.Underline />
            </ToolbarButton>
            
            <div style={{ width: 1, height: 16, background: '#ddd', margin: '0 8px' }} />
            
            <ToolbarButton 
              onClick={() => editor.chain().focus().setTextAlign('left').run()}
              active={editor.isActive({ textAlign: 'left' })}
              disabled={activeTab !== 'draft'}
            >
              <Icons.AlignLeft />
            </ToolbarButton>
            <ToolbarButton 
              onClick={() => editor.chain().focus().setTextAlign('center').run()}
              active={editor.isActive({ textAlign: 'center' })}
              disabled={activeTab !== 'draft'}
            >
              <Icons.AlignCenter />
            </ToolbarButton>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ position: 'relative' }} onMouseEnter={() => setIsExportOpen(true)} onMouseLeave={() => setIsExportOpen(false)}>
              <button className="btn" style={{ padding: '4px 8px', background: 'transparent' }} title="내보내기">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              </button>
              {isExportOpen && (
                <div style={{ position: 'absolute', top: '100%', right: 0, zIndex: 100, background: 'white', border: '1px solid #ddd', borderRadius: 4, padding: 4, boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
                  <button className="btn" onClick={onExportTxt} style={{ width: '100%', fontSize: 12, textAlign: 'left', border: 'none', padding: '6px 12px', background: 'white' }}>txt로 저장</button>
                  <button className="btn" onClick={onExportDocx} style={{ width: '100%', fontSize: 12, textAlign: 'left', border: 'none', padding: '6px 12px', background: 'white' }}>docx로 저장</button>
                </div>
              )}
            </div>
            <button className="btn" onClick={onToggleRightPanel} style={{ padding: '4px 8px', background: 'transparent' }} title="보고서 보기">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 4 }}>
          <TabButton label="초고쓰기" active={activeTab === 'draft'} onClick={() => setActiveTab('draft')} icon="✍️" />
          <TabButton label="가상 독자" active={activeTab === 'persona'} onClick={() => setActiveTab('persona')} icon="🎭" />
          <TabButton label="분석 실행" active={activeTab === 'run_analysis'} onClick={() => setActiveTab('run_analysis')} icon="⚡" />
          <TabButton label="하이라이트" active={activeTab === 'highlight'} onClick={() => setActiveTab('highlight')} icon="🖍️" />
        </div>
      </div>

      {/* 에이전트 범례 (본문 영역 왼쪽 상단에 컴팩트하게 배치) */}
      {activeTab === 'highlight' && (
        <div style={{ position: 'relative', height: 0, zIndex: 100 }}>
          <div 
            onMouseEnter={() => setIsLegendOpen(true)}
            onMouseLeave={() => setIsLegendOpen(false)}
            style={{ 
              position: 'absolute',
              top: 10,
              left: 16,
              padding: '4px 10px',
              fontSize: 11,
              fontWeight: 800,
              color: 'var(--text-muted)',
              cursor: 'help',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              background: 'var(--bg-card)',
              borderRadius: 6,
              border: '1px solid var(--border)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
              width: 'fit-content' 
            }}
          >
            <span>에이전트 범례</span>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M6 9l6 6 6-6"/></svg>
            
            {isLegendOpen && (
              <div style={{ 
                position: 'absolute',
                top: '100%',
                left: 0,
                zIndex: 1000,
                background: 'var(--bg-card)',
                padding: '12px',
                borderRadius: 8,
                boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                border: '1px solid var(--border)',
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
                whiteSpace: 'nowrap',
                marginTop: 4
              }}>
                {[ 
                  { label: '어조', color: 'rgba(92, 107, 192, 0.5)' },
                  { label: '논리/개연성', color: 'rgba(255, 167, 38, 0.5)' },
                  { label: '심리/트라우마', color: 'rgba(211, 47, 47, 0.6)' },
                  { label: '혐오/편향', color: 'rgba(255, 64, 129, 0.6)' },
                  { label: '장르 클리셰', color: 'rgba(66, 165, 245, 0.5)' },
                  { label: '맞춤법', color: 'rgba(0, 188, 212, 0.6)' },
                  { label: '긴장도', color: 'rgba(139, 195, 74, 0.5)' },
                ].map(item => (
                  <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, fontWeight: 700, color: 'var(--text-main)' }}>
                    <span style={{ width: 12, height: 12, borderRadius: 3, background: item.color }} />
                    {item.label}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 본문 에디터 영역 */}
      <div className="scroll-hide" style={{ 
        flex: 1, 
        overflowY: 'auto', 
        padding: '20px 20px 40px',
        background: '#f8f9fa'
      }}>
        <div style={{ 
          maxWidth: 800, 
          margin: '0 auto'
        }}>
          {/* 에디터 메인 영역 */}
          {activeTab === 'draft' && <EditorContent editor={editor} />}

          {/* 페르소나 설정 영역 */}
          {activeTab === 'persona' && (
            <div style={{ background: 'white', borderRadius: 12, padding: '40px', boxShadow: '0 4px 25px rgba(0,0,0,0.05)', border: '1px solid #eee' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '2rem', color: '#333', textAlign: 'center' }}>가상 독자 설정</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 24, maxWidth: 600, margin: '0 auto' }}>
                <div>
                  <label style={{ fontSize: 14, fontWeight: 700, color: '#444', marginBottom: 8, display: 'block' }}>가상 독자 간단 설정</label>
                  <input 
                    type="text" 
                    value={personaName}
                    onChange={(e) => setPersonaName(e.target.value)}
                    placeholder="예: 까칠한 웹소설 PD, 20대 로맨스 열혈 독자" 
                    style={{ width: '100%', padding: '12px 16px', borderRadius: 8, border: '1px solid #ddd', fontSize: 15, outline: 'none' }} 
                  />
                </div>
                <div>
                  <label style={{ fontSize: 14, fontWeight: 700, color: '#444', marginBottom: 8, display: 'block' }}>(옵션) 가상 독자 상세 설정</label>
                  <textarea 
                    value={personaDesc}
                    onChange={(e) => setPersonaDesc(e.target.value)}
                    placeholder="해당 페르소나의 성향을 자유롭게 적어주세요." 
                    style={{ width: '100%', height: 120, padding: '12px 16px', borderRadius: 8, border: '1px solid #ddd', fontSize: 15, outline: 'none', resize: 'none', lineHeight: 1.6 }} 
                  />
                </div>
                <button 
                  onClick={() => setActiveTab('run_analysis')} 
                  style={{ width: '100%', padding: '16px', background: '#333', color: 'white', border: 'none', borderRadius: 8, fontSize: 16, fontWeight: 700, cursor: 'pointer', marginTop: '8px' }}
                >
                  가상 독자 설정 완료 ✅
                </button>
              </div>
            </div>
          )}
          
          {activeTab === 'highlight' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 30 }}>
              <div className="ProseMirror">
                 <HighlightedText text={editor.getText()} analysisResult={analysisResult} setTooltip={setTooltip} />
              </div>
            </div>
          )}

          {activeTab === 'run_analysis' && (
            <div className="analysis-screen" style={{ background: 'white', borderRadius: 16, border: '1px solid #eee' }}>
              {!isAnalyzing ? (
                <>
                  <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🔬</div>
                  <h2 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '16px', color: '#333' }}>전문가 분석 준비 완료</h2>
                  <p style={{ color: '#666', marginBottom: '40px', lineHeight: 1.6 }}>
                    7개의 주요 에이전트가 당신의 문장을 기다리고 있습니다.<br/>
                    준비가 되셨다면 아래 버튼을 눌러주세요.
                  </p>
                  <button 
                    className="btn" 
                    onClick={() => onRunAnalysis(personaName, personaDesc)} 
                    style={{ 
                      padding: '18px 64px', fontSize: '1.1rem', fontWeight: 800, background: '#4CAF50', color: 'white', border: 'none', borderRadius: 12, cursor: 'pointer', boxShadow: '0 4px 15px rgba(76, 175, 80, 0.3)', transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => e.target.style.transform = 'translateY(-2px)'}
                    onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
                  >
                    분석 시작하기
                  </button>
                </>
              ) : (
                <div style={{ width: '100%', maxWidth: 500 }}>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '40px', color: '#333' }}>에이전트들이 원고를 읽고 있습니다</h2>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '40px' }}>
                    {[
                      { label: '어조', color: '#5C6BC0', icon: '🎭' },
                      { label: '논리', color: '#FFA726', icon: '🔍' },
                      { label: '심리', color: '#D32F2F', icon: '❤️' },
                      { label: '윤리', color: '#F06292', icon: '⚖️' },
                      { label: '클리셰', color: '#42A5F5', icon: '🌊' },
                      { label: '맞춤법', color: '#00BCD4', icon: '🖋️' },
                      { label: '긴장도', color: '#8BC34A', icon: '📈' },
                      { label: '종합', color: '#333', icon: '✨' },
                    ].map((agent, i) => (
                      <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                        <div className="agent-circle" style={{ 
                          width: '50px', 
                          height: '50px', 
                          borderRadius: '50%', 
                          background: '#f8f9fa', 
                          display: 'grid', 
                          placeItems: 'center',
                          fontSize: '20px',
                          border: `2px solid ${agent.color}`,
                          position: 'relative',
                          animation: `pulse-agent 2s infinite ${i * 0.2}s`
                        }}>
                          {agent.icon}
                        </div>
                        <span style={{ fontSize: '11px', fontWeight: 700, color: '#888' }}>{agent.label}</span>
                      </div>
                    ))}
                  </div>

                  <div style={{ height: '6px', background: '#eee', borderRadius: '3px', overflow: 'hidden', position: 'relative' }}>
                    <div className="analysis-progress-bar" style={{ 
                      width: '100%', height: '100%', background: 'linear-gradient(90deg, #4CAF50, #81C784)', animation: 'moving-gradient 2s infinite linear' 
                    }} />
                  </div>
                  <p style={{ marginTop: '16px', fontSize: '13px', color: '#4CAF50', fontWeight: 700 }}>AI 협업 분석 진행 중...</p>
                </div>
              )}
              
              <style>{`
                @keyframes pulse-agent {
                  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0,0,0,0.1); }
                  50% { transform: scale(1.1); box-shadow: 0 0 20px 0 rgba(0,0,0,0.05); }
                  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0,0,0,0.1); }
                }
                @keyframes moving-gradient {
                  0% { transform: translateX(-100%); }
                  100% { transform: translateX(100%); }
                }
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
              `}</style>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}