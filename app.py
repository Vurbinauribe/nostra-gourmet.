import streamlit as st
from datetime import datetime
import urllib.parse
import re
import difflib

# Configuración inicial de la página
st.set_page_config(
    page_title="NOSTRA GOURMET - Inventario Móvil",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos limpios y profesionales (Garantiza legibilidad perfecta)
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
# 1. INICIALIZAR MEMORIA DE SESIÓN (ESTADO PERSISTENTE)
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

if 'datos_cargados' not in st.session_state:
    st.session_state.datos_cargados = {} # Almacena {producto: {cant, venc, desp}}

# ----------------------------------------------------
# 2. CONEXIÓN CON BASES DE DATOS (SHEETS / FIRESTORE)
# ----------------------------------------------------
def obtener_inventario_anterior(nombre_cliente):
    inventario_previo = {}
    if not nombre_cliente or nombre_cliente == "-- Seleccionar Cliente --":
        return inventario_previo

    try:
        if "gcp_service_account" in st.secrets:
            import gspread
            gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
            sh = gc.open("NostraGourmetDB")
            sheet = sh.sheet1
            data = sheet.get_all_values()
            
            cliente_buscado = nombre_cliente.strip().lower()
            for i in range(len(data) - 1, 0, -1):
                fila = data[i]
                cliente_fila = (fila[1] if len(fila) > 1 and fila[1] else "") or (fila[2] if len(fila) > 2 and fila[2] else "")
                if cliente_fila.strip().lower() == cliente_buscado:
                    col_c = fila[2] if len(fila) > 2 else ""
                    lines = col_c.split('\n') if col_c else []
                    for line in lines:
                        if ':' in line:
                            parts = line.split(':')
                            p = parts[0].strip()
                            c_bruta = parts[1].strip()
                            c_limpia = c_bruta.split('(')[0].strip()
                            if p and p not in inventario_previo:
                                inventario_previo[p] = c_limpia
                    break
    except Exception as e:
        pass
    return inventario_previo

# ----------------------------------------------------
# 3. INTERFAZ DE CLIENTES Y FECHA
# ----------------------------------------------------
col_f1, col_f2 = st.columns(2)
with col_f1:
    fecha_val = st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%y"))
with col_f2:
    hora_val = st.text_input("Hora", value=datetime.now().strftime("%H:%M"))

cliente_sel = st.selectbox("Cliente / Establecimiento", st.session_state.clientes_lista)

cliente_final = cliente_sel
if cliente_sel == "MANUAL":
    nuevo_cliente_input = st.text_input("Escribe el nombre del Nuevo Cliente")
    if nuevo_cliente_input:
        cliente_final = nuevo_cliente_input.strip()
        # Guardar en la lista de clientes para que no se borre
        if cliente_final not in st.session_state.clientes_lista:
            st.session_state.clientes_lista.insert(2, cliente_final)

inventario_anterior = obtener_inventario_anterior(cliente_final)

st.divider()

# ----------------------------------------------------
# 4. CARGA RÁPIDA INTELIGENTE (CON COINCIDENCIA DIFUSA)
# ----------------------------------------------------
with st.expander("⚡ CARGA RÁPIDA (PEGAR TEXTO INTELIGENTE)"):
    texto_pasted = st.text_area("Pega aquí el inventario. Ej:\npieza de padano: 8\nProsciutto: 30 (12/10/26)")
    
    if st.button("📥 Procesar y Cargar en la Tabla"):
        nuevos_datos = {}
        base_low = {p.lower(): p for p in st.session_state.productos_base}
        
        for linea in texto_pasted.split('\n'):
            if ':' in linea:
                partes = linea.split(':')
                p_nombre = partes[0].strip()
                p_resto = partes[1].strip()
                
                # Extraer vencimiento entre paréntesis
                match_venc = re.search(r'\((.*?)\)', p_resto)
                venc_val = match_venc.group(1) if match_venc else ""
                cant_val = re.sub(r'\(.*?\)', '', p_resto).strip()
                
                if cant_val.isdigit():
                    p_norm = p_nombre.lower()
                    producto_asignado = None
                    
                    # 1. Coincidencia exacta o parcial
                    for pb_low, pb_real in base_low.items():
                        if p_norm in pb_low or pb_low in p_norm:
                            producto_asignado = pb_real
                            break
                    
                    # 2. Coincidencia aproximada inteligente (si no encontró por inclusión)
                    if not producto_asignado:
                        matches = difflib.get_close_matches(p_norm, list(base_low.keys()), n=1, cutoff=0.4)
                        if matches:
                            producto_asignado = base_low[matches[0]]
                    
                    # 3. Si de verdad es un producto nuevo que no existe en la base
                    if not producto_asignado:
                        producto_asignado = p_nombre.capitalize()
                        if producto_asignado not in st.session_state.productos_base:
                            st.session_state.productos_base.append(producto_asignado)
                    
                    nuevos_datos[producto_asignado] = {
                        "cant": int(cant_val),
                        "venc": venc_val,
                        "desp": 0
                    }
        
        st.session_state.datos_cargados = nuevos_datos
        st.success(f"¡Se procesaron y cargaron {len(nuevos_datos)} productos correctamente!")

# ----------------------------------------------------
# 5. TABLA DE PRODUCTOS
# ----------------------------------------------------
st.markdown("### 📋 Listado de Productos")

h1, h2, h3, h4, h5 = st.columns([2.2, 0.9, 1.3, 0.8, 0.8])
h1.markdown("**PRODUCTO**")
h2.markdown("**CANT.**")
h3.markdown("**F. VENC**")
h4.markdown("**DESP.**")
h5.markdown("**ANT.**")

inventario_ingresado = {}

for idx, prod in enumerate(st.session_state.productos_base):
    # Recuperar datos si vinieron de carga rápida o sesión previa
    pre = st.session_state.datos_cargados.get(prod, {"cant": 0, "venc": "", "desp": 0})
    val_ant = inventario_anterior.get(prod, "-")
    
    c = st.columns([2.2, 0.9, 1.3, 0.8, 0.8])
    with c[0]:
        st.write(prod)
    with c[1]:
        cant = st.number_input(f"c_{idx}", min_value=0, value=pre["cant"], key=f"cant_p_{idx}", label_visibility="collapsed")
    with c[2]:
        venc = st.text_input(f"v_{idx}", value=pre["venc"], placeholder="dd/mm/aa", key=f"venc_p_{idx}", label_visibility="collapsed")
    with c[3]:
        desp = st.number_input(f"d_{idx}", min_value=0, value=pre["desp"], key=f"desp_p_{idx}", label_visibility="collapsed")
    with c[4]:
        st.markdown(f"<div style='text-align: center; background: #f1f5f9; padding: 4px; border-radius: 4px; color: #64748b; font-size: 12px;'>{val_ant}</div>", unsafe_allow_html=True)
    
    if cant > 0 or desp > 0:
        inventario_ingresado[prod] = {"cantidad": cant, "vencimiento": venc, "despacho": desp}

# Productos libres adicionales (5 filas dinámicas)
st.markdown("---")
st.markdown("### ➕ Productos Libres Adicionales")
custom_inventario = {}
for i in range(1, 6):
    cc = st.columns([2.2, 0.9, 1.3, 0.8, 0.8])
    with cc[0]:
        c_prod = st.text_input(f"P {i}", placeholder=f"+ Producto libre {i}", key=f"custom_prod_{i}", label_visibility="collapsed")
    with cc[1]:
        c_cant = st.number_input(f"C {i}", min_value=0, value=0, key=f"custom_cant_{i}", label_visibility="collapsed")
    with cc[2]:
        c_venc = st.text_input(f"V {i}", placeholder="dd/mm/aa", key=f"custom_venc_{i}", label_visibility="collapsed")
    with cc[3]:
        c_desp = st.number_input(f"D {i}", min_value=0, value=0, key=f"custom_desp_{i}", label_visibility="collapsed")
    with cc[4]:
        st.markdown("<div style='text-align: center; background: #f1f5f9; padding: 4px; border-radius: 4px; color: #64748b; font-size: 12px;'>-</div>", unsafe_allow_html=True)
        
    if c_prod.strip() != "" and c_cant > 0:
        nombre_libre = c_prod.strip()
        custom_inventario[nombre_libre] = {"cantidad": c_cant, "vencimiento": c_venc, "despacho": c_desp}
        # Agregar automáticamente a la base de productos generales para futuras visitas
        if nombre_libre not in st.session_state.productos_base:
            st.session_state.productos_base.append(nombre_libre)

st.divider()

# ----------------------------------------------------
# 6. GENERACIÓN Y ENVÍO A WHATSAPP / SHEETS
# ----------------------------------------------------
if st.button("📲 Generar Vista Previa y Enviar a WhatsApp"):
    if not cliente_final or cliente_final == "-- Seleccionar Cliente --":
        st.error("Por favor seleccione o escriba un cliente válido.")
    elif not inventario_ingresado and not custom_inventario:
        st.error("No hay productos con inventario para reportar.")
    else:
        lineas_wa = [f"{cliente_final}", f"{fecha_val} {hora_val}", "Inventario", "", "PRODUCTO", ""]
        
        todo_inventario = {**inventario_ingresado, **custom_inventario}
        
        for prod, info in todo_inventario.items():
            linea = f"{prod}  {info['cantidad']}"
            if info['vencimiento']:
                linea += f" ({info['vencimiento']})"
            lineas_wa.append(linea)
            
        mensaje_final = "\n".join(lineas_wa)
        
        st.success("¡Reporte generado con éxito!")
        st.text_area("Vista previa del mensaje:", mensaje_final, height=150)
        
        # Enlace directo de WhatsApp con tu número corporativo
        numero_whatsapp = "584244527538"
        url_whatsapp = f"https://api.whatsapp.com/send?phone={numero_whatsapp}&text={urllib.parse.quote(mensaje_final)}"
        
        st.markdown(f'''
            <a href="{url_whatsapp}" target="_blank">
                <button style="width: 100%; background-color: #25D366; color: white; padding: 12px; border: none; border-radius: 8px; font-weight: bold; font-size: 15px; cursor: pointer; text-transform: uppercase;">
                    💬 Abrir WhatsApp con el Reporte
                </button>
            </a>
        ''', unsafe_allow_html=True)
        
        # Registro automático en Google Sheets
        try:
            if "gcp_service_account" in st.secrets:
                import gspread
                gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
                sh = gc.open("NostraGourmetDB")
                sheet = sh.sheet1
                
                col_prods = "\n".join(todo_inventario.keys())
                col_cants = "\n".join([str(info['cantidad']) for info in todo_inventario.values()])
                col_vencs = "\n".join([info['vencimiento'] if info['vencimiento'] else "-" for info in todo_inventario.values()])
                col_desps = "\n".join([str(info['despacho']) for info in todo_inventario.values()])
                
                sheet.append_row([f"{fecha_val} {hora_val}", cliente_final, col_prods, col_cants, col_vencs, col_desps])
                st.toast("✅ Datos guardados automáticamente en Google Sheets", icon="📊")
        except Exception as e:
            pass
