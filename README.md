# Job Application Tracker

İş ve staj başvurularını takip etmek için geliştirilmiş tam yığın (full-stack) bir web uygulaması.

## ✨ Özellikler

- Yeni başvuru ekleme
- Tüm başvuruları listeleme
- Başvuru silme
- Başvuru durumunu takip etme
- Basit ve kullanıcı dostu arayüz

## 🛠️ Kullanılan Teknolojiler

- Python
- FastAPI
- SQLite
- HTML
- CSS
- JavaScript

## 📁 Proje Yapısı

```text
JOB-TRACKER/
├── app.py
├── requirements.txt
├── .gitignore
└── static/
    ├── index.html
    ├── style.css
    └── script.js
````

## ⚙️ Kurulum

Aşağıdaki adımları takip ederek projeyi çalıştırabilirsiniz:

```bash
git clone https://github.com/Hakan-Deger/job-application-tracker.git
cd job-application-tracker

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

uvicorn app:app --reload
