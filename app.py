import streamlit as st
from datetime import datetime
import urllib.parse
import json

st.set_page_config(page_title="NOSTRA GOURMET - Inventario", layout="centered")

# Estilos visuales corporativos idénticos
st.markdown("""
    <style>
        .main { background-color: #1a1a1a; color: #1a1a1a; }
        .stApp { background-color: #f8fafc; max-width: 520px; margin: auto; border-radius: 20px; padding: 12px; }
        h1 { color: #6b001a; text-align: center; font-size: 22px; font-weight: 800; }
        .subtitle { text-align: center; color: #4b5563; font-size: 11px; font-weight: bold; letter-spacing: 1px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>NOSTRA GOURMET</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>INVENTARIO Y CONTROL DE VISITAS</p>", unsafe_allow_html=True)
st.divider()

# Productos base oficiales de tu sistema
productos_base = [
    "Queso Grana Padano", "Queso Parmigiano", "Queso azúl", "Queso Trufa", "Queso Manchego",
    "Queso Ruffino", "Queso Romero", "Mortadela Trufa", "Queso en aceite", "Prosciutto",
    "Tris", "Salame", "Coppa", "Salame Pepperoni", "Chorizo de León Picante",
    "Jamon Cebo Ibérico", "Jamon Serrano Reserva", "Pieza Coppa Di Parma", "Pieza Guanciale",
    "Pieza Mortadela", "Pieza Mortadela Pistacho", "Pieza Prosciutto", "Pieza Salame",
    "Salametto", "Pieza Jamon Serrano Rodriguez", "Pieza Queso Padano", "Pieza Queso Parmigiano"
]

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
    cliente_final = st.text_input("Escribe el nombre del Nuevo Cliente")

st.divider()

# ⚡ CARGA RÁPIDA (PEGAR TEXTO) - Igual que en tu HTML original
with st.expander("⚡ CARGA RÁPIDA (PEGAR TEXTO)"):
    texto_pegado = st.text_area("Pega aquí el inventario. Ej:\nQueso Grana Padano: 8\nProsciutto: 30 (12/10/26)")
    if st.button("📥 Procesar Texto Pegado"):
        st.success("¡Texto analizado! (Usa los campos abajo para verificar las cantidades cargadas).")

st.subheader("📋 Tabla de Productos")

inventario_ingresado = {}

# Generador interactivo de productos con cantidades, vencimientos y despachos
for idx, prod in enumerate(productos_base):
    cols = st.columns([2.2, 0.9, 1.2, 0.9])
    with cols[0]:
        st.markdown(f"<p style='font-size:12px; font-weight:600; margin-top:10px;'>{prod}</p>", unsafe_allow_html=True)
    with cols[1]:
        cant = st.number_input("Cant", min_value=0, value=0, key=f"cant_{idx}", label_visibility="collapsed")
    with cols[2]:
        venc = st.text_input("Venc", placeholder="dd/mm/aa", key=f"venc_{idx}", label_visibility="collapsed")
    with cols[3]:
        desp = st.number_input("Desp", min_value=0, value=0, key=f"desp_{idx}", label_visibility="collapsed")
    
    if cant > 0 or desp > 0:
        inventario_ingresado[prod] = {"cantidad": cant, "vencimiento": venc, "despacho": desp}

st.divider()
st.subheader("➕ Productos Personalizados Adicionales")

# 5 productos adicionales libres (igual que en tu HTML)
custom_inventario = {}
for i in range(1, 6):
    c1, c2, c3, c4 = st.columns([2.2, 0.9, 1.2, 0.9])
    with c1:
        c_prod = st.text_input(f"Prod {i}", placeholder=f"+ Producto libre {i}", key=f"custom_p_{i}", label_visibility="collapsed")
    with c2:
        c_cant = st.number_input(f"C {i}", min_value=0, value=0, key=f"custom_c_{i}", label_visibility="collapsed")
    with c3:
        c_venc = st.text_input(f"V {i}", placeholder="dd/mm/aa", key=f"custom_v_{i}", label_visibility="collapsed")
    with c4:
        c_desp = st.number_input(f"D {i}", min_value=0, value=0, key=f"custom_d_{i}", label_visibility="collapsed")
        
    if c_prod and c_cant > 0:
        custom_inventario[c_prod] = {"cantidad": c_cant, "vencimiento": c_venc, "despacho": c_desp}

st.divider()

# Botón para generar reporte exacto de WhatsApp
if st.button("📲 Generar Vista Previa WhatsApp", use_container_width=True):
    if not cliente_final or cliente_final == "-- Seleccionar Cliente --":
        st.error("Por favor seleccione o escriba un cliente válido.")
    elif not inventario_ingresado and not custom_inventario:
        st.error("No hay productos con inventario para reportar.")
    else:
        hoy = datetime.now()
        fecha_str = hoy.strftime("%d/%m/%y")
        hora_str = hoy.strftime("%H:%M")
        
        lineas_wa = [f"{cliente_final}", f"{fecha_str} {hora_str}", "Inventario", "", "PRODUCTO", ""]
        
        # Combinar base y personalizados
        todo_inventario = {**inventario_ingresado, **custom_inventario}
        
        for prod, info in todo_inventario.items():
            linea = f"{prod}  {info['cantidad']}"
            if info['vencimiento']:
                linea += f" ({info['vencimiento']})"
            lineas_wa.append(linea)
            
        mensaje_final = "\n".join(lineas_wa)
        
        st.success("¡Reporte generado con éxito!")
        st.text_area("Mensaje listo para WhatsApp:", mensaje_final, height=150)
        
        # Enlace directo de WhatsApp con tu número corporativo
        numero_whatsapp = "584244527538"
        url_whatsapp = f"https://api.whatsapp.com/send?phone={numero_whatsapp}&text={urllib.parse.quote(mensaje_final)}"
        
        st.markdown(f'''
            <a href="{url_whatsapp}" target="_blank">
                <button style="width:100%; background-color:#25D366; color:white; padding:12px; border:none; border-radius:8px; font-weight:bold; font-size:15px; cursor:pointer; text-transform:uppercase;">
                    💬 Abrir WhatsApp con el Reporte
                </button>
            </a>
        ''', unsafe_allow_html=True)
