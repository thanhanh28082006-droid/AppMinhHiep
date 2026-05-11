import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
import uuid
import plotly.express as px

# --- CẤU HÌNH ---
st.set_page_config(page_title="Tiệm Giặt Sấy Minh Hiệp", page_icon="💰", layout="wide")

st.title("🏪 Tiệm Giặt Sấy Minh Hiệp")
bay_gio = datetime.now()
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
    st.error("Lỗi kết nối! Hãy kiểm tra lại Secrets hoặc Link Sheets.")
    st.stop()


def lay_du_lieu():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df.columns = [str(col).strip().title() for col in df.columns]
        df.columns = ['ID' if col == 'Id' else col for col in df.columns]
        df['Số Tiền'] = pd.to_numeric(df['Số Tiền'], errors='coerce').fillna(0)
        df['Thời Gian'] = pd.to_datetime(df['Thời Gian'], format="%d/%m/%Y %H:%M:%S", errors='coerce')
    return df


# --- GIAO DIỆN TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🥤 Trà Tắc", "🧺 Giặt Sấy", "🛠️ Sửa Đồ", "📈 Báo Cáo Tổng"])

# --- TAB 1: TRÀ TẮC (CÓ CHỌN MÓN NHANH) ---
with tab1:
    st.header("🥤 Quản lý Trà Tắc")

    # Menu chọn món nhanh
    st.subheader("⚡ Chọn món nhanh")
    ds_mon = {
        "Tự nhập số tiền": 0,
        "Trà tắc (10k)": 10,
        "Nước cam (20k)": 20,
        "Trà chanh (15k)": 15
    }
    chon_mon = st.selectbox("Tích chọn món khách gọi:", list(ds_mon.keys()))

    # Lấy giá và tên món mặc định
    gia_mac_dinh = ds_mon[chon_mon]
    ten_mac_dinh = "Khách lẻ" if chon_mon == "Tự nhập số tiền" else chon_mon.split(" (")[0]

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        so_tien = st.number_input("Số tiền (k):", min_value=0, step=1, value=gia_mac_dinh, key="amt_tra_tac")
        hinh_thuc = st.radio("Thanh toán:", ["Tiền mặt", "Chuyển khoản"], horizontal=True, key="ht_tra_tac")
    with col_b:
        loai = st.radio("Loại giao dịch:", ["Thu (Doanh thu)", "Chi (Tiền ra)"], key="loai_tra_tac")
        ten_khach = st.text_input("Ghi chú / Tên khách:", value=ten_mac_dinh, key="khach_tra_tac")

    if st.button("Ghi sổ Trà Tắc", use_container_width=True, type="primary"):
        if so_tien > 0:
            thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            loai_clean = "Thu" if "Thu" in loai else "Chi"
            worksheet.append_row(
                [str(uuid.uuid4())[:8], thoi_gian, "Trà tắc", loai_clean, hinh_thuc, ten_khach, so_tien * 1000])
            st.success(f"✅ Đã ghi: {loai_clean} {ten_khach} - {so_tien}k ({hinh_thuc})")
            st.rerun()

# --- TAB 2: GIẶT SẤY ---
with tab2:
    st.header("🧺 Quản lý Giặt Sấy")
    col_a, col_b = st.columns(2)
    with col_a:
        so_tien_gs = st.number_input("Số tiền (k):", min_value=0, step=1, key="amt_gs")
        hinh_thuc_gs = st.radio("Thanh toán:", ["Tiền mặt", "Chuyển khoản"], horizontal=True, key="ht_gs")
    with col_b:
        loai_gs = st.radio("Loại giao dịch:", ["Thu (Doanh thu)", "Chi (Tiền ra)"], key="loai_gs")
        ten_khach_gs = st.text_input("Tên khách / Ghi chú:", value="Khách lẻ", key="khach_gs")

    if st.button("Ghi sổ Giặt Sấy", use_container_width=True, type="primary"):
        if so_tien_gs > 0:
            thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            loai_c = "Thu" if "Thu" in loai_gs else "Chi"
            worksheet.append_row(
                [str(uuid.uuid4())[:8], thoi_gian, "Giặt sấy", loai_c, hinh_thuc_gs, ten_khach_gs, so_tien_gs * 1000])
            st.success(f"✅ Đã lưu đơn Giặt Sấy {so_tien_gs}k")
            st.rerun()

# --- TAB 3: SỬA ĐỒ ---
with tab3:
    st.header("🛠️ Quản lý Sửa Đồ")
    col_a, col_b = st.columns(2)
    with col_a:
        so_tien_sd = st.number_input("Số tiền Thu (k):", min_value=0, step=1, key="amt_sd")
        hinh_thuc_sd = st.radio("Thanh toán:", ["Tiền mặt", "Chuyển khoản"], horizontal=True, key="ht_sd")
    with col_b:
        ten_khach_sd = st.text_input("Tên khách:", value="Khách lẻ", key="khach_sd")

    if st.button("Ghi sổ Sửa Đồ", use_container_width=True, type="primary"):
        if so_tien_sd > 0:
            thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            worksheet.append_row(
                [str(uuid.uuid4())[:8], thoi_gian, "Sửa đồ", "Thu", hinh_thuc_sd, ten_khach_sd, so_tien_sd * 1000])
            st.success(f"✅ Đã lưu đơn Sửa Đồ {so_tien_sd}k")
            st.rerun()

# --- TAB 4: BÁO CÁO TỔNG ---
with tab4:
    st.header("📈 Báo Cáo Doanh Thu & Lợi Nhuận")
    df = lay_du_lieu()
    if not df.empty:
        dich_vus = ["Trà tắc", "Giặt sấy", "Sửa đồ"]
        tong_ln = 0
        cols = st.columns(3)
        for i, dv in enumerate(dich_vus):
            with cols[i]:
                st.subheader(f"{dv}")
                thu = df[(df['Dịch Vụ'] == dv) & (df['Loại'] == 'Thu')]['Số Tiền'].sum()
                chi = df[(df['Dịch Vụ'] == dv) & (df['Loại'] == 'Chi')]['Số Tiền'].sum()
                tm = df[(df['Dịch Vụ'] == dv) & (df['Hình Thức'] == 'Tiền mặt') & (df['Loại'] == 'Thu')][
                    'Số Tiền'].sum()
                ck = df[(df['Dịch Vụ'] == dv) & (df['Hình Thức'] == 'Chuyển khoản') & (df['Loại'] == 'Thu')][
                    'Số Tiền'].sum()
                ln = thu - chi
                tong_ln += ln
                st.write(f"💵 Tiền mặt: **{tm:,.0f}đ**")
                st.write(f"💳 Chuyển khoản: **{ck:,.0f}đ**")
                st.write(f"🔻 Tổng Chi: **{chi:,.0f}đ**")
                st.metric(f"💰 Lợi nhuận", f"{ln:,.0f}đ")

        st.divider()
        st.metric("💎 TỔNG LỢI NHUẬN CỬA HÀNG", f"{tong_ln:,.0f}đ")

        df['Ngày'] = df['Thời Gian'].dt.date
        df_ngay = df.groupby(['Ngày', 'Loại'])['Số Tiền'].sum().unstack(fill_value=0)
        if 'Thu' not in df_ngay: df_ngay['Thu'] = 0
        if 'Chi' not in df_ngay: df_ngay['Chi'] = 0
        df_ngay['Lợi Nhuận'] = df_ngay['Thu'] - df_ngay['Chi']
        fig = px.line(df_ngay.reset_index(), x='Ngày', y='Lợi Nhuận', title="Biểu đồ lợi nhuận theo ngày")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Chưa có dữ liệu.")