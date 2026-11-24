import json
import os
import psycopg
import streamlit as st


def get_database_url() -> str:
    """Retrieves the PostgreSQL connection string from Streamlit secrets or environment."""
    try:
        for key in ["DATABASE_URL", "SUPABASE_DB_URL", "POSTGRES_URL"]:
            val = str(st.secrets.get(key, "")).strip()
            if val:
                return val
    except Exception:
        pass
    for key in ["DATABASE_URL", "SUPABASE_DB_URL", "POSTGRES_URL"]:
        val = str(os.environ.get(key, "")).strip()
        if val:
            return val
    return ""


def open_pg_conn():
    """Opens a safe psycopg3 PostgreSQL connection with autocommit disabled by default."""
    db_url = get_database_url()
    if not db_url:
        return None
    try:
        return psycopg.connect(db_url, connect_timeout=8)
    except Exception:
        return None


_open_legal_pg_conn = open_pg_conn


def get_user_delegated_caps_pg(usuario_target: str) -> dict:
    """Fetches individually delegated capabilities for a specific user from Supabase."""
    u_clean = str(usuario_target or "").strip().lower()
    if not u_clean:
        return {}
    conn = open_pg_conn()
    if not conn:
        return {}
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_custom_permissions (
                        usuario_login TEXT PRIMARY KEY,
                        permisos_json TEXT NOT NULL DEFAULT '{}',
                        updated_by TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute(
                    "SELECT permisos_json FROM user_custom_permissions WHERE LOWER(TRIM(usuario_login)) = %s LIMIT 1;",
                    (u_clean,)
                )
                row = cur.fetchone()
                if row and row[0]:
                    return json.loads(str(row[0]))
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return {}


def save_user_delegated_caps_pg(usuario_target: str, caps_dict: dict, autor: str) -> tuple[bool, str]:
    """Saves individually delegated capabilities for a specific user in PostgreSQL."""
    u_clean = str(usuario_target or "").strip()
    if not u_clean:
        return False, "Usuario inválido."
    conn = open_pg_conn()
    if not conn:
        return False, "No hay conexión con Supabase PostgreSQL."
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_custom_permissions (
                        usuario_login TEXT PRIMARY KEY,
                        permisos_json TEXT NOT NULL DEFAULT '{}',
                        updated_by TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    INSERT INTO user_custom_permissions (usuario_login, permisos_json, updated_by, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (usuario_login) DO UPDATE SET
                        permisos_json = EXCLUDED.permisos_json,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = CURRENT_TIMESTAMP;
                """, (u_clean, json.dumps(caps_dict, ensure_ascii=False), autor))
        return True, f"✅ Permisos delegados guardados para **{u_clean}**."
    except Exception as e:
        return False, f"Error al guardar delegación: {e}"
    finally:
        try:
            conn.close()
        except Exception:
            pass
