import os
import sys
import time
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from rapidocr import RapidOCR

BASE_URL = "https://www.cmfchile.cl/institucional/estadisticas/merc_seguros/cartera_inversiones/dcisgv/descarga_cartera_inv.php?tipoentidad={}"

def download_sample_zip(entity_type="CSGEN", year="2026", month="07", output_path="sample.zip"):
    ocr = RapidOCR()
    url = BASE_URL.format(entity_type)
    print(f"[CMF Downloader] Iniciando prueba de descarga para {entity_type} {year}-{month}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())

        try:
            print(f"  -> Navegando a: {url}")
            page.goto(url, timeout=60000, wait_until="networkidle")
            time.sleep(2)

            # Seleccionar año y mes
            print(f"  -> Seleccionando Año: {year}, Mes: {month}")
            page.select_option("#s_agno", str(year))
            page.select_option("#s_mes", f"{int(month):02d}")
            time.sleep(2)

            # Intentos de resolución de CAPTCHA
            max_intentos = 3
            success = False

            for intento in range(1, max_intentos + 1):
                captcha_el = page.wait_for_selector("#captcha_img", timeout=10000)
                if intento > 1:
                    print(f"  -> Recargando CAPTCHA (intento {intento}/{max_intentos})...")
                    captcha_el.click()
                    time.sleep(2)
                    captcha_el = page.wait_for_selector("#captcha_img", timeout=10000)

                img_bytes = captcha_el.screenshot()
                ocr_out = ocr(img_bytes)
                captcha_code = ""
                if ocr_out and hasattr(ocr_out, "txts") and ocr_out.txts:
                    captcha_code = re.sub(r'[^A-Za-z0-9]', '', ocr_out.txts[0]).upper()

                print(f"  -> Intento {intento}: CAPTCHA detectado '{captcha_code}'")
                if not captcha_code or len(captcha_code) < 4:
                    continue

                page.fill("#fcaptcha", captcha_code)
                time.sleep(1)

                try:
                    print("  -> Haciendo clic en '#b_descargar' y esperando archivo...")
                    with page.expect_download(timeout=15000) as download_info:
                        page.click("#b_descargar")
                    
                    download = download_info.value
                    download.save_as(output_path)
                    file_size_kb = os.path.getsize(output_path) / 1024
                    print(f"  [EXITO] Archivo descargado correctamente: {output_path} ({file_size_kb:.1f} KB)")
                    success = True
                    break
                except Exception as e:
                    print(f"  [AVISO] Intento {intento} falló o el captcha era incorrecto. Reintentando...")
                    time.sleep(2)

            return success

        except Exception as e:
            print(f"  [ERROR] Falló el flujo de navegación: {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(__file__), "test_download.zip")
    success = download_sample_zip(entity_type="CSGEN", year="2026", month="07", output_path=out_file)
    print(f"Resultado final: {'OK' if success else 'FALLO'}")
