import streamlit as st
from datetime import datetime
import urllib.parse

st.set_page_config(page_title="NOSTRA GOURMET - Inventario", layout="centered")

# Estilos visuales corporativos (Vinotinto y Dorado)
st.markdown("""
    <style>
        .main { background-color: #f8fafc; }
        h1 { color: #6b001a; text-align: center; font-size: 24px; font-weight: 800; }
        .subtitle { text-align: center; color: #4b5563; font-size: 11px; font-weight: bold; letter-spacing: 1px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>NOSTRA GOURMET</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>INVENTARIO Y CONTROL DE VISITAS</p>", unsafe_allow_html=True)
st.divider()

# Lista de tus productos base
productos_base = [
    "Queso Grana Padano", "Queso Parmigiano", "Queso azúl", "Queso Trufa", "Queso Manchego",
    "Queso Ruffino", "Queso Romero", "Mortadela Trufa", "Queso en aceite", "Prosciutto",
    "Tris", "Salame", "Coppa", "Salame Pepperoni", "Chorizo de León Picante",
    "Jamon Cebo Ibérico", "Jamon Serrano Reserva", "Pieza Coppa Di Parma", "Pieza Guanciale",
    "Pieza Mortadela", "Pieza Mortadela Pistacho", "Pieza Prosciutto", "Pieza Salame",
    "Salametto", "Pieza Jamon Serrano Rodriguez", "Pieza Queso Padano", "Pieza Queso Parmigiano"
]

# Selección de cliente
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
st.subheader("📋 Carga de Productos")

inventario_ingresado = {}

for idx, prod in enumerate(productos_base):
    cols = st.columns([2.5, 1, 1.5])
    with cols[0]:
        st.markdown(f"<p style='font-size:13px; font-weight:600; margin-top:8px;'>{prod}</p>", unsafe_allow_html=True)
    with cols[1]:
        cant = st.number_input("Cant", min_value=0, value=0, key=f"cant_{idx}", label_visibility="collapsed")
    with cols[2]:
        venc = st.text_input("Venc", placeholder="dd/mm/aa", key=f"venc_{idx}", label_visibility="collapsed")
    
    if cant > 0:
        inventario_ingresado[prod] = {"cantidad": cant, "vencimiento": venc}

st.divider()

if st.button("📲 Generar Vista Previa WhatsApp", use_container_width=True):
    if not cliente_final or cliente_final == "-- Seleccionar Cliente --":
        st.error("Por favor seleccione o escriba un cliente válido.")
    elif not inventario_ingresado:
        st.error("No hay productos con inventario para reportar.")
    else:
        hoy = datetime.now()
        fecha_str = hoy.strftime("%d/%m/%y")
        hora_str = hoy.strftime("%H:%M")
        
        lineas_wa = [f"{cliente_final}", f"{fecha_str} {hora_str}", "Inventario", "", "PRODUCTO", ""]
        for prod, info in inventario_ingresado.items():
            linea = f"{prod}  {info['cantidad']}"
            if info['vencimiento']:
                linea += f" ({info['vencimiento']})"
            lineas_wa.append(linea)
            
        mensaje_final = "\n".join(lineas_wa)
        
        st.success("¡Reporte generado con éxito!")
        st.text_area("Mensaje listo para WhatsApp:", mensaje_final, height=150)
        
        numero_whatsapp = "584244527538"
        url_whatsapp = f"https://api.whatsapp.com/send?phone={numero_whatsapp}&text={urllib.parse.quote(mensaje_final)}"
        
        st.markdown(f'''
            <a href="{url_whatsapp}" target="_blank">
                <button style="width:100%; background-color:#25D366; color:white; padding:12px; border:none; border-radius:8px; font-weight:bold; font-size:15px; cursor:pointer; text-transform:uppercase;">
                    💬 Abrir WhatsApp con el Reporte
                </button>
            </a>
        ''', unsafe_allow_html=True)
