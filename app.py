import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# 1. การตั้งค่าหน้าจอและฟังก์ชันการพิมพ์
# ==========================================
st.set_page_config(layout="wide", page_title="ระบบบริหารจัดการยานพาหนะ ชป.")

# CSS สำหรับซ่อนเมนูและปุ่มตอนสั่งพิมพ์
st.markdown("""
    <style>
    @media print {
        .stButton, .stSidebar, header, footer, .stTabs [data-baseweb="tab-list"] { display: none !important; }
        .st-emotion-cache-1y4p8pa { padding-top: 0rem; }
    }
    </style>
""", unsafe_allow_html=True)

def print_document():
    if st.button("🖨️ สั่งพิมพ์เอกสารหน้านี้"):
        st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        st.info("💡 หากตารางยาว ให้ตั้งค่า Layout เป็น Landscape (แนวนอน) ในหน้าต่างพิมพ์")

# ==========================================
# 2. โครงสร้างฐานข้อมูล (ครอบคลุมทุกช่อง)
# ==========================================
def init_db():
    conn = sqlite3.connect('irrigation_fleet.db')
    c = conn.cursor()
    # ตารางทะเบียนรถ (แบบ 1, 2, 7)
    c.execute('''CREATE TABLE IF NOT EXISTS Vehicles 
                 (v_id TEXT PRIMARY KEY, form_type TEXT, name TEXT, type TEXT, year TEXT, cc INTEGER, 
                  plate TEXT, position TEXT, price REAL, buy_year TEXT, buy_date TEXT, 
                  sell_date TEXT, fuel_type TEXT, rate REAL, remark TEXT)''')
    # ตารางขออนุญาต (แบบ 3, 10)
    c.execute('''CREATE TABLE IF NOT EXISTS Requests 
                 (req_id INTEGER PRIMARY KEY AUTOINCREMENT, form_type TEXT, req_date TEXT, dept TEXT, 
                  name TEXT, position TEXT, vehicle TEXT, passengers INTEGER, tel TEXT, 
                  destination TEXT, purpose TEXT, start_datetime TEXT, end_datetime TEXT)''')
    # ตารางการใช้งาน (แบบ 4)
    c.execute('''CREATE TABLE IF NOT EXISTS Usage 
                 (u_id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, vehicle TEXT, driver TEXT, 
                  dept TEXT, m_start REAL, m_end REAL, total REAL, fuel REAL, lube REAL, cond TEXT, remark TEXT)''')
    # ตารางอุบัติเหตุและซ่อมบำรุง (แบบ 5, 6)
    c.execute('''CREATE TABLE IF NOT EXISTS Maintenance 
                 (m_id INTEGER PRIMARY KEY AUTOINCREMENT, form_type TEXT, date TEXT, vehicle TEXT, 
                  meter REAL, driver TEXT, location TEXT, details TEXT, damage TEXT, cost REAL)''')
    # ตารางมลพิษ (แบบ 9)
    c.execute('''CREATE TABLE IF NOT EXISTS Pollution 
                 (p_id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, vehicle TEXT, co REAL, smoke REAL, noise REAL, result TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ฟังก์ชันดึงรายชื่อรถ
def get_vehicles():
    conn = sqlite3.connect('irrigation_fleet.db')
    df = pd.read_sql_query("SELECT v_id, name, plate FROM Vehicles", conn)
    conn.close()
    return [f"{row['v_id']} ({row['plate']})" for index, row in df.iterrows()]

v_list = get_vehicles()
default_dept = "โครงการส่งน้ำและบำรุงรักษาระโนด-กระแสสินธุ์"

# ==========================================
# 3. หน้าจอหลักและการแบ่งแท็บ
# ==========================================
st.title("🚜 ระบบบริหารจัดการยานพาหนะและเครื่องจักรกล")
tabs = st.tabs(["⚙️ ทะเบียนรถ (แบบ 1,2,7)", "📝 ขอใช้รถ (แบบ 3,10)", "📍 บันทึกใช้ (แบบ 4)", "🛠️ ซ่อม/อุบัติเหตุ (แบบ 5,6)", "💨 ตรวจมลพิษ (แบบ 9)", "📊 รายงานสรุป (แบบ 8)"])

# ------------------------------------------
# แท็บ 1: ทะเบียนรถ (แบบ 1, 2, 7)
# ------------------------------------------
with tabs[0]:
    st.subheader("บัญชีรายการประเภทยานพาหนะ และ เกณฑ์สิ้นเปลือง")
    v_form_type = st.radio("เลือกแบบฟอร์มทะเบียน", ["แบบ 1 (รถประจำตำแหน่ง)", "แบบ 2 (รถส่วนกลาง)"])
    
    with st.form("vehicle_form"):
        st.markdown("**ข้อมูลพื้นฐานยานพาหนะ**")
        c1, c2, c3 = st.columns(3)
        v_id = c1.text_input("หมายเลข ชป. (รหัสหลัก)")
        v_plate = c2.text_input("หมายเลขทะเบียน")
        v_name = c3.text_input("ชื่อของรถ")
        
        v_type = c1.text_input("แบบ / ประเภท")
        v_year = c2.text_input("รุ่นปี")
        v_cc = c3.number_input("ขนาด (ซีซี)", min_value=0)
        
        v_pos = c1.text_input("ประจำตำแหน่งใด / รหัสสังกัด")
        v_price = c2.number_input("ราคา (บาท)", min_value=0.0)
        v_buy_year = c3.text_input("ปีที่ซื้อ")
        
        v_buy_date = c1.text_input("วันได้มา (วันซื้อ/โอน)")
        v_sell_date = c2.text_input("วันจำหน่าย (จ่าย/โอน)")
        
        st.markdown("**แบบ 7: กำหนดเกณฑ์สิ้นเปลือง**")
        c4, c5 = st.columns(2)
        v_fuel = c4.selectbox("ชนิดเชื้อเพลิง", ["ดีเซล", "เบนซิน", "ไฟฟ้า"])
        v_rate = c5.number_input("เกณฑ์สิ้นเปลือง (กม. หรือ ชม./ลิตร)", min_value=0.0)
        v_remark = st.text_input("หมายเหตุ")
        
        if st.form_submit_button("บันทึกข้อมูลรถ (แบบ 1, 2, 7)"):
            if v_id:
                conn = sqlite3.connect('irrigation_fleet.db')
                conn.execute('''INSERT OR REPLACE INTO Vehicles 
                                (v_id, form_type, name, type, year, cc, plate, position, price, buy_year, buy_date, sell_date, fuel_type, rate, remark) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                             (v_id, v_form_type, v_name, v_type, v_year, v_cc, v_plate, v_pos, v_price, v_buy_year, v_buy_date, v_sell_date, v_fuel, v_rate, v_remark))
                conn.commit(); conn.close()
                st.success("✅ บันทึกข้อมูลทะเบียนรถเรียบร้อย")
            else:
                st.error("กรุณากรอก หมายเลข ชป.")
    
    st.markdown("---")
    st.markdown("##### 📄 ข้อมูลสำหรับสั่งพิมพ์บัญชีรายการรถ")
    conn = sqlite3.connect('irrigation_fleet.db')
    df_v = pd.read_sql_query("SELECT v_id as ชป, plate as ทะเบียน, name as ชื่อรถ, type as แบบ, cc as ซีซี, position as ตำแหน่ง_สังกัด, rate as เกณฑ์น้ำมัน FROM Vehicles", conn)
    conn.close()
    st.dataframe(df_v, use_container_width=True, hide_index=True)
    print_document()

# ------------------------------------------
# แท็บ 2: ขอใช้รถ (แบบ 3, 10)
# ------------------------------------------
with tabs[1]:
    req_type = st.radio("ประเภทใบขออนุญาต", ["แบบ 3 (รถส่วนกลาง)", "แบบ 10 (รถส่วนตัว)"])
    st.subheader(f"ใบขออนุญาตใช้ยานพาหนะ ({req_type})")
    
    with st.form("req_form"):
        c1, c2 = st.columns(2)
        r_date = c1.date_input("วันที่ทำรายการ")
        r_dept = c2.text_input("หน่วยงาน / สังกัด", value=default_dept)
        r_name = c1.text_input("ชื่อ-นามสกุล ผู้ขอ")
        r_pos = c2.text_input("ตำแหน่ง")
        
        if req_type == "แบบ 3 (รถส่วนกลาง)":
            r_veh = c1.selectbox("ขอใช้ยานพาหนะ (หมายเลข ชป.)", v_list) if v_list else c1.text_input("ระบุรถ")
        else:
            r_veh = c1.text_input("ข้อมูลรถส่วนตัว (ทะเบียน/ยี่ห้อ)")
            
        r_pass = c2.number_input("จำนวนผู้โดยสาร", min_value=1)
        
        r_dest = st.text_input("สถานที่ไปปฏิบัติงาน / ไปที่ไหน")
        r_purp = st.text_area("เพื่อวัตถุประสงค์")
        
        c3, c4 = st.columns(2)
        r_start = c3.text_input("ตั้งแต่วันที่ และ เวลา")
        r_end = c4.text_input("ถึงวันที่ และ เวลา")
        r_tel = st.text_input("เบอร์โทรศัพท์ติดต่อ / สถานที่ให้ไปรับ")
        
        if st.form_submit_button("บันทึกใบขออนุญาต"):
            conn = sqlite3.connect('irrigation_fleet.db')
            conn.execute('''INSERT INTO Requests (form_type, req_date, dept, name, position, vehicle, passengers, tel, destination, purpose, start_datetime, end_datetime)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', 
                         (req_type, r_date.strftime("%Y-%m-%d"), r_dept, r_name, r_pos, str(r_veh), r_pass, r_tel, r_dest, r_purp, r_start, r_end))
            conn.commit(); conn.close()
            st.success("✅ บันทึกใบขออนุญาตเรียบร้อย")
    print_document()

# ------------------------------------------
# แท็บ 3: บันทึกใช้งาน (แบบ 4)
# ------------------------------------------
with tabs[2]:
    st.subheader("สมุดบันทึกการใช้รถยนต์ ชป. (แบบ 4)")
    with st.form("usage_form"):
        c1, c2 = st.columns(2)
        u_date = c1.date_input("วันที่ปฏิบัติงาน")
        u_veh = c2.selectbox("หมายเลข ชป. / ทะเบียน", v_list) if v_list else c2.text_input("ระบุรถ")
        u_driver = c1.text_input("ชื่อพนักงานขับ (พขร.)")
        u_dept = c2.text_input("หน่วยงาน", value=default_dept)
        
        c3, c4, c5 = st.columns(3)
        u_m1 = c3.number_input("เลขไมล์เริ่มต้น", min_value=0.0)
        u_m2 = c4.number_input("เลขไมล์สิ้นสุด", min_value=0.0)
        u_total = u_m2 - u_m1
        c5.info(f"รวมระยะทาง: {u_total} หน่วย")
        
        c6, c7 = st.columns(2)
        u_fuel = c6.number_input("น้ำมันเชื้อเพลิงที่เติม (ลิตร)", min_value=0.0)
        u_lube = c7.number_input("น้ำมันหล่อลื่นที่เติม (ลิตร)", min_value=0.0)
        
        u_cond = st.selectbox("สภาพยานพาหนะ", ["1.ใช้การได้", "2.กำลังซ่อม", "3.ชำรุดรอซ่อม", "4.ชำรุดรอจำหน่าย", "5.รองาน"])
        u_remark = st.text_input("หมายเหตุ / สถานที่ไป")
        
        if st.form_submit_button("บันทึกการใช้งาน แบบ 4"):
            conn = sqlite3.connect('irrigation_fleet.db')
            conn.execute('''INSERT INTO Usage (date, vehicle, driver, dept, m_start, m_end, total, fuel, lube, cond, remark)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?)''', 
                         (u_date.strftime("%Y-%m-%d"), str(u_veh), u_driver, u_dept, u_m1, u_m2, u_total, u_fuel, u_lube, u_cond, u_remark))
            conn.commit(); conn.close()
            st.success("✅ บันทึกสมุดการใช้งานเรียบร้อย")
            
    st.markdown("---")
    st.markdown("##### 📄 ประวัติการใช้งาน (สำหรับพิมพ์ แบบ 4)")
    conn = sqlite3.connect('irrigation_fleet.db')
    df_u = pd.read_sql_query("SELECT date as วันที่, driver as พนักงานขับ, m_start as ไมล์เริ่ม, m_end as ไมล์จบ, total as ระยะรวม, fuel as เชื้อเพลิง, cond as สภาพรถ FROM Usage ORDER BY u_id DESC LIMIT 30", conn)
    conn.close()
    st.dataframe(df_u, use_container_width=True, hide_index=True)
    print_document()

# ------------------------------------------
# แท็บ 4: ซ่อมบำรุงและอุบัติเหตุ (แบบ 5, 6)
# ------------------------------------------
with tabs[3]:
    m_type = st.radio("เลือกประเภทรายงาน", ["แบบ 6 (ประวัติซ่อมบำรุง)", "แบบ 5 (รายงานอุบัติเหตุ)"])
    st.subheader(f"บันทึกข้อมูล {m_type}")
    
    with st.form("maint_form"):
        c1, c2 = st.columns(2)
        m_date = c1.date_input("วันที่ (ซ่อม/เกิดเหตุ)")
        m_veh = c2.selectbox("หมายเลข ชป.", v_list) if v_list else c2.text_input("ระบุรถ")
        
        if m_type == "แบบ 6 (ประวัติซ่อมบำรุง)":
            m_meter = c1.number_input("เลขไมล์ ณ วันที่ซ่อม", min_value=0.0)
            m_loc = c2.text_input("ชื่ออู่ / สถานที่ซ่อม")
            m_driver = c1.text_input("ช่างผู้ซ่อม / ผู้ควบคุมงาน")
            m_cost = c2.number_input("ค่าซ่อมบำรุงรวม (บาท)", min_value=0.0)
            m_detail = st.text_area("รายการอะไหล่ที่เปลี่ยน / การซ่อมบำรุง")
            m_damage = ""
        else:
            m_meter = 0.0
            m_driver = c1.text_input("ชื่อผู้ขับขี่ขณะเกิดเหตุ")
            m_loc = c2.text_input("สถานที่เกิดเหตุ")
            m_detail = st.text_area("ลักษณะการเกิดเหตุ / สาเหตุ")
            m_damage = st.text_area("ความเสียหาย (รถ ชป. และ คู่กรณี)")
            m_cost = 0.0

        if st.form_submit_button(f"บันทึกข้อมูล {m_type}"):
            conn = sqlite3.connect('irrigation_fleet.db')
            conn.execute('''INSERT INTO Maintenance (form_type, date, vehicle, meter, driver, location, details, damage, cost)
                            VALUES (?,?,?,?,?,?,?,?,?)''', 
                         (m_type, m_date.strftime("%Y-%m-%d"), str(m_veh), m_meter, m_driver, m_loc, m_detail, m_damage, m_cost))
            conn.commit(); conn.close()
            st.success(f"✅ บันทึก {m_type} เรียบร้อย")
    print_document()

# ------------------------------------------
# แท็บ 5: ตรวจมลพิษ (แบบ 9)
# ------------------------------------------
with tabs[4]:
    st.subheader("แบบรายงานการตรวจวัดมลพิษทางอากาศและเสียง (แบบ 9)")
    with st.form("pol_form"):
        c1, c2 = st.columns(2)
        p_date = c1.date_input("วันที่ตรวจสภาพ")
        p_veh = c2.selectbox("หมายเลข ชป.", v_list) if v_list else c2.text_input("ระบุรถ")
        
        c3, c4, c5 = st.columns(3)
        p_co = c3.number_input("ค่า CO (%)", min_value=0.0)
        p_smoke = c4.number_input("ค่าควันดำ (%)", min_value=0.0)
        p_noise = c5.number_input("ระดับเสียง (dBA)", min_value=0.0)
        
        p_res = st.selectbox("ผลการตรวจสภาพ", ["1. ผ่าน", "2. ไม่ผ่าน"])
        
        if st.form_submit_button("บันทึกข้อมูล แบบ 9"):
            conn = sqlite3.connect('irrigation_fleet.db')
            conn.execute('''INSERT INTO Pollution (date, vehicle, co, smoke, noise, result)
                            VALUES (?,?,?,?,?,?)''', (p_date.strftime("%Y-%m-%d"), str(p_veh), p_co, p_smoke, p_noise, p_res))
            conn.commit(); conn.close()
            st.success("✅ บันทึก แบบ 9 เรียบร้อย")
    print_document()

# ------------------------------------------
# แท็บ 6: รายงานสรุป (แบบ 8)
# ------------------------------------------
with tabs[5]:
    st.subheader("บันทึกผลการใช้ การซ่อมบำรุงและสภาพของยานพาหนะ (แบบ 8)")
    st.markdown("ระบบจะประมวลผลดึงข้อมูลจาก แบบ 4 (การใช้งาน) และ แบบ 6 (การซ่อมบำรุง) มารวมให้โดยอัตโนมัติ")
    
    conn = sqlite3.connect('irrigation_fleet.db')
    # Query ที่เชื่อมโยงข้อมูลรถ การใช้งาน และการซ่อมเข้าด้วยกัน
    query = '''
        SELECT 
            v.v_id as หมายเลข_ชป,
            v.plate as ทะเบียน,
            v.name as ชื่อรถ,
            v.type as ประเภท,
            COALESCE(SUM(u.total), 0) as รวมระยะทาง_เวลา,
            COALESCE(SUM(u.fuel), 0) as ใช้น้ำมัน_ลิตร,
            COALESCE(SUM(m.cost), 0) as ค่าซ่อมบำรุง,
            MAX(u.cond) as สภาพรถล่าสุด
        FROM Vehicles v
        LEFT JOIN Usage u ON v.v_id = SUBSTR(u.vehicle, 1, INSTR(u.vehicle, ' ')-1) 
             OR v.v_id = u.vehicle
        LEFT JOIN Maintenance m ON v.v_id = SUBSTR(m.vehicle, 1, INSTR(m.vehicle, ' ')-1) 
             OR v.v_id = m.vehicle AND m.form_type = 'แบบ 6 (ประวัติซ่อมบำรุง)'
        GROUP BY v.v_id
    '''
    try:
        df_summary = pd.read_sql_query(query, conn)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)
    except Exception as e:
        st.info("กรุณาบันทึกข้อมูลรถ (แบบ 1,2) และการใช้งานก่อน ระบบจึงจะแสดงรายงานได้ครับ")
    conn.close()
    
    print_document()