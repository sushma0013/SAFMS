from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to Smart Attendance")

def generate_qr(request):
    # your QR generation logic here
    return HttpResponse("QR generated")

def show_qr(request, session_id):
    # your logic to display QR
    return HttpResponse(f"QR for session {session_id}")
