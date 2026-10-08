
import os, re, time, csv, sys, logging
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests, pandas as pd
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

# ===================== CONFIG =====================
START_URL = "https://snies.mineducacion.gov.co/portal/ESTADISTICAS/Bases-consolidadas/"
VALID_YEARS = list(range(2021, 2100))
VALID_EXTS = (".xlsx", ".xls", ".csv", ".zip", ".xlsb")
PREF_EXT_ORDER = [".xlsx", ".xls", ".csv", ".zip", ".xlsb"]
YEAR_REGEX = r"(20\d{2})"

CATEGORY_PATTERNS_ORDERED = [
    ("Estudiantes_matriculados_primer_curso", r"\bestudiantes?\s+matriculados?\s+en\s+primer\s+curso\b"),
    ("Estudiantes_matriculados",              r"\bestudiantes?\s+matriculados?\b"),
    ("Estudiantes_admitidos",                 r"\bestudiantes?\s+admitidos?\b"),
    ("Estudiantes_inscritos",                 r"\bestudiantes?\s+inscritos?\b"),
    ("Docentes",                              r"\bdocentes?\b"),
    ("Administrativos",                       r"\badministrativ(?:o|os|a|as)\b"),
]
DISPLAY_LABELS = {
    "Administrativos": "Administrativos",
    "Docentes": "Docentes",
    "Estudiantes_matriculados": "Estudiantes matriculados",
    "Estudiantes_matriculados_primer_curso": "Estudiantes matriculados en primer curso",
    "Estudiantes_admitidos": "Estudiantes admitidos",
    "Estudiantes_inscritos": "Estudiantes inscritos",
}

DATA_RAW_DIR = "data/raw"
LOG_DIR = "logs"
OUT_DIR = "output"
MANIFEST_PATH = os.path.join(OUT_DIR, "manifest.csv")
LOG_PATH = os.path.join(LOG_DIR, "run.log")

# ===================== FS & LOG =====================
os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("snies")

# ===================== HELPERS =====================
def setup_driver(headless: bool = False, download_dir: str = DATA_RAW_DIR):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1366,900")
    opts.add_argument("--lang=es-ES")

    abs_raw = os.path.abspath(download_dir)
    prefs = {
        "download.default_directory": abs_raw,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "safebrowsing.disable_download_protection": True,
    }
    opts.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    d = webdriver.Chrome(service=service, options=opts)
    d.set_page_load_timeout(60)
    d.implicitly_wait(8)
    return d

def make_absolute(base: str, url: str) -> str:
    return url if urlparse(url).netloc else urljoin(base, url)

def strip_accents(s: str) -> str:
    return (s.replace("á","a").replace("é","e").replace("í","i")
             .replace("ó","o").replace("ú","u").replace("ñ","n"))

def normalize_category(text: str) -> str | None:
    norm = strip_accents((text or "").lower())
    import re as _re
    for cat, pat in CATEGORY_PATTERNS_ORDERED:
        if _re.search(pat, norm, _re.IGNORECASE):
            return cat
    return None

def extract_year(text_or_url: str):
    import re as _re
    m = _re.search(YEAR_REGEX, text_or_url or "")
    if not m: return None
    y = int(m.group(1))
    return y if y in VALID_YEARS else None

def dismiss_cookies(driver):
    try:
        for tag in ["button","a"]:
            for el in driver.find_elements(By.TAG_NAME, tag):
                txt = (el.text or "").strip().lower()
                if any(k in txt for k in ["acept", "entendido", "cerrar", "de acuerdo"]):
                    try: el.click(); time.sleep(0.5); return
                    except: pass
    except: pass

def set_page_size_max(driver):
    try:
        for s in driver.find_elements(By.TAG_NAME, "select"):
            try: sel = Select(s)
            except Exception: continue
            for v in ("100", "50", "25"):
                try: sel.select_by_value(v); time.sleep(1); return
                except Exception: pass
                try: sel.select_by_visible_text(v); time.sleep(1); return
                except Exception: pass
    except Exception as e:
        logger.debug(f"No se pudo cambiar el page size: {e}")

def canonical_url_key(u: str) -> str:
    """Clave canónica: esquema+host+path (sin query/fragment) en minúsculas."""
    p = urlparse(u)
    return f"{(p.scheme or 'https').lower()}://{p.netloc.lower()}{p.path}".lower()

# ========== SCRAPE LISTA ==========
def collect_rows_from_pagination(driver, page_url: str) -> list[dict]:
    driver.get(page_url); time.sleep(1); dismiss_cookies(driver); set_page_size_max(driver); time.sleep(0.6)

    all_rows, seen_pages = [], 0
    while True:
        seen_pages += 1
        trs = driver.find_elements(By.CSS_SELECTOR, "table tbody tr, .table tbody tr")
        for tr in trs:
            tds = tr.find_elements(By.CSS_SELECTOR, "td")
            if len(tds) < 2: continue
            year_txt = (tds[0].text or "").strip()
            perfil_txt = (tds[1].text or "").strip()
            href = None
            try: href = tds[1].find_element(By.CSS_SELECTOR, "a[href]").get_attribute("href")
            except: pass
            if not href: continue
            year = extract_year(year_txt) or extract_year(perfil_txt) or extract_year(href)
            cat  = normalize_category(perfil_txt) or normalize_category(href)
            all_rows.append({
                "abs_url": make_absolute(page_url, href),
                "text": perfil_txt, "category": cat, "year": year,
                "source_page": page_url,
            })

        next_btns = driver.find_elements(By.XPATH, "//a[contains(., 'Siguiente') and not(contains(@class,'disabled'))]")
        if not next_btns:
            next_btns = driver.find_elements(By.XPATH, "//li[contains(@class,'next')]/a[not(contains(@class,'disabled'))]")
        if not next_btns or seen_pages > 200: break
        try: next_btns[0].click(); time.sleep(1.0)
        except: break

    uniq, seen = [], set()
    for it in all_rows:
        u = it["abs_url"]
        if u in seen: continue
        seen.add(u); uniq.append(it)
    return uniq

# ========== ENLACES DE DESCARGA ==========
def collect_download_links(driver, page_url: str) -> list[dict]:
    driver.get(page_url); time.sleep(1); dismiss_cookies(driver)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);"); time.sleep(0.6)
    selector = ', '.join([f'a[href*="{ext}"]' for ext in VALID_EXTS])
    items = []
    for a in driver.find_elements(By.CSS_SELECTOR, selector):
        href = a.get_attribute("href")
        txt = (a.text or a.get_attribute("title") or "").strip()
        if href:
            items.append({"abs_url": make_absolute(page_url, href), "text": txt})
    return items

def choose_best_link(links: list[dict]) -> dict | None:
    if not links: return None
    def rank(u: str):
        p = urlparse(u).path.lower()
        for i, ext in enumerate(PREF_EXT_ORDER):
            if p.endswith(ext): return i
        return len(PREF_EXT_ORDER)
    return sorted(links, key=lambda d: rank(d["abs_url"]))[0]

def filter_links_by_year(links: list[dict], year: int) -> list[dict]:
    y = str(year)
    keep = []
    for d in links:
        txt = (d.get("text") or "").lower()
        url = d["abs_url"].lower()
        if y in txt or y in url:
            keep.append(d)
    return keep

# ========== NOMBRES Y DESCARGA ==========
def _guess_ext_from_headers(headers: dict, url_path: str) -> tuple[str, str]:
    cd = headers.get("content-disposition", "") or headers.get("Content-Disposition", "")
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd)
    fname = ""
    if m:
        fname = os.path.basename(m.group(1))
        ext = os.path.splitext(fname)[1].lower()
        if ext: return ext, fname
    ct = (headers.get("content-type") or "").lower()
    if "spreadsheetml" in ct or "excel" in ct:  return (".xlsx" if "spreadsheetml" in ct else ".xls"), fname
    if "csv" in ct:  return ".csv", fname
    if "zip" in ct:  return ".zip", fname
    if "vnd.ms-excel.sheet.binary.macroenabled" in ct: return ".xlsb", fname
    ext = os.path.splitext(url_path)[1].lower()
    return (ext or ".xlsx"), fname

def year_from_filename(name: str | None) -> int | None:
    if not name: return None
    m = re.search(YEAR_REGEX, name)
    if not m: return None
    y = int(m.group(1))
    return y if y in VALID_YEARS else None

def sanitize_for_windows(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]+', ' ', name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

def decide_final_filename(header_fname: str, url: str, used_ext: str) -> str:
    name = header_fname or os.path.basename(urlparse(url).path) or "download"
    if not os.path.splitext(name)[1]:
        name = f"{name}{used_ext or '.xlsx'}"
    return sanitize_for_windows(name)

def requests_session_from_driver(driver):
    sess = requests.Session()
    for c in driver.get_cookies():
        dom = c.get("domain") or ""
        if "snies.mineducacion.gov.co" in dom:
            sess.cookies.set(c["name"], c["value"], domain=dom, path=c.get("path", "/"))
    sess.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari"})
    return sess

def probe_server_filename(url: str, session: requests.Session) -> tuple[str, str]:
    """Intenta obtener nombre y extensión con HEAD (sin descargar)."""
    try:
        r = session.head(url, allow_redirects=True, timeout=30)
        if r.status_code == 200:
            ext, fname = _guess_ext_from_headers(r.headers, urlparse(url).path)
            return decide_final_filename(fname, url, ext), fname
    except Exception:
        pass
    # Fallback: derivar del path
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower() or ".xlsx"
    base = os.path.basename(path) or "download"
    return decide_final_filename(base, url, ext), base

def download_file_to_raw(url: str, raw_dir: str, session: requests.Session, retries: int = 3, sleep_s: float = 1.5):
    """
    Descarga directamente a /raw. Si el nombre final ya existe, SALTA como duplicado.
    Devuelve: (status, final_path, used_ext, header_fname)
    status ∈ {"ok","skipped_exists","error"}
    """
    url_path = urlparse(url).path
    # Pre-chequeo de nombre para saltar duplicados por nombre
    final_fname_guess, _ = probe_server_filename(url, session)
    candidate_path = os.path.join(raw_dir, final_fname_guess)
    if os.path.exists(candidate_path):
        return "skipped_exists", candidate_path, "", ""

    for i in range(retries):
        try:
            with session.get(url, stream=True, timeout=60) as r:
                if r.status_code != 200:
                    logger.warning(f"GET {url} -> {r.status_code}")
                    time.sleep(sleep_s); continue

                used_ext, header_fname = _guess_ext_from_headers(r.headers, url_path)
                final_fname = decide_final_filename(header_fname, url, used_ext)
                final_path = os.path.join(raw_dir, final_fname)

                # Chequeo final: si existe, saltar
                if os.path.exists(final_path):
                    return "skipped_exists", final_path, used_ext, header_fname

                total = int(r.headers.get("content-length", 0))
                with open(final_path, "wb") as f, tqdm(total=total or None, unit="B",
                                                       unit_scale=True, desc=final_fname, leave=False) as pbar:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                            if total: pbar.update(len(chunk))
            return "ok", final_path, used_ext, header_fname
        except Exception as e:
            logger.warning(f"Intento {i+1}/{retries} falló para {url}: {e}")
            time.sleep(sleep_s*(i+1))
    return "error", "", "", ""

# ===================== MAIN =====================
def run():
    start = time.time()
    manifest_rows = []
    driver = setup_driver(headless=False, download_dir=DATA_RAW_DIR)

    try:
        rows = collect_rows_from_pagination(driver, START_URL)

        # ---- Un trabajo por URL canónica única ----
        jobs = []
        seen_url_keys = set()

        for r in rows:
            year = r.get("year")
            if not (isinstance(year, int) and year in VALID_YEARS):
                continue

            links_all = collect_download_links(driver, r["abs_url"])
            links_y   = filter_links_by_year(links_all, year)
            links     = links_y if links_y else links_all

            best = choose_best_link(links) if links else None
            if not best:
                logger.warning(f"Sin links en {r['abs_url']} ({r['text']}) año {year}")
                continue

            url = best["abs_url"]
            key = canonical_url_key(url)
            if key in seen_url_keys:
                continue
            seen_url_keys.add(key)

            cat = r.get("category") or normalize_category(best.get("text","")) or normalize_category(url) or "Desconocido"

            jobs.append({
                "download_url": url,
                "text": r["text"],
                "category": cat,
                "year": year,
                "source_page": r["abs_url"]
            })

        # Sesión con cookies del navegador
        sess = requests_session_from_driver(driver)

        # Descargar (SIN renombrar) directo a /raw con desduplicación por nombre
        for job in jobs:
            url = job["download_url"]; text = job["text"]; cat = job["category"]; year = job["year"]; src = job["source_page"]

            status, final_path, used_ext, header_fname = download_file_to_raw(url, DATA_RAW_DIR, session=sess)

            # Validación suave de año (solo si descargó ok)
            if status == "ok":
                header_year = year_from_filename(header_fname)
                if header_year is not None and header_year != year:
                    try: os.remove(final_path)
                    except: pass
                    status = f"skipped_year_mismatch_header({header_year}!={year})"
                    final_path = ""

            manifest_rows.append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "category": cat, "year": year, "source_page": src,
                "link_text": text, "download_url": url,
                "local_path": final_path, "status": status
            })

        pd.DataFrame(manifest_rows).to_csv(MANIFEST_PATH, index=False, quoting=csv.QUOTE_MINIMAL)
        logger.info(f"Manifest guardado en {MANIFEST_PATH}")

        # Log informativo: qué faltó por año
        from collections import defaultdict
        got = defaultdict(set)
        for m in manifest_rows:
            if m["status"]=="ok" and isinstance(m["year"], int):
                got[m["year"]].add(m["category"])
        for y in sorted(set([r["year"] for r in rows if isinstance(r["year"], int) and r["year"] in VALID_YEARS])):
            miss = set(DISPLAY_LABELS) - got.get(y, set())
            if miss:
                logger.warning(f"Año {y}: faltan {sorted(miss)}")

    finally:
        try: driver.quit()
        except: pass

    elapsed = time.time() - start
    print(f"Listo. Registros procesados: {len(manifest_rows)} | Tiempo: {elapsed/60:.1f} min")
    print(f"Inventario: {MANIFEST_PATH}")
    print(f"Log:        {LOG_PATH}")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.exception("Fallo no controlado")
        print(f"ERROR: {e}", file=sys.stderr); sys.exit(1)
