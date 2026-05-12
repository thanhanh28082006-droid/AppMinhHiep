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

LINK_GOOGLE_SHEETS = "https://docs.google.com/spreadsheets/d/1rNjsqV3OUNtQeYd4OXAb3oNuPrpPj6jv2wZYvwv9oTw/edit?gid=0#gid=0"

@st.cache_resource
def ket_noi_sheets():
    # Kết nối qua Secrets (GitHub/Streamlit Cloud)
    creds_dict = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open_by_url(LINK_GOOGLE_SHEETS)
    return sh.sheet1

try:
    worksheet = ket_noi_sheets()
except Exception as e:
    st.error(f"Lỗi kết nối chi tiết: {e}")
    st.stop()

# --- CHỖ SỬA SỐ 1: BẬT BỘ NHỚ ĐỆM (CACHE) ---
@st.cache_data(ttl=120) 
def lay_du_lieu():
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        # Chuẩn hóa tên cột
        df.columns = [str(col).strip().title() for col in df.columns]
        df.columns = ['ID' if col == 'Id' else col for col in df.columns]
        # Xử lý định dạng
        df['Số Tiền'] = pd.to_numeric(df['Số Tiền'], errors='coerce').fillna(0)
        df['Thời Gian'] = pd.to_datetime(df['Thời Gian'], format="%d/%m/%Y %H:%M:%S", errors='coerce')
    return df

# --- CHỖ SỬA SỐ 2: TẢI DỮ LIỆU ĐÚNG 1 LẦN DÙNG CHO TOÀN BỘ APP ---
df_main = lay_du_lieu()

# --- GIAO DIỆN TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🥤 Trà Tắc", "🧺 Giặt Sấy", "🛠️ Sửa Đồ", "📈 Tổng thu"])

# --- HÀM HIỂN THỊ LỊCH SỬ NHANH DƯỚI MỖI TAB ---
def hien_thi_lich_su_tab(df, ten_dv):
    if not df.empty:
        # --- BẮT ĐẦU ĐOẠN THÊM TỔNG TIỀN ---
        df_dv = df[df['Dịch Vụ'] == ten_dv]
        tong_thu = df_dv[df_dv['Loại'] == 'Thu']['Số Tiền'].sum()
        tong_chi = df_dv[df_dv['Loại'] == 'Chi']['Số Tiền'].sum()
        
        st.write(f"---")
        st.info(f"💰 **Tổng lợi nhuận {ten_dv}: {tong_thu - tong_chi:,.0f}đ** (Thu: {tong_thu:,.0f}đ | Chi: {tong_chi:,.0f}đ)")
        # --- KẾT THÚC ĐOẠN THÊM TỔNG TIỀN ---
        
        st.write(f"🔔 **Đơn hàng {ten_dv} vừa nhập:**")
        df_loc = df_dv.sort_values(by='Thời Gian', ascending=False).head(5)
        st.dataframe(df_loc[['Thời Gian', 'Loại', 'Hình Thức', 'Tên Khách', 'Số Tiền']], use_container_width=True)

# --- TAB 1: TRÀ TẮC ---
with tab1:
    st.header("🥤 Quản lý Trà Tắc")
    ds_mon = {"Chọn Đồ Uống": 0, "Trà tắc (10k)": 10, "Nước cam (20k)": 20, "Trà chanh (15k)": 15}
    chon_mon = st.selectbox("⚡ Chọn món nhanh:", list(ds_mon.keys()))
    
    col_a, col_b = st.columns(2)
    with col_a:
        # Ép làm mới ô số tiền bằng cách thay đổi key theo món đang chọn
        so_tien = st.number_input("Số tiền (k):", min_value=0, step=1, value=ds_mon[chon_mon], key=f"amt_tra_tac_{chon_mon}")
        hinh_thuc = st.radio("Thanh toán:", ["Tiền mặt", "Chuyển khoản"], horizontal=True, key="ht_tra_tac")
    with col_b:
        loai = st.radio("Loại giao dịch:", ["Thu (Doanh thu)", "Chi (Tiền ra)"], key="loai_tra_tac")
        ten_mac_dinh = "Khách lẻ" if chon_mon == "Tự nhập số" else chon_mon.split(" (")[0]
        # Ép làm mới ô ghi chú
        ten_khach = st.text_input("Ghi chú:", value=ten_mac_dinh, key=f"khach_tra_tac_{chon_mon}")

    if st.button("Ghi sổ Trà Tắc", use_container_width=True, type="primary"):
        if so_tien > 0:
            worksheet.append_row([str(uuid.uuid4())[:8], (datetime.now() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"), "Trà tắc", "Thu" if "Thu" in loai else "Chi", hinh_thuc, ten_khach, so_tien * 1000])
            st.success("Đã lưu thành công!")
            st.cache_data.clear() # CHỖ SỬA SỐ 3: XÓA ĐỆM KHI GHI SỔ
            st.rerun()
    
    hien_thi_lich_su_tab(df_main, "Trà tắc")

# --- TAB 2: GIẶT SẤY ---
with tab2:
    st.header("🧺 Quản lý Giặt Sấy")
    col_a, col_b = st.columns(2)
    with col_a:
        so_tien_gs = st.number_input("Số tiền (k):", min_value=0, step=1, key="amt_gs")
        hinh_thuc_gs = st.radio("Thanh toán:", ["Tiền mặt", "Chuyển khoản"], horizontal=True, key="ht_gs")
    with col_b:
        loai_gs = st.radio("Loại giao dịch:", ["Thu (Doanh thu)", "Chi (Tiền ra)"], key="loai_gs")
        ten_khach_gs = st.text_input("Tên khách:", value="Khách lẻ", key="khach_gs")

    if st.button("Ghi sổ Giặt Sấy", use_container_width=True, type="primary"):
        if so_tien_gs > 0:
            worksheet.append_row([str(uuid.uuid4())[:8], (datetime.now() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"), "Giặt sấy", "Thu" if "Thu" in loai_gs else "Chi", hinh_thuc_gs, ten_khach_gs, so_tien_gs * 1000])
            st.cache_data.clear() # CHỖ SỬA SỐ 3
            st.rerun()
    
    hien_thi_lich_su_tab(df_main, "Giặt sấy")

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
            worksheet.append_row([str(uuid.uuid4())[:8], (datetime.now() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S"), "Sửa đồ", "Thu", hinh_thuc_sd, ten_khach_sd, so_tien_sd * 1000])
            st.cache_data.clear() # CHỖ SỬA SỐ 3
            st.rerun()
    
    hien_thi_lich_su_tab(df_main, "Sửa đồ")

# --- TAB 4: BÁO CÁO ---
with tab4:
    st.header("📈 Tổng Doanh Thu")
    df = df_main # Dùng lại dữ liệu đã tải 1 lần ở trên
    if not df.empty:
        df['Ngày'] = df['Thời Gian'].dt.date
        
        # --- BỘ LỌC NGÀY THÁNG ---
        st.write("---")
        st.subheader("📅 Chọn khoảng thời gian")
        ngay_min = df['Ngày'].min()
        ngay_max = df['Ngày'].max()
        
        ngay_chon = st.date_input("Lọc báo cáo theo ngày:", value=(ngay_min, ngay_max))
        
        # Xử lý lọc dữ liệu dựa trên ngày sếp chọn
        if len(ngay_chon) == 2:
            df_loc = df[(df['Ngày'] >= ngay_chon[0]) & (df['Ngày'] <= ngay_chon[1])]
        elif len(ngay_chon) == 1:
            df_loc = df[df['Ngày'] == ngay_chon[0]]
        else:
            df_loc = df.copy()

        if not df_loc.empty:
            # Metrics tổng (chỉ tính trong ngày đã lọc)
            thu_all = df_loc[df_loc['Loại'] == 'Thu']['Số Tiền'].sum()
            chi_all = df_loc[df_loc['Loại'] == 'Chi']['Số Tiền'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("💰 TỔNG DOANH THU", f"{thu_all:,.0f}đ")
            c2.metric("🔻 TỔNG CHI", f"{chi_all:,.0f}đ")
            c3.metric("💎 LỢI NHUẬN", f"{thu_all - chi_all:,.0f}đ")
            
            st.write("---")
            # BIỂU ĐỒ DOANH THU (Cột)
            st.subheader("📊 Biểu đồ doanh thu")
            df_doanh_thu = df_loc[df_loc['Loại'] == 'Thu'].groupby(['Ngày', 'Dịch Vụ'])['Số Tiền'].sum().reset_index()
            
            fig = px.bar(df_doanh_thu, x='Ngày', y='Số Tiền', color='Dịch Vụ', 
                         title="Doanh thu theo dịch vụ", barmode='stack', text_auto='.2s')
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📑 Lịch sử giao dịch")
            st.dataframe(df_loc[['Thời Gian', 'Dịch Vụ', 'Loại', 'Hình Thức', 'Số Tiền', 'Tên Khách']].sort_values(by='Thời Gian', ascending=False), use_container_width=True)
        else:
            st.warning("Không có giao dịch nào trong khoảng thời gian đã chọn.")
    else:
        st.write("Chưa có dữ liệu.")
