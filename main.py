import streamlit as st
import mysql.connector
import pandas as pd
import plotly.express as px

st.set_page_config(page_title='Food Delivery Enterprise', page_icon='🍔', layout='wide', initial_sidebar_state='expanded')

st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
html, body, [class*="css"] {font-family:Poppins, sans-serif;}
.stApp {background: linear-gradient(135deg,#f5f7fa,#e4ecf7);}
section[data-testid="stSidebar"] {background:#111827;color:white;}
section[data-testid="stSidebar"] * {color:white;}
.card{background:white;padding:18px;border-radius:22px;box-shadow:0 10px 25px rgba(0,0,0,.08);}
.title{font-size:34px;font-weight:700;margin-bottom:4px;}
.sub{color:#6b7280;margin-bottom:18px;}
div[data-testid="metric-container"]{background:white;border:0;padding:18px;border-radius:18px;box-shadow:0 8px 18px rgba(0,0,0,.06);} 
.stButton>button{border-radius:14px;padding:.6rem 1rem;font-weight:600;border:0;background:#111827;color:white;}
.stTextInput>div>div>input,.stNumberInput input{border-radius:12px;}
</style>
''', unsafe_allow_html=True)

# Session login
if 'logged' not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:
    c1,c2,c3 = st.columns([1,1.2,1])
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="title">🍔 Food Delivery Pro</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub">Secure admin dashboard login</div>', unsafe_allow_html=True)
        u = st.text_input('Username')
        p = st.text_input('Password', type='password')
        if st.button('Login', use_container_width=True):
            if u=='admin' and p=='admin123':
                st.session_state.logged=True
                st.rerun()
            else:
                st.error('Invalid credentials')
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# DB connection
conn = mysql.connector.connect(host='localhost', user='your_username', password='your_password', database='databasename')
cur = conn.cursor(dictionary=True)

st.markdown('<div class="title">🍔 Food Delivery Enterprise Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Manage customers, restaurants, orders and live analytics</div>', unsafe_allow_html=True)

page = st.sidebar.radio('📌 Navigation', ['Dashboard','Customers','Restaurants','Orders','Tracking','Add Order'])
st.sidebar.markdown('---')
if st.sidebar.button('Logout', use_container_width=True):
    st.session_state.logged=False
    st.rerun()

if page=='Dashboard':
    cur.execute('SELECT COUNT(*) c FROM customers'); a=cur.fetchone()['c']
    cur.execute('SELECT COUNT(*) c FROM restaurants'); b=cur.fetchone()['c']
    cur.execute('SELECT COUNT(*) c FROM orders'); c=cur.fetchone()['c']
    cur.execute('SELECT IFNULL(SUM(total_amount),0) s FROM orders'); d=cur.fetchone()['s']
    x1,x2,x3,x4 = st.columns(4)
    x1.metric('Customers', a)
    x2.metric('Restaurants', b)
    x3.metric('Orders', c)
    x4.metric('Revenue', f'₹{d}')

    col1,col2 = st.columns(2)
    with col1:
        cur.execute('''SELECT r.restaurant_name, SUM(o.total_amount) total FROM orders o JOIN restaurants r ON o.restaurant_id=r.restaurant_id GROUP BY r.restaurant_name''')
        df = pd.DataFrame(cur.fetchall())
        if not df.empty:
            fig = px.bar(df, x='restaurant_name', y='total', title='Revenue by Restaurant', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        cur.execute('SELECT status, COUNT(*) cnt FROM orders GROUP BY status')
        df2 = pd.DataFrame(cur.fetchall())
        if not df2.empty:
            fig2 = px.pie(df2, names='status', values='cnt', title='Order Status Distribution')
            st.plotly_chart(fig2, use_container_width=True)

elif page=='Customers':
    st.subheader('👥 Customer Records')
    cur.execute('SELECT * FROM customers')
    st.dataframe(pd.DataFrame(cur.fetchall()), use_container_width=True, height=500)

elif page=='Restaurants':
    st.subheader('🏬 Restaurant Directory')
    cur.execute('SELECT * FROM restaurants')
    st.dataframe(pd.DataFrame(cur.fetchall()), use_container_width=True, height=500)

elif page=='Orders':
    st.subheader('🧾 Order Management')
    term = st.text_input('Search status / customer')
    q='''SELECT o.order_id,c.name,r.restaurant_name,o.total_amount,o.status,o.order_date FROM orders o JOIN customers c ON o.customer_id=c.customer_id JOIN restaurants r ON o.restaurant_id=r.restaurant_id'''
    cur.execute(q)
    df = pd.DataFrame(cur.fetchall())
    if not df.empty and term:
        mask = df.astype(str).apply(lambda s: s.str.contains(term, case=False, na=False))
        df = df[mask.any(axis=1)]
    st.dataframe(df, use_container_width=True, height=500)

elif page=='Tracking':
    st.subheader('🚚 Delivery Tracking')
    cur.execute('''SELECT o.order_id,d.agent_name,d.vehicle_no,o.status FROM orders o JOIN delivery_agents d ON o.agent_id=d.agent_id''')
    st.dataframe(pd.DataFrame(cur.fetchall()), use_container_width=True, height=500)

else:
    st.subheader('➕ Create New Order')
    c1,c2 = st.columns(2)
    with c1:
        cid=st.number_input('Customer ID',1,step=1)
        rid=st.number_input('Restaurant ID',1,step=1)
    with c2:
        aid=st.number_input('Agent ID',1,step=1)
        amt=st.number_input('Total Amount',0.0)
    status=st.selectbox('Status',['Preparing','On the Way','Delivered'])
    if st.button('Place Order', use_container_width=True):
        cur.execute('INSERT INTO orders(customer_id,restaurant_id,agent_id,total_amount,status) VALUES(%s,%s,%s,%s,%s)',(cid,rid,aid,amt,status))
        conn.commit()
        st.success('✅ Order placed successfully')

conn.close()
