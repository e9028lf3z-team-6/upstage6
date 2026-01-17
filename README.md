# 🖋️ TEAM CONTEXTOR

> **원고 분석을 위한 지능형 멀티 에이전트 시스템**  
> 업로드한 원고(PDF/DOCX/TXT/MD)를 분석하여 가독성, 톤, 인과관계, 부적절한 표현 등을 체크하고 종합적인 전문가 리포트를 제공합니다.

---

## 🚀 Key Features

- **다양한 문서 지원**: PDF, DOCX, HWP, HWPX, TXT, MD 파일의 텍스트를 정확하게 추출합니다.
  - *Upstage Document Parse* 연동을 통한 고성능 파싱 지원.
  - *Robust Local Fallback*: HWP(Record Parsing), HWPX(XML), PDF/DOCX 자체 파서 내장.
- **지능형 멀티 에이전트 파이프라인**:
  - **Narrative Analyst**: 스토리의 인과관계와 긴장도 곡선을 분석합니다.
  - **Tone & Style Expert**: 문체와 가독성 수준을 평가합니다.
  - **Safety Guard**: 트라우마 유발 요소나 혐오 표현을 탐지합니다.
  - **Genre Specialist**: 장르적 클리셰와 독창성을 분석합니다.
- **Self-Evaluation System (New)**:
  - **LLM-as-a-Judge**: 각 에이전트의 분석 결과를 별도의 평가 에이전트가 교차 검증하여 신뢰도 점수(QA Score)를 산출합니다.
  - **Real-time Feedback**: 분석 즉시 각 에이전트의 성능 점수를 대시보드에서 확인할 수 있습니다.
- **Chief Editor's Report**: 분산된 에이전트의 분석 결과를 하나의 전문적인 Markdown 리포트로 합성하여 제공합니다.
- **실시간 대시보드**: React 기반의 반응형 UI로 분석 결과를 즉시 확인하고 관리할 수 있습니다.

---

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **LLM**: Upstage Solar (solar-pro2)
- **Database**: SQLite (SQLAlchemy)
- **Parsing**: Upstage Document Parse, python-docx, pypdf
- **Observability**: LangSmith (https://smith.langchain.com)

### Frontend
- **Framework**: React 18 (Vite)
- **UI/UX**: Modern CSS, Material Design Principles
- **Rendering**: react-markdown

---

## ⚙️ Getting Started

### 1. Prerequisites
- Python 3.11 이상
- Node.js 18 이상

### 2. Backend Setup
```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate

# 의존성 설치
pip install -e .

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 UPSTAGE_API_KEY를 입력하세요.

# 서버 실행
uvicorn main:app --port 8000
```

cd backend
.venv\Scripts\activate
python -m uvicorn main:app --port 8000
### 4. SQLite 마이그레이션 (필요 시)
기존 `backend/data/team.db`에 컬럼을 추가하려면 아래 스크립트를 실행하세요.
이미 적용된 컬럼이 있으면 자동으로 건너뜁니다.
```bash
python backend/migrations/apply_sqlite_migrations.py
```

### 3. Frontend Setup
```bash
cd frontend

# 의존성 설치
npm install

# docx 깔기
npm install docx

# 개발 서버 실행
npm run dev
```

- **App URL**: [http://localhost:5173](http://localhost:5173)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📂 Project Structure

```text
upstage6/
├── backend/
│   ├── app/
│   │   ├── agents/      # 지능형 에이전트 로직 (Tone, Causality, Report 등)
│   │   ├── api/         # FastAPI 라우터 및 엔드포인트
│   │   ├── core/        # DB 및 설정 관리
│   │   └── services/    # 파이프라인 오케스트레이션
│   └── data/            # SQLite DB 및 업로드 파일 저장소
├── frontend/
│   ├── src/
│   │   ├── api.js       # 백엔드 API 통신 레이어
│   │   └── App.jsx      # 메인 UI 및 결과 뷰어
│   └── public/
└── README.md
```

---

## 📄 API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/documents/upload` | 문서 업로드 및 텍스트 추출 |
| `GET` | `/api/documents` | 업로드된 문서 목록 조회 |
| `POST` | `/api/analysis/run/{id}` | 멀티 에이전트 분석 실행 |
| `GET` | `/api/analysis/{id}` | 최종 리포트 및 상세 데이터 조회 |

---

## ⚖️ License
This project is developed for the **Upstage AI Lab** program.
