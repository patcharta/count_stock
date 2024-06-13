FROM python:3.11

# ติดตั้ง libgl1-mesa-glx
RUN apt-get update && apt-get install -y libgl1-mesa-glx

# ติดตั้ง dependencies จาก requirements.txt
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy เหลือต่างๆ จากโปรเจกต์ของคุณ
COPY . .

# คำสั่งที่จะรันเมื่อ container เริ่มต้น
CMD ["python", "your_script.py"]
