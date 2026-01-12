# TEAM – CONTEXTOR (로컬호스트 웹)

업로드한 원고(PDF/DOCX/TXT/MD)를 **로컬에서 실행되는 웹(React) + API(FastAPI)** 로 분석 데모버전.

- 좌측: 원고/분석 기록 목록 + 삭제
- 중앙: 원고 텍스트 뷰어 (업로드 후 추출된 텍스트 표시)
- 우측: 멀티 에이전트 분석 결과(JSON) 및 요약

## 핵심 요구사항 반영

- **문서 인풋 다양화**: PDF/DOCX 업로드 → 텍스트 추출  
  - `UPSTAGE_API_KEY`가 있으면 Upstage Document Parse를 우선 시도  
  - 키가 없으면 로컬 파서(PDF: pypdf, DOCX: python-docx)로 폴백
- **멀티 에이전트 파이프라인**:
  - (1) 분리(독자 수준 분류) → 평가
  - (2) 말투 분석 → 평가
  - (3) 인과관계/긴장도/장르 클리셰 → 평가
  - (4) 부적절 표현(트라우마/혐오) → 평가
  - (5) 통합 → 최종 평가(독자 수준, 메트릭)

> 참고: `UPSTAGE_API_KEY`가 없으면 외부 LLM 호출 없이 **로컬 휴리스틱 모드**로 동작하여,
> 로컬호스트에서 UI/DB/흐름을 바로 시연할 수 있습니다.

## 실행 방법 (로컬)

### 1) 백엔드
```bash
cd backend
cp .env .env   # (선택) UPSTAGE_API_KEY 등 설정
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -e .
uvicorn main:app --reload --port 8000
```

### 2) 프론트엔드
```bash
cd frontend
# (선택) cp .env .env
npm install
npm run dev
```

- 브라우저: http://localhost:5173
- API: http://localhost:8000/docs

## API 요약

- `POST /api/documents/upload` : 문서 업로드
- `GET  /api/documents` : 문서 목록
- `GET  /api/documents/{id}` : 문서 상세(추출 텍스트 포함)
- `POST /api/analysis/run/{doc_id}` : 분석 실행(결과는 DB 저장)
- `GET  /api/analysis/{analysis_id}` : 분석 상세(JSON)

## 저장소(DB)

- SQLite: `backend/data/team.db`
- 업로드 파일: `backend/data/uploads/`

## 폴더 구조
```
TEAM/
  backend/   # FastAPI
  frontend/  # React(Vite)
  docs/      # 기획/도식/화면 참고 이미지
```
