from pathlib import Path
from PIL import Image


def generar_iconos_pwa_cei(
    ruta_origen: str = "static/LOGO CEI APP.png",
    carpeta_salida: str = "static",
    medidas: tuple[int, ...] = (192, 512),
    fondo_rgba: tuple[int, int, int, int] = (11, 37, 69, 255),
) -> list[Path]:
    """Redimensiona el logo institucional a medidas exactas de PWA sin deformarlo."""
    origen = Path(ruta_origen)
    if not origen.exists():
        raise FileNotFoundError(f"No se encontró la imagen original en: {origen.resolve()}")

    salida_dir = Path(carpeta_salida)
    salida_dir.mkdir(parents=True, exist_ok=True)

    img_original = Image.open(origen).convert("RGBA")
    archivos_generados: list[Path] = []

    for lado in medidas:
        # Escalar proporcionalmente para que quepa exacto en el cuadro sin distorsión
        copia = img_original.copy()
        copia.thumbnail((lado, lado), Image.Resampling.LANCZOS)

        # Centrar sobre lienzo cuadrado exacto (lado x lado)
        lienzo = Image.new("RGBA", (lado, lado), fondo_rgba)
        offset_x = (lado - copia.width) // 2
        offset_y = (lado - copia.height) // 2
        lienzo.paste(copia, (offset_x, offset_y), copia)

        destino = salida_dir / f"android-launchericon-{lado}-{lado}.png"
        lienzo.save(destino, format="PNG", optimize=True)
        archivos_generados.append(destino)
        print(f"✅ Generado: {destino} ({lado}x{lado} px)")

    return archivos_generados


if __name__ == "__main__":
    generar_iconos_pwa_cei()
