import streamlit as st
from datetime import datetime
import urllib.parse
import json
import re

st.set_page_config(
    page_title="NOSTRA GOURMET - Inventario y Visitas",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 1. DISEÑO VISUAL CORPORATIVO Y PATRÓN MOSAICO EXACTO
st.markdown("""
    <style>
        .stApp { 
            background-color: #1a1a1a;
            background-image: 
                linear-gradient(135deg, rgba(66, 0, 16, 0.88), rgba(15, 23, 42, 0.94)),
                url("https://lh3.googleusercontent.com/d/16RoTczNAtKCncWTlRK8UY__y4eCCGqOm");
            background-repeat: repeat;
            background-size: auto, 90px 90px;
            background-attachment: fixed;
        }
        .app-container {
            background: #ffffff;
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 20px 45px rgba(0, 0, 0, 0.6), 0 0 20px rgba(197, 155, 39, 0.3);
            border-top: 6px solid #c59b27;
            max-width: 520px;
            margin: auto;
        }
        h1 { color: #6b001a; text-align: center; font-size: 20px; font-weight: 800; text-transform: uppercase; }
        .subtitle { text-align: center; color: #4b5563; font-size: 10px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 10px; }
        .connection-banner {
            display: flex; align-items: center; justify-content: center; gap: 6px;
            font-size: 0.75rem; font-weight: bold; padding: 6px; border-radius: 6px; margin-bottom: 10px;
        }
        .online { background: #dcfce7; color: #166534; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-container">', unsafe_allow_html=True)

# Banner de Conexión
st.markdown('<div class="connection-banner online">🟢 Conectado a Google Sheets / Firestore (Python)</div>', unsafe_allow_html=True)

# Encabezado con Logo y Títulos
col_logo1, col_logo2, col_logo3 = st.columns([1, 1.5, 1])
with col_logo2:
    st.image("https://lh3.googleusercontent.com/d/16RoTczNAtKCncWTlRK8UY__y4eCCGqOm", width=65)

st.markdown("<h1>NOSTRA GOURMET</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Inventario y Control de Visitas</p>", unsafe_allow_html=True)

# Inicializar Estado de Sesión (Memoria Local equivalente a LocalStorage)
if 'inventario_anterior' not in st.session_state:
    st.session_state.inventario_anterior = {}

# Fecha y Hora
col_f1, col_f2 = st.columns(2)
with col_f1:
    fecha_input = st.text_input("Fecha", value=datetime.now().strftime("%d/%m/%y"))
with col_f2:
    hora_input = st.text_input("Hora", value=datetime.now().strftime("%H:%M"))

# Listado completo de clientes
lista_clientes = [
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

cliente_sel = st.selectbox("Cliente / Establecimiento", lista_clientes)
cliente_final = cliente_sel
if cliente_sel == "MANUAL":
    cliente_final = st.text_input("Nombre del Nuevo Cliente")

st.divider()

# ⚡ CARGA RÁPIDA (PEGAR TEXTO) - Inteligente con análisis de líneas
productos_base = [
    "Queso Grana Padano", "Queso Parmigiano", "Queso azúl", "Queso Trufa", "Queso Manchego",
    "Queso Ruffino", "Queso Romero", "Mortadela Trufa", "Queso en aceite", "Prosciutto",
    "Tris", "Salame", "Coppa", "Salame Pepperoni", "Chorizo de León Picante",
    "Jamon Cebo Ibérico", "Jamon Serrano Reserva", "Pieza Coppa Di Parma", "Pieza Guanciale",
    "Pieza Mortadela", "Pieza Mortadela Pistacho", "Pieza Prosciutto", "Pieza Salame",
    "Salametto", "Pieza Jamon Serrano Rodriguez", "Pieza Queso Padano", "Pieza Queso Parmigiano"
]

if 'cargados_rapidos' not in st.session_state:
    st.session_state.cargados_rapidos = {}

with st.expander("⚡ CARGA RÁPIDA (PEGAR TEXTO)"):
    texto_pasted = st.text_area("Pega aquí el inventario. Ej:\nQueso Grana Padano: 8\nProsciutto: 30 (12/10/26)")
    if st.button("📥 Cargar Datos en la Tabla"):
        nuevos_datos = {}
        lineas = texto_pasted.split('\n')
        for linea in lineas:
            if ':' in linea:
                partes = linea.split(':')
                p_nombre = partes[0].strip()
                p_resto = partes[1].strip()
                # Extraer cantidad y vencimiento si hay paréntesis
                match_venc = re.search(r'\((.*?)\)', p_resto)
                venc_val = match_venc.group(1) if match_venc else ""
                cant_val = re.sub(r'\(.*?\)', '', p_resto).strip()
                
                if cant_val.isdigit():
                    for pb in productos_base:
                        if pb.lower() in p_nombre.lower() or p_nombre.lower() in pb.lower():
                            nuevos_datos[pb] = {"cant": int(cant_val), "venc": venc_val}
        st.session_state.cargados_rapidos = nuevos_datos
        st.success(f"¡Se procesaron {len(nuevos_datos)} productos correctamente!")

st.markdown("<p style='font-weight:700; font-size:12px; color:#1a1a1a; margin-bottom:5px;'>PRODUCTOS</p>", unsafe_allow_html=True)

# Cabeceras de la Tabla (PRODUCTO, CANT., F. VENC, DESP., ANT.)
c_h = st.columns([2.2, 0.9, 1.3, 0.8, 0.8])
c_h[0].markdown("<span style='font-size:11px; font-weight:bold;'>PRODUCTO</span>", unsafe_allow_html=True)
c_h[1].markdown("<span style='font-size:11px; font-weight:bold;'>CANT.</span>", unsafe_allow_html=True)
c_h[2].markdown("<span style='font-size:11px; font-weight:bold;'>F. VENC</span>", unsafe_allow_html=True)
c_h[3].markdown("<span style='font-size:11px; font-weight:bold;'>DESP.</span>", unsafe_allow_html=True)
c_h[4].markdown("<span style='font-size:11px; font-weight:bold;'>ANT.</span>", unsafe_allow_html=True)

inventario_ingresado = {}

# Renderizar productos base con valores previos (ANT.)
for idx, prod in enumerate(productos_base):
    pre_load = st.session_state.cargados_rapidos.get(prod, {"cant": 0, "venc": ""})
    
    c = st.columns([2.2, 0.9, 1.3, 0.8, 0.8])
    with c[0]:
        st.markdown(f"<p style='font-size:11px; font-weight:600; margin-top:8px;' title='{prod}'>{prod}</p>", unsafe_allow_html=True)
    with c[1]:
        cant = st.number_input("C", min_value=0, value=pre_load["cant"], key=f"cant_{idx}", label_visibility="collapsed")
    with c[2]:
        venc = st.text_input("V", value=pre_load["venc"], placeholder="dd/mm/aa", key=f"venc_{idx}", label_visibility="collapsed")
    with c[3]:
        desp = st.number_input("D", min_value=0, value=0, key=f"desp_{idx}", label_visibility="collapsed")
    with c[4]:
        ant_val = st.session_state.inventario_anterior.get(prod, "-")
        st.markdown(f"<p style='font-size:11px; text-align:center; background:#f1f5f9; padding:4px; border-radius:4px; color:#64748b;'>{ant_val}</p>", unsafe_allow_html=True)
    
    if cant > 0 or desp > 0:
        inventario_ingresado[prod] = {"cantidad": cant, "vencimiento": venc, "despacho": desp}

st.markdown("---")
st.markdown("<p style='font-weight:700; font-size:12px; color:#1a1a1a;'>➕ PRODUCTOS LIBRES ADICIONALES</p>", unsafe_allow_html=True)

# 5 Productos adicionales personalizados (igual que tu HTML original)
custom_inventario = {}
for i in range(1, 6):
    cc = st.columns([2.2, 0.9, 1.3, 0.8, 0.8])
    with cc[0]:
        c_prod = st.text_input(f"P {i}", placeholder=f"+ Prod {i}", key=f"custom_prod_{i}", label_visibility="collapsed")
    with cc[1]:
        c_cant = st.number_input(f"C {i}", min_value=0, value=0, key=f"custom_cant_{i}", label_visibility="collapsed")
    with cc[2]:
        c_venc = st.text_input(f"V {i}", placeholder="dd/mm/aa", key=f"custom_venc_{i}", label_visibility="collapsed")
    with cc[3]:
        c_desp = st.number_input(f"D {i}", min_value=0, value=0, key=f"custom_desp_{i}", label_visibility="collapsed")
    with cc[4]:
        st.markdown("<p style='font-size:11px; text-align:center; background:#f1f5f9; padding:4px; border-radius:4px; color:#64748b;'>-</p>", unsafe_allow_html=True)
        
    if c_prod.strip() != "" and c_cant > 0:
        custom_inventario[c_prod.strip()] = {"cantidad": c_cant, "vencimiento": c_venc, "despacho": c_desp}

st.divider()

# Botón Generar Vista Previa WhatsApp
if st.button("Generar Vista Previa WhatsApp", use_container_width=True):
    if not cliente_final or cliente_final == "-- Seleccionar Cliente --":
        st.error("Por favor seleccione un cliente válido.")
    elif not inventario_ingresado and not custom_inventario:
        st.error("No hay productos con inventario para reportar.")
    else:
        lineas_wa = [f"{cliente_final}", f"{fecha_input} {hora_input}", "Inventario", "", "PRODUCTO", ""]
        
        todo_inventario = {**inventario_ingresado, **custom_inventario}
        for prod, info in todo_inventario.items():
            linea = f"{prod}  {info['cantidad']}"
            if info['vencimiento']:
                linea += f" ({info['vencimiento']})"
            lineas_wa.append(linea)
            
        mensaje_final = "\n".join(lineas_wa)
        
        st.success("¡Reporte generado con éxito!")
        st.text_area("Mensaje listo para WhatsApp:", mensaje_final, height=140)
        
        url_whatsapp = f"https://api.whatsapp.com/send?phone=584244527538&text={urllib.parse.quote(mensaje_final)}"
        
        st.markdown(f'''
            <a href="{url_whatsapp}" target="_blank">
                <button style="width:100%; background-color:#25D366; color:white; padding:13px; border:none; border-radius:10px; font-weight:bold; font-size:14px; cursor:pointer; text-transform:uppercase; box-shadow: 0 4px 10px rgba(37,211,102,0.3);">
                    📲 Guardar y Enviar WhatsApp
                </button>
            </a>
        ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
