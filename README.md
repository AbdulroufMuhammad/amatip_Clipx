# 🎥 Video Processing API (Django + MongoDB + MoviePy + Whisper)

## 🚀 Overview

This is a **Django-based API** for video processing using **MoviePy**, **Whisper AI**, and **MongoDB**.\
It supports **video downloads, automatic & custom clipping, transcription, summarization, and log storage**.

---

## 📌 Features

✔️ Download videos from YouTube\
✔️ Extract and transcribe audio using OpenAI's Whisper\
✔️ Summarize transcriptions using Hugging Face Transformers\
✔️ Generate **fixed-length** or **custom range** video clips\
✔️ Store logs and processing details in MongoDB\
✔️ Expose API endpoints for retrieval

---

## 🛠️ Setup & Installation

### **1️⃣ Clone the Repository**

```sh
git clone https://github.com/AbdulroufMuhammad/amatip_Clipx.git
cd video-processing-api
```

### **2️⃣ Create a Virtual Environment**

```sh
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate  # On Windows
```

### **3️⃣ Install Dependencies**

```sh
pip install -r requirements.txt
```

### **4️⃣ Set Up MongoDB**

- Ensure you have **MongoDB running** (either locally or using MongoDB Atlas).
- Update your **Django settings (**``**)**:
  ```python
  MONGO_URI = "mongodb://localhost:27017/video_ai"
  ```

### **5️⃣ Run Migrations**

Since we are using **MongoDB (NoSQL)**, migrations are not required, but you must ensure your **database is running**.

### **6️⃣ Start the Django Server**

```sh
python manage.py runserver
```

---

## 👀 API Endpoints

| Method   | Endpoint                         | Description                        |
| -------- | -------------------------------- | ---------------------------------- |
| **GET**  | `/`                              | Welcome message                    |
| **POST** | `/submit/`                       | Submit a video for processing      |
| **GET**  | `/status/<video_id>/`            | Check video processing status      |
| **GET**  | `/logs/<video_id>/`              | Retrieve logs                      |
| **GET**  | `/clips/<video_id>/`             | List generated clips               |
| **GET**  | `/download/<clip_name>/`         | Download a specific clip           |
| **GET**  | `/api/video-results/<video_id>/` | Get transcript, summary, and clips |

---

## 📌 How to Use the API (Testing with Postman)

### **1️⃣ Submit a Video for Processing**

#### **🔹 Request (POST **``**)**

```json
{
    "video_url": "https://www.youtube.com/watch?v=12345",
    "clip_length": 30,
    "custom_prompt": "motivation, success",
    "selected_genre": "Motivation",
    "speech_language": "English",
    "timeframe": [60, 300]
}
```

💚 This will **automatically generate clips** of 30 seconds each with AI-based highlights.

#### **🔹 OR Custom Clipping (POST **``**)**

```json
{
    "video_url": "https://www.youtube.com/watch?v=12345",
    "clip_ranges": [[5, 120], [200, 300]]
}
```

💚 This will create **clips from specific time ranges** (in seconds).

- 🎮 **First Clip:** 00:05 → 02:00
- 🎮 **Second Clip:** 03:20 → 05:00

---

### **2️⃣ Check Video Status**

#### **🔹 Request (GET **``**)**

```json
{
    "video_id": "b15d9e68-cc7d-4e12-8f75-a12bc1234abc"
}
```

💚 Returns **video processing status**.

---

### **3️⃣ Get Logs**

#### **🔹 Request (GET **``**)**

```json
{
    "video_id": "b15d9e68-cc7d-4e12-8f75-a12bc1234abc"
}
```

💚 Returns **processing logs** from MongoDB.

---

### **4️⃣ List Available Clips**

#### **🔹 Request (GET **``**)**

```json
{
    "video_id": "b15d9e68-cc7d-4e12-8f75-a12bc1234abc"
}
```

💚 Returns **a list of available video clips**.

---

## 🚀 Built With

- **Django + Django REST Framework** 🚀
- **MongoDB** (NoSQL Database) 🗂️
- **MoviePy** (Video Processing) 🎥
- **Whisper AI** (Audio Transcription) 🎵
- **Transformers** (Text Summarization) 📝

---

## 🌍 Author

👨‍💻 **Abdulroufmuhammad**\
📧 [**abdulraufmuhammad28@gmail.com**](mailto\:abdulraufmuhammad28@gmail.com)

