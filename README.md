# Agriculture Voice Bot and Crop Prediction (Telugu)

A Django web application that recommends a crop from soil and weather measurements and provides a Telugu voice-guided crop-prediction flow. The project includes a crop dataset, a pre-trained machine-learning model, prediction and dataset pages, model-training visualizations, email OTP registration, and an admin area for managing registered users.

> **Status:** Academic/demo project. Review the security notes below before using it with real users or deploying it publicly.

## Features

- Predicts a suitable crop from nitrogen (N), phosphorus (P), potassium (K), temperature, humidity, soil pH, and rainfall.
- Uses a Random Forest classifier trained from the crop recommendation dataset; the included model is stored in `media/crop_model.pkl`.
- Displays the crop dataset and provides a model-training page with feature-distribution charts and a correlation heatmap.
- Offers a Telugu voice flow using speech recognition, translation, and text-to-speech.
- Supports registration with email OTP verification and an admin workflow for activating, blocking, and deleting users.

## Requirements

- Python 3.10 or newer is recommended.
- Windows is recommended for the supplied dependency list; audio packages such as PyAudio may require additional system setup on other platforms.
- Internet access is needed for the Google speech-recognition, translation, and gTTS services used by the voice flow. The voice flow also needs microphone access on the machine running the Django server.
- Gmail SMTP credentials (or equivalent SMTP configuration) are needed to send registration OTP emails.

## Run locally (Windows PowerShell)

From the project root—the directory containing `manage.py`—create and activate a virtual environment, then install the pinned dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirment.txt
```

The dependency file is currently named `requirment.txt` (spelling as in the repository).

Configure Django and email settings in the current PowerShell session before running the app. Use your own values; do not commit credentials or put them in source code:

```powershell
$env:DJANGO_SECRET_KEY = "replace-with-a-unique-random-secret"
$env:EMAIL_HOST_USER = "your-sending-address@example.com"
$env:EMAIL_HOST_PASSWORD = "your-smtp-app-password"
```

Apply database migrations and start the development server:

```powershell
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in a browser. Registration and OTP email require the SMTP environment variables above. Django's built-in administration site is at <http://127.0.0.1:8000/admin/>; create its administrator with `python manage.py createsuperuser`.

## Main pages

| Page | Route | Purpose |
| --- | --- | --- |
| Home | `/` | Application landing page |
| Sign up | `/userregister/` | Register and request an email OTP |
| User login | `/userlogin/` | Sign in to the user area |
| Crop prediction | `/predict_crop_view/` | Submit soil and climate values for a prediction |
| Dataset | `/dataset_view/` | Browse the crop recommendation data |
| Train model | `/train_model_view/` | Train the classifier and view evaluation plots |
| Voice bot | `/chatfunction/` | Start the Telugu voice-guided flow |
| Admin login | `/adminlogin/` | Open the project's custom user-management area |

## Data and model

The dataset is `media/Crop_recommendation.csv`. Its seven input features are `N`, `P`, `K`, `temperature`, `humidity`, `ph`, and `rainfall`; `label` is the crop class. The training page saves the fitted model and generated charts under `media/`. The checked-in pre-trained model allows crop prediction without first training a new model.

## Project layout

- `crop_predication_chatbot/` — Django project settings and URL configuration.
- `home/` — registration, user pages, dataset/model operations, and voice flow.
- `admins/` — custom admin-area views.
- `templates/` and `static/` — HTML templates, CSS, and frontend assets.
- `media/` — crop dataset, pre-trained model, and exploratory-data-analysis charts.
- `home/migrations/` — database schema migrations.

## Security and deployment notes

- Do not use real user credentials with this demo. Account password handling in the current application is not suitable for production; replace it with Django's built-in authentication and password hashing.
- The custom admin login currently uses hard-coded demo credentials in the source. Replace it with authenticated, permission-checked Django admin functionality before deployment.
- Set a unique `DJANGO_SECRET_KEY`, configure SMTP credentials through environment variables, set `DEBUG = False`, and configure `ALLOWED_HOSTS` for the deployment environment.
- Add HTTPS, CSRF/session protections, authorization checks on protected views, secure media handling, and production-grade logging before exposing the application to the internet.
- The local SQLite database and user-uploaded profile photos are intentionally excluded from Git. Run migrations to create a fresh local database.

## License

No license is currently specified. Contact the repository owner before redistributing this project or its assets.
