from datetime import datetime
from zoneinfo import ZoneInfo
import psycopg
import streamlit as st

TZ_SONORA = ZoneInfo("America/Hermosillo")

DEFAULT_TERMS_BY_ROLE = {
    "docente": """TÉRMINOS, CONDICIONES Y CÓDIGO DE COMPLIANCE DOCENTE — CAREER ENGLISH INSTITUTE (CEI)

1. NATURALEZA ACADÉMICA Y PROFESIONAL: El Docente declara contar con las credenciales académicas, Cédula Profesional y certificación del idioma inglés declaradas en su expediente, comprometiéndose a impartir sus sesiones conforme al Marco Común Europeo de Referencia (CEFR) y lineamientos pedagógicos de CEI.
2. CUMPLIMIENTO FISCAL Y REQUISITOS DE COBRO (SAT MÉXICO): Para recibir el pago de honorarios o comisiones asignadas, el Docente se obliga a mantener actualizada su Bóveda Legal y Fiscal en Mi Portal Docente CEI con:
   a) Constancia de Situación Fiscal (CSF) con antigüedad menor a 30 días.
   b) Opinión de Cumplimiento de Obligaciones Fiscales (32-D) en sentido Positivo (menor a 30 días).
   c) Carátula bancaria con CLABE interbancaria de 18 dígitos a su nombre e INE/Cédula vigente.
   d) Comprobante Fiscal Digital por Internet (CFDI 4.0 en PDF y XML) emitido antes del día 25 de cada mes.
3. ÍNDICE DE COMPLIANCE Y CONFIANZA: El Docente acepta ser evaluado periódicamente mediante el Índice Estadístico de Compliance y Confianza Institucional (0 a 100 puntos). La falta de documentación fiscal vigente suspenderá temporalmente la dispersión bancaria hasta su regularización.
4. CONFIDENCIALIDAD Y PROTECCIÓN DE DATOS (LFPDPPP): Queda estrictamente prohibido descargar, divulgar o utilizar con fines externos los datos personales, teléfonos o calificaciones de los estudiantes asignados.
5. PROPIEDAD INTELECTUAL: Todo el material didáctico, folios generados por IA y metodologías de CEI son propiedad exclusiva de Career English Institute.""",

    "afiliado": """TÉRMINOS, CONDICIONES Y POLÍTICA DE COMPLIANCE DE SOCIOS AFILIADOS — CAREER ENGLISH INSTITUTE (CEI)

1. OBJETO DE LA AFILIACIÓN: El Socio Afiliado actúa como promotor independiente autorizado para canalizar prospectos a los programas académicos de Career English Institute (CEI) mediante su Código QR oficial y enlace personalizado.
2. REQUISITOS FISCALES Y COMPLIANCE PARA PAGO DE COMISIONES: Las comisiones se calculan exclusivamente sobre colegiaturas efectivamente cobradas y conciliadas de alumnos inscritos con el ID del Socio Afiliado. Para liberar cualquier pago, el Socio deberá mantener vigente su RFC, identificación oficial (INE) y expedir factura electrónica CFDI 4.0 (PDF + XML) conforme a la legislación fiscal vigente.
3. ÍNDICE ESTADÍSTICO DE COMPLIANCE Y CONFIANZA: El expediente del Socio Afiliado está sujeto al monitoreo continuo del Índice de Compliance Institucional (0–100 pts). El uso de publicidad engañosa, alteración de tarifas oficiales o captación fraudulenta causará la revocación inmediata del ID de Afiliado.
4. PROTECCIÓN DE DATOS PERSONALES (LFPDPPP): El Socio Afiliado se obliga a resguardar la privacidad de los prospectos y a utilizar exclusivamente los canales oficiales de inscripción de CEI.""",

    "estudiante": """REGLAMENTO ACADÉMICO, TÉRMINOS DE USO Y COMPLIANCE ESTUDIANTIL — CAREER ENGLISH INSTITUTE (CEI)

1. COMPROMISO ACADÉMICO E INTEGRIDAD: El Estudiante se compromete a realizar de forma personal y honesta sus lecturas, prácticas de pronunciación y evaluaciones por Folio dentro de la plataforma CEI, manteniendo su racha semanal activa.
2. REGULARIDAD ADMINISTRATIVA Y PAGOS (9 BLOQUES): El acceso continuo a los módulos y la emisión de certificados con timbre digital HMAC-SHA256 y Código QR están sujetos al cumplimiento oportuno de los bloques de colegiatura correspondientes.
3. ÍNDICE DE COMPLIANCE Y CONFIANZA: El progreso académico, disciplina de estudio y regularidad administrativa alimentan el Índice Estadístico de Confianza del Estudiante dentro de la institución.
4. PRIVACIDAD Y USO DE PLATAFORMA: Las credenciales de acceso son personales e intransferibles. Los datos personales recabados son tratados conforme al Aviso de Privacidad de Career English Institute y la LFPDPPP."""
}


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
        puertos = [pg_port, 6543] if pg_port != 6543 else
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
                if row and str(row or "").strip():
                    ts_str = row.astimezone(TZ_SONORA).strftime("%d/%m/%Y %H:%M") if row else ""
                    return {"texto": str(row), "updated_by": str(row or "Owner"), "updated_at": ts_str}
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
