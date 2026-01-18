import React, { useEffect, useState } from 'react'

export default function Intro({ onFinish }) {
  const [visible, setVisible] = useState(false)
  const [line1, setLine1] = useState('')
  const [line2, setLine2] = useState('')
  
  const text1 = "매일 쏟아지는 수천 편의 이야기 속에서,"
  const text2 = "당신의 문장이 빛을 발하도록."

  useEffect(() => {
    requestAnimationFrame(() => setVisible(true))

    let i = 0
    let j = 0
    
    // 첫 번째 줄 타이핑
    const timer1 = setInterval(() => {
      if (i < text1.length) {
        setLine1(prev => prev + text1.charAt(i))
        i++
      } else {
        clearInterval(timer1)
        // 두 번째 줄 타이핑 시작
        const timer2 = setInterval(() => {
          if (j < text2.length) {
            setLine2(prev => prev + text2.charAt(j))
            j++
          } else {
            clearInterval(timer2)
          }
        }, 60)
      }
    }, 60)

    return () => {
      clearInterval(timer1)
    }
  }, [])

  const handleStart = () => {
    setVisible(false)
    setTimeout(() => {
      onFinish()
    }, 800) // 페이드 아웃 시간과 맞춤
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&display=swap');
        
        .serif-font {
          font-family: 'Nanum Myeongjo', 'Batang', serif;
        }

        .ink-spread {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 60vw;
          height: 60vw;
          background: radial-gradient(circle, rgba(20,20,25,0.95) 0%, rgba(10,10,15,0.0) 70%);
          opacity: 0.8;
          z-index: 0;
          pointer-events: none;
        }

        .fade-in-up {
          animation: fadeInUp 1s ease-out forwards;
          opacity: 0;
          transform: translateY(20px);
        }

        @keyframes fadeInUp {
          to { opacity: 1; transform: translateY(0); }
        }
        
        .book-btn:hover {
          background-color: #fff !important;
          color: #000 !important;
          transform: translateY(-2px);
          box-shadow: 0 4px 20px rgba(255, 255, 255, 0.15);
        }
      `}</style>

      <div className="serif-font" style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: '#0a0a0c', // 아주 깊은 먹색
        color: '#e0e0e0',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999,
        opacity: visible ? 1 : 0,
        transition: 'opacity 0.8s ease-in-out',
        backgroundImage: 'url("https://www.transparenttextures.com/patterns/stardust.png")', // 노이즈 텍스처 느낌
      }}>
        
        {/* 배경 잉크 효과 */}
        <div className="ink-spread" />

        <div style={{ zIndex: 10, textAlign: 'center', padding: '0 20px' }}>
          
          {/* 메인 타이틀 */}
          <h1 style={{ 
            fontSize: 'clamp(3rem, 6vw, 5rem)', 
            fontWeight: 800, 
            marginBottom: '3rem',
            color: '#f5f5f5',
            letterSpacing: '0.05em',
            textShadow: '0 2px 10px rgba(0,0,0,0.5)',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            paddingBottom: '20px',
            display: 'inline-block'
          }}>
            CONTEXTOR
          </h1>

          {/* 감성 문구 타이핑 */}
          <div style={{ minHeight: '80px', marginBottom: '3rem' }}>
            <p style={{ fontSize: '1.2rem', color: '#aaa', marginBottom: '10px', fontWeight: 400 }}>
              {line1}
            </p>
            <p style={{ fontSize: '1.4rem', color: '#fff', fontWeight: 700 }}>
              {line2}<span style={{ animation: 'blink 1s infinite' }}>|</span>
            </p>
          </div>

          {/* 시장 분석 요약 (작게) */}
          <div className="fade-in-up" style={{ animationDelay: '2.5s', marginBottom: '4rem' }}>
            <p style={{ fontSize: '0.9rem', color: '#666', lineHeight: 1.6, letterSpacing: '0.02em' }}>
              TAM 20조원 · SAM 1.3조원 · SOM 500억원<br />
              <span style={{ color: '#888' }}>질적 완결성을 위한 단 하나의 선택</span>
            </p>
          </div>

          {/* 시작 버튼 */}
          <button 
            className="book-btn fade-in-up"
            onClick={handleStart}
            style={{
              animationDelay: '3s',
              padding: '16px 48px',
              fontSize: '1.1rem',
              fontFamily: 'inherit',
              fontWeight: 700,
              backgroundColor: 'transparent',
              color: '#fff',
              border: '1px solid rgba(255,255,255,0.4)',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              letterSpacing: '0.1em'
            }}
          >
            집필 시작하기
          </button>
        </div>
      </div>
    </>
  )
}