# Repository Guidelines

## 프로젝트 구조 및 모듈 구성
- `backend/`는 FastAPI 서비스이며 진입점은 `backend/main.py`입니다.
- 백엔드 핵심 모듈은 `backend/app/`에 있습니다. `api/`, `webapi/`는 라우팅, `agents/`, `graph/`는 분석 플로우, `services/`는 오케스트레이션, `llm/`은 모델 헬퍼, `schemas/`는 Pydantic 모델, `core/`는 설정/DB를 담당합니다.
- `frontend/`는 Vite React 앱이며 `frontend/src/`에 `App.jsx`, `api.js`가 있고 정적 자산은 `frontend/public/`에 있습니다.
- SQLite 데이터는 런타임에 `backend/data/` 아래에 생성됩니다(`db_url`: `sqlite+aiosqlite:///./data/team.db`).

## 빌드, 테스트, 개발 명령
- 백엔드 세팅( `backend/` 기준): `python -m venv .venv` 후 `pip install -e .`.
- 백엔드 개발 서버: `uvicorn main:app --reload --port 8000`.
- 프런트엔드 세팅( `frontend/` 기준): `npm install`.
- 프런트엔드 개발 서버: `npm run dev`.
- 프런트엔드 프로덕션 빌드/프리뷰: `npm run build` 후 `npm run preview`.

## 코딩 스타일 및 네이밍 규칙
- Python은 4칸 들여쓰기, `backend/app/` 내 기존 패키지 경계와 타입 힌트를 유지합니다.
- JS/JSX는 2칸 들여쓰기, 컴포넌트는 PascalCase(`App`, `Badge`), 함수는 camelCase를 사용합니다.
- 강제되는 포매터/린터는 없으므로 주변 코드 스타일을 따르고 변경 범위를 최소화합니다.

## 테스트 가이드
- 현재 테스트 프레임워크/디렉터리가 없습니다.
- 테스트를 추가한다면 `tests/`(루트) 또는 `backend/tests/`를 권장하며 실행 방법을 PR에 명시합니다.

## 커밋 및 PR 가이드
- 최근 커밋은 짧은 메시지(한글 포함)와 간헐적 접두사(`fix:`)를 사용합니다.
- 메시지는 간결하고 구체적으로 작성합니다(예: `fix: improve HWP parsing`, `spelling agent 추가`).
- PR에는 목적, 핵심 변경점, 로컬 실행 방법, UI 변경 시 스크린샷을 포함합니다.

## 설정 및 보안
- 백엔드 설정: `backend/.env.example`을 `backend/.env`로 복사하고 `UPSTAGE_API_KEY`를 설정합니다.
- 프런트엔드 설정: `frontend/.env.example`의 Vite 변수는 선택 사항이며, 프런트엔드에 비밀값을 넣지 않습니다.
- 설정 값은 `backend/app/core/settings.py`에 정의되어 있습니다(`frontend_origin`, `db_url`, API 엔드포인트).
