# Repository Guidelines

## 프로젝트 구조 및 모듈 구성
- `backend/`는 FastAPI 서비스이며, 엔트리 포인트는 `backend/main.py`입니다. 주요 로직은 `backend/app/`(api, webapi, services, graph, agents, llm, schemas, core)에 위치합니다.
- `backend/migrations/`에는 SQLite 마이그레이션 스크립트가, `backend/scripts/`에는 로컬 평가 유틸리티가 있습니다.
- `frontend/`는 Vite + React 앱입니다. UI 코드는 `frontend/src/`(`App.jsx`, `api.js`)에 있으며 설정은 `frontend/vite.config.js`에 있습니다.
- 예시 환경 파일은 `backend/.env.example`, `frontend/.env.example`에 있습니다.

## 빌드, 테스트 및 개발 명령어
- `cd backend && python -m venv .venv` 후 `pip install -e .`로 백엔드 가상환경과 의존성을 설정합니다.
- `cd backend && uvicorn main:app --reload --port 8000`로 API를 실행합니다.
- `python backend/migrations/apply_sqlite_migrations.py`로 SQLite 스키마 업데이트를 적용합니다.
- `cd frontend && npm install`로 프런트엔드 의존성을 설치합니다.
- `cd frontend && npm run dev`로 UI 개발 서버를 실행합니다.
- `cd frontend && npm run build` 또는 `npm run preview`로 프로덕션 빌드/미리보기를 수행합니다.

## 코딩 스타일 및 네이밍 규칙
- Python: 4칸 들여쓰기, PEP 8 네이밍(함수/모듈은 snake_case, 클래스는 CapWords). 로직은 `backend/app/...` 구조를 유지합니다.
- JavaScript/React: 기존 스타일을 따르며(2칸 들여쓰기, 작은따옴표, 세미콜론 없음), 컴포넌트는 PascalCase, 훅은 `useX` 패턴을 사용합니다.

## 테스트 가이드라인
- 자동화된 테스트가 아직 없습니다. 백엔드 테스트를 추가한다면 `backend/tests`에 `test_*.py`로 작성하고 pytest를 사용하세요.
- 프런트엔드 테스트는 `frontend/src/__tests__`에 `*.test.jsx`로 추가하는 것을 권장합니다(React Testing Library 도입 시 명시).
- PR에는 수동 검증 항목(문서 업로드, 분석 실행, 리포트 확인 등)을 적어주세요.

## 커밋 및 PR 가이드라인
- 커밋 히스토리는 한국어 짧은 메시지와 Conventional Commit이 혼재합니다. `feat:`, `fix:`, `chore:`, `docs:` 형태의 간결한 메시지를 권장하며, 팀 관례에 따라 한국어 요약도 허용됩니다.
- PR에는 변경 요약, 실행/검증 방법, 연결 이슈, UI 변경 시 스크린샷을 포함하세요. 마이그레이션이나 `.env` 변경 사항은 반드시 명시합니다.

## 설정 및 보안 정보
- `.env.example`을 복사해 `.env`를 만들고, 비밀키는 Git에 커밋하지 않습니다(`.env`는 ignore됨).
- 핵심 설정 예시: `UPSTAGE_API_KEY`, `FRONTEND_ORIGIN`, `VITE_API_BASE`.
