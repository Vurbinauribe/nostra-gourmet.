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

# GESTIÓN SEGURA DEL REINICIO (Evita el error de widgets instanciados)
if st.session_state.get('trigger_reset', False):
    for idx in range(len(st.session_state.productos_base)):
        st.session_state.pop(f"cant_p_{idx}", None)
        st.session_state.pop(f"venc_p_{idx}", None)
        st.session_state.pop(f"desp_p_{idx}", None)
    for i in range(1, 6):
        st.session_state.pop(f"custom_prod_{i}", None)
        st.session_state.pop(f"custom_cant_{i}", None)
        st.session_state.pop(f"custom_venc_{i}", None)
        st.session_state.pop(f"custom_desp_{i}", None)
    st.session_state.inv_anterior_map = {}
    st.session_state.trigger_reset = False

# ----------------------------------------------------
# 2. NORMALIZACIÓN Y BÚSQUEDA EN CASCADA
# ----------------------------------------------------
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

    # 1º PASO: GOOGLE SHEETS
    try:
        if "gcp_service_account" in st.secrets:
            import gspread
            gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
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
        if "gcp_service_account" in st.secrets or "firebase" in st.secrets:
            import firebase_admin
            from firebase_admin import credentials, firestore
            if not firebase_admin._apps:
                cred_dict = dict(st.secrets.get("firebase", st.secrets.get("gcp_service_account")))
                cred = credentials.Certificate(cred_dict)
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
        if "gcp_service_account" in st.secrets:
            import gspread
            gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
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
        if "gcp_service_account" in st.secrets or "firebase" in st.secrets:
            import firebase_admin
            from firebase_admin import credentials, firestore
            if not firebase_admin._apps:
                cred_dict = dict(st.secrets.get("firebase", st.secrets.get("gcp_service_account")))
                cred = credentials.Certificate(cred_dict)
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
                partes = linea_str.split(':', 1)
                p_nombre = partes[0].strip()
                p_resto = partes[1].strip()
            else:
                m = re.match(r'^([^\d]+)\s+(\d+.*)$', linea_str)
                if m:
                    p_nombre = m.group(1).strip()
                    p_resto = m.group(2).strip()
            
            if p_nombre and p_resto:
                match_venc = re.search(r'\((.*?)\)', p_resto)
                venc_val = match_venc.group(1).strip() if match_venc else ""
                cant_str = re.sub(r'\(.*?\)', '', p_resto).strip()
                
                if cant_str.isdigit():
                    cant_num = int(cant_str)
                    norm_input = normalizar(p_nombre)
                    
                    target_idx = None
                    if norm_input in base_norm_map:
                        target_idx = base_norm_map[norm_input]
                    else:
                        for n_key, idx in base_norm_map.items():
                            if n_key in norm_input or norm_input in n_key:
                                target_idx = idx
                                break
                    
                    if target_idx is not None:
                        st.session_state[f"cant_p_{target_idx}"] = cant_num
                        st.session_state[f"venc_p_{target_idx}"] = venc_val
                        cargados += 1
                    else:
                        nuevo_p = p_nombre.strip().title()
                        if nuevo_p not in st.session_state.productos_base:
                            st.session_state.productos_base.append(nuevo_p)
                            n_idx = len(st.session_state.productos_base) - 1
                            st.session_state[f"cant_p_{n_idx}"] = cant_num
                            st.session_state[f"venc_p_{n_idx}"] = venc_val
                            cargados += 1

        st.success(f"¡Cargados {cargados} productos a la tabla!")
        st.rerun()

# ----------------------------------------------------
# 5. TABLA DE PRODUCTOS
# ----------------------------------------------------
st.markdown("### 📋 Tabla de Productos")

h1, h2, h3, h4, h5 = st.columns([2.2, 0.9, 1.3, 0.8, 0.8])
h1.markdown("**PRODUCTO**")
h2.markdown("**CANT.**")
h3.markdown("**F. VENC**")
h4.markdown("**DESP.**")
h5.markdown("**ANT.**")

inventario_ingresado = {}

for idx, prod in enumerate(st.session_state.productos_base):
    val_ant = st.session_state.inv_anterior_map.get(prod, "-")
    
    c = st.columns([2.2, 0.9, 1.3, 0.8, 0.8])
    with c[0]:
        st.write(prod)
    with c[1]:
        cant = st.number_input(f"c_{idx}", min_value=0, key=f"cant_p_{idx}", label_visibility="collapsed")
    with c[2]:
        venc = st.text_input(f"v_{idx}", placeholder="dd/mm/aa", key=f"venc_p_{idx}", label_visibility="collapsed")
    with c[3]:
        desp = st.number_input(f"d_{idx}", min_value=0, key=f"desp_p_{idx}", label_visibility="collapsed")
    with c[4]:
        st.markdown(f"<div style='text-align: center; background: #f1f5f9; padding: 4px; border-radius: 4px; color: #64748b; font-size: 12px;'>{val_ant}</div>", unsafe_allow_html=True)
    
    if cant > 0 or desp > 0:
        inventario_ingresado[prod] = {"cantidad": cant, "vencimiento": venc, "despacho": desp}

st.markdown("---")
st.markdown("### ➕ Productos Libres Adicionales")
custom_inventario = {}
for i in range(1, 6):
    cc = st.columns([2.2, 0.9, 1.3, 0.8, 0.8])
    with cc[0]:
        c_prod = st.text_input(f"P {i}", placeholder=f"+ Producto {i}", key=f"custom_prod_{i}", label_visibility="collapsed")
    with cc[1]:
        c_cant = st.number_input(f"C {i}", min_value=0, key=f"custom_cant_{i}", label_visibility="collapsed")
    with cc[2]:
        c_venc = st.text_input(f"V {i}", placeholder="dd/mm/aa", key=f"custom_venc_{i}", label_visibility="collapsed")
    with cc[3]:
        c_desp = st.number_input(f"D {i}", min_value=0, key=f"custom_desp_{i}", label_visibility="collapsed")
    with cc[4]:
        st.markdown("<div style='text-align: center; background: #f1f5f9; padding: 4px; border-radius: 4px; color: #64748b; font-size: 12px;'>-</div>", unsafe_allow_html=True)
        
    if c_prod.strip() != "" and c_cant > 0:
        custom_inventario[c_prod.strip()] = {"cantidad": c_cant, "vencimiento": c_venc, "despacho": c_desp}

st.divider()

# ----------------------------------------------------
# 6. ACCIÓN DE ENVÍO, WHATSAPP Y REINICIO MANUAL
# ----------------------------------------------------
if st.button("📲 GENERAR Y GUARDAR REPORTE"):
    if not cliente_final or cliente_final == "-- Seleccionar Cliente --":
        st.error("Por favor seleccione un cliente válido.")
    elif not inventario_ingresado and not custom_inventario:
        st.error("No hay productos cargados en el inventario.")
    else:
        todo_inv = {**inventario_ingresado, **custom_inventario}
        
        prods_l, cants_l, vencs_l, desps_l = [], [], [], []
        lineas_wa = [f"{cliente_final}", f"{fecha_val} {hora_val}", "Inventario", "", "PRODUCTO", ""]
        
        for p, info in todo_inv.items():
            l = f"{p}  {info['cantidad']}"
            if info['vencimiento']:
                l += f" ({info['vencimiento']})"
            lineas_wa.append(l)
            
            prods_l.append(p)
            cants_l.append(str(info['cantidad']))
            vencs_l.append(info['vencimiento'] if info['vencimiento'] else "-")
            desps_l.append(str(info['despacho']))
            
        mensaje_wa = "\n".join(lineas_wa)
        
        # Guardar en Sheets y Firebase inmediatamente
        payload = {
            "fechaHora": f"{fecha_val} {hora_val}",
            "cliente": cliente_final,
            "colProductos": "\n".join(prods_l),
            "colCantidades": "\n".join(cants_l),
            "colVencimientos": "\n".join(vencs_l),
            "colDespachos": "\n".join(desps_l)
        }
        guardar_registros(payload)
        
        st.success("¡Reporte generado y guardado en la base de datos!")
        st.text_area("Vista previa WhatsApp:", mensaje_wa, height=140)
        
        url_wa = "https://api.whatsapp.com/send?phone=584244527538&text=" + urllib.parse.quote(mensaje_wa)
        
        # Botón de WhatsApp fijo
        st.markdown(f'''
            <a href="{url_wa}" target="_blank">
                <button style="width: 100%; background-color: #25D366; color: white; padding: 14px; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; text-transform: uppercase; margin-bottom: 10px;">
                    💬 ABRIR WHATSAPP CON EL REPORTE
                </button>
            </a>
        ''', unsafe_allow_html=True)

# Botón independiente para limpiar y vaciar la tabla para una nueva visita
if st.button("🔄 NUEVA VISITA / LIMPIAR FORMULARIO"):
    st.session_state.trigger_reset = True
    st.rerun()
