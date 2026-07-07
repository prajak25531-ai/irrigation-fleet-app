import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# 1. สร้างโครงสร้างฐานข้อมูล (ไม่มีข้อมูลจำลอง)
# ==========================================
def init_db():
    conn = sqlite3.connect('irrigation_fleet.db')
    
    # สร้างเฉพาะตารางเปล่าๆ (รองรับ 10 แบบฟอร์ม)
    conn.execute('''CREATE TABLE IF NOT EXISTS Vehicles (vehicle_id TEXT PRIMARY KEY, vehicle_category TEXT, vehicle_type TEXT, consumption_rate REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS Vehicle_Requests (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, name TEXT, vehicle_id TEXT, destination TEXT, purpose TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS Personal_Car_Requests (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, name TEXT, car_info TEXT, destination TEXT, purpose TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS Usage_Logs (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, vehicle_id TEXT, driver TEXT, meter_start REAL, meter_end REAL, total REAL, fuel_added REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS Accident_Logs (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, vehicle_id TEXT, driver TEXT, location TEXT, details TEXT, damage TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS Maintenance_Logs (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, vehicle_id TEXT, meter REAL, details TEXT, cost REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS Pollution_Logs (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, vehicle_id TEXT, co_percent REAL, black_smoke REAL, noise_db REAL, result TEXT)''')
    
    conn.commit()
    conn.close()

init_db()

# ฟังก์ชันสำหรับดึงข้อมูลมาทำตัวเลือก Dropdown
def get_options(query, column):
    conn = sqlite3.connect('irrigation_fleet.db')
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df[column].tolist()

# ==========================================
# 2. ส่วนหน้าจอแอปพลิเคชัน (UI)
# ==========================================
st.set_page_config(page_title="ระบบยานพาหนะ ชป.", layout="wide")
st.title("🚜 ระบบบริหารจัดการยานพาหนะและเครื่องจักรกล (ชป.)")

# ดึงข้อมูลรหัสรถมาเตรียมไว้ (ถ้าลบ DB แล้ว ค่านี้จะว่างเปล่าในตอนแรก)
vehicle_list = get_options("SELECT vehicle_id || ' (' || vehicle_type || ')' as v_info FROM Vehicles", "v_info")

# แบ่งกลุ่มการทำงานเป็นแท็บ
tab_req, tab_use, tab_mnt, tab_pol, tab_rep, tab_set = st.tabs([
    "📝 1. ขอใช้รถ (แบบ 3,10)", 
    "📍 2. บันทึกใช้งาน (แบบ 4)", 
    "🛠️ 3. ซ่อม/อุบัติเหตุ (แบบ 5,6)", 
    "💨 4. ตรวจมลพิษ (แบบ 9)", 
    "📊 5. รายงาน (แบบ 8)", 
    "⚙️ ตั้งค่า (เพิ่มรถเข้าฐานข้อมูล)"
])

# --- แท็บตั้งค่า (แบบ 1, 2, 7) ---
with tab_set:
    st.subheader("➕ ลงทะเบียนยานพาหนะใหม่เข้าสู่ระบบ")
    st.info("💡 กรุณาเพิ่มข้อมูลรถที่นี่ก่อน จึงจะมีรายชื่อรถให้เลือกในแบบฟอร์มอื่นๆ")
    with st.form("add_vehicle"):
        col1, col2 = st.columns(2)
        with col1:
            v_id = st.text_input("หมายเลข ชป. / ทะเบียน (เช่น ข.1234, กค-9999)")
            v_cat = st.selectbox("หมวดหมู่รถ", ["รถส่วนกลาง (แบบ 2)", "รถประจำตำแหน่ง (แบบ 1)"])
        with col2:
            v_type = st.text_input("ประเภท (เช่น รถขุด, รถกระบะ, เครื่องสูบน้ำ)")
            v_rate = st.number_input("เกณฑ์สิ้นเปลือง (แบบ 7) - กม. หรือ ชม./ลิตร", min_value=0.0)
            
        if st.form_submit_button("บันทึกข้อมูลรถใหม่"):
            if v_id:
                try:
                    conn = sqlite3.connect('irrigation_fleet.db')
                    conn.execute("INSERT INTO Vehicles VALUES (?, ?, ?, ?)", (v_id, v_cat, v_type, v_rate))
                    conn.commit(); conn.close()
                    st.success(f"บันทึกข้อมูลรถ {v_id} สำเร็จ! กรุณารีเฟรชหน้าเว็บ 1 ครั้งเพื่อให้ชื่อรถอัปเดต")
                except sqlite3.IntegrityError:
                    st.error("❌ มีหมายเลขรถนี้ในระบบแล้วครับ")

    st.markdown("---")
    st.markdown("**ตารางยานพาหนะในระบบปัจจุบัน**")
    conn = sqlite3.connect('irrigation_fleet.db')
    df_vehicles = pd.read_sql_query("SELECT vehicle_id as หมายเลข_ชป, vehicle_category as หมวดหมู่, vehicle_type as ประเภท, consumption_rate as เกณฑ์สิ้นเปลือง FROM Vehicles", conn)
    conn.close()
    st.dataframe(df_vehicles, use_container_width=True, hide_index=True)

# --- แท็บขออนุญาต (แบบ 3, 10) ---
with tab_req:
    req_type = st.radio("เลือกประเภทการขออนุญาต", ["ขอใช้รถส่วนกลาง (แบบ 3)", "ขอใช้รถส่วนตัวไปราชการ (แบบ 10)"])
    if req_type == "ขอใช้รถส่วนกลาง (แบบ 3)":
        with st.form("form_req_3"):
            req_name = st.text_input("ชื่อผู้ขออนุญาต")
            req_veh = st.selectbox("เลือกรถส่วนกลาง", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มีรถในระบบ กรุณาไปเพิ่มที่แท็บ '⚙️ ตั้งค่า'")
            req_date = st.date_input("วันที่ใช้งาน")
            req_dest = st.text_input("สถานที่ไป")
            req_purpose = st.text_area("วัตถุประสงค์")
            if st.form_submit_button("บันทึกใบขออนุญาต (แบบ 3)"):
                if vehicle_list:
                    v_id = req_veh.split(" ")[0]
                    conn = sqlite3.connect('irrigation_fleet.db')
                    conn.execute("INSERT INTO Vehicle_Requests (date, name, vehicle_id, destination, purpose) VALUES (?,?,?,?,?)", (req_date.strftime("%Y-%m-%d"), req_name, v_id, req_dest, req_purpose))
                    conn.commit(); conn.close()
                    st.success("✅ บันทึก แบบ 3 สำเร็จ")
    else:
        with st.form("form_req_10"):
            req_name = st.text_input("ชื่อผู้ขออนุญาต (แบบ 10)")
            car_info = st.text_input("ข้อมูลรถส่วนตัว (ยี่ห้อ/ทะเบียน)")
            req_date = st.date_input("วันที่เดินทาง")
            req_dest = st.text_input("สถานที่ไปราชการ")
            req_purpose = st.text_area("เหตุผลความจำเป็น")
            if st.form_submit_button("บันทึกขอใช้รถส่วนตัว (แบบ 10)"):
                conn = sqlite3.connect('irrigation_fleet.db')
                conn.execute("INSERT INTO Personal_Car_Requests (date, name, car_info, destination, purpose) VALUES (?,?,?,?,?)", (req_date.strftime("%Y-%m-%d"), req_name, car_info, req_dest, req_purpose))
                conn.commit(); conn.close()
                st.success("✅ บันทึก แบบ 10 สำเร็จ")

# --- แท็บบันทึกใช้งาน (แบบ 4) ---
with tab_use:
    st.subheader("บันทึกการใช้งาน (แบบ 4)")
    with st.form("form_use_4"):
        use_date = st.date_input("วันที่ปฏิบัติงาน")
        use_veh = st.selectbox("เลือกรถ", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มีรถในระบบ กรุณาไปเพิ่มที่แท็บ '⚙️ ตั้งค่า'")
        driver = st.text_input("ชื่อพนักงานขับ / ผู้ควบคุม")
        col1, col2 = st.columns(2)
        with col1: meter_start = st.number_input("เลขไมล์/ชั่วโมง (เริ่มต้น)", min_value=0.0)
        with col2: meter_end = st.number_input("เลขไมล์/ชั่วโมง (สิ้นสุด)", min_value=0.0)
        fuel = st.number_input("เติมน้ำมัน (ลิตร)", min_value=0.0)
        
        if st.form_submit_button("บันทึกข้อมูล (แบบ 4)"):
            if vehicle_list:
                v_id = use_veh.split(" ")[0]
                total = meter_end - meter_start
                conn = sqlite3.connect('irrigation_fleet.db')
                conn.execute("INSERT INTO Usage_Logs (date, vehicle_id, driver, meter_start, meter_end, total, fuel_added) VALUES (?,?,?,?,?,?,?)", (use_date.strftime("%Y-%m-%d"), v_id, driver, meter_start, meter_end, total, fuel))
                conn.commit(); conn.close()
                st.success(f"✅ บันทึกสำเร็จ! ระยะทาง/เวลาที่ใช้: {total} หน่วย")

# --- แท็บซ่อมบำรุงและอุบัติเหตุ (แบบ 5, 6) ---
with tab_mnt:
    mnt_type = st.radio("เลือกการบันทึก", ["บันทึกประวัติซ่อมบำรุง (แบบ 6)", "รายงานอุบัติเหตุ (แบบ 5)"])
    if mnt_type == "บันทึกประวัติซ่อมบำรุง (แบบ 6)":
        with st.form("form_mnt_6"):
            m_date = st.date_input("วันที่ซ่อม")
            m_veh = st.selectbox("เลือกรถที่ซ่อม", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มีรถในระบบ")
            m_meter = st.number_input("เลขไมล์ ณ วันที่ซ่อม", min_value=0.0)
            m_detail = st.text_area("รายการซ่อม")
            m_cost = st.number_input("ค่าซ่อมบำรุง (บาท)", min_value=0.0)
            if st.form_submit_button("บันทึกประวัติซ่อม (แบบ 6)"):
                if vehicle_list:
                    conn = sqlite3.connect('irrigation_fleet.db')
                    conn.execute("INSERT INTO Maintenance_Logs (date, vehicle_id, meter, details, cost) VALUES (?,?,?,?,?)", (m_date.strftime("%Y-%m-%d"), m_veh.split(" ")[0], m_meter, m_detail, m_cost))
                    conn.commit(); conn.close()
                    st.success("✅ บันทึก แบบ 6 สำเร็จ")
    else:
        with st.form("form_acc_5"):
            a_date = st.date_input("วันที่เกิดเหตุ")
            a_veh = st.selectbox("เลือกรถที่เกิดเหตุ", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มีรถในระบบ")
            a_driver = st.text_input("ชื่อผู้ขับขี่ขณะเกิดเหตุ")
            a_loc = st.text_input("สถานที่เกิดเหตุ")
            a_detail = st.text_area("ลักษณะการเกิดเหตุ")
            a_damage = st.text_input("ความเสียหายเบื้องต้น")
            if st.form_submit_button("บันทึกรายงานอุบัติเหตุ (แบบ 5)"):
                if vehicle_list:
                    conn = sqlite3.connect('irrigation_fleet.db')
                    conn.execute("INSERT INTO Accident_Logs (date, vehicle_id, driver, location, details, damage) VALUES (?,?,?,?,?,?)", (a_date.strftime("%Y-%m-%d"), a_veh.split(" ")[0], a_driver, a_loc, a_detail, a_damage))
                    conn.commit(); conn.close()
                    st.success("✅ บันทึก แบบ 5 สำเร็จ")

# --- แท็บตรวจมลพิษ (แบบ 9) ---
with tab_pol:
    st.subheader("รายงานการตรวจวัดมลพิษ (แบบ 9)")
    with st.form("form_pol_9"):
        p_date = st.date_input("วันที่ตรวจ")
        p_veh = st.selectbox("เลือกรถที่ตรวจ", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มีรถในระบบ")
        col1, col2, col3 = st.columns(3)
        with col1: p_co = st.number_input("CO (%)", min_value=0.0)
        with col2: p_smoke = st.number_input("ควันดำ (%)", min_value=0.0)
        with col3: p_noise = st.number_input("ระดับเสียง (dBA)", min_value=0.0)
        p_res = st.selectbox("ผลการตรวจ", ["ผ่าน", "ไม่ผ่าน"])
        
        if st.form_submit_button("บันทึกข้อมูล (แบบ 9)"):
            if vehicle_list:
                conn = sqlite3.connect('irrigation_fleet.db')
                conn.execute("INSERT INTO Pollution_Logs (date, vehicle_id, co_percent, black_smoke, noise_db, result) VALUES (?,?,?,?,?,?)", (p_date.strftime("%Y-%m-%d"), p_veh.split(" ")[0], p_co, p_smoke, p_noise, p_res))
                conn.commit(); conn.close()
                st.success("✅ บันทึก แบบ 9 สำเร็จ")

# --- แท็บรายงานสรุป (แบบ 8) ---
with tab_rep:
    st.subheader("📊 รายงานสรุปผลประจำเดือน (แบบ 8)")
    conn = sqlite3.connect('irrigation_fleet.db')
    
    df_logs = pd.read_sql_query('''
        SELECT u.date as วันที่, u.vehicle_id as หมายเลข_ชป, v.vehicle_type as ประเภท, 
               u.driver as ผู้ควบคุม, u.total as ระยะทาง_หน่วย, u.fuel_added as น้ำมันที่เติม
        FROM Usage_Logs u LEFT JOIN Vehicles v ON u.vehicle_id = v.vehicle_id
        ORDER BY u.id DESC LIMIT 100
    ''', conn)
    
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีประวัติการใช้งานในระบบ")
        
    conn.close()