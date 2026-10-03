#!/usr/bin/env python3
"""
Captura screenshots (desktop e mobile) e executa auditoria Lighthouse e Acessibilidade
sobre a versão compilada em dist/ servida localmente.
"""

import json
import os
import subprocess
import time
import sys

CHROME_BIN = "/home/noritomi/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome"
ARTIFACTS_DIR = "/home/noritomi/.gemini/antigravity-cli/brain/45f53b36-6e5d-40a2-80ab-9ecacc1c3101"
PORT = 8085
URL = f"http://127.0.0.1:{PORT}/"


def wait_for_server(port, timeout=10):
    import urllib.request
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    if not os.path.exists("dist"):
        print("Erro: diretório dist/ não existe. Execute o export primeiro.")
        sys.exit(1)

    # 1. Inicia servidor HTTP local
    print(f"Iniciando servidor HTTP estático na porta {PORT}...")
    server_proc = subprocess.Popen([
        sys.executable, "-m", "http.server", str(PORT), "--directory", "dist"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        if not wait_for_server(PORT):
            print("Erro: servidor HTTP não respondeu a tempo.")
            sys.exit(1)
        print("✓ Servidor HTTP respondendo com sucesso.")

        # 2. Captura Screenshot Desktop (1920x1080)
        desktop_img = os.path.join(ARTIFACTS_DIR, "screenshot_desktop.png")
        print(f"Capturando screenshot Desktop em {desktop_img}...")
        cmd_desktop = [
            CHROME_BIN,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--virtual-time-budget=6000",
            f"--screenshot={desktop_img}",
            URL,
        ]
        subprocess.run(cmd_desktop, check=True)
        if os.path.exists(desktop_img):
            print(f"✓ Screenshot Desktop gerada ({os.path.getsize(desktop_img):,} bytes)")

        # 3. Captura Screenshot Mobile (390x844 - iPhone / Mobile moderno)
        mobile_img = os.path.join(ARTIFACTS_DIR, "screenshot_mobile.png")
        print(f"Capturando screenshot Mobile em {mobile_img}...")
        cmd_mobile = [
            CHROME_BIN,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--window-size=390,844",
            "--virtual-time-budget=6000",
            f"--screenshot={mobile_img}",
            URL,
        ]
        subprocess.run(cmd_mobile, check=True)
        if os.path.exists(mobile_img):
            print(f"✓ Screenshot Mobile gerada ({os.path.getsize(mobile_img):,} bytes)")

        # 4. Auditoria Lighthouse via npx
        lh_json = "docs/lighthouse_report.json"
        print("Executando auditoria Lighthouse...")
        env = os.environ.copy()
        env["CHROME_PATH"] = CHROME_BIN
        cmd_lh = [
            "/home/noritomi/.nvm/versions/node/v24.18.1/bin/npx",
            "--yes",
            "lighthouse",
            URL,
            "--chrome-flags=--headless=new --no-sandbox --disable-gpu",
            "--output=json",
            f"--output-path={lh_json}",
            "--quiet",
        ]
        try:
            subprocess.run(cmd_lh, env=env, check=True, timeout=90)
            if os.path.exists(lh_json):
                with open(lh_json, "r", encoding="utf-8") as fp:
                    lh_data = json.load(fp)

                cats = lh_data.get("categories", {})
                perf = int((cats.get("performance", {}).get("score", 0) or 0) * 100)
                a11y = int((cats.get("accessibility", {}).get("score", 0) or 0) * 100)
                bp = int((cats.get("best-practices", {}).get("score", 0) or 0) * 100)
                seo = int((cats.get("seo", {}).get("score", 0) or 0) * 100)

                audits = lh_data.get("audits", {})
                lcp = audits.get("largest-contentful-paint", {}).get("displayValue", "N/A")
                fcp = audits.get("first-contentful-paint", {}).get("displayValue", "N/A")
                tbt = audits.get("total-blocking-time", {}).get("displayValue", "N/A")
                cls = audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A")

                print("\n==================================================")
                print(" RESULTADOS DO AUDIT LIGHTHOUSE")
                print("==================================================")
                print(f" Performance:    {perf} / 100")
                print(f" Acessibilidade: {a11y} / 100")
                print(f" Best Practices: {bp} / 100")
                print(f" SEO:            {seo} / 100")
                print("--------------------------------------------------")
                print(f" First Contentful Paint (FCP):  {fcp}")
                print(f" Largest Contentful Paint (LCP): {lcp}")
                print(f" Total Blocking Time (TBT):     {tbt}")
                print(f" Cumulative Layout Shift (CLS): {cls}")
                print("==================================================")
        except Exception as e:
            print(f"Aviso no Lighthouse: {e}")

    finally:
        server_proc.terminate()
        server_proc.wait()
        print("Servidor HTTP encerrado.")


if __name__ == "__main__":
    main()
