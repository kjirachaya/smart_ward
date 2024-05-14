from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def home(request):
  return redirect('/patients/ward')

def sign_in(request):
  # template = loader.get_template('login.html')
  # return HttpResponse(template.render())
  if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request, 
            username=username,
            password=password
        )
        print(user)
        if user is not None:
            # Log user in
            request.session.set_expiry(300)
            login(request, user)
            return redirect("/patients/ward")
            # if 'next_page' not in request.POST:
            #     return redirect("/documents")
            # next_page = request.POST['next_page']
            # print(next_page)
            # next_page = next_page.replace(".djt.html", "")
            # next_page = "/" + next_page
            # print(next_page)
            # if next_page != "/":
            #     return redirect(next_page)
            # return redirect("/documents")
        messages.error(request, 'Invalid Login')
        
  return render(request, 'login.html', {}) 

def sign_out(request):
  # Sign user out
  logout(request)
  return redirect("login")
