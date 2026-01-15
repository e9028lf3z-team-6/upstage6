# Backend Overview

## 역할 요약
- FastAPI 기반 API 서버로 문서 업로드/파싱, 멀티 에이전트 분석, 평가 결과 저장을 담당합니다.
- Upstage LLM을 사용한 LangGraph 파이프라인과 로컬 휴리스틱 fallback을 모두 제공합니다.

## 디렉터리 구조
- `backend/main.py`: 앱 생성, 미들웨어, 라우팅, 헬스체크.
- `backend/app/webapi/`: 문서/분석/평가/인증 API.
- `backend/app/graph/`: LangGraph 파이프라인 정의 및 노드.
- `backend/app/agents/`: 분석 에이전트 및 QA evaluator.
- `backend/app/services/`: 분석 오케스트레이션, 파서, 평가 리포트.
- `backend/app/core/`: 설정, DB, 인증, 로깅.
- `backend/migrations/`: SQLite 마이그레이션 스크립트.
- `backend/scripts/`: 로컬 평가 유틸리티.

## 실행/개발
- 가상환경: `cd backend && python -m venv .venv && pip install -e .`
- 서버 실행: `cd backend && uvicorn main:app --reload --port 8000`
- 마이그레이션: `python backend/migrations/apply_sqlite_migrations.py`

## 환경 변수/설정
- `UPSTAGE_API_KEY`: Upstage LLM/문서 파서 사용 여부 결정.
- `FRONTEND_ORIGIN`: CORS 및 OAuth 리다이렉트에 사용.
- `SECRET_KEY`: 세션/JWT 서명 키(운영에서는 변경 권장).
- `LANGSMITH_*`: 관측(트레이싱/피드백) 사용 시 설정.
- 기능 플래그: `enable_split_map`, `enable_normalized_issues`.

## 데이터 모델 (SQLite)
- `users`: OAuth 사용자 정보.
- `documents`: 업로드 파일 메타 + 추출 텍스트.
- `analyses`: 분석 결과/요약 JSON.
- `eval_runs`: 평가 지표 및 스코어 기록.

## 핵심 플로우
- 문서 업로드: `/api/documents/upload` → `document_parser` → `documents` 저장.
- 분석 실행: `/api/analysis/run/{doc_id}` → `run_analysis_for_text` → `analyses` 저장.
- 평가 실행: `/api/eval/run` → 분석 재실행 + 점수화 → `eval_runs` 저장.
- 로그인 없이 접근 시 `causality_only` 모드로 제한 분석 수행.

## LangGraph 파이프라인
- 순서: `reader_persona` → `split` → `summary` → `persona_feedback` → (tone/logic/trauma/hate/genre/spelling/tension) → `aggregate` → `rewrite` → `report` → `qa_scores`.
- `summary_node`가 `global_summary`를 생성하며, 이후 노드에서 참조 가능.
- `aggregate` 결과는 `decision`(rewrite/report)로 분기합니다.

## 분석 결과 스키마 참고
- 공통 필드: `tone`, `logic`, `trauma`, `hate_bias`, `genre_cliche`, `spelling`, `tension_curve`, `aggregate`, `final_report`.
- `enable_normalized_issues`: `normalized_issues`, `highlights` 추가.
- `enable_split_map`: `split_sentences`, `split_map` 추가.

## 파서/LLM 연동
- 문서 파서: Upstage Document Parse 우선, 실패 시 로컬 파서 사용.
- `.hwp`는 `olefile` 필요(미설치 시 에러 문자열 반환).
- LLM 호출 로깅은 길이/성공 여부만 기록하도록 유지.

## 인증/보안
- Google OAuth: `/api/auth/login` → `/api/auth/callback` → JWT 발급.
- JWT는 `Authorization: Bearer <token>`로 전달.
- `get_current_user`는 토큰이 없으면 `None` 반환.

## 개발/디버그 API
- `/api/tools/run`: 파이프라인 간소 실행.
- `/api/dev/metric/run`: 개발용 평가/집계 정보 제공.

## 주의사항
- `split_agent`에서 임베딩 호출이 제거되어 있음(재도입 시 분할/길이 제한 필요).
- 프런트의 `persona_count`, `creative_focus`는 현재 API에서 사용되지 않습니다.
