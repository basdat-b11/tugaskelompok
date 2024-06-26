import uuid
from django.shortcuts import redirect, render
from django.db import connection
from django.http import HttpResponse
from django.contrib import messages  
import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import psycopg2


def first_view(request):
    # Lakukan operasi atau logika yang diperlukan
    context = {
        'variable': 'nilai_variable'
    }
    return render(request, 'LoginRegister.html', context)

def role_register_view(request):
    # Lakukan operasi atau logika yang diperlukan
    context = {
        'variable': 'nilai_variable'
    }
    return render(request, 'RoleRegister.html', context)

def subscription_page(request):
    email = request.session.get('email')
    context = {
        'email': email
    }
    return render(request, 'langganan-paket.html', context)

@require_http_methods(['GET', 'POST'])
def bayar_paket(request):
    if request.method == 'POST':

        email = request.session.get('email')
        transaction_id = uuid.uuid4()
        jenis_paket = request.POST['jenis_paket']
        harga = request.POST['harga']
        metode_pembayaran = request.POST['payment']
        interval = 0
        harga = 0
        if jenis_paket == '1 bulan':
            interval = '30 days'; harga = 65000
        elif jenis_paket == '3 bulan':
            interval = '3 months'; harga = 180000
        elif jenis_paket == '6 bulan':
            interval = '6 months'; harga = 330000
        else:
            interval = '1 years'; harga = 600000
        
        try:
            with connection.cursor() as cursor:
                cursor = connection.cursor()
                cursor.execute("SET SEARCH_PATH TO MARMUT;")
                cursor.execute(f"INSERT INTO TRANSACTION VALUES ('{transaction_id}', '{jenis_paket}', '{email}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '{interval}', '{metode_pembayaran}', {harga})")
                connection.commit()
                cursor.close()
                connection.close()
            
            return redirect('authentication:dashboard')
        
        except psycopg2.Error as e:
            if e.pgcode == 'P0001':  # Exception code for our custom exception
                print("Hello")
                messages.error(request, str(e))
                return redirect('authentication:dashboard')
            else:
                print(e)
                return HttpResponse("Error occurred while connecting to the database")
    
    else:
        package = request.GET.get('package')
        if package:
            
            with connection.cursor() as cursor:
                cursor = connection.cursor()
                cursor.execute("SET SEARCH_PATH TO MARMUT;")
                cursor.execute(f"SELECT jenis, harga FROM PAKET WHERE jenis = '{package}'")
                paket = cursor.fetchone()
                cursor.close()
                connection.close()
                
                data_paket = {
                    'jenis': paket[0],
                    'harga': paket[1],
                }

                context = {
                    'data_paket': data_paket
                }

                return render(request, "pembayaran-paket.html", context)
        else:
            return HttpResponse("No package selected.")
        
@require_http_methods(['GET'])
def riwayat_langganan(request):
    email = request.session.get('email')
    with connection.cursor() as cursor:
        cursor = connection.cursor()
        cursor.execute("SET SEARCH_PATH TO MARMUT;")
        cursor.execute(f"SELECT jenis_paket, timestamp_dimulai, timestamp_berakhir, metode_bayar, nominal FROM TRANSACTION WHERE email = '{email}'")
        riwayat_paket = cursor.fetchall()
        context = {
            'data_langganan': [{
                'jenis_paket': paket[0],
                'timestamp_dimulai': paket[1],
                'timestamp_berakhir': paket[2],
                'metode_bayar': paket[3],
                'nominal': paket[4],
                } for paket in riwayat_paket],
        } 
        return render(request, 'riwayat-transaksi.html', context)
    
def unduhan_lagu(request):
    email = request.session.get('email')
    with connection.cursor() as cursor:
        cursor = connection.cursor()
        cursor.execute("SET SEARCH_PATH TO MARMUT;")
        cursor.execute(f"SELECT email FROM PREMIUM WHERE email = '{email}';")
        email_didapat = cursor.fetchone()
        if email == email_didapat[0]:
            cursor.execute(f"SELECT KONTEN.judul AS song_title, AKUN.nama AS artist_name, d.id_song as id FROM DOWNLOADED_SONG d JOIN SONG ON d.id_song = SONG.id_konten JOIN KONTEN ON SONG.id_konten = KONTEN.id JOIN ARTIST ON SONG.id_artist = ARTIST.id JOIN AKUN on ARTIST.email_akun = AKUN.email WHERE d.email_downloader = '{email}';")
            lagu_didownload = cursor.fetchall()
            context = {
                'daftar_lagu': [{
                    'song_title': row[0],
                    'artist_name': row[1],
                    'id': row[2]
                    } for row in lagu_didownload],
            }
            cursor.close()
            connection.close()
            return render(request, 'downloaded-song.html', context)
        else:
            return redirect('authentication:dashboard')
        
def pencarian(request):
    with connection.cursor() as cursor:
        cursor = connection.cursor()
        cursor.execute("SET SEARCH_PATH TO MARMUT;")
        query = request.GET.get('query')
        cursor.execute(f"SELECT judul, AKUN.nama, k.id FROM KONTEN k JOIN SONG ON k.id = SONG.id_konten JOIN ARTIST ON SONG.id_artist = ARTIST.id JOIN AKUN ON AKUN.email = ARTIST.email_akun WHERE k.judul ILIKE '%{query}%';")
        daftar_lagu = cursor.fetchall()
        cursor.execute(f"SELECT judul, AKUN.nama, k.id FROM KONTEN k JOIN PODCAST ON k.id = PODCAST.id_konten JOIN PODCASTER ON PODCAST.email_podcaster = PODCASTER.email JOIN AKUN ON AKUN.email = PODCASTER.email WHERE k.judul ILIKE '%{query}%';")
        daftar_podcast = cursor.fetchall()
        cursor.execute(f"SELECT judul, AKUN.nama, id_user_playlist FROM USER_PLAYLIST p JOIN AKUN ON AKUN.email = p.email_pembuat WHERE p.judul ILIKE '%{query}%';")
        daftar_playlist = cursor.fetchall()

        context = {
            'daftar_lagu': [{
                    'judul': row[0],
                    'artist': row[1],
                    'id': row[2]
                    } for row in daftar_lagu],
            'daftar_podcast': [{
                    'judul': row[0],
                    'podcaster': row[1],
                    'id': row[2]
                    } for row in daftar_podcast],
            'daftar_playlist': [{
                    'judul': row[0],
                    'user': row[1],
                    'id': row[2]
                    } for row in daftar_playlist],
            'hasil_pencarian': query,
        }
        return render(request, 'search-result-page.html', context)
    
def hapus_lagu(request, id_lagu):
    email = request.session.get('email')
    with connection.cursor() as cursor:
        cursor = connection.cursor()
        cursor.execute("SET SEARCH_PATH TO MARMUT;")
        cursor.execute(f"UPDATE SONG SET total_download = total_download - 1 WHERE id_konten = '{id_lagu}';")
        connection.commit()
        cursor.execute(f"DELETE FROM DOWNLOADED_SONG WHERE id_song = '{id_lagu}' AND email_downloader = '{email}';")
        connection.commit()
        cursor.close()
        connection.close()
    
    return redirect('main:unduhan_lagu')

def register_pengguna(request):
    
    is_verified = "f"
    is_male = "0"
    if request.method == "POST":
        email = request.POST['inputEmail']
        password = request.POST['inputPasswordl']
        name = request.POST['inputName']
        gender = request.POST['inputGender']
        birth_place = request.POST['inputPlaceOfBirth']
        birth_date = request.POST['inputDateOfBirth']
        city = request.POST['inputCity']
        role = request.POST['inputRole']
        if (role != ""):
            is_verified = "t"

        if (gender == "Male"):
            is_male = "1"

        with connection.cursor() as cursor:
            cursor.execute("Set search_path to marmut;")
            cursor.execute("""
                            INSERT INTO akun (
                                email,
                                password,
                                nama,
                                gender, 
                                tempat_lahir,
                                tanggal_lahir,
                                is_verified,
                                kota_asal
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, [email, password, name, is_male, birth_place, birth_date, is_verified, city])
    return render(request, 'RegisterPengguna.html')

def login_user(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')
        gender = request.POST.get('gender')
        birth_place = request.POST.get('birth_place')
        birth_date = request.POST.get('birth_date')
        city = request.POST.get('city')
        role = request.POST.get('role')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            request.session['nama'] = name
            request.session['email'] = email
            request.session['roles'] = role
            return redirect('main:show_main')
        else:
            messages.info(request, 'Sorry, incorrect username or password. Please try again.')
    context = {}
    return render(request, 'LoginPage.html', context)

def logout_user(request):
    logout(request)
    return redirect('main:login')