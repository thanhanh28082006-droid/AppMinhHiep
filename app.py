import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import uuid
import plotly.express as px

# --- 1. CẤU HÌNH HỆ THỐNG (KHÔNG ĐỔI) ---
st.set_page_config(page_title="Tiệm Giặt Sấy Minh Hiệp", page_icon="💰", layout="wide")

st.title("🏪 Tiệm Giặt Sấy Minh Hiệp")
bay_gio = datetime.now() + timedelta(hours=7)
st.write(f"### 📅 {bay_gio.strftime('Ngày %d tháng %m năm %Y')}")
st.markdown("---")

# ID Bảng tính của sếp
SHEET_ID = "1rNjsqV3OUNtQeYd4OXAb3oNuPrpPj6jv2wZYww9oTw"

# --- 2. KẾT NỐI DỮ LIỆU (TỐI ƯU CHỐNG LẶP) ---
@st.cache_resource
def ket_noi_sheets():
    creds_dict = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open_by_key(SHEET_ID)
    return sh.sheet1

try:
    worksheet = ket_noi_sheets()
except Exception as e:
    st.error("Lỗi kết nối rồi sếp ơi! Sếp kiểm tra lại Internet hoặc quyền chia sẻ Sheets nhé.")
    st.stop()

# Tự động tải lại dữ liệu mỗi 5 giây, không cần dùng lệnh xóa cache gây chớp màn hình
@st.cache_data(ttl=5)
def lay_du_lieu():
    data = worksheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=['ID', 'Thời Gian', 'Dịch Vụ', 'Loại', 'Hình Thức', 'Tên Khách', 'Số Tiền'])
    df = pd.DataFrame(data)
    df.columns = [str(col).strip().title() for col in df.columns]
    df.columns = ['ID' if col == 'Id' else col for col in df.columns]
    df['Số Tiền'] = pd.to_numeric(df['Số Tiền'], errors='coerce').fillna(0)
    df['Thời Gian'] = pd.to_datetime(df['Thời Gian'], format="%d/%m/%Y %H:%M:%S", errors='coerce')
    return df

df_all = lay_du_lieu()

# --- 3. GIAO DIỆN TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🥤 Trà Tắc", "🧺 Giặt Sấy", "🛠️ Sửa Đồ", "📈 Tổng thu"])

# --- TAB 1: TRÀ TẮC (BẢN FIX TRIỆT ĐỂ CHỚP MÀN HÌNH) ---
with tab1:
    st.header("🥤 Quản lý Trà Tắc")
    ds_mon = {"Chọn Đồ Uống": 0, "Trà tắc (10k)": 10, "Nước cam (20k)": 20, "Trà chanh (15k)": 15}
    
    # Để ngoài form để chọn món là nó nhảy giá ngay (nhưng không bị lặp vì không có logic ghi đè state)
    mon_chon = st.selectbox("⚡ Chọn món nhanh:", list(ds_mon.keys()), key="sb_tra_tac")
    
    # Dùng form để "khóa" hành động ghi, chống tình trạng app tự load lại khi đang nhập
    with st.form("form_tra_tac", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            tien_nhap = st.number_input("Số tiền (k):", min_value=0, step=1, value=ds_mon[mon_chon])
            ht_tt = st.radio("Thanh toán:", ["Tiền mặt", "Chuyển khoản"], horizontal=True)
        with col_b:
            loai_tt = st.radio("Loại giao dịch:", ["Thu (Doanh thu)", "Chi (Tiền ra)"])
            ghi_chu_tt = st.text_input("Ghi chú:", value=("Khách lẻ" if mon_chon == "Chọn Đồ Uống" else mon_chon.split(" (")[0]))
        
        btn_tt = st.form_submit_button("Ghi sổ Trà Tắc", use_container_width=True)
        
        if btn_tt:
            if tien_nhap > 0:
                worksheet.append_row([
                    str(uuid.uuid4())[:8],
                    (datetime.now() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                    "Trà tắc", "Thu" if "Thu" in loai_tt else "Chi", ht_tt, ghi_chu_tt, tien_nhap * 1000
                ])
                st.success("✅ Đã ghi sổ xong! Sếp chờ 5 giây để bảng bên dưới cập nhật nhé.")
            else:
                st.warning("Sếp chưa nhập số tiền kìa!")

    # Hiển thị lịch sử
    df_tt = df_all[df_all['Dịch Vụ'] == 'Trà tắc']
    if not df_tt.empty:
        st.write("---")
        st.dataframe(df_tt.sort_values(by='Thời Gian', ascending=False).head(5), use_container_width=True)

# --- TAB 2: GIẶT SẤY ---
with tab2:
    st.header("🧺 Quản lý Giặt Sấy")
    with st.form("form_gs", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st_gs = st.number_input("Số tiền (k):", min_value=0, step=1)
            ht_gs = st.radio("Thanh toán:", ["Tiền mặt", "Chuyển khoản"], horizontal=True, key="h1")
        with c2:
            l_gs = st.radio("Loại:", ["Thu (Doanh thu)", "Chi (Tiền ra)"], key="l1")
            t_gs = st.text_input("Tên khách:", value="Khách lẻ")
        
        if st.form_submit_button("Ghi sổ Giặt Sấy", use_container_width=True):
            if st_gs > 0:
                worksheet.append_row([str(uuid.uuid4())[:8], (datetime.now() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"), "Giặt sấy", "Thu" if "Thu" in l_gs else "Chi", ht_gs, t_gs, st_gs * 1000])
                st.success("✅ Đã ghi xong!")
    
    df_gs = df_all[df_all['Dịch Vụ'] == 'Giặt sấy']
    st.dataframe(df_gs.sort_values(by='Thời Gian', ascending=False).head(5), use_container_width=True)

# --- TAB 3: SỬA ĐỒ ---
with tab3:
    st.header("🛠️ Quản lý Sửa Đồ")
    with st.form("form_sd", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st_sd = st.number_input("Số tiền Thu (k):", min_value=0, step=1)
            ht_sd = st.radio("Thanh toán:", ["Tiền mặt", "Chuyển khoản"], horizontal=True, key="h2")
        with c2:
            t_sd = st.text_input("Tên khách:", value="Khách lẻ")
        
        if st.form_submit_button("Ghi sổ Sửa Đồ", use_container_width=True):
            if st_sd > 0:
                worksheet.append_row([str(uuid.uuid4())[:8], (datetime.now() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"), "Sửa đồ", "Thu", ht_sd, t_sd, st_sd * 1000])
                st.success("✅ Đã ghi xong!")

    df_sd = df_all[df_all['Dịch Vụ'] == 'Sửa đồ']
    st.dataframe(df_sd.sort_values(by='Thời Gian', ascending=False).head(5), use_container_width=True)

# --- TAB 4: BÁO CÁO (KHÔNG CHỚP) ---
with tab4:
    st.header("📈 Báo Cáo Doanh Thu")
    if not df_all.empty:
        df_all['Ngày'] = df_all['Thời Gian'].dt.date
        thu = df_all[df_all['Loại'] == 'Thu']['Số Tiền'].sum()
        chi = df_all[df_all['Loại'] == 'Chi']['Số Tiền'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 TỔNG THU", f"{thu:,.0f}đ")
        c2.metric("🔻 TỔNG CHI", f"{chi:,.0f}đ")
        c3.metric("💎 LỢI NHUẬN", f"{thu - chi:,.0f}đ")
        
        st.write("---")
        st.subheader("📑 Chi tiết giao dịch")
        st.dataframe(df_all.sort_values(by='Thời Gian', ascending=False), use_container_width=True)
    else:
        st.write("Chưa có dữ liệu sếp ơi!")
