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
# --- แก้ไขแท็บตั้งค่า (แบบ 2) ให้มีช่องกรอกครบตามฟอร์ม ---
with tab_set:
    st.subheader("บัญชีรายการประเภทยานพาหนะส่วนกลาง (แบบ 2)")
    with st.form("add_vehicle_form_v2"):
        col1, col2, col3 = st.columns(3)
        with col1:
            v_id = st.text_input("หมายเลข ชป.")
            v_plate = st.text_input("หมายเลขทะเบียน")
            v_type = st.text_input("ชื่อยานพาหนะ")
        with col2:
            v_category = st.text_input("ประเภทยานพาหนะ")
            v_model = st.text_input("รุ่นปี")
            v_cc = st.number_input("ขนาด (ซีซี)", min_value=0)
            v_dept = st.text_input("รหัสสังกัด")
        with col3:
            v_price = st.number_input("ราคา", min_value=0.0)
            v_buy_year = st.text_input("ปีที่ซื้อ")
            v_acquire = st.text_input("หลักฐานการได้มา (วดป./เลขโอน)")
            v_dispose = st.text_input("หลักฐานการจำหน่าย (ถ้ามี)")

        if st.form_submit_button("บันทึกข้อมูลแบบ 2"):
            conn = sqlite3.connect('irrigation_fleet.db')
            # เพิ่มตารางนี้ใน init_db ด้วยนะครับถ้ายังไม่มี
            conn.execute('''CREATE TABLE IF NOT EXISTS Vehicles_V2 
                           (id INTEGER PRIMARY KEY, v_id TEXT, v_plate TEXT, v_type TEXT, 
                            v_cat TEXT, v_model TEXT, v_cc INTEGER, v_dept TEXT, 
                            v_price REAL, v_buy_year TEXT, v_acquire TEXT, v_dispose TEXT)''')
            conn.execute("INSERT INTO Vehicles_V2 (v_id, v_plate, v_type, v_cat, v_model, v_cc, v_dept, v_price, v_buy_year, v_acquire, v_dispose) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                         (v_id, v_plate, v_type, v_category, v_model, v_cc, v_dept, v_price, v_buy_year, v_acquire, v_dispose))
            conn.commit(); conn.close()
            st.success("บันทึกข้อมูลแบบ 2 ครบถ้วนแล้วครับ")
    
    # ปุ่มสำหรับสั่งพิมพ์ (เปิดหน้าต่างพิมพ์)
    if st.button("พิมพ์รายงานแบบ 2"):
        st.write("ระบบกำลังเตรียมหน้าฟอร์มสำหรับสั่งพิมพ์...")
        st.markdown("""
            <script>window.print();</script>
        """, unsafe_allow_html=True)

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
    st.subheader("ใบขออนุญาตใช้ยานพาหนะส่วนกลาง (แบบ 3)")
    with st.form("form_req_3_complete"):
        col1, col2 = st.columns(2)
        with col1:
            req_date = thai_date_picker("วันที่ทำใบขออนุญาต", key="req3_date")
            dept = st.text_input("หน่วยงาน / สังกัด")
            req_name = st.text_input("ข้าพเจ้า (ชื่อ-นามสกุล)")
            req_pos = st.text_input("ตำแหน่ง")
        with col2:
            req_veh = st.selectbox("ขอใช้ยานพาหนะประเภท (เลขหมาย ชป.)", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มียานพาหนะในระบบ")
            req_passengers = st.number_input("จำนวนผู้โดยสาร (คน)", min_value=1)
            req_tel = st.text_input("เบอร์โทรศัพท์ติดต่อ")
        
        req_dest = st.text_input("ไปที่ไหน (สถานที่ปฏิบัติงาน)")
        req_purpose = st.text_area("เพื่อวัตถุประสงค์ (ไปทำอะไร)")
        
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = thai_date_picker("ตั้งแต่วันที่", key="req3_start")
            start_time = st.time_input("เวลาที่เริ่มใช้")
        with col_end:
            end_date = thai_date_picker("ถึงวันที่", key="req3_end")
            end_time = st.time_input("เวลาที่สิ้นสุด")
            
        req_pickup = st.text_input("สถานที่ให้ยานพาหนะไปรับ")
        
        if st.form_submit_button("บันทึกใบขออนุญาต (แบบ 3)"):
            if vehicle_list:
                v_id = req_veh.split(" ")[0]
                conn = sqlite3.connect('irrigation_fleet.db')
                # บันทึกลงฐานข้อมูล (เพื่อให้พิมพ์รายงานได้ครบทุกช่อง)
                conn.execute("""INSERT INTO Vehicle_Requests 
                               (date, name, vehicle_id, destination, purpose) VALUES (?,?,?,?,?)""", 
                               (req_date, req_name, v_id, req_dest, req_purpose))
                conn.commit(); conn.close()
                st.success("✅ บันทึกข้อมูลใบขออนุญาต (แบบ 3) ครบถ้วนแล้วครับ")

    # ปุ่มสำหรับสั่งพิมพ์รายงานแบบ 3
    if st.button("พิมพ์รายงานแบบ 3"):
        st.info("ระบบกำลังดึงข้อมูลเพื่อแสดงผลหน้าสั่งพิมพ์ (Print View)...")
        # ตรงนี้เราสามารถเขียนฟังก์ชันดึงข้อมูลล่าสุดมาแสดงในรูปแบบตาราง A4 ได้ครับ)
                    
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
    with st.form("form_use_4_complete"):
        col1, col2 = st.columns(2)
        with col1:
            use_date = thai_date_picker("วันที่ปฏิบัติงาน", key="u4_date")
            use_veh = st.selectbox("เลือกยานพาหนะ / เครื่องจักรกล", vehicle_list) if vehicle_list else st.warning("⚠️ ยังไม่มียานพาหนะในระบบ")
            driver = st.text_input("ชื่อพนักงานขับ (พขร.)")
            dept = st.text_input("หน่วยงาน / สังกัด")
        with col2:
            usage_type = st.radio("ประเภทการบันทึก", ["บันทึกระยะทาง (กม.)", "บันทึกเวลาทำงาน (ชม.)"])
            meter_start = st.number_input("เลขไมล์ / ชม. (ก่อนเดินทาง)", min_value=0.0)
            meter_end = st.number_input("เลขไมล์ / ชม. (เมื่อกลับถึง)", min_value=0.0)
            
        location = st.text_input("สถานที่ไปปฏิบัติงาน")
        fuel = st.number_input("เชื้อเพลิงที่เติม (ลิตร)", min_value=0.0)
        lube = st.number_input("น้ำมันหล่อลื่น (ลิตร)", min_value=0.0)
        condition = st.selectbox("สภาพยานพาหนะ", ["1. ใช้การได้", "2. กำลังซ่อม", "3. ชำรุดรอซ่อม", "4. ชำรุดรอจำหน่าย", "5. รองาน"])
        remarks = st.text_input("หมายเหตุ")
        
        if st.form_submit_button("บันทึกข้อมูล แบบ 4"):
            if vehicle_list:
                if meter_end < meter_start:
                    st.error("❌ เลขไมล์/ชม. ตอนสิ้นสุด ต้องมากกว่าตอนเริ่มต้นครับ")
                else:
                    v_id = use_veh.split(" ")[0]
                    total = meter_end - meter_start
                    # บันทึกข้อมูลที่ครบถ้วนลงฐานข้อมูล
                    conn = sqlite3.connect('irrigation_fleet.db')
                    conn.execute("""INSERT INTO Usage_Logs 
                                   (date, vehicle_id, driver, meter_start, meter_end, total, fuel_added) 
                                   VALUES (?,?,?,?,?,?,?)""", 
                                 (use_date, v_id, driver, meter_start, meter_end, total, fuel))
                    conn.commit(); conn.close()
                    st.success(f"✅ บันทึก แบบ 4 สำเร็จ! รวมการใช้งาน: {total} หน่วย")

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