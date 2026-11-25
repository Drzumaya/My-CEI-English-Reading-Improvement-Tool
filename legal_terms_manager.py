from zoneinfo import ZoneInfo
import psycopg
import streamlit as st

TZ_SONORA = ZoneInfo("America/Hermosillo")

DEFAULT_TERMS_BY_ROLE = {
    "docente": """### Términos, Condiciones y Código de Compliance Docente

**Career English Institute (CEI) — Agua Prieta, Sonora, México**

1. **Naturaleza Académica y Profesional:** El Docente declara contar con las credenciales académicas, Cédula Profesional y certificación del idioma inglés declaradas en su expediente, comprometiéndose a impartir sus sesiones conforme al Marco Común Europeo de Referencia (CEFR) y lineamientos pedagógicos de CEI.
2. **Cumplimiento Fiscal y Requisitos de Cobro (SAT México):** Para recibir el pago de honorarios o comisiones asignadas, el Docente se obliga a mantener actualizada su Bóveda Legal y Fiscal en *Mi Portal Docente CEI* con:
   * Constancia de Situación Fiscal (CSF) con antigüedad menor a 30 días.
   * Opinión de Cumplimiento de Obligaciones Fiscales (32-D) en sentido Positivo (menor a 30 días).
   * Carátula bancaria con CLABE interbancaria de 18 dígitos a su nombre e INE/Cédula vigente.
   * Comprobante Fiscal Digital por Internet (CFDI 4.0 en PDF y XML) emitido antes del día 25 de cada mes.
3. **Índice de Compliance y Confianza:** El Docente acepta ser evaluado periódicamente mediante el Índice Estadístico de Compliance y Confianza Institucional (0 a 100 puntos). La falta de documentación fiscal vigente suspenderá temporalmente la dispersión bancaria hasta su regularización.
4. **Confidencialidad y Protección de Datos (LFPDPPP):** Queda estrictamente prohibido descargar, divulgar o utilizar con fines externos los datos personales, teléfonos o calificaciones de los estudiantes asignados.""",

    "afiliado": """### Términos, Condiciones y Política de Compliance de Socios Afiliados

**Career English Institute (CEI) — Agua Prieta, Sonora, México**

1. **Objeto de la Afiliación:** El Socio Afiliado actúa como promotor independiente autorizado para canalizar prospectos a los programas académicos de Career English Institute (CEI) mediante su Código QR oficial y enlace personalizado.
2. **Requisitos Fiscales y Compliance para Pago de Comisiones:** Las comisiones se calculan exclusivamente sobre colegiaturas efectivamente cobradas y conciliadas de alumnos inscritos con el ID del Socio Afiliado. Para liberar cualquier pago, el Socio deberá mantener vigente su RFC, identificación oficial (INE) y expedir factura electrónica CFDI 4.0 (PDF + XML) conforme a la legislación fiscal vigente.
3. **Índice Estadístico de Compliance y Confianza:** El expediente del Socio Afiliado está sujeto al monitoreo continuo del Índice de Compliance Institucional (0–100 pts). El uso de publicidad engañosa, alteración de tarifas oficiales o captación fraudulenta causará la revocación inmediata del ID de Afiliado.
4. **Protección de Datos Personales (LFPDPPP):** El Socio Afiliado se obliga a resguardar la privacidad de los prospectos y a utilizar exclusivamente los canales oficiales de inscripción de CEI.""",

    "estudiante": """### Términos, Condiciones y Reglamento Académico de Inscripción

**Career English Institute (CEI) — Agua Prieta, Sonora, México**

**Primera. Naturaleza del Servicio (Modalidad 100 % en Línea) y Marco Legal Aplicable**

Los presentes Términos y Condiciones regulan la prestación de servicios educativos privados de enseñanza del idioma inglés en modalidad 100 % en línea, mediante clases sincrónicas por videoconferencia y plataforma educativa interactiva, impartidos por Career English Institute (CEI), con sede administrativa en Agua Prieta, Sonora, México. Este acuerdo se rige por las disposiciones aplicables del Código Civil Federal, la Ley General de Educación y la Ley Federal de Protección al Consumidor vigentes en los Estados Unidos Mexicanos y en el Estado de Sonora.

**Segunda. Calibración al Marco Común Europeo de Referencia para las Lenguas (CEFR)**

Los programas académicos de CEI son flexibles y ajustables al dominio real del estudiante conforme al Marco Común Europeo de Referencia para las Lenguas (CEFR, por sus siglas en inglés: niveles A1, A2, B1, B2, C1 y C2; Council of Europe, 2020). Al formalizar la inscripción, la plataforma educativa y la totalidad de las lecciones, audios, evaluaciones y ejercicios generados en ella quedarán calibrados automáticamente al nivel CEFR declarado en este formulario, pudiendo ajustarse previa valoración académica institucional.

**Tercera. Duración del Programa (Nueve Periodos) y Periodos Vacacionales Activos**

1. *Estructura del nivel.* Cada nivel académico está organizado en nueve (9) periodos mensuales de cuatro (4) semanas cada uno.
2. *Periodos vacacionales activos (verano e invierno).* Durante los recesos vacacionales prolongados de verano e invierno no se imparten clases sincrónicas en línea; no obstante, la plataforma educativa permanecerá plenamente operativa las 24 horas para que el estudiante continúe practicando y conserve su continuidad académica.
3. *Conclusión y acreditación del nivel.* Al concluir satisfactoriamente los nueve (9) periodos y acreditar la rúbrica institucional correspondiente, el estudiante obtiene su constancia o certificado académico del nivel cursado.

**Cuarta. Asistencia en Línea, Inasistencias Justificadas y Recuperación de Sesiones**

1. *Asistencia del estudiante y asignación de trabajo (homework).* El estudiante se compromete a conectarse puntualmente a sus sesiones sincrónicas en línea. En caso de requerir ausentarse por causa justificada, deberá notificar con anticipación a la institución o al docente titular para recibir su asignación de trabajo (*homework*). La entrega y el cumplimiento oportuno de dicha asignación acreditarán la sesión correspondiente.
2. *Ausencia justificada del docente.* En caso de que el docente deba ausentarse por causa justificada, se notificará oportunamente al estudiante y, por mutuo acuerdo entre ambas partes, se reprogramará y recuperará íntegramente la sesión sin costo adicional.

**Quinta. Rúbrica de Evaluación por Criterios y Acceso al Boletín Informativo**

1. *Evaluación integral por competencias.* El estudiante deberá completar en tiempo y forma los criterios de la rúbrica de evaluación correspondientes a su nivel: *Reading & Quiz* (30 %), *Viewing & Listening* (25 %), *Alphabetical & Speaking* (25 %) y *Writing Skill APA 7* (20 %).
2. *Puntualidad en colegiaturas y acceso al boletín.* El estudiante —o su padre, madre o tutor legal— se compromete a mantenerse al corriente en el pago de sus mensualidades dentro de la cuarta semana de cada bloque y a reportarlo oportunamente en la plataforma para conservar activo su acceso al Boletín Informativo de Calificaciones y avances.

**Sexta. Protección de Datos Personales y Jurisdicción**

De conformidad con la Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP, 2010), los datos personales recabados se tratarán exclusivamente para fines académicos, administrativos y de certificación interna. Para cualquier controversia derivada de la interpretación o el cumplimiento de este instrumento, las partes se someten a las leyes vigentes y a los tribunales competentes de Agua Prieta, Sonora, México.

**Séptima. Compliance Institucional, Índice Estadístico de Confianza e Integridad Digital**

El estudiante reconoce que su continuidad académica, disciplina de estudio y regularidad administrativa alimentan el Índice Estadístico de Compliance y Confianza Institucional (escala de 0 a 100 puntos). Las credenciales de acceso son estrictamente personales e intransferibles; cualquier suplantación de identidad o alteración de folios o certificados protegidos mediante sello criptográfico HMAC-SHA256 constituirá causal de baja definitiva.

---

**Referencias Normativas y Académicas (Formato APA, 7.ª ed.)**

* Council of Europe. (2020). *Common European Framework of Reference for Languages: Learning, teaching, assessment – Companion volume*. Council of Europe Publishing. https://coe.int
* Ley Federal de Protección de Datos Personales en Posesión de los Particulares [LFPDPPP]. (2010, 5 de julio). *Diario Oficial de la Federación*. https://diputados.gob.mx
* Ley General de Educación [LGE]. (2019, 30 de septiembre). *Diario Oficial de la Federación*. https://diputados.gob.mx"""
}
# ==============================================================================
# PARTE 2 DE 2 (FINAL) — CONEXIÓN POSTGRESQL Y GESTOR DE TÉRMINOS LEGALES
# ==============================================================================
def _find_secret_lt(key_name: str) -> str:
    if key_name in st.secrets:
        return str(st.secrets[key_name]).strip()
    key_low = key_name.lower()
    for k, v in st.secrets.items():
        if str(k).lower() == key_low and not isinstance(v, dict):
            return str(v).strip()
        if isinstance(v, dict):
            for sk, sv in v.items():
                if str(sk).lower() == key_low:
                    return str(sv).strip()
    return ""


def _open_pg_lt():
    pg_host = _find_secret_lt("PG_HOST") or _find_secret_lt("DB_HOST")
    pg_user = _find_secret_lt("PG_USER") or _find_secret_lt("DB_USER")
    pg_pass = _find_secret_lt("PG_PASSWORD") or _find_secret_lt("DB_PASSWORD")
    pg_port = int(_find_secret_lt("PG_PORT") or _find_secret_lt("DB_PORT") or 6543)
    pg_db = _find_secret_lt("PG_DBNAME") or _find_secret_lt("DB_NAME") or "postgres"
    if pg_host and pg_user and pg_pass:
        puertos = [pg_port, 6543] if pg_port != 6543 else [6543]
        for p in puertos:
            try:
                return psycopg.connect(
                    host=pg_host, port=p, dbname=pg_db, user=pg_user, password=pg_pass,
                    sslmode="require", connect_timeout=10, prepare_threshold=None
                )
            except Exception:
                pass
    return None


def get_institutional_terms_pg(tipo_rol: str = "docente") -> dict:
    """Obtiene los Términos y Condiciones vigentes para 'docente', 'afiliado' o 'estudiante'."""
    key_rol = str(tipo_rol or "docente").strip().lower()
    default_txt = DEFAULT_TERMS_BY_ROLE.get(key_rol, DEFAULT_TERMS_BY_ROLE["docente"])
    conn = _open_pg_lt()
    if not conn:
        return {"texto": default_txt, "updated_at": "", "updated_by": "Sistema CEI"}
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS institutional_legal_terms (
                        tipo_rol TEXT PRIMARY KEY,
                        texto TEXT NOT NULL,
                        updated_by TEXT DEFAULT 'Owner',
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    SELECT texto, updated_by, updated_at
                    FROM institutional_legal_terms
                    WHERE tipo_rol = %s
                    LIMIT 1;
                """, (key_rol,))
                row = cur.fetchone()
                if row and str(row[0] or "").strip():
                    ts_str = row[2].astimezone(TZ_SONORA).strftime("%d/%m/%Y %H:%M") if row[2] else ""
                    return {
                        "texto": str(row[0]).replace("\\n", "\n"),
                        "updated_by": str(row[1] or "Owner"),
                        "updated_at": ts_str
                    }
                cur.execute("""
                    INSERT INTO institutional_legal_terms (tipo_rol, texto, updated_by)
                    VALUES (%s, %s, 'Sistema CEI')
                    ON CONFLICT (tipo_rol) DO NOTHING;
                """, (key_rol, default_txt))
        return {"texto": default_txt, "updated_at": "", "updated_by": "Sistema CEI"}
    except Exception:
        return {"texto": default_txt, "updated_at": "", "updated_by": "Sistema CEI"}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def save_institutional_terms_pg(tipo_rol: str, texto_nuevo: str, updated_by: str) -> tuple[bool, str]:
    """Guarda y publica nuevos Términos y Condiciones con marca de tiempo."""
    key_rol = str(tipo_rol or "docente").strip().lower()
    conn = _open_pg_lt()
    if not conn:
        return False, "❌ Sin conexión con la base de datos institucional."
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS institutional_legal_terms (
                        tipo_rol TEXT PRIMARY KEY,
                        texto TEXT NOT NULL,
                        updated_by TEXT DEFAULT 'Owner',
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    INSERT INTO institutional_legal_terms (tipo_rol, texto, updated_by, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (tipo_rol) DO UPDATE SET
                        texto = EXCLUDED.texto,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = NOW();
                """, (key_rol, texto_nuevo.strip(), str(updated_by or "Owner").strip()))
        return True, f"✅ Términos y Condiciones ({key_rol.upper()}) actualizados y publicados."
    except Exception as e:
        return False, f"Error al guardar términos: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass
