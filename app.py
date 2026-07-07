import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# 1. โครงสร้างฐานข้อมูลหลัก
# ==========================================
def init_db():
    conn = sqlite3.connect('irrigation_fleet.db')
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

def get_options(query, column):
    conn = sqlite3.connect('irrigation_fleet.db')
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df[column].tolist()

# ==========================================
# ฟังก์ชันพิเศษ: สร้างกล่องเลือกวันที่แบบไทย (วัน/เดือน/ปี พ.ศ.)
# ==========================================
def thai_date_picker(label, key):
    st.markdown(f"**{label}**")
    cols = st.columns([1, 1, 1]) # แบ่งเป็น 3 ช่องเท่าๆ กัน
    today = datetime.today()
    months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
    
    with cols[0]:
        day = st.selectbox("วัน", range(1, 32), index=today.day-1, key=f"day_{key}")
    with cols[1]:
        month = st.selectbox("เดือน", months, index=today.month-1, key=f"month_{key}")
    with cols[2]:
        current_year_be = today.year + 543
        # ให้เลือกย้อนหลังและล่วงหน้าได้ 5 ปี
        years = list(range(current_year_be - 5, current_year_be + 6))
        year = st.selectbox("ปี พ.ศ.", years, index=5, key=f"year_{key}")
        
    return f"{day} {month} {year}"

# ==========================================
# 2. ส่วนหน้าจอแอปพลิเคชัน
# ==========================================
st.set_page_config(page_title="ระบบยานพาหนะ ชป.", layout="wide")
st.title("🚜 ระบบบริหารจัดการเครื่องจักรกลและยานพาหนะ ชป.")
st.markdown("อ้างอิงตามระเบียบยานพาหนะ กรมชลประทาน (ครอบคลุม 10 แบบฟอร์ม)")

vehicle_list = get_options("SELECT vehicle_id || ' (' || vehicle_type || ')' as v_info FROM Vehicles", "v_info")

tab_req, tab_use, tab_mnt, tab_pol, tab_rep, tab_set = st.tabs([
    "📝 ขออนุญาตใช้รถ (แบบ 3,10)", 
    "📍 บันทึกการใช้งาน (แบบ 4)", 
    "🛠️ ซ่อมบำรุง/อุบัติเหตุ (แบบ 5,6)", 
    "💨 ตรวจวัดมลพิษ (แบบ 9)", 
    "📊 รายงานสรุป (แบบ 8)", 
    "⚙️ ตั้งค่าระบบ (แบบ 1,2,7)"
])

# --- แท็บตั้งค่า (แบบ 1, 2, 7) ---
with tab_set:
    st.subheader("➕ บัญชีรายการประเภทยานพาหนะ (แบบ 1, 2 และ 7)")
    with st.form("add_vehicle"):
        col1, col2 = st.columns(2)
        with col1:
            v_id = st.text_input("หมายเลข ชป. / หมายเลขทะเบียน")
            v_cat = st.selectbox("หมวดหมู่รถ", ["ยานพาหนะส่วนกลาง (แบบ 2)", "รถประจำตำแหน่ง (แบบ 1)"])
        with col2:
            v_type = st.text_input("ประเภทรถ (เช่น รถขุดตีนตะขาบ, รถกระบะ, เครื่องสูบน้ำ)")
            v_rate = st.number_input("เกณฑ์การใช้สิ้นเปลืองเชื้อเพลิง (กม./ลิตร หรือ ชม./ลิตร)", min_value=0.0)
            
        if st.form_submit_button("บันทึกข้อมูลยานพาหนะ"):
            if v_id:
                try:
                    conn = sqlite3.connect('irrigation_fleet.db')
                    conn.execute("INSERT INTO Vehicles VALUES (?, ?, ?, ?)", (v_id, v_cat, v_type, v_rate))
                    conn.commit(); conn.close()
                    st.success(f"✅ บันทึกข้อมูลรถ {v_id} สำเร็จ! กรุณารีเฟรชหน้าเว็บ 1 ครั้ง")
                except sqlite3.IntegrityError:
                    st.error("❌ หมายเลขยานพาหนะนี้มีอยู่ในระบบแล้วครับ")

    st.markdown("---")
    st.markdown("**ตารางบัญชียานพาหนะในระบบปัจจุบัน**")
    conn = sqlite3.connect('irrigation_fleet.db')
    df_vehicles = pd.read_sql_query("SELECT vehicle_id as หมายเลข_ชป, vehicle_category as หมวดหมู่, vehicle_type as ประเภท, consumption_rate as เกณฑ์สิ้นเปลือง FROM Vehicles", conn)
    conn.close()
    st.dataframe(df_vehicles, use_container_width=True, hide_index=True)

# --- แท็บขออนุญาต (แบบ 3, 10) ---
with tab_req:
    req_type = st.radio("เลือกประเภทใบขออนุญาต", ["ใบขออนุญาตใช้ยานพาหนะส่วนกลาง (แบบ 3)", "ใบขออนุญาตใช้รถส่วนตัวเดินทางไปราชการ (แบบ 10)"])
    if req_type == "ใบขออนุญาตใช้ยานพาหนะส่วนกลาง (แบบ 3)":
        st.subheader("ใบขออนุญาตใช้ยานพาหนะส่วนกลาง (แบบ 3)")
        with st.form("form_req_3"):
            req_name = st.text_input("ชื่อผู้ขออนุญาต")
            req_veh = st.selectbox("ขอใช้ยานพาหนะประเภท", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มียานพาหนะในระบบ กรุณาไปเพิ่มที่แท็บ '⚙️ ตั้งค่าระบบ'")
            
            # --- เปลี่ยนมาใช้ปฏิทินแบบไทย ---
            req_date = thai_date_picker("วันที่ต้องการใช้งาน", key="req3")
            
            req_dest = st.text_input("ไปที่ไหน / สถานที่ไปปฏิบัติงาน")
            req_purpose = st.text_area("วัตถุประสงค์เพื่อ")
            
            if st.form_submit_button("บันทึกใบขออนุญาต (แบบ 3)"):
                if vehicle_list:
                    v_id = req_veh.split(" ")[0]
                    conn = sqlite3.connect('irrigation_fleet.db')
                    conn.execute("INSERT INTO Vehicle_Requests (date, name, vehicle_id, destination, purpose) VALUES (?,?,?,?,?)", (req_date, req_name, v_id, req_dest, req_purpose))
                    conn.commit(); conn.close()
                    st.success("✅ บันทึกใบขออนุญาตใช้ยานพาหนะส่วนกลาง สำเร็จ!")
                    
    else:
        st.subheader("ใบขออนุญาตใช้รถส่วนตัวเดินทางไปราชการ (แบบ 10)")
        with st.form("form_req_10"):
            req_name = st.text_input("ชื่อผู้ขออนุญาต")
            car_info = st.text_input("ข้อมูลรถส่วนตัว (ยี่ห้อ / หมายเลขทะเบียน)")
            
            # --- เปลี่ยนมาใช้ปฏิทินแบบไทย ---
            req_date = thai_date_picker("วันที่เดินทาง", key="req10")
            
            req_dest = st.text_input("สถานที่เดินทางไปราชการ")
            req_purpose = st.text_area("เหตุผลความจำเป็น")
            
            if st.form_submit_button("บันทึกใบขออนุญาต (แบบ 10)"):
                conn = sqlite3.connect('irrigation_fleet.db')
                conn.execute("INSERT INTO Personal_Car_Requests (date, name, car_info, destination, purpose) VALUES (?,?,?,?,?)", (req_date, req_name, car_info, req_dest, req_purpose))
                conn.commit(); conn.close()
                st.success("✅ บันทึกใบขออนุญาตใช้รถส่วนตัว สำเร็จ!")

# --- แท็บบันทึกใช้งาน (แบบ 4) ---
with tab_use:
    st.subheader("สมุดบันทึกการใช้รถยนต์ ชป. (แบบ 4)")
    with st.form("form_use_4"):
        
        # --- เปลี่ยนมาใช้ปฏิทินแบบไทย ---
        use_date = thai_date_picker("วันที่ปฏิบัติงาน", key="use4")
        
        use_veh = st.selectbox("เลือกยานพาหนะ / เครื่องจักรกล", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มียานพาหนะในระบบ")
        driver = st.text_input("ชื่อผู้ควบคุมยานพาหนะ / พนักงานขับ")
        
        col1, col2 = st.columns(2)
        with col1: meter_start = st.number_input("เลขไมล์ / ชั่วโมง (เริ่มต้น)", min_value=0.0)
        with col2: meter_end = st.number_input("เลขไมล์ / ชั่วโมง (สิ้นสุด)", min_value=0.0)
        
        fuel = st.number_input("ปริมาณน้ำมันเชื้อเพลิงที่เติม (ลิตร)", min_value=0.0)
        
        if st.form_submit_button("บันทึกข้อมูลการใช้งาน (แบบ 4)"):
            if vehicle_list:
                if meter_end < meter_start:
                    st.error("❌ เลขไมล์ตอนสิ้นสุด ต้องมากกว่าตอนเริ่มต้นครับ")
                else:
                    v_id = use_veh.split(" ")[0]
                    total = meter_end - meter_start
                    conn = sqlite3.connect('irrigation_fleet.db')
                    conn.execute("INSERT INTO Usage_Logs (date, vehicle_id, driver, meter_start, meter_end, total, fuel_added) VALUES (?,?,?,?,?,?,?)", (use_date, v_id, driver, meter_start, meter_end, total, fuel))
                    conn.commit(); conn.close()
                    st.success(f"✅ บันทึกสำเร็จ! รวมระยะทาง/เวลา: {total} หน่วย")

# --- แท็บซ่อมบำรุงและอุบัติเหตุ (แบบ 5, 6) ---
with tab_mnt:
    mnt_type = st.radio("เลือกประเภทการบันทึก", ["บันทึกประวัติซ่อมบำรุง (แบบ 6)", "รายงานอุบัติเหตุ (แบบ 5)"])
    if mnt_type == "บันทึกประวัติซ่อมบำรุง (แบบ 6)":
        st.subheader("บันทึกประวัติซ่อมบำรุงยานพาหนะ (แบบ 6)")
        with st.form("form_mnt_6"):
            
            # --- เปลี่ยนมาใช้ปฏิทินแบบไทย ---
            m_date = thai_date_picker("วันตรวจรับ / วันที่เข้าซ่อม", key="mnt6")
            
            m_veh = st.selectbox("เลือกยานพาหนะที่ซ่อม", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มียานพาหนะในระบบ")
            m_meter = st.number_input("เลขไมล์ / ชั่วโมง (ณ วันที่ซ่อม)", min_value=0.0)
            m_detail = st.text_area("รายละเอียดการซ่อมบำรุง")
            m_cost = st.number_input("จำนวนเงินที่ซ่อม (บาท)", min_value=0.0)
            
            if st.form_submit_button("บันทึกประวัติการซ่อม (แบบ 6)"):
                if vehicle_list:
                    conn = sqlite3.connect('irrigation_fleet.db')
                    conn.execute("INSERT INTO Maintenance_Logs (date, vehicle_id, meter, details, cost) VALUES (?,?,?,?,?)", (m_date, m_veh.split(" ")[0], m_meter, m_detail, m_cost))
                    conn.commit(); conn.close()
                    st.success("✅ บันทึกประวัติการซ่อมบำรุง สำเร็จ!")
                    
    else:
        st.subheader("แบบรายงานอุบัติเหตุ (แบบ 5)")
        with st.form("form_acc_5"):
            
            # --- เปลี่ยนมาใช้ปฏิทินแบบไทย ---
            a_date = thai_date_picker("วันที่เกิดเหตุ", key="acc5")
            
            a_veh = st.selectbox("เลือกยานพาหนะที่เกิดเหตุ", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มียานพาหนะในระบบ")
            a_driver = st.text_input("ชื่อผู้ขับขี่ขณะเกิดเหตุ")
            a_loc = st.text_input("สถานที่เกิดเหตุ")
            a_detail = st.text_area("ลักษณะการเกิดเหตุ (โดยสังเขป)")
            a_damage = st.text_input("ความเสียหายเบื้องต้น")
            
            if st.form_submit_button("บันทึกรายงานอุบัติเหตุ (แบบ 5)"):
                if vehicle_list:
                    conn = sqlite3.connect('irrigation_fleet.db')
                    conn.execute("INSERT INTO Accident_Logs (date, vehicle_id, driver, location, details, damage) VALUES (?,?,?,?,?,?)", (a_date, a_veh.split(" ")[0], a_driver, a_loc, a_detail, a_damage))
                    conn.commit(); conn.close()
                    st.success("✅ บันทึกรายงานอุบัติเหตุ สำเร็จ!")

# --- แท็บตรวจมลพิษ (แบบ 9) ---
with tab_pol:
    st.subheader("แบบรายงานการตรวจวัดมลพิษทางอากาศและเสียง (แบบ 9)")
    with st.form("form_pol_9"):
        
        # --- เปลี่ยนมาใช้ปฏิทินแบบไทย ---
        p_date = thai_date_picker("วันที่ตรวจสภาพ", key="pol9")
        
        p_veh = st.selectbox("เลือกยานพาหนะที่ตรวจ", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มียานพาหนะในระบบ")
        col1, col2, col3 = st.columns(3)
        with col1: p_co = st.number_input("ค่า CO (%)", min_value=0.0)
        with col2: p_smoke = st.number_input("ค่าควันดำ (%)", min_value=0.0)
        with col3: p_noise = st.number_input("ระดับเสียง (dBA)", min_value=0.0)
        p_res = st.selectbox("ผลการตรวจสภาพ", ["๑. ผ่าน", "๒. ไม่ผ่าน"])
        
        if st.form_submit_button("บันทึกข้อมูลการตรวจวัด (แบบ 9)"):
            if vehicle_list:
                conn = sqlite3.connect('irrigation_fleet.db')
                conn.execute("INSERT INTO Pollution_Logs (date, vehicle_id, co_percent, black_smoke, noise_db, result) VALUES (?,?,?,?,?,?)", (p_date, p_veh.split(" ")[0], p_co, p_smoke, p_noise, p_res))
                conn.commit(); conn.close()
                st.success("✅ บันทึกแบบรายงานการตรวจวัดมลพิษ สำเร็จ!")

# --- แท็บรายงานสรุป (แบบ 8) ---
with tab_rep:
    st.subheader("บันทึกผลการใช้ การซ่อมบำรุงและสภาพของยานพาหนะ (แบบ 8)")
    conn = sqlite3.connect('irrigation_fleet.db')
    
    df_logs = pd.read_sql_query('''
        SELECT u.date as วันที่, u.vehicle_id as หมายเลข_ชป, v.vehicle_type as ประเภท, 
               u.driver as ผู้ควบคุม, u.total as ระยะทางหรือเวลา, u.fuel_added as เชื้อเพลิง_ลิตร
        FROM Usage_Logs u LEFT JOIN Vehicles v ON u.vehicle_id = v.vehicle_id
        ORDER BY u.id DESC LIMIT 100
    ''', conn)
    
    if not df_logs.empty:
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีข้อมูลการใช้งานในระบบ")
        
    conn.close()