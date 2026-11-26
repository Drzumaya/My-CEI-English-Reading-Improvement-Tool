import streamlit as st
import streamlit.components.v1 as _st_components


def ocultar_badges_plataforma_cei(es_owner_o_admin: bool = False) -> None:
    """Oculta la cabecera de Streamlit y los logotipos flotantes de GitHub/Streamlit."""
    if es_owner_o_admin:
        return

    st.markdown(
        """
        <style>
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="manage-app-button"],
        #MainMenu,
        footer,
        div[class*="viewerBadge"],
        div[class*="profileContainer"],
        div[class*="profilePreview"],
        div[class*="_container_gzau3"],
        div[class*="_terminalButton_"],
        a[href*="streamlit.io/cloud"],
        a[href*="share.streamlit.io"],
        a[href*="github.com"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1.5rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _st_components.html(
        """
        <script>
        (function ocultarBadgesCEI() {
            const selectors = [
                '[data-testid="manage-app-button"]',
                '[data-testid="stStatusWidget"]',
                'div[class*="viewerBadge"]',
                'div[class*="profileContainer"]',
                'div[class*="profilePreview"]',
                'div[class*="_container_gzau3"]',
                'div[class*="_terminalButton_"]',
                'a[href*="streamlit.io/cloud"]',
                'a[href*="share.streamlit.io"]',
                'a[href*="github.com"]'
            ];
            function limpiar(doc) {
                if (!doc) return;
                selectors.forEach(sel => {
                    doc.querySelectorAll(sel).forEach(el => {
                        el.style.setProperty('display', 'none', 'important');
                        el.style.setProperty('visibility', 'hidden', 'important');
                        el.style.setProperty('opacity', '0', 'important');
                        el.style.setProperty('pointer-events', 'none', 'important');
                    });
                });
            }
            const run = () => {
                limpiar(document);
                try { limpiar(window.parent.document); } catch (e) {}
                try { limpiar(window.top.document); } catch (e) {}
            };
            run();
            setInterval(run, 800);
        })();
        </script>
        """,
        height=0,
    )
