# 릴리스 노트

## v0.1.1 (2025-02-14)

### LangGraph 기반 분석 정착
- LangGraph 파이프라인 실행 안정화(상태 병합 충돌 제거).
- `persona_feedback` 의존성 재정리(분할 결과 선행).
- LLM JSON 파싱 안전화(BaseAgent 안전 파서 적용).
- 논리 결과 키를 `logic_result`로 통일해 집계/리포트 반영.

### API/라우팅 정리
- `/api/documents` 경로 복구(목록/업로드/조회/삭제).
- `/api/analysis` 중복 정의 해소.

### 분석 결과 구조 개선
- 문서 파싱 메타 저장(`documents.meta_json`).
- 분석 요약 컬럼 저장(`decision`, `has_issues`, `issue_counts_json`).
- 분석 응답에 요약 필드 포함.
- 휴리스틱 fallback 스텁 추가로 스키마 안정화.

### 비동기 큐(안정화 단계)
- Redis + RQ 기반 큐로 전환(`/api/analysis/queue/run/{doc_id}`).
- 큐 상태/진행률 조회 API 추가(`/api/analysis/queue/status/{analysis_id}`).
- 큐 작업 메타(progress) 기록.

### 관측/평가 도구
- LangSmith 트레이싱(LLM run/Tool run) 적용.

### 데이터베이스 마이그레이션
- SQLite 마이그레이션 SQL 추가.
- 적용 스크립트 `backend/migrations/apply_sqlite_migrations.py` 제공.

### 운영 메모
- 기존 SQLite DB는 마이그레이션 스크립트 실행이 필요합니다.
- RQ 워커 실행 필요(예: `rq worker analysis`).

## v0.1.2 (2025-02-15)

### 평가 리포트 고도화
- 섹션별 해석 문구 자동 생성(LLM 기반) 및 형식 정리.
- 해석 문장 규칙 강화(숫자/단위 금지, 1문장 고정, 환각 방지).
- 변화량 해석/본문 일관성 개선.

### 품질 점수 개선
- `quality_score_v2` 고도화(밀도/불일치/총이슈/일관성/페르소나 정렬 반영).
- 철자 이슈 과다 반영 완화(가중치 적용).
- 점수 breakdown/inputs 분리로 해석 가능성 강화.
- LLM Judge 실패 시 가중치 재분배로 점수 붕괴 방지.

### LLM Judge 안정화
- JSON 파싱 강화(코드펜스/블록 추출 + 재시도 복구).
- 평가 rationale 한글 번역 추가(리포트 표시).

### 평가 데이터 기록/추세
- 평가 이력 메타/델타/에이전트 지연 저장 강화.
- 품질 점수 추세 및 일관성 지표 표시.

### 환경 설정
- 루트 `.env` 명시 로드(로컬 실행 시 환경변수 일관성 확보).
