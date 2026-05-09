import streamlit as st
import joblib
import pandas as pd
import os

# Cấu hình trang web
st.set_page_config(page_title="AI Dự Đoán Doanh Thu", layout="wide")

# 1. HÀM NẠP DỮ LIỆU VÀ MÔ HÌNH
@st.cache_resource
def load_all_resources():
    # Kiểm tra file mô hình
    if not os.path.exists('mo_hinh_tinh_tien.pkl') or not os.path.exists('danh_sach_cot.pkl'):
        return None, None, [], []

    model = joblib.load('mo_hinh_tinh_tien.pkl')
    model_columns = joblib.load('danh_sach_cot.pkl')
    
    # Kiểm tra file Excel để lấy danh sách Vị trí/Mô hình
    file_name = 'Doanh thu quán nước trung bình trong 1 ngày (Câu trả lời) (1).xlsx'
    
    if os.path.exists(file_name):
        try:
            df = pd.read_excel(file_name)
            # Đổi tên cột tạm thời để lấy dữ liệu cho Selectbox
            df.columns = [
                'Time', 'MoHinh', 'GiaoHang', 'GioPhucVu', 'LuongKhach', 'GiaNuoc',
                'BanDoAnKem', 'GiaDoAnKem', 'SoLuongDoAnKem', 'SoNhanVien', 'SinhVienNgoiLau',
                'DienTich', 'ViTri', 'DoiThu', 'DoanhThu'
            ]
            vi_tri_list = sorted(df['ViTri'].dropna().unique().tolist())
            mo_hinh_list = sorted(df['MoHinh'].dropna().unique().tolist())
        except Exception as e:
            st.error(f"Lỗi khi đọc file Excel: {e}")
            vi_tri_list, mo_hinh_list = ["Lỗi đọc file"], ["Lỗi đọc file"]
    else:
        vi_tri_list, mo_hinh_list = ["Không tìm thấy file Excel"], ["Không tìm thấy file Excel"]
        
    return model, model_columns, vi_tri_list, mo_hinh_list

# Thực hiện nạp
model, model_columns, vi_tri_list, mo_hinh_list = load_all_resources()

# Kiểm tra nếu chưa nạp được mô hình
if model is None:
    st.error("❌ Không tìm thấy file 'mo_hinh_tinh_tien.pkl'. Vui lòng chạy file .ipynb trước để lưu mô hình!")
    st.stop()

# 2. GIAO DIỆN WEB
st.title("💰 AI Dự Đoán Doanh Thu Quán Nước")
st.write("Nhập thông số thực tế để AI dự đoán doanh thu hàng ngày của quán.")

with st.form("main_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Số liệu vận hành")
        luong_khach = st.number_input("Lượng khách trung bình/ngày", min_value=0, value=100)
        gia_nuoc = st.number_input("Giá bán trung bình (VNĐ)", min_value=0, value=35000, step=1000)
        dien_tich = st.number_input("Diện tích quán (m2)", min_value=0, value=40)
        so_nhan_vien = st.number_input("Số lượng nhân viên", min_value=0, value=2)
        doi_thu = st.number_input("Số đối thủ (bán kính 500m)", min_value=0, value=3)

    with col2:
        st.subheader("📍 Đặc điểm & Vị trí")
        vi_tri = st.selectbox("Chọn Vị trí quán", vi_tri_list)
        mo_hinh = st.selectbox("Chọn Mô hình quán", mo_hinh_list)
        
        delivery = st.radio("Có bán trên App giao hàng (Grab/Shopee)?", ["Có", "Không"])
        ngoi_lau = st.radio("Khách (Sinh viên) thường ngồi lâu?", ["Có", "Không"])
        do_an = st.radio("Có bán kèm đồ ăn không?", ["Có", "Không"])

    submit = st.form_submit_button("🚀 XEM KẾT QUẢ DỰ ĐOÁN")

# 3. XỬ LÝ DỰ ĐOÁN
if submit:
    # Tạo DataFrame trống với các cột chuẩn
    input_df = pd.DataFrame(0, index=[0], columns=model_columns)
    
    # Điền giá trị số
    input_df['LuongKhach'] = luong_khach
    input_df['GiaNuoc'] = gia_nuoc
    input_df['DienTich'] = dien_tich
    input_df['SoNhanVien'] = so_nhan_vien
    input_df['DoiThu'] = doi_thu
    
    # Chuyển Có/Không -> 1/0
    input_df['GiaoHang'] = 1 if delivery == "Có" else 0
    input_df['SinhVienNgoiLau'] = 1 if ngoi_lau == "Có" else 0
    input_df['BanDoAnKem'] = 1 if do_an == "Có" else 0
    
    # Xử lý Vị trí và Mô hình (One-Hot Encoding)
    col_v = f"ViTri_{vi_tri}"
    col_m = f"MoHinh_{mo_hinh}"
    
    if col_v in model_columns: input_df[col_v] = 1
    if col_m in model_columns: input_df[col_m] = 1

    # Thực hiện dự đoán
    try:
        du_doan = model.predict(input_df)[0]
        # Tránh trường hợp dự đoán ra số âm (nếu có)
        du_doan = max(0, du_doan)
        
        st.divider()
        st.balloons()
        st.success(f"## 💵 Doanh thu dự kiến: {du_doan:,.0f} VNĐ / ngày")
        st.info("💡 Mẹo: Tăng lượng khách hoặc thêm dịch vụ giao hàng để cải thiện con số này!")
    except Exception as e:
        st.error(f"Có lỗi xảy ra khi tính toán: {e}")