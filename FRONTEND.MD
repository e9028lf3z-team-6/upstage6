# Frontend Overview

## 역할 요약
- Vite + React 기반 단일 페이지 UI로 문서 업로드, 분석 실행, 결과 리포트를 제공합니다.
- 분석 결과 하이라이트와 마크다운 리포트 렌더링을 포함합니다.

## 디렉터리 구조
- `frontend/src/App.jsx`: 전체 UI/상태/하이라이트 로직.
- `frontend/src/api.js`: 백엔드 API 래퍼.
- `frontend/src/main.jsx`: React 엔트리.
- `frontend/index.html`: 루트 템플릿.
- `frontend/vite.config.js`: Vite 설정.

## 실행/빌드
- 개발 서버: `cd frontend && npm run dev`
- 빌드/미리보기: `npm run build`, `npm run preview`

## 환경 변수
- `VITE_API_BASE`: 기본값 `http://localhost:8000/api`.

## 주요 화면 구성
- 좌측: 사용자 정보/문서 목록/분석 기록/업로드 패널/설정 패널.
- 중앙: 원문 표시(하이라이트), 내보내기(txt/docx), 텍스트 입력 저장.
- 우측: 분석 리포트(마크다운) 및 JSON 뷰.
- 하단: QA 점수 위젯.

## 하이라이트 로직
- `analysisResult.highlights` 또는 `normalized_issues`의 `doc_start/doc_end`를 우선 사용해 원문 기준 하이라이트.
- 겹침 구간은 모든 이슈를 툴팁에 합쳐 표시하며, 색상은 agent 기준.
- `highlights/normalized_issues`가 없으면 `split_sentences` 기반 하이라이트로 fallback.

## 인증 흐름
- 로그인: `/api/auth/login`으로 이동 → 콜백에서 토큰 수신 → `localStorage` 저장.
- 사용자 정보: `/api/auth/me` 호출.
- 로그아웃 시 토큰 제거 후 새로고침.

## API 연동 요약
- 문서: `/documents`, `/documents/upload`, `/documents/{id}`.
- 분석: `/analysis/run/{id}`, `/analysis/{id}`, `/analysis/by-document/{id}`.
- 평가: `/eval/run` (필요 시 별도 호출).

## 주의사항
- 설정 UI의 `personaCount`, `creativeFocus`는 현재 백엔드에서 사용되지 않습니다.
- 401 응답 시 토큰을 제거하며, 에러 메시지는 원문 그대로 표시됩니다.
