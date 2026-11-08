import streamlit as st
from datetime import datetime
import urllib.parse
import re
import difflib

st.set_page_config(
    page_title="NOSTRA GOURMET - Inventario",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        .main-title { color: #6b001a; text-align: center; font-size: 22px; font-weight: 800; text-transform: uppercase; margin-bottom: 0px; }
        .sub-title { text-align: center; color: #4b5563; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 15px; }
        .stButton>button { width: 100%; background-color: #6b001a; color: white; font-weight: bold; border-radius: 8px; padding: 10px; text-transform: uppercase; }
        .stButton>button:hover { background-color: #420010; color: white; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">NOSTRA GOURMET</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Inventario y Control de Visitas</p>', unsafe_allow_html=True)

# ----------------------------------------------------
# 1. ESTADO DE SESIÓN Y LISTADOS BASE
# ----------------------------------------------------
if 'productos_base' not in st.session_state:
    st.session_state.productos_base = [
        "Queso Grana Padano", "Queso Parmigiano", "Queso azúl", "Queso Trufa", "Queso Manchego",
        "Queso Ruffino", "Queso Romero", "Mortadela Trufa", "Queso en aceite", "Prosciutto",
        "Tris", "Salame", "Coppa", "Salame Pepperoni", "Chorizo de León Picante",
        "Jamon Cebo Ibérico", "Jamon Serrano Reserva", "Pieza Coppa Di Parma", "Pieza Guanciale",
        "Pieza Mortadela", "Pieza Mortadela Pistacho", "Pieza Prosciutto", "Pieza Salame",
        "Salametto", "Pieza Jamon Serrano Rodriguez", "Pieza Queso Padano", "Pieza Queso Parmigiano"
    ]

if 'clientes_lista' not in st.session_state:
    st.session_state.clientes_lista = [
        "-- Seleccionar Cliente --", "MANUAL",
        "Automercado El Hato", "Balys (todo en uno)", "BARAKI CIRCULO MILITAR", "BARAKI CIRCULO MILITAR MARACAY", 
        "BARAKI EL VIÑEDO", "Bodegón 2 Doce valencia", "CATANIA PATIO TRIGAL", "COFFE MARKET", 
        "CORNER", "CRAKOS", "DELIPLAZA", "DISTRIBUDORA LA VALENCIANA", "EUROMERCADO", 
        "FRIGORÍFICO BETOLI", "FRIGORIFICO HENRIQUEZ", "Frigorifico Tucacas", "JEQUE MARKET", 
        "KALEA LA GRANJA", "KALEA TRIGALEÑA", "KALEA VALLES DE CAMORUCO", "King Fish C.A", 
        "KOZMOS EL PARRAL", "KOZMOS NISPEROS", "Kromi Guataparo", "KROMI MAÑONGO", 
        "KROMI PREBO III", "KROMI TRIGAL NORTE", "LA BOTTEGA", "LA CATANIA ISABELICA", 
        "LA MANSION DE NEW YORK", "LA MANSION DE VICTOR", "LA MANSION DEL PAN", "LA PUNTA STEAK", 
        "LA PUNTAEL VIÑEDO", "LA VICTORIANA", "Luxor El Bosque", "LUXOR CIRCULO MILITAR MARACAY", 
        "LUXOR EL CASTAÑO", "LUXOR EUROMAX PLUS", "LUXOR IPFSA", "LUXOR LA MORITA", 
        "LUXOR NAGUANAGUA", "MAPKET", "MERCACHEVERE", "MI PEQUEÑA MANSION", "Panadería Santa Cecilia"
    ]

if 'inv_anterior_map' not in st.session_state:
    st.session_state.inv_anterior_map = {}

if 'local_storage_db' not in st.session_state:
    st.session_state.local_storage_db = {}

# ----------------------------------------------------
# 2. CONEXIÓN SEGURA Y LIMPIEZA DE CREDENCIALES (PEM)
# ----------------------------------------------------
def get_gcp_creds():
    """Limpia y repara automáticamente los saltos de línea y comillas de la llave privada"""
    try:
        if "gcp_service_account" in st.secrets:
            creds = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds:
                pk = str(creds["private_key"]).strip()
                if (pk.startswith('"') and pk.endswith('"')) or (pk.startswith("'") and pk.endswith("'")):
                    pk = pk[1:-1].strip()
                pk = pk.replace("\\n", "\n")
                creds["private_key"] = pk
            return creds
    except Exception as e:
        st.sidebar.error(f"Error credenciales: {e}")
    return None

def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower().strip()
    replacements = (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ü", "u"))
    for a, b in replacements:
        texto = texto.replace(a, b)
    return re.sub(r'[^a-z0-9]', '', texto)

def consultar_inv_cascada(cliente_nombre):
    if not cliente_nombre or cliente_nombre in ["-- Seleccionar Cliente --", "MANUAL"]:
        return {}
    
    cliente_target = cliente_nombre.strip().lower()
    mapa_res = {}
    creds = get_gcp_creds()

    # 1º PASO: GOOGLE SHEETS
    try:
        if creds:
            import gspread
            gc = gspread.service_account_from_dict(creds)
            sh = gc.open("INVENTARIO NOSTRA GOURMET")
            sheet = sh.worksheet("Hoja 1")
            rows = sheet.get_all_values()

            for i in range(len(rows) - 1, 0, -1):
                fila = rows[i]
                c_nom = (fila[1] if len(fila) > 1 else "").strip().lower()
                if c_nom == cliente_target:
                    col_p = fila[2] if len(fila) > 2 else ""
                    col_c = fila[3] if len(fila) > 3 else ""

                    arr_p = col_p.split('\n')
                    arr_c = col_c.split('\n')
                    for j in range(len(arr_p)):
                        p_item = arr_p[j].strip()
                        c_item = arr_c[j].strip() if j < len(arr_c) else "0"
                        if p_item and p_item not in mapa_res:
                            mapa_res[p_item] = c_item
                    if len(mapa_res) > 0:
                        return mapa_res
    except Exception as e:
        pass

    # 2º PASO: FIREBASE FIRESTORE
    try:
        if creds:
            import firebase_admin
            from firebase_admin import credentials, firestore
            if not firebase_admin._apps:
                cred = credentials.Certificate(creds)
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            doc_ref = db.collection("inventarios").document(cliente_target).get()
            if doc_ref.exists:
                data_fs = doc_ref.to_dict()
                if "ultimoInventario" in data_fs:
                    return data_fs["ultimoInventario"]
    except Exception as e:
        pass

    # 3º PASO: MEMORIA LOCAL
    if cliente_target in st.session_state.local_storage_db:
        return st.session_state.local_storage_db[cliente_target]

    return mapa_res

def guardar_registros(datos):
    cliente_key = datos['cliente'].strip().lower()
    creds = get_gcp_creds()
    
    # Memoria Local
    mapa_local = {}
    prods = datos['colProductos'].split('\n')
    cants = datos['colCantidades'].split('\n')
    for i in range(len(prods)):
        if prods[i]:
            mapa_local[prods[i]] = cants[i] if i < len(cants) else "0"
    st.session_state.local_storage_db[cliente_key] = mapa_local

    # Google Sheets (Columnas A-G)
    try:
        if creds:
            import gspread
            gc = gspread.service_account_from_dict(creds)
            sh = gc.open("INVENTARIO NOSTRA GOURMET")
            sheet = sh.worksheet("Hoja 1")
            sheet.append_row([
                datos['fechaHora'],      # Col A
                datos['cliente'],        # Col B
                datos['colProductos'],   # Col C
                datos['colCantidades'],  # Col D
                datos['colVencimientos'],# Col E
                datos['colDespachos'],   # Col F
                ""                       # Col G (nota)
            ])
    except Exception as e:
        st.error(f"Error Google Sheets: {e}")

    # Firebase Firestore
    try:
        if creds:
            import firebase_admin
            from firebase_admin import credentials, firestore
            if not firebase_admin._apps:
                cred = credentials.Certificate(creds)
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            db.collection("inventarios").document(cliente_key).set({
                "ultimoInventario": mapa_local,
                "ultimaActualizacion": datos['fechaHora']
            }, merge=True)
    except Exception as e:
        st.error(f"Error Firebase: {e}")

# ----------------------------------------------------
# 3. INTERFAZ DE CLIENTES Y FECHA
# ----------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    fecha_val = st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%y"))
with col2:
    hora_val = st.text_input("Hora", value=datetime.now().strftime("%H:%M"))

def al_cambiar_cliente():
    sel = st.session_state.cliente_select_key
    if sel and sel != "-- Seleccionar Cliente --":
        st.session_state.inv_anterior_map = consultar_inv_cascada(sel)

cliente_sel = st.selectbox(
    "Cliente / Establecimiento",
    st.session_state.clientes_lista,
    key="cliente_select_key",
    on_change=al_cambiar_cliente
)

cliente_final = cliente_sel
if cliente_sel == "MANUAL":
    cli_manual = st.text_input("Nombre del Nuevo Cliente")
    if cli_manual:
        cliente_final = cli_manual.strip()
        if cliente_final not in st.session_state.clientes_lista:
            st.session_state.clientes_lista.insert(2, cliente_final)

st.divider()

# ----------------------------------------------------
# 4. CARGA RÁPIDA (PEGAR TEXTO ROBUSTA)
# ----------------------------------------------------
with st.expander("⚡ CARGA RÁPIDA (PEGAR TEXTO)"):
    texto_pasted = st.text_area("Pega aquí el inventario. Ej:\nQueso Grana Padano : 100\nQueso Parmigiano : 1777\nQueso azúl: 5")
    
    if st.button("📥 CARGAR DATOS EN LA TABLA"):
        base_norm_map = {normalizar(p): idx for idx, p in enumerate(st.session_state.productos_base)}
        cargados = 0
        
        for linea in texto_pasted.split('\n'):
            linea_str = linea.strip()
            if not linea_str:
                continue
            
            p_nombre, p_resto = "", ""
            if ':' in linea_str:
