# PAIMANA — Frontend Web Client

**Smart India Hackathon 2026 · Problem Statement SIH26103**<br/>
*Predictive Infrastructure Risk Intelligence Platform — Ministry of Statistics and Programme Implementation (MoSPI)*

---

## 1. Frontend Purpose

The PAIMANA web client is a specialized, responsive surveillance application for central infrastructure project monitoring. It transitions capital project oversight from retrospective accounting to prospective, early-warning decision support.

The application serves the five authoritative surveillance screens:
1. **Portfolio Overview Dashboard** (`/dashboard`): Macro portfolio KPIs, attention distribution histogram, supervisory action breakdown.
2. **Risk Ranking Leaderboard** (`/risk-ranking`): Standard competition ranking table (#1 to #419) with search and multi-field filters.
3. **Project Detail Profile** (`/projects/:canonicalProjectKey`): Multi-hazard risk cards ($P_c, P_s$, compound exposure) and baseline physical-financial outlay metrics.
4. **Explainable Risk Drivers** (`/projects/:canonicalProjectKey/drivers`): Top 3 local marginal reference perturbation drivers ($\Delta$) with observed MoSPI source facts.
5. **Intervention Action Panel** (`/projects/:canonicalProjectKey/interventions`): Standardized 7-protocol action checklists, evidence triggers, and mandatory MoSPI governance notices.

---

## 2. Locked Technology Stack

* **Build Tooling & Server**: Vite 5.x (ESM, Fast HMR, optimized production chunks)
* **Framework**: React 18 (`react`, `react-dom`)
* **Language**: TypeScript 5.x in Strict Mode (`strict: true`, strict null checks)
* **Styling**: Tailwind CSS 3.x (custom enterprise navy palette & locked attention tier tokens)
* **Routing**: React Router v6 (`react-router-dom`)
* **State & Data Fetching**: TanStack Query v5 (`@tanstack/react-query`) + Axios
* **Data Visualization**: Recharts (composable SVG charts for distributions and gauges)
* **Icons**: Lucide React
* **UI Primitives**: Radix UI (`@radix-ui/react-slot`) + custom accessible components

*(Note: Next.js is strictly prohibited by project architecture rules).*

---

## 3. Installation & Local Development

### 3.1 Prerequisites
* Node.js 18+ (verified with Node.js v24.x)
* npm 9+ (verified with npm 11.x)

### 3.2 Install Dependencies
Navigate to the `frontend/` directory and install packages:
```bash
cd frontend
npm install
```

### 3.3 Start Local Development Server
```bash
npm run dev
```
The application will launch at `http://localhost:5173`.

### 3.4 Type-Checking
Validate strict TypeScript types:
```bash
npm run lint
```

### 3.5 Production Build
Compile and bundle optimized static assets:
```bash
npm run build
```
Build output is generated in `frontend/dist/`.

To preview the production build locally:
```bash
npm run preview
```

---

## 4. Directory Structure

```text
frontend/
├── index.html                    # Single-page application root HTML
├── package.json                  # Locked frontend dependencies and scripts
├── postcss.config.js             # PostCSS plugins (Tailwind, Autoprefixer)
├── tailwind.config.js            # Enterprise theme, colors, and tier tokens
├── tsconfig.json                 # Strict TypeScript configuration
├── vite.config.js                # Vite build config & '@' path alias
├── README.md                     # This documentation
└── src/
    ├── assets/                   # Static icons and branding media
    ├── components/               # Reusable UI primitives
    │   ├── common/
    │   │   └── PageHeader.tsx    # Standard page title, breadcrumbs, actions
    │   └── ui/
    │       ├── AdvisoryBanner.tsx# Governance & non-causal warning banners
    │       ├── Badge.tsx         # Generic styled badge
    │       ├── Button.tsx        # Accessible button with loading/icon states
    │       ├── Card.tsx          # Card container primitives
    │       ├── CoverageBadge.tsx # FULL vs PARTIAL coverage badge
    │       ├── EmptyState.tsx    # Fallback view for zero results
    │       ├── Input.tsx         # Form input with validation states
    │       ├── LoadingState.tsx  # Loading spinner and skeleton state
    │       ├── RiskIndicator.tsx # Probability gauge with unobserved handling
    │       └── TierBadge.tsx     # Locked Tier 1..Tier 4 quantile badge
    ├── hooks/
    │   └── useProjects.ts        # TanStack Query custom hooks
    ├── layouts/
    │   ├── AppShell.tsx          # Main MoSPI government shell & sidebar
    │   └── AuthLayout.tsx        # Authentication shell
    ├── lib/
    │   └── utils.ts              # cn() class merger, formatters (Crores, Pct)
    ├── mock/
    │   ├── mockData.ts           # Realistic holdout seed records (N=437 aligned)
    │   └── mockService.ts        # Async mock service matching REST contracts
    ├── pages/
    │   ├── auth/
    │   │   ├── LoginPage.tsx     # Official surveillance login screen
    │   │   └── SignupPage.tsx    # Access request registration screen
    │   ├── dashboard/
    │   │   └── DashboardPage.tsx # Screen 1: Portfolio Overview Dashboard
    │   ├── project/
    │   │   ├── ProjectDetailPage.tsx       # Screen 3: Project Detail Profile
    │   │   ├── ProjectDriversPage.tsx      # Screen 4: Explainable Risk Drivers
    │   │   └── ProjectInterventionsPage.tsx# Screen 5: Intervention Action Panel
    │   ├── ranking/
    │   │   └── RiskRankingPage.tsx         # Screen 2: Risk Ranking Leaderboard
    │   └── NotFoundPage.tsx      # 404 handler
    ├── routes/
    │   └── AppRoutes.tsx         # React Router route definitions
    ├── services/
    │   ├── apiClient.ts          # Configured Axios instance with interceptors
    │   └── projectService.ts     # Facade service switching mock / live API
    ├── types/
    │   ├── api.ts                # Paginated request/response & error schemas
    │   └── models.ts             # Domain models, enums, controlled vocabularies
    ├── App.tsx                   # QueryClientProvider & router setup
    ├── index.css                 # Tailwind base styles and custom scrollbars
    └── main.tsx                  # React 18 DOM mount
```

---

## 5. Mock Data Architecture & API Integration

### 5.1 Dual-Mode Service Facade
The frontend features a clean separation between UI components and data providers via `src/services/projectService.ts`:

```text
[UI View Component]
       │
       ▼
[TanStack Query Hook (useProjects.ts)]
       │
       ▼
[projectService.ts]
       │
       ├─► (Default: VITE_USE_MOCK=true)  ──► mockService.ts  ──► mockData.ts
       │
       └─► (Future:  VITE_USE_MOCK=false) ──► apiClient.ts    ──► FastAPI /api/v1
```

### 5.2 Transitioning to Live FastAPI Backend
1. When the backend service is deployed, set in `.env`:
   ```bash
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   VITE_USE_MOCK=false
   ```
2. No component or hook code needs to be modified. `projectService.ts` automatically redirects all requests to `apiClient.ts` querying the live `/api/v1` routes specified in `docs/api_contract.md`.

---

## 6. Domain Constraints & Semantic Rules

All frontend developers and components MUST strictly respect these non-negotiable rules:
1. **Tier Naming**: Risk tiers are strictly labeled `"Tier 1"`, `"Tier 2"`, `"Tier 3"`, `"Tier 4"`. They represent relative empirical quantiles and must **NEVER** be renamed "Critical / High / Medium / Low Risk".
2. **Partial Coverage Handling**: For the 132 projects lacking schedule baseline milestone dates, $P_s$ and compound exposure are strictly `null`. Components must **never render `0.0%` or "Low Risk"**; they must render an amber `PARTIAL COVERAGE` badge and "Unobserved".
3. **Compound Exposure**: $\min(P_c, P_s)$ is a heuristic dual-hazard sentinel, **NOT a joint probability**. It must always include the required footnote.
4. **Non-Causal Language**: Explanations must be presented as statistical associations, never as causal claims of fault, negligence, or contractor culpability.
5. **Governance Notice**: Intervention panels must display the mandatory MoSPI disclaimer prohibiting automated administrative sanctions.
