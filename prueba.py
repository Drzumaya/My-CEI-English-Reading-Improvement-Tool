from core.database import open_pg_conn

DEFAULT_CAMPUS_ID = "CEI-AP-01"


def ensure_multicampus_schema_pg(default_address: str = "Agua Prieta, Sonora, México") -> bool:
    """Creates the master campuses table and adds campus_id across core tables safely."""
    conn = open_pg_conn()
    if not conn:
        return False
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS campuses (
                        campus_id TEXT PRIMARY KEY,
                        nombre_plantel TEXT NOT NULL,
                        ciudad_estado TEXT NOT NULL,
                        direccion_oficial TEXT NOT NULL,
                        telefono_contacto TEXT DEFAULT '',
                        moneda TEXT DEFAULT 'MXN',
                        iva_pct NUMERIC(5,2) DEFAULT 16.00,
                        director_usuario TEXT DEFAULT '',
                        estatus TEXT DEFAULT 'Activo',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    INSERT INTO campuses (
                        campus_id, nombre_plantel, ciudad_estado, direccion_oficial,
                        telefono_contacto, moneda, iva_pct, estatus
                    )
                    VALUES (
                        'CEI-AP-01',
                        'Career English Institute — Sede Matriz Agua Prieta',
                        'Agua Prieta, Sonora, México',
                        %s, '', 'MXN', 16.00, 'Activo'
                    )
                    ON CONFLICT (campus_id) DO NOTHING;
                """, (default_address,))

                for table_name in ["users_padron", "affiliate_partners", "certificates", "lessons_history"]:
                    try:
                        cur.execute(f"""
                            ALTER TABLE {table_name}
                            ADD COLUMN IF NOT EXISTS campus_id TEXT DEFAULT 'CEI-AP-01';
                        """)
                        cur.execute(f"""
                            UPDATE {table_name}
                            SET campus_id = 'CEI-AP-01'
                            WHERE campus_id IS NULL OR TRIM(campus_id) = '';
                        """)
                    except Exception:
                        pass
        return True
    except Exception:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_campuses_pg(default_address: str = "Agua Prieta, Sonora, México") -> list[dict]:
    """Returns all registered campuses/franchises ordered by creation date."""
    ensure_multicampus_schema_pg(default_address)
    conn = open_pg_conn()
    if not conn:
        return [{
            "campus_id": DEFAULT_CAMPUS_ID,
            "nombre_plantel": "Career English Institute — Sede Matriz Agua Prieta",
            "ciudad_estado": "Agua Prieta, Sonora, México",
            "direccion_oficial": default_address,
            "telefono_contacto": "",
            "moneda": "MXN",
            "iva_pct": 16.0,
            "director_usuario": "",
            "estatus": "Activo"
        }]
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT campus_id, nombre_plantel, ciudad_estado, direccion_oficial,
                       COALESCE(telefono_contacto, ''), COALESCE(moneda, 'MXN'),
                       COALESCE(iva_pct, 16.0), COALESCE(director_usuario, ''), COALESCE(estatus, 'Activo')
                FROM campuses
                ORDER BY created_at ASC;
            """)
            rows = cur.fetchall() or []
            return [
                {
                    "campus_id": r[0],
                    "nombre_plantel": r[1],
                    "ciudad_estado": r[2],
                    "direccion_oficial": r[3],
                    "telefono_contacto": r[4],
                    "moneda": r[5],
                    "iva_pct": float(r[6] or 16.0),
                    "director_usuario": r[7],
                    "estatus": r[8]
                }
                for r in rows
            ]
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def upsert_campus_pg(
    campus_id: str,
    nombre_plantel: str,
    ciudad_estado: str,
    direccion_oficial: str,
    telefono_contacto: str = "",
    moneda: str = "MXN",
    iva_pct: float = 16.0,
    director_usuario: str = "",
    estatus: str = "Activo"
) -> tuple[bool, str]:
    """Creates or updates a franchise campus record in PostgreSQL."""
    cid = str(campus_id or "").strip().upper()
    if not cid or not str(nombre_plantel or "").strip():
        return False, "El ID del plantel y el nombre son obligatorios."
    ensure_multicampus_schema_pg(direccion_oficial)
    conn = open_pg_conn()
    if not conn:
        return False, "Sin conexión a Supabase PostgreSQL."
    try:
        with conn:
            with conn.cursor() as cur: 
                cur.execute("""
                    INSERT INTO campuses (
                        campus_id, nombre_plantel, ciudad_estado, direccion_oficial,
                        telefono_contacto, moneda, iva_pct, director_usuario, estatus
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (campus_id) DO UPDATE SET
                        nombre_plantel = EXCLUDED.nombre_plantel,
                        ciudad_estado = EXCLUDED.ciudad_estado,
                        direccion_oficial = EXCLUDED.direccion_oficial,
                        telefono_contacto = EXCLUDED.telefono_contacto,
                        moneda = EXCLUDED.moneda,
                        iva_pct = EXCLUDED.iva_pct,
                        director_usuario = EXCLUDED.director_usuario,
                        estatus = EXCLUDED.estatus;
                """, (
                    cid, nombre_plantel.strip(), ciudad_estado.strip(), direccion_oficial.strip(),
                    telefono_contacto.strip(), moneda.strip().upper(), float(iva_pct),
                    director_usuario.strip(), estatus.strip()
                ))
        return True, f"✅ Plantel **{cid} — {nombre_plantel.strip()}** guardado correctamente."
    except Exception as e:
        return False, f"Error al guardar plantel: {e}"
    finally:
        try: 
            conn.close()
        except Exception:
            pass
