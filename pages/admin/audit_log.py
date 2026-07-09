"""
Halaman Admin - Audit Log
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from database import get_all_audit_logs, count_all_audit_logs, get_all_departments
from utils import format_date
from config import ITEMS_PER_PAGE


def render(user):
    """Render halaman audit log"""
    st.title("📜 Audit Log Sistem")
    st.markdown("### Catatan Seluruh Aktivitas di Sistem")

    # Filter
    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])

    with col_f1:
        action_filter = st.multiselect(
            "🔍 Filter Aksi",
            options=["CREATE", "UPDATE", "DELETE", "CREATE_USER", "UPDATE_USER",
                    "DELETE_USER", "RESET_PASSWORD", "CREATE_DEPARTMENT",
                    "UPDATE_DEPARTMENT", "DELETE_DEPARTMENT", "CREATE_CATEGORY",
                    "UPDATE_CATEGORY", "DELETE_CATEGORY", "APPROVE", "REJECT"],
            default=["CREATE", "UPDATE", "DELETE"]
        )

    with col_f2:
        departments = get_all_departments()
        dept_options = [("Semua", 0)] + [(d[1], d[0]) for d in departments]
        selected_dept = st.selectbox("🏢 Filter Bidang", dept_options,
                                    format_func=lambda x: x[0])

    with col_f3:
        search_log = st.text_input("🔍 Cari di Log")

    # Load data
    all_logs = get_all_audit_logs()

    if all_logs:
        df = pd.DataFrame(all_logs, columns=[
            'ID', 'Aksi', 'Doc ID', 'Judul', 'Email', 'Nama', 'Role',
            'Tanggal', 'Detail', 'Dept ID', 'IP', 'Dept Name'
        ])

        # Filter
        filtered = df.copy()
        if action_filter:
            filtered = filtered[filtered['Aksi'].isin(action_filter)]
        if selected_dept[1] != 0:
            filtered = filtered[filtered['Dept ID'] == selected_dept[1]]
        if search_log:
            filtered = filtered[
                filtered['Judul'].str.contains(search_log, case=False, na=False) |
                filtered['Nama'].str.contains(search_log, case=False, na=False) |
                filtered['Detail'].str.contains(search_log, case=False, na=False) |
                filtered['Email'].str.contains(search_log, case=False, na=False)
            ]

        # Info
        st.info(f"📊 Menampilkan **{len(filtered)}** dari **{len(df)}** aktivitas")

        # Pagination
        total_items = len(filtered)
        total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

        if total_pages > 1:
            page = st.number_input("Halaman", min_value=1, max_value=total_pages, value=1)
            start_idx = (page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            filtered = filtered.iloc[start_idx:end_idx]

        # Display
        if not filtered.empty:
            display_df = filtered[['Aksi', 'Judul', 'Nama', 'Role', 'Dept Name',
                                  'Tanggal', 'Detail']].copy()
            display_df['Tanggal'] = display_df['Tanggal'].apply(format_date)
            display_df.columns = ['🔧 Aksi', '📄 Dokumen/User', '👤 Pelaku', '🎭 Role',
                                 '🏢 Bidang', '📅 Waktu', '📝 Detail']

            # Color coding untuk aksi
            def color_action(val):
                if val in ['CREATE', 'CREATE_USER', 'CREATE_DEPARTMENT', 'CREATE_CATEGORY']:
                    return 'background-color: #d4edda; color: #155724'
                elif val in ['UPDATE', 'UPDATE_USER', 'UPDATE_DEPARTMENT', 'UPDATE_CATEGORY', 'RESET_PASSWORD']:
                    return 'background-color: #fff3cd; color: #856404'
                elif val in ['DELETE', 'DELETE_USER', 'DELETE_DEPARTMENT', 'DELETE_CATEGORY']:
                    return 'background-color: #f8d7da; color: #721c24'
                elif val == 'APPROVE':
                    return 'background-color: #d1ecf1; color: #0c5460'
                elif val == 'REJECT':
                    return 'background-color: #f8d7da; color: #721c24'
                return ''

            styled_df = display_df.style.applymap(color_action, subset=['🔧 Aksi'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True, height=500)

            # Export
            st.markdown("---")
            if st.button("📊 Export Audit Log ke Excel"):
                export_df = filtered[['Aksi', 'Judul', 'Nama', 'Role', 'Dept Name',
                                     'Tanggal', 'Detail']].copy()
                export_df.to_excel("audit_log.xlsx", index=False)
                with open("audit_log.xlsx", "rb") as file:
                    st.download_button(
                        "📥 Download Excel",
                        data=file,
                        file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.info("Tidak ada aktivitas yang sesuai dengan filter.")
    else:
        st.info("Belum ada aktivitas tercatat di sistem.")