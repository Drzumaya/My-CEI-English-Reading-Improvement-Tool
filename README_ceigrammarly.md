# 🎓 CEI ENGLISH LEARNING PLATFORM — Global Pedagogical & SaaS Suite (v3.5)

**Institución Titular:** Career English Institute (Sede Matriz: Agua Prieta, Sonora, México)  
**Autor y Arquitecto Líder:** Jacob Zumaya Prianti  
**Estándar Académico:** Marco Común Europeo de Referencia (CEFR A1–C2) & APA 7th Edition  
**App en Vivo:** [https://streamlit.app](https://streamlit.app)  
**Instalador Oficial PWA (1 Clic):** [https://github.io](https://github.io)

---

## 🚀 Descripción General

**CEI English Learning Platform (v3.5 Enterprise Modular)** es una plataforma educativa inteligente y suite institucional SaaS Multi-Tenant diseñada para el aprendizaje, evaluación y certificación del idioma inglés. 

Combina **Inteligencia Artificial Generativa Multimodal (Google Gemini)** con un **ERP Académico y Financiero Multi-Sede**, permitiendo a estudiantes transformar sus propias ideas o borradores iniciales en lecciones académicas estilizadas bajo el estándar **APA 7th Edition**, calibradas a su nivel **CEFR (A1–C2)**, grado académico y contexto profesional/geográfico.

---

## 🏗️ Arquitectura Modular del Repositorio

El sistema opera bajo una arquitectura desacoplada de clase empresarial con integración continua (**CI/CD**):

```text
My-CEI-English-Reading-Improvement-Tool/
│
├── ceigrammarly.py                  # Orquestador principal de interfaz (Streamlit SPA)
├── requirements.txt                 # Dependencias Python de producción
├── README_ceigrammarly.md           # Documentación técnica e institucional
│
├── index.html                       # Wrapper PWA nativo en GitHub Pages (instalación 1-clic)
├── manifest.json                    # Manifiesto PWA con escudo oficial CEI
├── sw.js                            # Service Worker para soporte móvil y standalone
│
├── .streamlit/
│   └── config.toml                  # Tema institucional y servicio de activos estáticos
│
├── .github/
│   └── workflows/
│       └── ci.yml                   # Quality Gate CI/CD (py_compile + pytest automatizado)
│
├── core/                            # Núcleo de infraestructura e IA
│   ├── database.py                  # Conexión Supabase PostgreSQL, RLS/RBAC y permisos delegados
│   └── ai_engine.py                 # Motor Google Gemini y estilización APA 7 fiel al borrador del alumno
│
├── modules/                         # Módulos de negocio y dominio institucional
│   ├── franchises.py                # Torre de Control Multi-Sede (campus_id), divisas e IVA por plantel
│   ├── pedagogy.py                  # Normalización CEFR, categorías Bronce/Plata/Oro, rachas y WhatsApp
│   └── finance.py                   # Cobranza de 9 bloques (28 días), cálculo exacto de IVA y mora
│
├── static/                          # Activos institucionales
│   ├── LOGO CEI APP.png             # Escudo oficial de Career English Institute
│   ├── manifest.json                # Manifiesto PWA interno
│   └── sw.js                        # Service Worker interno
│
└── tests/                           # Pruebas unitarias automatizadas
    └── test_core.py                 # Suite pytest para core y modules
```

---

## ✨ Capacidades Principales (v3.5)

### 1. Motor Pedagógico IA & Estilización APA 7 (`core/ai_engine.py` & `modules/pedagogy.py`)
* **Co-creación Fiel al Estudiante:** Respeta la idea original del borrador del alumno (incluso con errores de ortografía, gramática o transferencia del español) y la eleva al estándar **APA 7th Edition**.
* **Contextualización por Perfil de Inscripción:** Adapta vocabulario, ejemplos y referencias bibliográficas al nivel CEFR (`A1`–`C2`), grado académico, ubicación y contexto profesional.
* **Evaluación Integral de 4 Habilidades:**
  * 📖 **Reading Comprehension** (30%)
  * 🎧 **Listening & Audio Synthesis** (`gTTS`) (25%)
  * 🎙️ **Speaking & Pronunciation Diagnostics** (25%)
  * ✍️ **Academic Summary & APA 7 References** (20%)
* **Gamificación y Retención:** Rachas semanales consecutivas, categorías automáticas (**🥉 Bronce, 🥈 Plata, 🥇 Oro**) y enlaces preconfigurados de motivación por **WhatsApp**.

### 2. Gobernanza, Seguridad y Certificación Criptográfica (`core/database.py`)
* **Persistencia Relacional en Supabase PostgreSQL:** Trazabilidad permanente por **Folio único** (`lessons_folios`), vinculada al usuario y matrícula del estudiante con auditoría administrativa en tiempo real (`📚 Ver Lecciones Creadas`).
* **Control de Acceso Granular (RBAC):** Perfiles para *Propietario (Owner)*, *Administradores*, *Docentes*, *Socios Afiliados* y *Estudiantes*, con delegación individual de capacidades desde el panel administrativo.
* **Certificados Digitales Verificables:** Emisión de constancias PDF con firma **HMAC-SHA256** y **Código QR** de validación pública instantánea.

### 3. Torre de Control Multi-Sede & Finanzas (`modules/franchises.py` & `modules/finance.py`)
* **Arquitectura Multi-Tenant (`campus_id`):** Gestión centralizada desde la Sede Matriz (`CEI-AP-01`) hacia nuevas franquicias o escuelas suscritas con moneda, tasa de IVA, director y QR propios.
* **Cobranza de 9 Bloques:** Control automatizado de colegiaturas por periodos de 28 días, cálculo de IVA, detección de mora y estados financieros en tiempo real.

### 4. Ecosistema Móvil PWA & QR Institucional
* **Instalación Multiplataforma:** Instalable con escudo oficial CEI en **iOS (iPhone/iPad)**, **Android** y **macOS (Dock)** mediante wrapper PWA dedicado.
* **QR Ocultable y Expansible en Cabecera:** Interruptor `📲 QR App` controlado por permisos en el encabezado institucional con proyección a pantalla completa en un clic.

---

## ⚙️ Configuración de Variables de Entorno (`Streamlit Secrets`)

Para desplegar una instancia o franquicia en **Streamlit Community Cloud**, configura las siguientes llaves en **Settings → Secrets**:

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

## 🧪 Pruebas Automatizadas y CI/CD

Cada `push` hacia la rama principal ejecuta automáticamente `.github/workflows/ci.yml`:
1. Compilación estática (`py_compile`) de `ceigrammarly.py`, `core/*` y `modules/*`.
2. Ejecución de pruebas unitarias con `pytest -v` (`tests/test_core.py`) validando cálculos fiscales, categorías estudiantiles, rachas semanales y prompts APA 7.

---

## 📄 Licencia y Propiedad Intelectual

© 2026 **Career English Institute (CEI)** — Todos los derechos reservados.  
Arquitectura de software, diseño pedagógico y algoritmos propietarios desarrollados por **Jacob Zumaya Prianti**.
