# 🎓 CEFR Academic Grammar & Discourse System
**Career English Institute — Digital Credentialing & Multimodal AI Learning Platform**

Plataforma educativa y administrativa desarrollada en **Python** y **Streamlit**, diseñada para la generación automatizada de contenidos académicos calibrados al Marco Común Europeo de Referencia para las Lenguas (**CEFR A1–C2**) y niveles educativos (desde Preescolar hasta Doctorado), evaluación interactiva y emisión de certificados digitales verificables.

---

## ✨ Características Principales

* **🧠 Generación Académica Multimodal:** Creación de lecturas, historias y ejercicios en inglés (formato APA 7.ª edición) calibrados por nivel CEFR y grado académico, acompañados de contexto visual y síntesis de voz.
* **📝 Evaluaciones Interactivas:** Generación dinámica de cuestionarios de opción múltiple vinculados al folio de cada lección con calificación automática.
* **🎙️ Práctica Oral y Audiovisual:** Grabación de pronunciación en audio y video directamente desde el navegador con respaldo vinculado al folio del estudiante.
* **🏅 Certificación Oficial con Verificación QR:** Emisión de diplomas institucionales en formato PDF con código QR de validación pública instantánea.
* **🔐 Control de Acceso Basado en Roles (RBAC):** Matriz de permisos configurable en tiempo real para gestionar estudiantes, docentes y personal administrativo.

---

## 🛠️ Stack Tecnológico

* **Interfaz y Servidor:** Streamlit
* **Inteligencia Artificial:** Google GenAI SDK (`google-genai`)
* **Persistencia de Datos:** Google Sheets API (`gspread` y `pandas`)
* **Procesamiento Documental y Multimedia:** `fpdf2`, `qrcode`, `Pillow`, `gTTS`

---

## ⚙️ Configuración de Entorno (Streamlit Secrets)

Para desplegar la aplicación en **Streamlit Community Cloud**, configura las variables correspondientes en el panel **App Settings > Secrets**:

```toml
APP_BASE_URL = "https://streamlit.app"
INSTITUTE_ADDRESS = "Dirección oficial de la institución"
GEMINI_API_KEY = "TU_API_KEY"
HMAC_SECRET_KEY = "TU_LLAVE_DE_FIRMA"
spreadsheet_key = "ID_DE_HOJA_DE_CALCULO"

[gcp_service_account]
# Credenciales JSON de la cuenta de servicio convertidas a formato TOML
```

### Ejecución Local

```bash
git clone https://github.com
cd tu-repositorio
pip install -r requirements.txt
streamlit run app.py
```

---

## 🏛️ Autoría y Derechos

* **Autor / Desarrollador:** Jacob Zumaya Prianti
* **Institución:** Career English Institute (2026)
* **Ubicación:** Agua Prieta, Sonora, México.
* **Licencia:** Todos los derechos reservados. Uso exclusivo institucional.
