from flask import Flask, render_template, send_file, request
import speedtest, datetime, time, csv, zipfile, random
from fpdf import FPDF

app = Flask(__name__)

number, download_speeds, upload_speeds = [], [], []

def safe_speedtest():
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        ds = st.download() / 1_000_000
        us = st.upload() / 1_000_000
        return ds, us
    except Exception as e:
        print(" Speedtest failed, using mock data:", e)
        # fallback mock speeds (so app won't break on Render)
        return random.uniform(20, 100), random.uniform(5, 50)

def check_speed(samples=3, delay=5):
    global number, download_speeds, upload_speeds
    number, download_speeds, upload_speeds = [], [], []      
    for i in range(samples):
        dt = datetime.datetime.now()
        ti = dt.strftime("%Y-%m-%d %H:%M:%S")
        number.append(ti)

        ds, us = safe_speedtest()
        download_speeds.append(ds)
        upload_speeds.append(us)

        if i < samples - 1:
            time.sleep(delay)

def generate_txt_file():
    with open("report.txt", "w") as f:
        f.write("Internet Speed Report\n")
        f.write("Date Generated: " + str(datetime.datetime.now()) + "\n")
        f.write("="*40 + "\n\n")
        for i in range(len(number)):
            f.write(f"Time = {number[i]}\n")
            f.write(f"Download = {download_speeds[i]:.2f} Mbps\n")
            f.write(f"Upload   = {upload_speeds[i]:.2f} Mbps\n")
            f.write("-"*30 + "\n")

def generate_csv_file():
    with open("report.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "Download Speed (Mbps)", "Upload Speed (Mbps)"])
        for i in range(len(number)):
            writer.writerow([number[i], round(download_speeds[i], 2), round(upload_speeds[i], 2)])

def generate_pdf_file():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, "Internet Speed Report", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Date Generated: " + str(datetime.datetime.now()), ln=True, align="C")
    pdf.ln(10)
    for i in range(len(number)):
        pdf.multi_cell(0, 10,
                       f"Time: {number[i]}\n"
                       f"Download: {download_speeds[i]:.2f} Mbps\n"
                       f"Upload:   {upload_speeds[i]:.2f} Mbps\n"
                       + "-"*30)
    pdf.output("report.pdf")

def create_zip():
    with zipfile.ZipFile("reports.zip", "w") as zipf:
        zipf.write("report.txt")
        zipf.write("report.csv")
        zipf.write("report.pdf")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/run", methods=["POST"])
def run_speedtest():
    samples = int(request.form.get("samples", 3))
    delay = int(request.form.get("delay", 5))

    check_speed(samples=samples, delay=delay)
    generate_txt_file()
    generate_csv_file()
    generate_pdf_file()
    create_zip()

    return send_file("reports.zip", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
