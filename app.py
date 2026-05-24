import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Lapas pamata konfigurācija un vizuālais stils
st.set_page_config(
    page_title="NordTech | E-komercijas audits",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Pielāgots CSS, lai dashboard izskatītos tīrāks un modernāks
st.markdown("""
    <style>
    .main-title { font-size:2.4rem !important; font-weight: 700; color: #1E3A8A; margin-bottom: 5px; }
    .subtitle { font-size:1.1rem; color: #6B7280; margin-bottom: 25px; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: bold; color: #1F2937; }
    </style>
""", unsafe_allow_html=True)

# 2. Datu ielāde
@st.cache_data
def load_dashboard_data():
    data = pd.read_csv('enriched_data.csv')
    data['Date'] = pd.to_datetime(data['Date'])
    # Aprēķinām kopējo vērtību katram pirkumam (cena * daudzums)
    data['Total_Order_Value'] = data['Price'] * data['Quantity']
    return data

df = load_dashboard_data()

# 3. Interaktīvā sānjosla (Sidebar) filtriem
st.sidebar.header("⚙️ Filtri un uzstādījumi")
st.sidebar.markdown("Izmanto šos filtrus, lai analizētu konkrētus segmentus.")

# Filtrs pa produktu kategorijām
categories = ['Visi'] + list(df['Product_Category'].unique())
selected_category = st.sidebar.selectbox("Izvēlies produktu kategoriju:", categories)

# Filtrs pa produktiem (dinamiski pielāgojas izvēlētajai kategorijai)
if selected_category != 'Visi':
    available_products = ['Visi'] + list(df[df['Product_Category'] == selected_category]['Product_Name'].unique())
else:
    available_products = ['Visi'] + list(df['Product_Name'].unique())
selected_product = st.sidebar.selectbox("Izvēlies konkrētu produktu:", available_products)

# Datu filtrēšanas loģika bāzējoties uz lietotāja izvēli
filtered_df = df.copy()
if selected_category != 'Visi':
    filtered_df = filtered_df[filtered_df['Product_Category'] == selected_category]
if selected_product != 'Visi':
    filtered_df = filtered_df[filtered_df['Product_Name'] == selected_product]

# 4. Dashboard Galvene (Header)
st.markdown('<div class="main-title">📊 NordTech E-komercijas Stratēģiskais Audits</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Datu analītikas rīks ieņēmumu, atgriešanu un klientu sūdzību signālu identificēšanai</div>', unsafe_allow_html=True)

# 5. Stratēģiskie KPI rādītāji (Galvenie biznesa metriki)
st.subheader("📌 Galvenie biznesa darbības rādītāji (KPI)")
kpi1, kpi2, kpi3 = st.columns(3)

total_revenue = filtered_df['Total_Order_Value'].sum()
total_refunds = filtered_df['Refund_Amount'].sum()
return_rate = (total_refunds / total_revenue * 100) if total_revenue > 0 else 0.0
active_tickets = filtered_df[filtered_df['Problem_Category'] != 'Nav sūdzību'].shape[0]

with kpi1:
    st.metric(label="Kopējie Ieņēmumi", value=f"{total_revenue:,.2f} EUR")
with kpi2:
    status_emoji = "🚨" if return_rate > 10 else "✅"
    st.metric(label=f"Atgriešanas Procents {status_emoji}", value=f"{return_rate:.2f}%", delta=f"{total_refunds:,.2f} EUR atgriezts", delta_color="inverse")
with kpi3:
    st.metric(label="Klientu Sūdzību Skaits", value=str(active_tickets))

st.markdown("---")

# 6. Vizuālā analītika (Grafiki divās kolonnās)
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Finanšu tendence pa mēnešiem")
    filtered_df['YearMonth'] = filtered_df['Date'].dt.to_period('M').astype(str)
    
    trend_df = filtered_df.groupby('YearMonth').agg(
        Ieņēmumi=('Total_Order_Value', 'sum'),
        Atgriešanas=('Refund_Amount', 'sum')
    ).reset_index()
    
    fig_trend = px.line(trend_df, x='YearMonth', y=['Ieņēmumi', 'Atgriešanas'], 
                        labels={'value': 'Summa (EUR)', 'YearMonth': 'Mēnesis', 'variable': 'Metrika'},
                        color_discrete_map={'Ieņēmumi': '#1E3A8A', 'Atgriešanas': '#EF4444'},
                        markers=True)
    fig_trend.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_trend, use_container_width=True)

with col2:
    st.subheader("⚠️ Klientu sūdzību iemeslu sadalījums")
    ticket_df = filtered_df[filtered_df['Problem_Category'] != 'Nav sūdzību']
    
    if not ticket_df.empty:
        reasons = ticket_df['Problem_Category'].value_counts().reset_index()
        reasons.columns = ['Iemesls', 'Skaits']
        fig_reasons = px.bar(reasons, x='Skaits', y='Iemesls', orientation='h',
                             color='Skaits', color_continuous_scale='Reds',
                             labels={'Skaits': 'Pieteikumu skaits', 'Iemesls': 'Problēmas kategorija'})
        fig_reasons.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_reasons, use_container_width=True)
    else:
        st.info("Šim atlasītajam produktam vai kategorijai nav reģistrētu klientu sūdzību.")

st.markdown("---")

# 7. Detalizēta datu tabula (Deep Dive)
st.subheader("🔍 Pārlūkot filtrētos datus")
st.markdown("Zemāk redzami detalizēti dati atbulstoši izvēlētajiem sānjoslas filtriem.")

view_cols = ['Transaction_ID', 'Date', 'Product_Name', 'Price', 'Quantity', 'Total_Order_Value', 'Problem_Category', 'Sentiment']
st.dataframe(filtered_df[view_cols].sort_values(by='Date', ascending=False), use_container_width=True)