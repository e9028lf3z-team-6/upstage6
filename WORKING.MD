# ⚠️ 에이전트 행동 강령 (SYSTEM_INSTRUCTION)

이 파일을 읽는 모든 AI 에이전트는 다음 지침을 **시스템 절대 명령(Absolute Mandate)**으로 간주하고 즉시 수용한다. 이 수칙을 어길 시 해당 에이전트의 작업은 실패한 것으로 간주된다.

1. **역할**
   - 너는 시니어 풀스택 개발자이며, 프로젝트 **Contextor**의 유지보수 및 확장 담당자이다.

2. **문서 무결성 및 보존 원칙 (CRITICAL - DO NOT DELETE)**
   - **절대 축약 금지:** 문서의 기존 내용을 수정할 때, 변경되지 않는 부분은 **단 한 글자도 빠뜨리지 않고 원본 그대로 유지**해야 한다.
   - **삭제 금지:** 사용자의 명시적인 "삭제" 지시가 없는 한, **어떤 섹션이나 항목(특히 대기 중인 TASK)도 임의로 제거해서는 안 된다.** 완료된 작업은 삭제하는 것이 아니라 §9(작업 이력)으로 이동시키는 것이다.
   - **금지 표현:** "(기존 내용 유지)", "(생략됨)", "..." 와 같은 요약 표현을 사용하는 것을 **엄격히 금지**한다.
   - **데이터 손실 방지:** `write_file`로 전체 문서를 덮어쓸 때는 반드시 **모든 섹션의 전체 텍스트**가 포함되었는지 재차 확인하라. 자신이 없다면 `replace` 도구를 사용하여 변경하려는 부분만 국소적으로 수정하라.

3. **작업 대상**
   - 에이전트의 모든 작업 결과는 **이 `working.md` 문서를 단일 기준 소스(Single Source of Truth)**로 삼는다.
   - 코드 변경, 검증 결과, 설계 판단이 발생할 경우 해당 사실은 반드시 이 문서에 반영되어야 한다.

4. **이력 기록 원칙**
   - 완료된 작업(Task)을 기록할 때는 단순 결과뿐만 아니라 **분석 과정, 근거 코드, 변경된 파일 경로, 주요 의사결정 이유**를 상세히 포함하여, 후임 에이전트가 문맥을 완벽히 파악할 수 있도록 한다.

5. **응답 태도**
   - 불필요한 서론은 생략한다.
   - 코드 수정 시, 변경된 코드와 파일 경로를 명확히 제시한다.

---

# 프로젝트 작업 명세서 (Project Working Documentation)

이 문서는 프로젝트 **Contextor**의 아키텍처, 프레임워크 상세 구성, 구현 로직, 그리고 데이터 흐름을 심층적으로 기술합니다. 성능이 낮은 AI 에이전트나 새로운 개발자가 프로젝트에 투입되었을 때 즉시 이해하고 작업을 시작할 수 있도록, 최대한 구체적이고 명확한 문장으로 작성되었습니다.

## 1. 프레임워크 및 라이브러리 상세 (Framework & Libraries)

### Frontend (Client-Side)
사용자 인터페이스와 상호작용을 담당합니다.

- **Core Framework: React v18.3.1**
  - **선정 이유:** 컴포넌트 기반 아키텍처를 통해 UI 재사용성을 극대화하고, Virtual DOM을 이용한 효율적인 렌더링을 위해 사용되었습니다. `useEffect`, `useState` 등의 Hooks 패턴을 적극 활용하여 함수형 프로그래밍 스타일을 따릅니다.
  - **실행 환경:** 브라우저 (SPA - Single Page Application)
  - **Package Manager:** `npm` (Node Package Manager)

- **Build Tool: Vite v5.4.0**
  - **역할:** 개발 서버 구동(HMR 지원) 및 프로덕션 빌드 번들링.
  - **설정 (`vite.config.js`):** `@vitejs/plugin-react` 플러그인을 사용하여 JSX/TSX 변환을 처리하며, 개발 서버 포트는 `5173`으로 설정되어 있습니다.

- **Dependencies:**
  - **`react-markdown` (v10.1.0):** 백엔드 분석 결과(Markdown 포맷)를 HTML로 렌더링하여 사용자에게 보여주는 핵심 라이브러리입니다.
  - **`docx` (v9.5.1):** 사용자가 편집한 내용을 서버를 거치지 않고 브라우저에서 즉시 `.docx` 파일로 생성하여 다운로드할 수 있게 합니다.

- **Styling: Plain CSS-in-JS**
  - 별도의 CSS 파일 없이 React 컴포넌트 내 `style={{ ... }}` 속성을 직접 사용합니다.
  - **장점:** 외부 CSS 의존성 없이 컴포넌트가 스타일을 완전히 소유하여 이식성이 높고, 프로토타이핑 속도가 빠릅니다.

### Backend (Server-Side)
API 제공 및 비즈니스 로직, AI 파이프라인 처리를 담당합니다.

- **Core Framework: FastAPI (>=0.111.0)**
  - **선정 이유:** Python의 비동기(`async`/`await`) 처리를 네이티브로 지원하여 I/O 바운드 작업(DB 조회, AI API 호출)에 최적화되어 있습니다. Pydantic을 이용한 강력한 데이터 검증 기능을 제공합니다.
  - **진입점:** `backend/main.py`의 `create_app()` 함수.
  - **ASGI Server:** `Uvicorn` (비동기 서버 게이트웨이 인터페이스 구현체) 위에서 동작합니다.
  - **Package Manager:** `uv` (Rust 기반의 고성능 Python 패키지 관리자)를 사용하여 의존성(`uv.lock`)을 관리합니다.

- **Language & Runtime: Python 3.11+**
  - 타입 힌팅(`Type Hinting`)을 적극 활용하여 코드 안정성을 확보했습니다.

- **Configuration & Environment:**
  - **`pydantic-settings`:** `.env` 파일 및 시스템 환경 변수를 Pydantic 모델로 매핑하여 타입 안전하게 관리합니다 (`app/core/settings.py`).
  - **필수 환경 변수 (.env):**
    - `UPSTAGE_API_KEY`: Upstage Solar LLM 사용 (필수).
    - `OPENAI_API_KEY`: OpenAI 모델 사용 시.
    - `DB_URL`: DB 연결 문자열 (기본: `sqlite+aiosqlite:///./data/team.db`).
    - `SECRET_KEY`: 세션 암호화 키.
    - **Observability:** `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` (LangSmith 연동).
    - **Auth:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (Google OAuth).
    - **Feature Flags:** `ENABLE_SPLIT_MAP` (문장 분리 활성화).

- **Database & ORM:**
  - **SQLAlchemy (v2.0.30) + aiosqlite:** 비동기 ORM을 사용하여 SQLite 데이터베이스와 상호작용합니다.
  - **SQLite:** 로컬 개발 환경에서의 편의성을 위해 파일 기반 DB(`app.db`)를 사용합니다.

- **AI & LLM Pipeline:**
  - **LangChain (>=1.2.3) & LangGraph (>=1.0.5):** 복잡한 에이전트 워크플로우(분석 단계별 체인 연결)를 그래프 구조로 정의하고 실행합니다.
  - **HTTP Client:** `httpx` (비동기)를 사용하여 OpenAI, Upstage 등 외부 AI 서비스 API를 호출합니다.

- **Document Parsing:**
  - **Upstage Document Parse:** `UPSTAGE_API_KEY`가 있을 경우 우선 사용.
  - **Local Fallback:** PDF(pypdf layout mode), DOCX(python-docx), HWP(olefile+zlib), HWPX(zipfile+xml) 자체 파서 내장.

- **Authentication:**
  - `authlib`, `itsdangerous`를 사용하여 세션 기반 인증 및 토큰 처리를 수행합니다. `SessionMiddleware`가 적용되어 있습니다.

---

## 2. 스타일링 방식 및 디자인 시스템 (Styling & Design System)

이 프로젝트는 외부 UI 라이브러리 없이, **React Inline Style**과 **Scoped CSS**를 혼합하여 경량화된 독자적인 디자인 시스템을 구축했습니다.

### Color System (색상 체계)
- **Theme Strategy:**
  - 기본적으로 **Dark Theme**으로 작성되며, Light Theme은 최상위 `div`에서 CSS Filter(`invert(1) hue-rotate(180deg)`)를 적용하여 수학적으로 반전시킵니다.
  - **Backgrounds:** `#0f0f12` (Main), `#141417` (Panel/Card), `#2a2a2c` (Border).
  - **Text:** `#e6e6ea` (Primary), `#cfcfd6` (Secondary), `#9aa0a6` (Muted).

- **Semantic Colors (상태 표시):**
  - **Success:** `#2e7d32` (Green) - 저장 성공, 분석 완료 등.
  - **Warning:** `#ed6c02` 6 (Orange) - 경고, 데이터 없음.
  - **Error:** `#d32f2f` (Red) - API 오류, 삭제 버튼.
  - **Info:** `#1976d2` (Blue) - 일반 알림.

- **Agent Identity Colors (`ISSUE_COLORS`):**
  각 분석 에이전트의 결과를 텍스트에 하이라이팅할 때 사용하는 고유 색상입니다.
  - `Tone` (어조): Indigo (`rgba(92, 107, 192, 0.5)`)
  - `Logic` (논리/인과): Yellow (`rgba(255, 214, 0, 0.5)`)
  - `Trauma` (트라우마): Red (`rgba(239, 83, 80, 0.5)`)
  - `Hate/Bias` (혐오): Purple (`rgba(171, 71, 188, 0.5)`)
  - `Genre/Cliche` (장르): Blue (`rgba(66, 165, 245, 0.5)`)
  - `Spelling` (맞춤법): Pink (`rgba(236, 64, 122, 0.5)`)
  - `Tension` (긴장도): Light Green (`rgba(139, 195, 74, 0.5)`)

### Typography (타이포그래피)
- **Font Family:** 시스템 기본 산세리프 폰트를 사용하며, 별도의 웹폰트를 로드하지 않습니다.
- **Monospace:** 원고 텍스트, 코드 블록, JSON 뷰어에는 고정폭 글꼴을 적용하여 가독성을 높입니다.
  - CSS Class: `.mono`
- **Size:** 기본 13~14px, 본문 15px, 헤더 16~18px.

### Custom Utility Classes (`<style>` in `App.jsx`)
`App.jsx` 내부의 `<style>` 태그에 정의된 핵심 유틸리티 클래스입니다.
- **`.scroll-hide`:** 브라우저 기본 스크롤바를 숨기고, 스크롤 기능만 유지하여 깔끔한 UI를 제공합니다 (`scrollbar-width: none`).
- **`.card`:** 패널이나 모달 등 컨테이너 역할을 하는 요소에 적용되는 기본 스타일 (배경색, 테두리 등).
- **`.btn`:** 버튼의 기본 리셋 및 레이아웃 스타일.
- **`.muted`:** 부가 설명이나 덜 중요한 텍스트의 불투명도를 낮춥니다.

### Icon Strategy (아이콘 전략)
- **No Libraries:** FontAwesome이나 Feather Icons 같은 외부 라이브러리를 사용하지 않습니다.
- **Inline SVG:** 필요한 아이콘(설정, 다운로드, 닫기, 플레이 버튼 등)을 JSX 내부에 직접 `<svg>` 태그로 작성하여 렌더링 성능을 최적화하고 번들 사이즈를 줄였습니다.

### Layering System (Z-Index)
화면 요소 간의 겹침 순서를 명시적으로 관리합니다.
- **Level 1 (Default):** 일반 콘텐츠.
- **Level 50:** 드롭다운 메뉴 (내보내기 메뉴 등).
- **Level 60:** 범례(Legend) 팝업.
- **Level 1200:** Toast 알림 메시지 (우측 상단).
- **Level 1400:** 모달 오버레이 (문서 기록 조회 등).
- **Level 1500:** Tooltip (마우스 호버 시 최상단 표시).

### Layout & Responsiveness
- **Layout:** CSS Grid를 활용한 3단 구조 (`Left Panel` | `Center Panel` | `Right Panel`).
- **Media Queries:**
  - `< 1200px`: 오른쪽 패널 숨김 (토글 버튼으로 접근).
  - `< 768px`: 왼쪽 패널 숨김 (모바일 뷰, 전체 1단).

---

## 3. 프로젝트 구조 (Project Structure)

프로젝트는 프론트엔드(React)와 백엔드(FastAPI)가 분리된 모노레포(Monorepo) 유사 구조를 띱니다.

### Root Directory
- **.venv/**: Python 가상 환경 (서버 실행 의존성).
- **.gemini/**: AI 에이전트의 컨텍스트 메모리 및 임시 작업 공간.
- **backend/**: 서버 애플리케이션 및 AI 로직.
  - **migrations/**: DB 스키마 변경 SQL (001~006).
  - **scripts/**: 로컬 테스트 및 관리 스크립트.
- **frontend/**: 클라이언트 애플리케이션.
- **working.md**: 현재 문서를 포함한 프로젝트 작업 명세서.

### Backend Structure (`backend/app/`)
백엔드는 **Layered Architecture**와 **LangGraph 기반의 Pipeline** 구조가 혼합되어 있습니다.

#### 1. Core & Configuration
- **`main.py`**: FastAPI 앱 생성, CORS/Session 미들웨어 설정, 서버 구동 진입점.
- **`core/`**: 시스템 전반의 핵심 기능.
  - `db.py`: DB 모델 정의(`User`, `Document`, `Analysis`, `EvalRun`) 및 비동기 세션 관리.
  - `settings.py`: `.env` 로딩 및 환경 설정 관리.
  - `logging.py`: 로깅 포맷 및 핸들러 설정.
  - `auth.py`: 사용자 인증 관련 유틸리티.

#### 2. API Interface (`webapi/`)
프론트엔드와 통신하는 RESTful API 엔드포인트입니다.
- **`routes.py`**: 도메인별 라우터 통합.
- **`documents.py`**: 문서 CRUD (업로드, 조회, **수정**, 삭제).
- **`analysis.py`**: 분석 요청(`POST /run/{id}`) 및 결과 조회.
- **`auth.py`**: 로그인/로그아웃 및 사용자 정보 조회.
- **`eval.py`**: 에이전트 평가 실행 및 결과 조회.
- **`develope_route.py`**: `/api/dev/metric/run` (디버깅용 파이프라인).
- **`router.py` (Tools)**: `/api/tools/run` (프로덕션 에이전트 실행).

#### 3. AI Agents & Logic (`agents/`)
개별 분석 작업을 수행하는 순수 LLM 로직의 집합입니다.
- **`tools/`**: 각 분석 관점별 에이전트 구현체.
  - `tone_agent.py`, `logic_agent.py`, `trauma_agent.py` 등.
  - `summary_agent.py`: 텍스트 요약.
  - `render_persona.py`: 독자 페르소나 생성.
- **`evaluators/`**: 평가 및 점수 산정 로직 (`base_evaluator.py` 등).

#### 4. Workflow Pipeline (`graph/`)
LangGraph를 사용하여 에이전트들을 실행 가능한 워크플로우(그래프)로 엮습니다.
- **`graph.py`**: 전체 그래프 구조 정의.
  - **Entry:** `reader_persona` -> `split` -> `summary` -> `persona_feedback`
  - **Parallel Evaluators:** `tone`, `logic`, `trauma`, `hate_bias`, `genre_cliche`, `spelling`, `tension_curve`
  - **Aggregation:** `aggregate` -> `rewrite` (conditional) or `report` -> `qa_scores` -> `END`
- **`state.py`**: 그래프 내에서 공유되는 상태 데이터 모델(`AgentState`) 정의.
- **`nodes/`**: 그래프의 각 노드 실행 함수 (`tone_node.py` 등).

#### 5. Business Services (`services/`)
API와 AI 로직 사이의 비즈니스 로직 및 유틸리티 서비스입니다.
- **`document_parser.py`**: 업로드된 파일(.pdf, .docx)에서 텍스트와 메타데이터 추출.
- **`analysis_runner.py`**: 분석 실행 요청을 처리하고 결과를 DB에 저장하는 오케스트레이터.
- **`pipeline_runner.py`**: LangGraph 실행 및 결과 처리.
- **`issue_normalizer.py`**: 다양한 에이전트가 내놓은 이슈 포맷을 프론트엔드용으로 정규화.
- **`split_map.py`**: 텍스트 문장 분리 및 인덱싱 매핑 (하이라이팅 기능 지원).

### Frontend Structure (`frontend/src/`)
React 애플리케이션의 소스 코드입니다. 복잡도를 낮추기 위해 **Single File Component** 패턴을 일부 차용하여 핵심 로직을 집중시켰습니다.

- **`main.jsx`**: React DOM 렌더링 진입점, 글로벌 스타일(`index.css` 등) 로드.
- **`App.jsx`**: **[핵심]** 애플리케이션의 메인 컨트롤러.
  - **State:** 문서 목록, 선택된 문서, 분석 결과, 편집 모드 상태 등을 관리.
  - **Components:** `HighlightedText`(결과 시각화), `Tooltip`(상세 보기), `Badge` 등 내부 컴포넌트 포함.
  - **Logic:** 파일 업로드 핸들러, 편집/저장 로직, 분석 요청 트리거(`runAnalysis` w/ `personaCount`, `creativeFocus` option).
- **`api.js`**: 백엔드 API 호출을 위한 Fetch Wrapper 함수 모음.
  - `updateDocument`: 문서 수정 API (`PATCH`).
  - `runAnalysis`: 분석 실행 API (`POST`).
  - `listDocuments`, `getDocument`: 문서 조회 API.

### Data Directory (`backend/data/`)
- **`uploads/`**: 사용자가 업로드한 원본 파일이 저장되는 로컬 디렉토리.
- **`team.db`**: SQLite 데이터베이스 파일.

---

## 4. 데이터 관리 및 흐름 (Data Management & Flow)

프로젝트의 모든 영구 데이터는 `backend/data/team.db` (SQLite)에서 통합 관리됩니다.

### 4.1. Database Schema & Table Roles
시스템 데이터는 성격에 따라 **Blueprint(설계도)**와 **Output(결과물)**으로 이원화됩니다.

- **Document (Blueprint):** 분석의 대상과 환경 설정을 정의합니다.
  - `id`, `user_id`, `title`, `filename`.
  - `extracted_text`: 분석할 원문 텍스트 (직접 입력 .txt 포함).
  - `meta_json`: 파일 소스 정보 및 **문서별 상세 설정(Target Audience, Genre, AI Model 등)**을 포함하는 JSON 필드.
  - `stored_path`: 서버 내 물리 파일 경로.

- **Analysis (Output):** 설계도를 바탕으로 도출된 분석 결과 기록입니다. (1:N 관계)
  - `id`, `document_id`, `status`, `decision`.
  - `result_json`: 에이전트별 분석 결과, 하이라이팅 데이터, **QA Scores(자체 평가 점수)** 포함.
  - `issue_counts_json`: 이슈 통계 요약.

- **User (Extension):** 향후 계정 기반 확장을 위한 사용자 정보입니다.
  - 현재는 로그인 여부에 따른 분석 모드 분기(`full` vs `causality`)에만 사용됩니다.

- **EvalRun (Developer Debug):** AI 에이전트 성능 평가 기록입니다.
  - 프론트엔드와 연결되지 않은 **개발자 전용 로그 저장소** 성격이 강합니다.
  - **LangSmith 연동 시:** 클라우드 대시보드(LangSmith)가 이 역할을 대체하며, `EvalRun`은 로컬 백업용으로만 기능합니다.

### 4.2. Analysis Execution Flow (Sync Wait)
분석 요청은 비동기 함수로 정의되어 있지만, 클라이언트 입장에서는 동기적으로 처리됩니다.

1.  **Request:** 프론트엔드가 `POST /api/analysis/run/{docId}` 호출.
2.  **Processing:**
    - **Mode Check:** 로그인 유저는 `full`, 비로그인은 `causality_only`.
    - **LangGraph Flow:** 문장 분리 -> 요약 -> 평가 에이전트 병렬 실행 -> 리포트 합성 -> QA Scoring.
3.  **Persist & Response:** 결과를 `Analysis` 테이블에 저장하고 200 OK 응답.

### 4.3. Frontend State Lifecycle (React)
- **Single Source of Truth:** `activeDocId` 변경 시 관련 문서와 분석 목록을 비동기 로드.
- **Edit Mode:** `isEditing` 플래그를 통해 뷰어와 에디터(`<textarea>`)를 배타적으로 전환.

### 4.4. 문서별 설정 관리 구조 (Document Settings System)
문서별 설정은 `Document.meta_json` 필드 내 `settings` 키를 사용하여 관리합니다.

- **JSON 구조 설계:**
  ```json
  {
    "source": "upstage_document_parse",
    "file_name": "sample.pdf",
    "settings": {
      "target_audience": "20대 직장인",
      "genre": "자기계발",
      "selected_agents": ["tone", "logic", "cliche"]
    }
  }
  ```
- **병합 로직:** `PATCH /documents/{id}` API 호출 시, 백엔드는 기존 `meta_json`을 읽어 `settings` 객체만 병합(Merge)하고 파일 정보(`source` 등)는 보존합니다. 이를 통해 스키마 변경 없이 유연한 설정 확장이 가능합니다.

---

## 5. 핵심 컴포넌트 코드 분석 (Key Component Code Analysis)

프론트엔드의 로직은 대부분 `App.jsx`에 집중되어 있으며, 그 중에서도 시각화의 핵심인 `HighlightedText` 컴포넌트가 가장 복잡한 로직을 가집니다.

### 1. `HighlightedText` Component
분석된 이슈를 텍스트 위에 시각적으로 덧입히는(Highlighting) 핵심 뷰어입니다.

- **Rendering Algorithm (Segment Mapping):**
  - 단순한 `String.replace` 방식을 사용하지 않습니다. 원본 텍스트를 훼손하지 않기 위해 **인덱스 기반의 세그먼트(Segment) 분할 방식**을 사용합니다.
  1.  **Sentence Splitting:** 백엔드에서 제공한 `split_sentences` 배열을 순회하며 문장 단위로 렌더링 영역을 확보합니다.
  2.  **Issue Mapping:** 각 문장의 인덱스에 해당하는 이슈들(`issuesBySentence[idx]`)을 가져옵니다.
  3.  **Fragmentation:** 문장 내에서 이슈가 있는 구간(`start`~`end`)과 없는 구간을 계산하여 여러 개의 `<span>` 또는 `<mark>` 태그 조각(Fragment)으로 쪼갭니다.
  
- **Conflict Resolution:**
  - 동일한 구간에 여러 에이전트의 이슈가 겹칠 경우, `severity`(심각도)가 높은 순서대로, 혹은 에이전트 이름 알파벳순으로 정렬하여 **가장 중요한 이슈의 색상**을 배경색으로 채택합니다.
  - 마우스 호버 시에는 겹친 모든 이슈를 툴팁에 리스트 형태로 보여줍니다.

### 2. `App` Component (Main Controller)
애플리케이션의 모든 비즈니스 로직과 UI 상태를 관리하는 **Monolithic Component**입니다.

- **State Management Strategy:**
  - **Single Source of Truth:** `activeDocId`가 변경되면 `useEffect`가 트리거되어 `activeDoc`(내용)과 `analyses`(분석 목록)를 비동기로 다시 불러옵니다.
  - **Editing State:** `isEditing` 플래그 하나로 뷰어 모드와 에디터 모드를 배타적으로 전환합니다.

- **Toast Notification System:**
  - `pushToast(message, variant)` 함수를 통해 작동합니다.

- **UI Layout Control:**
  - `leftMode` ('list' | 'upload' | 'settings'): 왼쪽 패널의 콘텐츠를 조건부 렌더링으로 교체합니다.
  - `rightView` ('report' | 'json'): 오른쪽 패널에서 마크다운 리포트와 Raw JSON 데이터를 토글합니다.

---

## 6. 제약사항 및 고려사항 (Constraints & Considerations)

- **Performance:** 동기적 분석 대기로 인한 타임아웃 위험 및 SQLite 동시성(Lock) 문제.
- **UX:** 대용량 문서 렌더링 부하 및 URL 라우팅 부재.
- **Security:** CORS 정책 미비 및 파일 바이너리 검증 부재.

---

## 7. 에이전트 작업 가이드라인 (Agent Guidelines)

- **Convention:** 기존 CSS-in-JS 스타일 및 단일 파일 구조(`App.jsx`) 유지.
- **Context Awareness:** `replace` 사용 시 전후 최소 3줄 이상 맥락 포함.
- **Integrity:** `working.md` 내용의 상세 보존 및 즉시 업데이트.

---

## 8. 코드베이스 커버리지 감사 (Codebase Coverage Audit)

*(2026-01-17 업데이트)*
- LangSmith 연동(`langsmith.py`), 개발/프로덕션 API 분리, 수동 마이그레이션 방식 확인 및 문서화 완료.

---

## 9. 작업 이력 (Task History / Log)

### 2026-01-17

#### 1. 코드베이스 커버리지 감사 (Codebase Coverage Audit)
- **분석:** 현재 프로젝트의 폴더 구조와 문서 간의 불일치 여부 전수 조사.
- **결과:** `migrations`, `scripts`, `langsmith.py` 등 누락 구조 확인 및 문서 현행화 완료.

#### 2. 원고 수정을 위한 편집 기능 추가 (Document Editing Feature)
- **구현:** `App.jsx`, `api.js` 수정으로 직접 편집 UI(textarea) 구현 및 `PATCH` API 연동 완료.

#### 3. Persona 입력 실제 사용 여부 검증 (Task-1)
- **분석:** `ReaderPersona` 데이터가 평가 에이전트에게 전달되지 않고 있음을 코드 레벨에서 증명.
- **의사결정:** 페르소나(프로필)는 '기준'으로 모든 에이전트에 주입, 피드백(반응)은 '근거'로 리포트 생성기에 주입. 에이전트 역할을 '독자 대변인'으로 재정의.

#### 4. 에이전트 페르소나 주입 및 프롬프트 고도화 (Task-1 & Task-2)
- **구현:** 6개 핵심 에이전트에 `reader_context` 파라미터 추가 및 '독자 대변인' 관점의 강력한 프롬프트 엔지니어링 적용 완료.

#### 5. 문서별 설정 시스템 구축 (Task-3)
- **설계:** 별도 테이블 없이 `Document.meta_json` 필드 내 `settings` 객체로 관리하기로 결정.
- **구현:** `DocumentUpdate` 모델 수정, `meta_json` 병합 로직 및 `SettingsModal` UI 구현 완료.

#### 6. 문서 설정 UI 위치 변경 및 데이터 동기화 버그 수정 (Task-1)
- **구현:** 설정 버튼을 왼쪽 패널 문서 카드 내부로 이동.
- **버그 수정:**
  - 1차: `onSaveSettings` 실행 시 프론트엔드의 `docs` 목록 상태가 갱신되지 않아 설정값이 초기화되던 현상 해결. `updated` 데이터로 `docs` 배열을 매핑 업데이트하는 로직 추가.
  - **최종 수정:** `onSaveSettings` 완료 후 `getDocument`를 명시적으로 호출하여 **서버로부터 최신 `meta_json` 데이터를 다시 받아오도록 강제**함. 이를 통해 로컬/서버 상태 불일치 문제를 원천 차단함.

#### 7. 문서 제목 관리 기능 강화 (Task-2)
- **구현:** `EditableTitle` 컴포넌트(더블 클릭 수정) 도입. 문서 목록, 헤더, 모달에 적용 완료. Draft 저장 시 제목 입력 기능 추가.

#### 8. 선택적 에이전트 실행 구현 (Task-0)
- **분석:** `graph.py` 분석 결과 모든 에이전트가 무조건 실행됨을 확인. 프론트엔드 에이전트 목록과 실제 백엔드 에이전트 불일치 확인.
- **구현 (Backend):** `graph.py`에 `route_to_evaluators` 함수 추가 및 `add_conditional_edges` 적용. `meta_json`의 `selected_agents` 기반으로 실행 노드를 동적으로 결정하도록 수정.
- **구현 (Frontend):** `App.jsx`의 `PERSONA_LEGEND`를 실제 7개 에이전트로 정리하고 키 이름(`tension`->`tension_curve`) 동기화.

#### 9. UI 디자인 정렬 (Task-1)
- **구현 (Frontend):** `Draft input` 섹션의 제목 `input`과 본문 `textarea`의 너비를 `100%`로 통일하고 `box-sizing: border-box`를 적용하여 레이아웃을 정렬함. 또한 실수로 삭제되었던 `HighlightedText` 및 헬퍼 함수들을 복구함.

#### 10. 설정 모달 오버레이 클릭 닫기 (Task-2)
- **구현 (Frontend):** `SettingsModal`의 배경(`div`) 클릭 시 `onClose`를 호출하고, 내부 컨텐츠 클릭 시에는 `stopPropagation`으로 닫힘을 방지하여 UX를 개선함.

#### 11. 사용자별 데이터 격리 및 접근 제어 강화 (Task-3)
- **구현 (Backend):** `webapi/documents.py` 및 `analysis.py`의 모든 엔드포인트에 `get_current_user` 의존성을 추가하고, 쿼리에 `user_id` 필터링 및 소유권 검증 로직(`403 Forbidden`)을 적용하여 보안성을 강화함.
- **마이그레이션:** 기존 고아 문서 14개를 `migrate_orphaned_docs.py` 스크립트를 통해 현재 관리자 계정(`pw7107@gmail.com`)으로 일괄 이전 완료.

#### 12. 맞춤법 전문 API 도입 검토 (Task-4)
- **분석:**
  - `py-hanspell` (네이버 기반): 비공식 라이브러리로 서비스 지속성 및 안정성 보장 어려움.
  - `부산대 맞춤법 검사기`: 정확도는 최고이나 공식 API가 폐쇄적/유료이며 웹 래핑 방식은 느림.
  - `LLM (현행)`: 문맥 파악과 '문학적 허용' 판단에 유리하나 할루시네이션 위험 존재.
- **결론:** 현재 단계에서는 LLM 방식을 유지하되 프롬프트 엔지니어링을 통해 '명백한 오류'와 '문체'를 구분하도록 고도화하는 것이 최선임. 추후 예산 확보 시 부산대 등 상용 API 도입을 재검토.

#### 13. 로깅 시스템 포맷 개선 및 안정화 (Task-5)
- **구현:**
  - `app/core/logging.py`: 가독성 높은 `TextFormatter` (`[TIME] [LEVEL] [LOGGER] Message`) 추가 및 `httpx`, `uvicorn` 등 외부 라이브러리 로그 레벨을 `WARNING`으로 조정하여 노이즈 제거.
  - `backend/main.py`: `log_requests` 미들웨어에 `try...except` 블록을 추가하여 예외 발생 시 서버 중단을 방지하고 500 에러 로그를 남기도록 수정. 로그 메시지에 HTTP 메서드, 경로, 상태 코드, 소요 시간을 직관적으로 표시하도록 변경.

#### 14. 비로그인(익명) 사용자 지원 및 권한 로직 최적화
- **분석:** 전면적인 로그인 필수 정책으로 인해 비로그인 사용자의 기본 기능(업로드, 개연성 분석)이 차단되는 문제 및 `AttributeError: 'NoneType'` 발생 확인.
- **구현 (Backend):**
  - `auth.py`에 `get_required_user`를 추가하여 인증 필수 구간을 명확히 하였으나, 게스트 모드 지원을 위해 `get_current_user`(Optional)를 기반으로 한 조건부 권한 검사 적용.
  - `Document.user_id`가 `None`인 익명 문서는 누구나 접근 및 분석 가능하도록 수정.
  - 비로그인 분석 요청 시 분석 모드를 `causality_only`로 자동 분기 처리.
- **구현 (Frontend):**
  - 비로그인 상태에서는 서버로부터 목록을 받아올 수 없으므로, 업로드(`uploadOneFile`, `onSaveDraft`) 및 삭제(`onDeleteDoc`) 시 로컬 `docs` 상태를 직접 조작하여 UI 동기화 문제를 해결.

#### 15. 맞춤법 전문 API 도입 검토 (Task-4)
- **분석:** `py-hanspell`, 부산대 맞춤법 검사기 등을 검토했으나, 비공식 라이브러리의 불안정성 및 공식 API의 폐쇄성으로 인해 즉시 교체는 부적합함.
- **결론:** LLM 기반의 현행 방식을 유지하되, 프롬프트 엔지니어링을 통해 문학적 허용과 명백한 오류를 구분하는 성능을 고도화하는 방향으로 결정.

---

## 10. 작업 지시 (Task Instructions for Next Agent)

### 1. 해커톤 발표 준비 및 프로덕트 고도화 (Hackathon & Product Polish)

멘토링 피드백(2026-01-17)을 반영하여 발표 자료와 프로덕트를 일치시키고, 시스템의 견고함과 차별점을 부각해야 합니다.

#### 1.1. Edge Case 대응 및 테스트 자동화 (Edge Case Handling)
- **Task:** 입력 데이터와 시스템 환경의 다양한 엣지 케이스에 대한 방어 로직을 강화하고 검증합니다.
- **시나리오:**
  - **입력:** 빈 텍스트, 공백만 있는 경우, 초단문(토큰 부족), 장문(토큰 초과), 특수문자/다국어 혼합.
  - **컨텍스트:** `meta_json` 파싱 실패, 자료형 불일치(Dict vs Str), 필수 필드 누락.
  - **외부 의존성:** LLM API 타임아웃, 429 Rate Limit, JSON 파싱 실패(Output Parser Error).
- **실행:**
  - `run_evaluation_test.py`를 확장하여 위 시나리오를 시뮬레이션하는 테스트 스위트 작성.
  - `graph.py` 및 각 에이전트(`ReaderPersonaAgent` 등)에 `try-except` 블록 및 Fallback 로직 강화.

#### 1.2. 아키텍처 및 기술 차별점 정리 (Technical Differentiation)
- **Task:** "왜 우리 서비스인가?"를 기술적으로 증명할 수 있는 자료와 기능을 준비합니다.
- **포지셔닝:** "한국형 튜닙(Safety) + 문학적 튜닝(Context) + 독자 시뮬레이션(Persona)" = **웹소설 작가 전용 AI 편집자**.
- **경쟁 우위:**
  - **vs Wrtn(생성):** 우리는 '비평(Critique)'과 '심층 분석'에 특화.
  - **vs Tunib(안전):** 문학적 허용(악역의 대사 등)을 이해하는 문맥 기반 탐지.
  - **vs SpellChecker(교정):** 단순 오타가 아닌 페르소나 기반의 정성적 피드백 제공.
- **구현:**
  - 발표용 아키텍처 다이어그램 업데이트 (내부 함수 제외, 에이전트 간 데이터 흐름 강조).
  - `highlighting` 기능이 작동하는 과정을 시각적으로 보여줄 수 있는 데모 시나리오 준비.

#### 1.3. UX/UI 개선 (User Experience Polish)
- **Task:** 사용자 경험을 개선하고 발표 시연 효과를 극대화합니다.
- **개선 사항:**
  - **Loading Indicator:** 각 에이전트별 진행 상황(진행률, 현재 분석 중인 항목)을 더 구체적으로 시각화 (예: "혐오 표현 분석 중...", "페르소나 생성 완료").
  - **Highlighting:** 리포트 텍스트보다 하이라이팅 기능을 최상단에 배치하여 시각적 임팩트 강화.
  - **Persona Feedback:** 리포트 상단에 적용된 페르소나(예: "20대 직장인 김철수 님")를 명시적으로 표시.

#### 1.4. 발표 자료(PPT) 및 라이브 데모 준비 (Presentation Prep)
- **Task:** 멘토 피드백을 반영하여 논리적 흐름을 갖춘 발표 자료와 데모를 준비합니다.
- **흐름:** 문제 제시 -> 해결 방안(Contextor) -> 핵심 기술(LangGraph, Multi-Agent) -> 데모(하이라이팅, 페르소나) -> 기대 효과.
- **준비물:**
  - 팀원 역할(R&R) 페이지.
  - 아키텍처 다이어그램 (LangGraph 흐름).
  - 시연용 예제 텍스트 (엣지 케이스 포함).
  - 기대 효과 및 활용 사례(사용자 시나리오).

> **[에이전트 안내]**
> 위 내용을 바탕으로 현재 진행 중인 작업이나 다음 우선순위 작업을 선택하여 진행하십시오.
