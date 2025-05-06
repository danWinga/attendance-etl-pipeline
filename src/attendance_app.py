import pandas as pd
import streamlit as st
import io
from datetime import timedelta

st.set_page_config(page_title="Attendance Processor", layout="wide")
st.title("📊 Attendance Report Generator")

# File upload
uploaded_file = st.file_uploader("Upload Excel File (.xls, .xlsx, .xlsm, .xltx)",
                                   type=["xls", "xlsx", "xlsm", "xltx"])

def parse_time_to_minutes(time_str):
    """Convert 'H:MM' to minutes, handling negatives."""
    hours, minutes = map(int, time_str.strip().split(':'))
    return hours * 60 + (minutes if hours >= 0 else -minutes)

def format_minutes_to_hhmm(total_minutes):
    """Convert minutes to 'H:MM' format, handling negatives."""
    sign = "-" if total_minutes < 0 else ""
    total_minutes = abs(int(total_minutes))
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{sign}{h}:{m:02d}"

def process_attendance(df):
    required_columns = ['Name', 'Emp ID', 'Time', 'Attendance State']
    for col in required_columns:
        if col not in df.columns:
            st.error(f"Missing required column: {col}")
            return None, None, None

    # Convert Time column to datetime
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
    df.dropna(subset=['Time'], inplace=True)
    df['Date'] = df['Time'].dt.date

    # Sort the data
    df = df.sort_values(by=['Emp ID', 'Date', 'Time'])

    # Process CheckIn and CheckOut per employee per day
    processed_data = []
    for (emp_id, date), group in df.groupby(['Emp ID', 'Date']):
        check_in = group[group['Attendance State'] == 'Check In']
        check_out = group[group['Attendance State'] == 'Check Out']

        intime = check_in['Time'].iloc[0] if not check_in.empty else None
        outtime = check_out['Time'].iloc[0] if not check_out.empty else None

        name = group['Name'].iloc[0] if not group.empty else ''

        # Fix overnight shift
        if intime and outtime and intime > outtime:
            outtime += timedelta(hours=12)

        # Calculate WorkHrs, Overtime, and ExtraWorkHrs
        if intime and outtime:
            total_minutes = (outtime - intime).total_seconds() / 60
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            workhrs = f"{hours}:{minutes:02d}"

            overtime_minutes = max(0, total_minutes - 600)  # Over 10 hours
            ot_hours = int(overtime_minutes // 60)
            ot_minutes = int(overtime_minutes % 60)
            overtime = f"{ot_hours}:{ot_minutes:02d}"

            all_minutes = total_minutes - 600
            all_work_hrs = format_minutes_to_hhmm(all_minutes)

            # Suppress overtime < 15 mins
            if ot_hours == 0 and ot_minutes < 15:
                overtime = "0:00"
        else:
            workhrs = "0:00"
            overtime = "0:00"
            all_work_hrs = "0:00"

        processed_data.append({
            'Name': name,
            'Emp ID': emp_id,
            'Date': date,
            'CheckIn': intime,
            'CheckOut': outtime,
            'WorkHrs': workhrs,
            'Overtime': overtime,
            'More/LessWorkHrs': all_work_hrs
        })

    final_df = pd.DataFrame(processed_data)

    # Create summary
    summary_data = []
    for name, name_group in final_df.groupby('Name'):
        total_work_mins = name_group['WorkHrs'].apply(parse_time_to_minutes).sum()
        total_overtime_mins = name_group['Overtime'].apply(parse_time_to_minutes).sum()
        total_extra_mins = name_group['More/LessWorkHrs'].apply(parse_time_to_minutes).sum()

        emp_id = name_group['Emp ID'].iloc[0]
        if isinstance(emp_id, tuple):
            emp_id = emp_id[0]

        rate = 500 if emp_id in [6, 40] else 250

        total_extra_adj = total_extra_mins

        off_work_hrs = 26 * 60  # in minutes
        standard_monthly_workhrs = 240

        total_WorkHrs = total_work_mins + off_work_hrs
        total_paid_workHrs = total_WorkHrs + total_extra_adj

        if total_paid_workHrs > (240 * 60):
            total_ov_time = total_paid_workHrs - (240 * 60)
            calc_overtime = round(rate * (total_ov_time / 60))
            deducted_Hrs = 0
            deducted_amount = 0.00
        else:
            total_ov_time = 0
            calc_overtime = 0.00
            deducted_Hrs = (240 * 60) - total_paid_workHrs
            deducted_amount = round(rate * (deducted_Hrs / 60))

        summary_data.append({
            'Emp ID': emp_id,
            'Name': name,
            'Standard Monthly workHrs': f"{standard_monthly_workhrs:.2f}",
            'Biometric WorkHrs': format_minutes_to_hhmm(total_work_mins),
            'Off WorkHrs': f"{off_work_hrs / 60:.2f}",
            'Total_WorkHrs(with Off Hrs)': format_minutes_to_hhmm(total_WorkHrs),
            'Less/More WorkHrs': format_minutes_to_hhmm(total_extra_adj),
            'Total Paid WorkHrs': format_minutes_to_hhmm(total_paid_workHrs),
            'TotalOvertime': format_minutes_to_hhmm(total_ov_time),
            'Rate': rate,
            'OvertimeAmnt': f"{calc_overtime:.2f}",
            'TotalDeducted Hrs': format_minutes_to_hhmm(deducted_Hrs),
            'Total Deducted Amnt': f"{deducted_amount:.2f}"
        })

    summary_df = pd.DataFrame(summary_data)
    return df, final_df, summary_df

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, engine=None)
        raw_data, daily_summary, overall_summary = process_attendance(df)

        if daily_summary is not None:
            st.subheader("📄 Raw Attendance Data")
            st.dataframe(raw_data)

            st.subheader("✅ Daily Summary")
            st.dataframe(daily_summary)

            st.subheader("📈 Overall Summary")
            st.dataframe(overall_summary)

            # Download link for processed data
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                raw_data.to_excel(writer, sheet_name="Raw Data", index=False)
                daily_summary.to_excel(writer, sheet_name="Daily Summary", index=False)
                overall_summary.to_excel(writer, sheet_name="Summary", index=False)

            st.download_button(
                label="📥 Download Processed Report",
                data=output.getvalue(),
                file_name="processed_attendance.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
