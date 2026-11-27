from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _cargar_fuente_cinta(tamano: int):
    for ruta_f in (
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNS.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if Path(ruta_f).exists():
            try:
                return ImageFont.truetype(ruta_f, tamano)
            except Exception:
                pass
    return ImageFont.load_default()


def generar_iconos_pwa_cei(
    ruta_origen: str = "static/LOGO CEI APP.png",
    carpeta_salida: str = "static",
    medidas: tuple[int, ...] = (192, 512),
    fondo_rgba: tuple[int, int, int, int] = (11, 37, 69, 255),
) -> list[Path]:
    """Genera los íconos oficiales PWA/APK para App Principal, Docentes y Socios Afiliados."""
    origen = Path(ruta_origen)
    if not origen.exists():
        raise FileNotFoundError(f"No se encontró la imagen original en: {origen.resolve()}")

    salida_dir = Path(carpeta_salida)
    salida_dir.mkdir(parents=True, exist_ok=True)

    img_original = Image.open(origen).convert("RGBA")
    archivos_generados: list[Path] = []

    perfiles = [
        ("android-launchericon-{lado}-{lado}.png", "", ""),
        ("icon-docentes-{lado}.png", "CEI DOCENTES", "#1d4ed8"),
        ("icon-socios-{lado}.png", "CEI SOCIOS", "#047857"),
    ]

    for plantilla_nombre, etiqueta, color_cinta in perfiles:
        for lado in medidas:
            lienzo = Image.new("RGBA", (lado, lado), fondo_rgba)
            copia = img_original.copy()

            if not etiqueta:
                copia.thumbnail((lado, lado), Image.Resampling.LANCZOS)
                offset_x = (lado - copia.width) // 2
                offset_y = (lado - copia.height) // 2
                lienzo.paste(copia, (offset_x, offset_y), copia)
            else:
                max_logo = int(lado * 0.70)
                copia.thumbnail((max_logo, max_logo), Image.Resampling.LANCZOS)
                offset_x = (lado - copia.width) // 2
                offset_y = int(lado * 0.05)
                lienzo.paste(copia, (offset_x, offset_y), copia)

                draw = ImageDraw.Draw(lienzo)
                pad_x = int(lado * 0.07)
                y1 = int(lado * 0.78)
                y2 = int(lado * 0.94)
                radio = max(8, int(lado * 0.04))
                draw.rounded_rectangle([(pad_x, y1), (lado - pad_x, y2)], radius=radio, fill=color_cinta)

                font = _cargar_fuente_cinta(max(14, int(lado * 0.074)))
                bbox = draw.textbbox((0, 0), etiqueta, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                tx = (lado - tw) / 2
                ty = y1 + ((y2 - y1) - th) / 2 - bbox[1]
                draw.text((tx, ty), etiqueta, fill="#ffffff", font=font)

            destino = salida_dir / plantilla_nombre.format(lado=lado)
            lienzo.save(destino, format="PNG", optimize=True)
            archivos_generados.append(destino)
            print(f"✅ Generado: {destino} ({lado}x{lado} px)")

    return archivos_generados


if __name__ == "__main__":
    generar_iconos_pwa_cei()
