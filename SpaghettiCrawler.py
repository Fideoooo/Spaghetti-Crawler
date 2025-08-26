import os
import requests
import signal
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, quote, urlparse
from art import tprint, text2art
from colorama import Fore, Style, init
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


init(autoreset=True)


def signal_handler(sig, frame):
    print(Fore.RED + Style.BRIGHT+"\nPrograma detenido por el usuario")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


ascii_art1 = text2art("Spaghetti", font="slant")
print(Fore.YELLOW + Style.BRIGHT + ascii_art1)
ascii_art2 = text2art("Crawler", font="slant")
print(Fore.YELLOW + Style.BRIGHT + ascii_art2)
print(Fore.GREEN + "Crawler / Scraper de imágenes desarrollado en Python 3.9")
r = requests.get('http://jsonip.com')
PUB_ip = r.json()['ip']
print(Fore.MAGENTA + Style.BRIGHT)
print()
print(Fore.WHITE + "Creado por", end=" ")
print(Fore.BLUE + f"Fideo")
print(Style.RESET_ALL)
print()
print(Fore.RED + Style.BRIGHT + "ADVERTENCIA: TU IP PÚBLICA " + str(PUB_ip) + " ES VISIBLE")
print(Fore.RED + Style.BRIGHT + "USA UN VPN PARA CAMBIARLA")
print()

def validar_url_con_w3c(url):
    if not url.startswith("http"):
        print(Fore.RED + "[✘] Ingresa una URL válida que comience con http:// o https://")
        return False

    validador_base = "https://validator.w3.org/nu/?out=json&doc="
    encoded_url = quote(url, safe='')
    full_url = validador_base + encoded_url

    try:
        response = requests.get(full_url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            data = response.json()
            mensajes = data.get("messages", [])
            if not mensajes:
                print(Fore.GREEN + "[✔] Página web válida según W3C.")
                return True
            else:
                hay_errores = any(m.get("type") == "error" for m in mensajes)
                hay_io_error = any(m.get("type") == "non-document-error" for m in mensajes)
                if hay_io_error:
                    print(Fore.RED + "[✘] Error: Página no encontrada o inaccesible.")
                    return False
                elif hay_errores:
                    print(Fore.YELLOW + "[!] La página existe pero tiene errores de validación W3C.")
                    for m in mensajes:
                        if m.get("type") == "error":
                            print(Fore.RED + "  • " + m.get("message", "Error desconocido"))
                    return True
                else:
                    print(Fore.GREEN + "[✔] Página con advertencias menores pero sin errores críticos.")
                    return True
        else:
            print(Fore.RED + f"[✘] No se pudo validar la página. Código: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(Fore.RED + f"[✘] Error al validar la URL: {e}")
        return False



def es_url_interna(base_url, link):
    return urlparse(link).netloc == "" or urlparse(link).netloc == urlparse(base_url).netloc



def descargar_imagen(url):
    try:
        nombre = os.path.basename(url.split("?")[0])
        ruta = os.path.join(output_folder, nombre)
        if not os.path.exists(ruta):
            respuesta = requests.get(url, timeout=10)

            content_type = respuesta.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                print(Fore.YELLOW + f"[✗] No es una imagen válida: {url} ({content_type})")
                return

            with open(ruta, "wb") as f:
                f.write(respuesta.content)
            print(Fore.GREEN + f"[✓] Descargada: {nombre}")
        else:
            print(Fore.CYAN + f"[=] Ya existe: {nombre}")
    except Exception as e:
        print(Fore.RED + f"[✗] Error con {url}: {e}")



try:
    while True:
        url_usuario = input(Fore.CYAN + Style.BRIGHT + "[?] Ingresa la URL de la página que deseas scrapear (ejem:https://ejemplo.com): ").strip()
        if validar_url_con_w3c(url_usuario):
            break


    output_folder = "imagenes_descargadas"
    os.makedirs(output_folder, exist_ok=True)


    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

    try:
        print(Fore.YELLOW + f"[*] Iniciando rastreo en: {url_usuario}")

        img_urls = []
        visitadas = set()
        cola_urls = [url_usuario]

        while cola_urls:
            url_actual = cola_urls.pop()
            if url_actual in visitadas:
                continue
            try:
                print(Fore.CYAN + f"[+] Visitando: {url_actual}")
                driver.get(url_actual)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')


                img_tags = soup.find_all("img")
                for img in img_tags:
                    src = img.get("src")
                    if src:
                        full_url = urljoin(driver.current_url, src)
                        if full_url not in img_urls:
                            img_urls.append(full_url)


                for enlace in soup.find_all("a", href=True):
                    href = enlace["href"]
                    full_link = urljoin(driver.current_url, href)
                    if es_url_interna(url_usuario, full_link) and full_link not in visitadas:
                        cola_urls.append(full_link)

                visitadas.add(url_actual)

            except Exception as e:
                print(Fore.RED + f"[✗] Error en {url_actual}: {e}")

        print(Fore.YELLOW + f"[*] Se encontraron {len(img_urls)} imágenes (cantidad estimada).")
        print(Fore.YELLOW + "[*] Descargando imágenes en paralelo...\n")
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(descargar_imagen, img_urls)

        print(Fore.GREEN + Style.BRIGHT + "\n[✔] Descarga finalizada.")
        print(Fore.GREEN + Style.BRIGHT + "Se creó la carpeta: imagenes_descargadas con las imágenes descargadas.")

    except KeyboardInterrupt:
        print(Fore.RED + "\n[✘] Interrupción manual detectada. Cerrando el programa...")

    except Exception as e:
        print(Fore.RED + f"\n[✘] Error inesperado: {e}")

    finally:
        driver.quit()

except Exception as e:
    print(Fore.RED + f"\n[✘] Error fatal al iniciar el programa: {e}")
