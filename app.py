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

# Estilos corporativos limpios y legibles
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
# 1. LISTADOS BASE
# ----------------------------------------------------
if 'clientes_lista' not in st.session_state:
    st.session_state.clientes_lista = [
        "-- Seleccionar Cliente --", "MANUAL",
        "Balys (todo en uno)", "BARAKI CIRCULO MILITAR", "BARAKI CIRCULO MILITAR MARACAY", 
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

if 'productos_base' not in st.session_state:
    st.session_state.productos_base = [
        "Queso Grana Padano", "Queso Parmigiano", "Queso azúl", "Queso Trufa", "Queso Manchego",
        "Queso Ruffino", "Queso Romero", "Mortadela Trufa", "Queso en aceite", "Prosciutto",
        "Tris", "Salame", "Coppa", "Salame Pepperoni", "Chorizo de León Picante",
        "Jamon Cebo Ibérico", "Jamon Serrano Reserva", "Pieza Coppa Di Parma", "Pieza Guanciale",
        "Pieza Mortadela", "Pieza Mortadela Pistacho", "Pieza Prosciutto", "Pieza Salame",
        "Salametto", "Pieza Jamon Serrano Rodriguez", "Pieza Queso Padano", "Pieza Queso Parmigiano"
    ]

# Inicializar inventario anterior en estado
if 'inv_anterior_map' not in st.session_state:
    st.session_state.inv_anterior_map = {}

# ----------------------------------------------------
# 2. FUNCIONES DE CONEXIÓN A GOOGLE SHEETS / FIRESTORE
# ----------------------------------------------------
def consultar_ultimo_inventario_sheets(nombre_cliente):
    """Consulta directa a la base de datos en Google Sheets / Firestore"""
    mapa_anterior = {}
    if not nombre_cliente or nombre_cliente == "-- Seleccionar Cliente --":
        return mapa_anterior

    try:
        if "gcp_service_account" in st.secrets:
            import gspread
            gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
            # Nombre exacto de tu hoja o ID de Spreadsheet
            sh = gc.open("NostraGourmetDB") 
            sheet = sh.sheet1
            data = sheet.get_all_values()
            
            cliente_buscado = nombre_cliente.strip().lower()
            
            # Recorrer de abajo hacia arriba (igual que en GAS)
            for i in range(len(data) - 1, 0, -1):
                fila = data[i]
                cliente_fila = (fila[1] if len(fila) > 1 and fila[1] else "") or (fila[2] if len(fila) > 2 and fila[2] else "")
                
                if cliente_fila.strip().lower() == cliente_buscado:
                    col_c = fila[2] if len(fila) > 2 else ""
                    col_d = fila[3] if len(fila) > 3 else ""
                    
                    # Formato Nuevo (Col C prods, Col D cants)
                    if ':' not in col_c and col_d != "":
                        arr_p = col_c.split('\n')
                        arr_c = col_d.split('\n')
                        for j in range(len(arr_p)):
                            p_nom = arr_p[j].strip()
                            p_cant = arr_c[j].strip() if j < len(arr_c) else "0"
                            if p_nom and p_nom not in mapa_anterior:
                                mapa_anterior[p_nom] = p_cant
                    # Formato Viejo (Texto condensado con :)
                    else:
                        lineas = col_c.split('\n') if ':' in col_c else col_d.split('\n')
                        for lin in lineas:
                            if ':' in lin:
                                p_partes = lin.split(':')
                                prod = p_partes[0].strip()
                                cant_b = p_partes[1].strip()
                                cant_l = cant_b.split('(')[0].strip()
                                if prod and prod not in mapa_anterior:
                                    mapa_anterior[prod] = cant_l
                    if len(mapa_anterior) > 0:
                        break
    except Exception as e:
        print("Aviso al consultar base de datos:", e)
        
    return mapa_anterior

def guardar_visita_sheets_firestore(datos):
    """Guarda los datos en Google Sheets y Firestore al presionar el botón"""
    try:
        if "gcp_service_account" in st.secrets:
            import gspread
            gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
            sh = gc.open("NostraGourmetDB")
            sheet = sh.sheet1
            
            sheet.append_row([
                datos['fechaHora'],
                datos['cliente'],
                datos['colProductos'],
                datos['colCantidades'],
                datos['colVencimientos'],
                datos['colDespachos']
            ])
            st.toast("✅ ¡Registrado con éxito en Google Sheets!", icon="📊")
    except Exception as e:
        st.warning(f"Reporte generado localmente. (Para guardar en Sheets en vivo, configura st.secrets). Error: {e}")

# ----------------------------------------------------
# 3. CONTROLES Y SELECCIÓN DE CLIENTE
# ----------------------------------------------------
col_f1, col_f2 = st.columns(2)
with col_f1:
    fecha_val = st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%y"))
with col_f2:
    hora_val = st.text_input("Hora", value=datetime.now().strftime("%H:%M"))

def al_cambiar_cliente():
    cliente_sel = st.session_state.cliente_select_key
    if cliente_sel and cliente_sel != "-- Seleccionar Cliente --" and cliente_sel != "MANUAL":
        st.session_state.inv_anterior_map = consultar_ultimo_inventario_sheets(cliente_sel)

cliente_sel = st.selectbox(
    "Cliente / Establecimiento", 
    st.session_state.clientes_lista,
    key="cliente_select_key",
    on_change=al_cambiar_cliente
)

cliente_final = cliente_sel
if cliente_sel == "MANUAL":
    nuevo_cli = st.text_input("Nombre del Nuevo Cliente")
    if nuevo_cli:
        cliente_final = nuevo_cli.strip()
        if cliente_final not in st.session_state.clientes_lista:
            st.session_state.clientes_lista.insert(2, cliente_final)

st.divider()

# ----------------------------------------------------
# 4. CARGA RÁPIDA (PEGAR TEXTO CORREGIDO)
# ----------------------------------------------------
with st.expander("⚡ CARGA RÁPIDA (PEGAR TEXTO)"):
    texto_pasted = st.text_area("Pega aquí el inventario. Ej:\nQueso Grana Padano: 8\nProsciutto: 30 (12/10/26)")
    
    if st.button("📥 Cargar Datos en la Tabla"):
        base_low = {p.lower(): i for i, p in enumerate(st.session_state.productos_base)}
        cargados_count = 0
        
        for linea in texto_pasted.split('\n'):
            if ':' in linea:
                partes = linea.split(':')
                p_nombre = partes[0].strip()
                p_resto = partes[1].strip()
                
                match_venc = re.search(r'\((.*?)\)', p_resto)
                venc_val = match_venc.group(1) if match_venc else ""
                cant_val = re.sub(r'\(.*?\)', '', p_resto).strip()
                
                if cant_val.isdigit():
                    cant_num = int(cant_val)
                    p_norm = p_nombre.lower()
                    
                    # Buscar coincidencia en productos base
                    found_idx = None
                    for pb_low, idx in base_low.items():
                        if p_norm in pb_low or pb_low in p_norm:
                            found_idx = idx
                            break
                    
                    if found_idx is None:
                        matches = difflib.get_close_matches(p_norm, list(base_low.keys()), n=1, cutoff=0.4)
                        if matches:
                            found_idx = base_low[matches[0]]
                    
                    # Asignar directamente a las llaves de los inputs en Streamlit
                    if found_idx is not None:
                        st.session_state[f"cant_p_{found_idx}"] = cant_num
                        st.session_state[f"venc_p_{found_idx}"] = venc_val
                        cargados_count += 1
                    else:
                        # Si es producto nuevo, agregarlo a productos base
                        nuevo_p_name = p_nombre.capitalize()
                        if nuevo_p_name not in st.session_state.productos_base:
                            st.session_state.productos_base.append(nuevo_p_name)
                            n_idx = len(st.session_state.productos_base) - 1
                            st.session_state[f"cant_p_{n_idx}"] = cant_num
                            st.session_state[f"venc_p_{n_idx}"] = venc_val
                            cargados_count += 1

        st.success(f"¡Se cargaron {cargados_count} productos directamente en la tabla!")
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
# 6. ACCIÓN GENERAL: GENERAR, GUARDAR Y WHATSAPP
# ----------------------------------------------------
if st.button("📲 Generar Vista Previa y Guardar"):
    if not cliente_final or cliente_final == "-- Seleccionar Cliente --":
        st.error("Por favor seleccione un cliente válido.")
    elif not inventario_ingresado and not custom_inventario:
        st.error("No hay productos con inventario para reportar.")
    else:
        lineas_wa = [f"{cliente_final}", f"{fecha_val} {hora_val}", "Inventario", "", "PRODUCTO", ""]
        todo_inventario = {**inventario_ingresado, **custom_inventario}
        
        prods_list, cants_list, vencs_list, desps_list = [], [], [], []
        
        for prod, info in todo_inventario.items():
            linea = f"{prod}  {info['cantidad']}"
            if info['vencimiento']:
                linea += f" ({info['vencimiento']})"
            lineas_wa.append(linea)
            
            prods_list.append(prod)
            cants_list.append(str(info['cantidad']))
            vencs_list.append(info['vencimiento'] if info['vencimiento'] else "-")
            desps_list.append(str(info['despacho']))
            
        mensaje_final = "\n".join(lineas_wa)
        
        # 1. ENVIAR A SHEETS Y FIRESTORE AL INSTANTE
        datos_envio = {
            "fechaHora": f"{fecha_val} {hora_val}",
            "cliente": cliente_final,
            "colProductos": "\n".join(prods_list),
            "colCantidades": "\n".join(cants_list),
            "colVencimientos": "\n".join(vencs_list),
            "colDespachos": "\n".join(desps_list)
        }
        guardar_visita_sheets_firestore(datos_envio)
        
        # 2. VISTA PREVIA Y BOTÓN WHATSAPP
        st.success("¡Reporte generado y enviado a la base de datos!")
        st.text_area("Vista previa mensaje WhatsApp:", mensaje_final, height=150)
        
        url_whatsapp = f"https://api.whatsapp.com/send?phone=584244527538&text={urllib.parse.quote(mensaje_final)}"
        
        st.markdown(f'''
            <a href="{url_whatsapp}" target="_blank">
                <button style="width: 100%; background-color: #25D366; color: white; padding: 12px; border: none; border-radius: 8px; font-weight: bold; font-size: 15px; cursor: pointer; text-transform: uppercase;">
                    💬 Abrir WhatsApp con el Reporte
                </button>
            </a>
        ''', unsafe_allow_html=True)
