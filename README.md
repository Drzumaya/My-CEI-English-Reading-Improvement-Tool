# 🎓 CEI ENGLISH LEARNING PLATFORM — Global Pedagogical & SaaS Suite (v3.5)

**Institución Titular:** Career English Institute (Sede Matriz: Agua Prieta, Sonora, México)  
**Autor y Arquitecto Líder:** Jacob Zumaya Prianti  
**Estándar Académico:** Marco Común Europeo de Referencia (CEFR A1–C2) & APA 7th Edition  
**Plataforma en Vivo:** [https://streamlit.app](https://streamlit.app)  
**Instalador Oficial PWA (1 Clic):** [https://github.io](https://github.io)

---

## 🚀 Visión General del Sistema

**CEI English Learning Platform (v3.5 Enterprise Modular)** es una plataforma educativa inteligente y suite institucional SaaS Multi-Tenant diseñada para la enseñanza, evaluación multimodal y certificación verificable del idioma inglés.

El sistema integra **Inteligencia Artificial Generativa (Google Gemini)** con un **ERP Académico y Financiero Multi-Sede**, permitiendo a cada estudiante transformar sus propias ideas o borradores iniciales en lecciones académicas estilizadas bajo el estándar **APA 7th Edition**, calibradas a su nivel **CEFR (A1–C2)**, grado académico y contexto profesional/geográfico.

---

## 🏗️ Arquitectura Modular del Repositorio

```text
My-CEI-English-Reading-Improvement-Tool/
│
├── ceigrammarly.py                  # Orquestador principal de interfaz (Streamlit SPA)
├── requirements.txt                 # Dependencias Python de producción
├── README.md                        # Documentación principal del repositorio
├── README_ceigrammarly.md           # Documentación técnica extendida
│
├── index.html                       # Wrapper PWA nativo en GitHub Pages (instalación 1-clic)
├── manifest.json                    # Manifiesto PWA con escudo oficial CEI
├── sw.js                            # Service Worker para instalación móvil y standalone
│
├── .streamlit/
│   └── config.toml                  # Configuración visual institucional y activos estáticos
│
├── .github/
│   └── workflows/
│       └── ci.yml                   # Pipeline CI/CD automatizado (py_compile + pytest)
│
├── core/                            # Núcleo de infraestructura e IA
│   ├── database.py                  # Conexión Supabase PostgreSQL, RBAC y permisos delegados
│   └── ai_engine.py                 # Motor Google Gemini y estilización APA 7 fiel al alumno
│
├── modules/                         # Módulos de negocio y dominio institucional
│   ├── franchises.py                # Torre de Control Multi-Sede (campus_id), divisas e IVA
│   ├── pedagogy.py                  # Normalización CEFR, categorías Bronce/Plata/Oro y rachas
│   └── finance.py                   # Cobranza de 9 bloques (28 días), cálculo de IVA y mora
│
├── static/                          # Activos gráficos y PWA internos
│   ├── LOGO CEI APP.png             # Escudo oficial de Career English Institute
│   ├── manifest.json                # Manifiesto PWA interno
│   └── sw.js                        # Service Worker interno
│
└── tests/                           # Suite de pruebas unitarias automatizadas
    └── test_core.py                 # Pruebas pytest para infraestructura y lógica de negocio
```

---

## ✨ Módulos y Capacidades Clave

### 1. Motor Pedagógico IA & Estilización APA 7 (`core/ai_engine.py` & `modules/pedagogy.py`)
* **Co-creación Fiel al Borrador del Estudiante:** Preserva la idea e intención comunicativa original del alumno (sin penalizar errores iniciales) y la transforma en un texto modelo **APA 7th Edition** calibrado al nivel CEFR (`A1`–`C2`).
* **Contextualización por Perfil de Inscripción:** Adapta vocabulario, escenarios y bibliografía al grado académico, ubicación y perfil profesional del usuario.
* **Evaluación Integral de 4 Habilidades:**
  * 📖 **Reading Comprehension** (30%)
  * 🎧 **Listening & Audio Synthesis** (`gTTS`) (25%)
  * 🎙️ **Speaking & Pronunciation Diagnostics** (25%)
  * ✍️ **Academic Summary & APA 7 References** (20%)
* **Retención y Gamificación:** Rachas semanales consecutivas, categorías automáticas (**🥉 Bronce, 🥈 Plata, 🥇 Oro**) y seguimiento motivacional por **WhatsApp**.

### 2. Persistencia, Seguridad RBAC y Certificación Digital (`core/database.py`)
* **Historial por Folio Único (`lessons_folios`):** Trazabilidad permanente en PostgreSQL vinculada al usuario y matrícula, con buscador y auditoría administrativa en tiempo real (`📚 Ver Lecciones Creadas`).
* **Control de Acceso Granular (RBAC):** Perfiles diferenciados para *Propietario (Owner)*, *Administradores*, *Docentes*, *Socios Afiliados* y *Estudiantes*, con delegación individual de permisos.
* **Constancias con Sello Criptográfico:** Emisión de diplomas PDF firmados con **HMAC-SHA256** y **Código QR** de verificación pública instantánea.

### 3. Torre de Control Multi-Sede & Finanzas (`modules/franchises.py` & `modules/finance.py`)
* **Escalamiento Multi-Tenant (`campus_id`):** Administración centralizada desde la Sede Matriz (`CEI-AP-01`) hacia planteles o escuelas asociadas con moneda, tasa de IVA, director y QR independientes.
* **Gestión de Colegiaturas (9 Bloques):** Control de periodos de 28 días, desglose fiscal de IVA, detección automática de mora y estados financieros en tiempo real.

### 4. Distribución Móvil PWA & QR Institucional
* **App Instalable Multiplataforma:** Instalación directa con el escudo oficial de **CEI** en **iOS**, **Android** y **macOS (Dock)** mediante wrapper PWA dedicado.
* **QR Ocultable y Expansible en Cabecera:** Controlado por permisos desde el encabezado institucional con proyección a pantalla completa.

---

## ⚙️ Variables de Entorno (`Streamlit Secrets`)

```toml
GEMINI_API_KEY = "tu_api_key_de_google_gemini"
PG_HOST = "://supabase.com"
PG_PORT = "6543"
PG_DBNAME = "postgres"
PG_USER = "postgres.tu_proyecto"
PG_PASSWORD = "tu_password_supabase"
OWNER_MASTER_USER = "usuario_propietario"
OWNER_MASTER_KEY = "clave_maestra_segura"
PUBLIC_APP_URL = "https://streamlit.app"
APP_INSTALL_QR_URL = "https://github.io"
```

---

## 📄 Propiedad Intelectual

© 2026 **Career English Institute (CEI)** — Todos los derechos reservados.  
Arquitectura de software, diseño pedagógico y algoritmos propietarios desarrollados por **Jacob Zumaya Prianti**.
