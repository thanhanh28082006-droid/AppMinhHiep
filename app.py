import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta
import uuid
import plotly.express as px

# --- CẤU HÌNH ---
st.set_page_config(page_title="Tiệm Giặt Sấy Minh Hiệp", page_icon="💰", layout="wide")

st.title("🏪 Tiệm Giặt Sấy Minh Hiệp")
bay_gio = datetime.now() + timedelta(hours=7)
st.write(f"### 📅 {bay_gio.strftime('Ngày %d tháng %m năm %Y')}")
st.markdown("---")

LINK_GOOGLE_SHEETS = "https://docs.google.com/spreadsheets/d/1rNjsqV3OUNtQeYd4OXAb3oNuPrpPj6jv2wZYww9oTw/edit"

@st.cache_resource
def ket_noi_sheets():
    creds_dict = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open_by_url(LINK_GOOGLE_SHEETS)
    return sh.sheet1

try:
    worksheet = ket_noi_sheets()
except Exception as e:
    st.error(f"Lỗi kết nối chi tiết: {e}")
    st.stop()

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

tab1, tab2, tab3, tab4 = st.tabs(["🥤 Trà Tắc", "🧺 Giặt Sấy", "🛠️ Sửa Đồ", "📈 Tổng thu"])

def hien_thi_lich_su_tab(df, ten_dv):
    if not df.empty:
        df_dv = df[df['Dịch Vụ'] == ten_dv]
        tong_thu = df_dv[df_dv['Loại'] == 'Thu']['Số Tiền'].sum()
        tong_chi = df_dv[df_dv['Loại'] == 'Chi']['Số Tiền'].sum()
        st.write("---")
        st.info(f"💰 **Tổng lợi nhuận {ten_dv}: {tong_thu - tong_chi:,.0f}đ** (Thu: {tong_thu:,.0f}đ | Chi: {tong_chi:,.0f}đ)")
        df_loc = df_dv.sort_values(by='Thời Gian', ascending=False).head(5)
        st.dataframe(df_loc[['Thời Gian', 'Loại', 'Hình Thức', 'Tên Khách', 'Số Tiền']], use_container_width=True)

# =========================================================
# TAB 1 - TRÀ TẮC (ĐÃ FIX LỖI STREAMLIT API EXCEPTION)
# =========================================================
with tab1:
    st.header("🥤 Quản lý Trà Tắc")
    ds_mon = {"Chọn Đồ Uống": 0, "Trà tắc (10k)": 10, "Nước cam (20k)": 20, "Trà chanh (15k)": 15}

    if 'tt_tien' not in st.session_state: st.session_state.tt_tien = 0
    if 'tt_ghi_chu' not in st.session_state: st.session_state.tt_ghi_chu = "Khách lẻ"
    if 'tt_mon' not in st.session_state: st.session_state.tt_mon = "Chọn Đồ Uống"

    def auto_dien_gia():
        mon = st.session_state.tt_mon
        st.session_state.tt_tien = ds_mon[mon]
        st.session_state.tt_ghi_chu = "Khách lẻ" if mon == "Chọn Đồ Uống" else mon.split(" (")[0]

    # HÀM XỬ LÝ LƯU (CALLBACK) - GIÚP RESET MÀ KHÔNG LỖI
    def xu_ly_ghi_so_tra_tac():
        if st.session_state.tt_tien > 0:
            worksheet.append_row([
                str(uuid.uuid4())[:8],
                (datetime.now() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"),
                "Trà tắc", 
                "Thu" if "Thu" in st.session_state.tt_loai else "Chi", 
                st.session_state.tt_ht, 
                st.session_state.tt_ghi_chu, 
                st.session_state.tt_tien * 1000
            ])
            st.cache_data.clear()
            # Reset dữ liệu an toàn
            st.session_state.tt_tien = 0
            st.session_state.tt_mon = "Chọn Đồ Uống"
            st.session_state.tt_ghi_chu = "Khách lẻ"
            st.session_state.notif_success = True
        else:
            st.session_state.notif_error = True

    st.selectbox("⚡ Chọn món nhanh:", list(ds_mon.keys()), key='tt_mon', on_change=auto_dien_gia)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.number_input("Số tiền (k):", min_value=0, step=1, key='tt_tien')
        st.radio("Thanh toán:", ["Tiền mặt", "Chuyển khoản"], horizontal=True, key='tt_ht')
    with col_b:
        st.radio("Loại giao dịch:", ["Thu (Doanh thu)", "Chi (Tiền ra)"], key='tt_loai')
        st.text_input("Ghi chú:", key='tt_ghi_chu')

    # Nút bấm gọi hàm Callback
    st.button("Ghi sổ Trà Tắc", use_container_width=True, type="primary", on_click=xu_ly_ghi_so_tra_tac)

    # Hiển thị thông báo
    if st.session_state.get('notif_success'):
        st.success("Đã lưu thành công!")
        st.session_state.notif_success = False
    if st.session_state.get('notif_error'):
        st.warning("Số tiền phải lớn hơn 0")
        st.session_state.notif_error = False

    hien_thi_lich_su_tab(df_all, "Trà tắc")

# =========================================================
# TAB 2 - GIẶT SẤY (GIỮ NGUYÊN)
# =========================================================
with tab2:
    st.header("🧺 Quản lý Giặt Sấy")
    with st.form("form_giat_say"):
        col_a, col_b = st.columns(2)
        with col_a:
            so_tien_gs = st.number_input("Số tiền (k):", min_value=0, step=1)
            hinh_thuc_gs = st.radio("Thanh toán:", ["Tiền mặt", "Chuyển khoản"], horizontal=True)
        with col_b:
            loai_gs = st.radio("Loại giao dịch:", ["Thu (Doanh thu)", "Chi (Tiền ra)"])
            ten_khach_gs = st.text_input("Tên khách:", value="Khách lẻ")
        submit_gs = st.form_submit_button("Ghi sổ Giặt Sấy", use_container_width=True)
        if submit_gs:
            if so_tien_gs <= 0: st.warning("Số tiền phải lớn hơn 0")
            else:
                worksheet.append_row([str(uuid.uuid4())[:8], (datetime.now() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"), "Giặt sấy", "Thu" if "Thu" in loai_gs else "Chi", hinh_thuc_gs, ten_khach_gs, so_tien_gs * 1000])
                st.cache_data.clear()
                st.success("Đã lưu thành công!")
                st.rerun()
    hien_thi_lich_su_tab(df_all, "Giặt sấy")

# =========================================================
# TAB 3 - SỬA ĐỒ (GIỮ NGUYÊN)
# =========================================================
with tab3:
    st.header("🛠️ Quản lý Sửa Đồ")
    with st.form("form_sua_do"):
        col_a, col_b = st.columns(2)
        with col_a:
            so_tien_sd = st.number_input("Số tiền Thu (k):", min_value=0, step=1)
            hinh_thuc_sd = st.radio("Thanh toán:", ["Tiền mặt", "Chuyển khoản"], horizontal=True)
        with col_b:
            ten_khach_sd = st.text_input("Tên khách:", value="Khách lẻ")
        submit_sd = st.form_submit_button("Ghi sổ Sửa Đồ", use_container_width=True)
        if submit_sd:
            if so_tien_sd <= 0: st.warning("Số tiền phải lớn hơn 0")
            else:
                worksheet.append_row([str(uuid.uuid4())[:8], (datetime.now() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"), "Sửa đồ", "Thu", hinh_thuc_sd, ten_khach_sd, so_tien_sd * 1000])
                st.cache_data.clear()
                st.success("Đã lưu thành công!")
                st.rerun()
    hien_thi_lich_su_tab(df_all, "Sửa đồ")

# =========================================================
# TAB 4 - BÁO CÁO (GIỮ NGUYÊN)
# =========================================================
with tab4:
    st.header("📈 Tổng Doanh Thu")
    df = df_all
    if not df.empty:
        df['Ngày'] = df['Thời Gian'].dt.date
        st.write("---")
        st.subheader("📅 Chọn khoảng thời gian")
        ngay_min, ngay_max = df['Ngày'].min(), df['Ngày'].max()
        if pd.isna(ngay_min) or pd.isna(ngay_max):
            st.warning("Chưa có dữ liệu ngày."); st.stop()
        ngay_chon = st.date_input("Lọc báo cáo theo ngày:", value=(ngay_min, ngay_max))
        if len(ngay_chon) == 2:
            df_loc = df[(df['Ngày'] >= ngay_chon[0]) & (df['Ngày'] <= ngay_chon[1])]
        elif len(ngay_chon) == 1:
            df_loc = df[df['Ngày'] == ngay_chon[0]]
        else: df_loc = df.copy()
        if not df_loc.empty:
            thu_all = df_loc[df_loc['Loại'] == 'Thu']['Số Tiền'].sum()
            chi_all = df_loc[df_loc['Loại'] == 'Chi']['Số Tiền'].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 TỔNG DOANH THU", f"{thu_all:,.0f}đ")
            c2.metric("🔻 TỔNG CHI", f"{chi_all:,.0f}đ")
            c3.metric("💎 LỢI NHUẬN", f"{thu_all - chi_all:,.0f}đ")
            st.write("---")
            st.subheader("📊 Biểu đồ doanh thu")
            df_doanh_thu = df_loc[df_loc['Loại'] == 'Thu'].groupby(['Ngày', 'Dịch Vụ'])['Số Tiền'].sum().reset_index()
            fig = px.bar(df_doanh_thu, x='Ngày', y='Số Tiền', color='Dịch Vụ', barmode='stack', text_auto='.2s')
            st.plotly_chart(fig, use_container_width=True)
            st.subheader("📑 Lịch sử giao dịch")
            st.dataframe(df_loc[['Thời Gian', 'Dịch Vụ', 'Loại', 'Hình Thức', 'Số Tiền', 'Tên Khách']].sort_values(by='Thời Gian', ascending=False), use_container_width=True)
        else: st.warning("Không có giao dịch nào trong khoảng thời gian đã chọn.")
    else: st.write("Chưa có dữ liệu.")
