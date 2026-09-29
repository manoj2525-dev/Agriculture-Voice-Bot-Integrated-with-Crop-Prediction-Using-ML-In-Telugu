from django.shortcuts import render,redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import userProfile
from django.shortcuts import render, get_object_or_404
from .models import userProfile
from django.utils.timezone import now
from django.urls import reverse
from django.contrib import messages
from django.core.mail import send_mail
import random
import datetime
from django.utils.html import format_html
from .forms import UserProfileForm
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.conf import settings
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle


# Create your views here.
def basefunction(request):
    return render(request,'base.html') 

def index(request):
    return render(request, 'index.html')

def userlogin(request):
    return render(request,'userlogin.html')
# ----------------------------------------User Registration------------------------------------
def userregister(request):
    print("User registration initiated.")  # Debug message
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            print("Form is valid. Proceeding with OTP generation.")  # Debug message
            # Generate a 6-digit OTP
            otp = random.randint(100000, 999999)
            email = form.cleaned_data['email']
            name = form.cleaned_data['name']
            otp_expiry_minutes = 5  # OTP expiry time in minutes
            # Handle file upload
            profile_photo = request.FILES.get('profile_photo')
            if profile_photo:
                # Save the file to a temporary location
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'temp', profile_photo.name)
                with open(temp_file_path, 'wb+') as destination:
                    for chunk in profile_photo.chunks():
                        destination.write(chunk)
                # Store the file path in the session
                request.session['profile_photo_path'] = temp_file_path
            # Store OTP and form data in session
            request.session['registration_data'] = request.POST
            request.session['otp'] = otp
            request.session['otp_expiry'] = (datetime.datetime.now() + datetime.timedelta(minutes=otp_expiry_minutes)).strftime("%Y-%m-%d %H:%M:%S")
            request.session['email'] = email  
            print(f"Generated OTP: {otp} for email: {email}")  # Debug message
            # Email content
            subject = "OTP Verification - Secure Your Registration"
            message = format_html(f"""
                <p>Dear <b>{name}</b>,</p>
                <p>Thank you for registering. To complete your registration, please use the following One-Time Password (OTP):</p>
                <h2 style="color: red; text-align: center;">{otp}</h2>
                <p>This OTP is valid for <b>{otp_expiry_minutes} minutes</b>. Do not share this OTP with anyone for security reasons.</p>
                <p>If you did not request this, please ignore this email.</p>
                <br>
                <p>Best Regards,</p>
                <p><b>System Generated Mail - No Reply Allowed</b></p>
            """)
            # Send OTP via Email
            send_mail(
                subject,
                '',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
                html_message=message,  # Sending HTML email
            )
            messages.success(request, "OTP has been sent to your email. Please verify.")
            print("Redirecting to OTP verification page.")  # Debug message
            return redirect(reverse('verify_otp'))  # Redirect to OTP verification page
        else:
            messages.error(request, "OOPS! Please correct the errors below.")
            print("Form validation failed.")  # Debug message
    else:
        form = UserProfileForm()
        print("Displaying registration form.")  # Debug message
    return render(request, 'registration.html', {'form': form})
# ----------------------------------------OTP Verification------------------------------------
def verify_otp(request):
    print("OTP verification page accessed.")  # Debug message
    email = None
    masked_email = None
    # Retrieve email from session if available
    if 'registration_data' in request.session:
        email = request.session['registration_data'].get('email', '')
    if email:
        first_part = email[:3]  # First 3 characters
        domain = email.split('@')[-1]  # Extract domain
        masked_email = f"{first_part}xxxxxxxx@{domain}"
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        print(f"Entered OTP: {entered_otp}, Stored OTP: {stored_otp}")  # Debug message
        if str(entered_otp) == str(stored_otp):  # OTP matches
            print("OTP verified successfully!")  # Debug message
            registration_data = request.session.get('registration_data')
            profile_photo_path = request.session.get('profile_photo_path')  # Retrieve file path
            if registration_data:
                # Reconstruct the form with POST data
                form = UserProfileForm(registration_data)
                # Add the file back to the form if it exists
                if profile_photo_path and os.path.exists(profile_photo_path):
                    with open(profile_photo_path, 'rb') as file:
                        form.files['profile_photo'] = ContentFile(file.read(), name=os.path.basename(profile_photo_path))
                if form.is_valid():
                    form.save()
                    print(f"Profile Photo received: {form.cleaned_data['profile_photo']}")                 
                    messages.success(request, "Account created successfully! Wait for admin approval.")                   
                    # Clear session data
                    request.session.pop('registration_data', None)
                    request.session.pop('profile_photo_path', None)  # Clear file path
                    request.session.pop('otp', None)
                    # Clean up the temporary file
                    if profile_photo_path and os.path.exists(profile_photo_path):
                        os.remove(profile_photo_path)
                    print("User registered successfully. Redirecting to registration page.")  # Debug message
                    return redirect(reverse('userregister'))  # Redirect to registration page
                else:
                    messages.error(request, "Error saving user data. Please try again.")
                    print("Form validation failed after OTP verification.")  # Debug message
                    return redirect(reverse('userregister'))
            else:
                messages.error(request, "Session expired! Please register again.")
                print("Session expired. Redirecting to registration page.")  # Debug message
                return redirect(reverse('userregister'))
        else:
            messages.error(request, "Invalid OTP! Please try again.")
            print("Invalid OTP entered.")  # Debug message

    return render(request, 'verify_otp.html', {'masked_email': masked_email})
# ----------------------------------------Resend OTP------------------------------------
def resend_otp(request):
    """Resend OTP after 1-minute cooldown."""
    email = request.session.get('email', '')
    name = request.session.get('registration_data', {}).get('name', '')
    if not email:
        messages.error(request, "Session expired! Please register again.")
        return redirect(reverse('userregister'))
    last_otp_time = request.session.get('otp_sent_time')
    now = datetime.datetime.now()
    if last_otp_time:
        last_otp_time = datetime.datetime.strptime(last_otp_time, "%Y-%m-%d %H:%M:%S")
        time_diff = (now - last_otp_time).seconds

        if time_diff < 60:
            messages.error(request, "Please wait 1 minute before resending OTP.")
            return redirect(reverse('verify_otp'))
    # Generate a new OTP
    otp = random.randint(100000, 999999)
    request.session['otp'] = otp
    request.session['otp_sent_time'] = now.strftime("%Y-%m-%d %H:%M:%S")
    # Send new OTP via email
    send_otp_email(name, email, otp, 5)
    messages.success(request, "A new OTP has been sent to your email.")
    return redirect(reverse('verify_otp'))

def send_otp_email(name, email, otp, expiry_minutes):
    """Send OTP email with professional formatting."""
    subject = "OTP Verification - Secure Your Registration"
    message = format_html(f"""
        <p>Dear <b>{name}</b>,</p>
        <p>Thank you for registering. Please use the following One-Time Password (OTP) to complete your registration:</p>
        <h2 style="color: red; text-align: center;">{otp}</h2>
        <p>This OTP is valid for <b>{expiry_minutes} minutes</b>. Do not share this OTP with anyone for security reasons.</p>
        <p>If you did not request this, please ignore this email.</p>
        <br>
        <p>Best Regards,</p>
        <p><b>System Generated Mail - No Reply Allowed</b></p>
    """)
    send_mail(
        subject,
        '',
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
        html_message=message,
    )

# ----------------------------------------User Login------------------------------------
def userlogin(request):
    return render(request,'userlogin.html')

def userlogincheck(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip().lower()
        password = request.POST.get('password')
        try:
            user = userProfile.objects.get(email__iexact=email)
            print(f"Debug: Retrieved user status: {user.status}")            
            if user.status.lower() == 'blocked':
                messages.error(request, 'Your account is blocked. Please contact our admin team.')
                return render(request, 'userlogin.html')           
            if user.status.lower() != 'activated':
                messages.warning(request, 'Your account is not active. Please wait for admin approval.')
                return render(request, 'userlogin.html')
            if user.password == password:
                request.session['email'] = user.email
                request.session['name'] = user.name
                request.session['profile_photo'] = user.profile_photo.url if user.profile_photo else '/media/profile_photos/default.png'
                user.last_login = now()
                user.save()
                print(f"Debug: Logged-in user email: {request.session['email']}")
                print(f"Debug: Logged-in user name: {request.session['name']}")
                print(f"Debug: Session data: {request.session.items()}")
                return redirect('userhome', name=user.name)
            else:
                messages.error(request, 'Invalid password. Please try again.')
                return render(request, 'userlogin.html')
        except userProfile.DoesNotExist:
            messages.error(request, 'Email is not registered. Please sign up first.')
            return render(request, 'userlogin.html')   
    return render(request, 'userlogin.html')
# ----------------------------------------User Home---------------------------------
def userhome(request, name):
    email = request.session.get('email')
    if not email:
        messages.error(request, "You need to log in first.")
        return redirect('userlogin')
    try:
        user = userProfile.objects.get(email=email)
        return render(request, 'users/userhome.html', {'user': user, 'name': name})
    except userProfile.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('userlogin')
 

# --------------------------------Training Model--------------------------------------------------
def train_model_view(request):
    output_dir = os.path.join(settings.MEDIA_ROOT, 'eda')
    os.makedirs(output_dir, exist_ok=True)

    # 📥 Load dataset
    path = os.path.join(settings.MEDIA_ROOT, 'Crop_recommendation.csv')
    df = pd.read_csv(path)

    # 🧹 Basic data cleaning
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)

    # 🎨 Global Seaborn style
    sns.set_theme(
        style="whitegrid",
        context="talk",  # Slightly bigger fonts
        palette="Set2",
    )

    # 📊 Generate distribution plots for each feature
    for col in df.columns[:-1]:
        plt.figure(figsize=(8, 5))
        sns.histplot(
            df[col],
            kde=True,
            bins=30,
            color='#2ca02c',
            edgecolor='black',
            linewidth=0.7,
            alpha=0.9
        )
        plt.title(f'{col} Distribution', fontsize=18, fontweight='bold', pad=15)
        plt.xlabel(col, fontsize=14)
        plt.ylabel('Count', fontsize=14)

        plt.grid(True, linestyle='--', linewidth=0.6, alpha=0.7)
        sns.despine()

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{col}_distribution.png'), dpi=300)
        plt.close()

    # 📈 Generate correlation heatmap
    plt.figure(figsize=(12, 10))
    corr = df.drop(columns=['label']).corr()

    sns.heatmap(
        corr,
        annot=True,
        fmt='.2f',
        cmap='coolwarm',
        linewidths=0.5,
        linecolor='white',
        cbar_kws={'shrink': 0.8, 'aspect': 30},
        square=True,
        annot_kws={"size": 10}
    )

    plt.title('Feature Correlation Matrix 🔗', fontsize=22, fontweight='bold', pad=20)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'correlation_heatmap.png'), dpi=300)
    plt.close()

    # 🧠 Model training
    X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
    y = df['label']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # 💾 Save trained model
    model_path = os.path.join(settings.MEDIA_ROOT, 'crop_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    # 🖼 Prepare plot paths
    plot_names = [f'eda/{col}_distribution.png' for col in df.columns[:-1]] + ['eda/correlation_heatmap.png']

    # ✅ Fetch user info from session
    email = request.session.get('email')
    user = None
    if email:
        try:
            from .models import userProfile  # Update path if needed
            user = userProfile.objects.get(email=email)
        except userProfile.DoesNotExist:
            pass

    return render(request, 'users/results.html', {
        'accuracy': accuracy * 100,
        'plots': plot_names,
        'media_url': settings.MEDIA_URL,
        'user': user
    })
# --------------------------------Prediction--------------------------------------------------
def predict_crop_view(request):
    prediction = None
    class_probabilities = None
    N = P = K = temperature = humidity = ph = rainfall = None

    # Ensure user is logged in
    email = request.session.get('email')
    user = None
    name = None
    if email:
        try:
            from .models import userProfile
            user = userProfile.objects.get(email=email)
            name = user.name
        except userProfile.DoesNotExist:
            pass

    if request.method == 'POST':
        try:
            # Get user inputs safely
            N = float(request.POST.get('N', 0))
            P = float(request.POST.get('P', 0))
            K = float(request.POST.get('K', 0))
            temperature = float(request.POST.get('temperature', 0))
            humidity = float(request.POST.get('humidity', 0))
            ph = float(request.POST.get('ph', 0))
            rainfall = float(request.POST.get('rainfall', 0))

            # Load model
            model_path = os.path.join(settings.MEDIA_ROOT, 'crop_model.pkl')
            if not os.path.exists(model_path):
                raise FileNotFoundError("Model file not found at {}".format(model_path))

            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            input_data = pd.DataFrame([{
                'N': N,
                'P': P,
                'K': K,
                'temperature': temperature,
                'humidity': humidity,
                'ph': ph,
                'rainfall': rainfall
            }])

            # Make prediction
            prediction = model.predict(input_data)[0]

            # Get class probabilities if available
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(input_data)[0]
                class_labels = model.classes_
                class_probabilities = {label: round(prob * 100, 2) for label, prob in zip(class_labels, probs)}
            else:
                class_probabilities = {}

        except Exception as e:
            prediction = f"Error: {str(e)}"
            class_probabilities = {}

    return render(request, 'users/predict_crop.html', {
        'prediction': prediction,
        'class_probabilities': class_probabilities,
        'N': N,
        'P': P,
        'K': K,
        'temperature': temperature,
        'humidity': humidity,
        'ph': ph,
        'rainfall': rainfall,
        'user': user,
        'name': name,
        'media_url': settings.MEDIA_URL,
    })

#----------------------------------------Voice bot---------------------------------
from django.shortcuts import render
from django.http import HttpResponse
import threading
from . import chat1
from .models import userProfile  # Make sure this is imported

result_data = {}  # Global dictionary to store chatbot result

def run_voice_bot_and_store():
    global result_data
    result = chat1.start_chatbot()
    result_data = result if result else {}

def chatfunction(request):
    global result_data
    user = None
    name = None  # Default value for name
    
    # Ensure user is logged in
    email = request.session.get('email')
    if email:
        try:
            user = userProfile.objects.get(email=email)
            name = user.name  # Assuming `userProfile` has a `name` field
        except userProfile.DoesNotExist:
            pass

    if request.GET.get('action') == 'stop':
        chat1.is_running = False
        return HttpResponse("🎙️ Voice Bot Stopping... Please wait a moment.")

    # Start chatbot in a thread and wait
    thread = threading.Thread(target=run_voice_bot_and_store)
    thread.start()
    thread.join()  # Wait for completion

    # Now return results in HTML page with user name and chatbot data
    return render(request, "users/chat.html", {
        'inputs': result_data.get('inputs', {}),
        'prediction': result_data.get('prediction', ''),
        'user': user,  # Pass user info to the template
        'name': name,  # Pass user name to the template
    })
# --------------------------------------Dataset View-------------------------------------
def dataset_view(request):
    email = request.session.get('email')
    user = None
    name = None
    if email:
        try:
            user = userProfile.objects.get(email=email)
            name = user.name
        except userProfile.DoesNotExist:
            pass

    # Load the dataset
    path = os.path.join(settings.MEDIA_ROOT, 'Crop_recommendation.csv')
    dataset = pd.read_csv(path)

    # Drop the last column
    dataset = dataset.iloc[:, :-1]

    # Convert DataFrame to list of dicts
    dataset_dict = dataset.to_dict(orient='records')

    return render(request, 'users/datasetview.html', {
        'dataset': dataset_dict,
        'user': user,
        'name': name,
    })


