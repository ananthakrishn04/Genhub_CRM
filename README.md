# Genhub_CRM

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/ananthakrishn04/Genhub_CRM.git
cd Genhub_CRM
```

### 2. Create Virtual Environment
```bash
# For Unix/macOS
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Navigate to Backend Directory
```bash
cd backend
```

### 5. Run Database Migrations
```bash
python manage.py migrate
```

### 6. Start Development Server
```bash
python manage.py runserver
```


Docs should be visible at http://127.0.0.1:8000/api/schema/swagger-ui/