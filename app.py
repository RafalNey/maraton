# Sekcja importowa
import os
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langfuse import Langfuse
from langfuse.decorators import observe
from langfuse.openai import OpenAI as LangfuseOpenAI
from pycaret.regression import load_model, predict_model

# Wczytanie sekretow z .env
load_dotenv()

# Wczytanie modelu regresyjnego
model = load_model('maraton_rafal_model')

# Ustawienie początkowych wartości w session_state
if 'text' not in st.session_state:
    st.session_state.text = ""
if 'time' not in st.session_state:
    st.session_state.time = 0
if 'gender' not in st.session_state:
    st.session_state.gender = "Mężczyzna"
if 'age' not in st.session_state:
    st.session_state.age = 35
if 'weight' not in st.session_state:
    st.session_state.weight = 70
if 'height' not in st.session_state:
    st.session_state.height = 170
if 'sport_activity' not in st.session_state:
    st.session_state.sport_activity = 1

# Oznaczenie, ze dane nie zostały jeszcze wyciągnięte z AI
if 'data_extracted' not in st.session_state:
    st.session_state.data_extracted = False

# Wartości poczatkowe dla problemow z odswiezaniem
if 'needs_calculation' not in st.session_state:
    st.session_state.needs_calculation = False
if 'current_activity_display' not in st.session_state:
    st.session_state.current_activity_display = 1
if 'needs_rerun' not in st.session_state:
    st.session_state.needs_rerun = False

# Inicjacja Langfuse
langfuse = Langfuse()
langfuse.auth_check()
llm_client = LangfuseOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# FUNKCJE ----------------------------------------------


# Funkcja do walidacji wartości
def validate_input(value, min_value, max_value):
    if value < min_value:
        return min_value
    elif value > max_value:
        return max_value
    return value


# Obliczanie BMI
def calculate_bmi(weight, height):
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    return bmi


# Zamiana sekund na godziny i minuty
def format_time(seconds):
    total_minutes = seconds // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60

    return hours, minutes


# Funkcja suwakowa
def slider_callback():
    st.session_state.needs_calculation = True


# @st.cache_data(ttl=0)  # usuwanie cachu dla pycareta
# def make_prediction(model, data):
#     return predict_model(model, data=data)


# Zapytanie do openAI, podpięte pod Langfuse
@st.cache_resource
@observe()
def get_data_from_text(text):

    # Inicjalizacja zmiennych
    gender = None
    age = None
    weight = None
    height = None
    sport_activity = None

    prompt = """
    Twoim zadaniem jest wyciągnięcie odpowiednich informacji z tekstu podanego przez użytkownika. Postaraj się wyciągną lub wyinterpretować z tekstu następujące dane:

    <gender> jakiej płci jest użytkownik. Odpowiednio przydziel K dla kobiety lub M dla mężczyzny.Jeśli nie znajdziesz żadnych informacji na ten temat lub wskazówek w tekście użytkownika, przyjmij że masz do czynienia z mężczyzną.

    <age> określ wiek użytkownika w latach. Minimalny wiek to 10 lat, maksymalny to 100. Jeśli użytkownik poda wiek niższy niż 10, to przypisz mu 10, a jeśli większy niż 100, to przypisz mu 100. Jeśli w żaden sposób nie będziesz w stanie wyciągnąć wieku z danych, przyjmij 35.

    <weight> ile waży użytkownik w kilogramach. Minimalna waga to 45, maksymalna to 350. Jeśli użytkownik poda wagę niższą niż 45, to przypisz mu 45, a jeśli większą niż 350, to przypisz mu 350.Jeśli nie będziesz tego w stanie w żaden sposób określić, przyjmij, że dla kobiety to będzie 65, a dla mężczyzny 80.

    <height> jaki jest wzrost użytkownika w centymetrach. Minimalny wzrost to 120, maksymalny to 250. Jeśli użytkownik poda wzrost niższy niż 120, to przypisz mu 120, a jeśli większy niż 250, to przypisz mu 250.Jeśli nie będziesz w stanie określić jego wzrostu, przyjmij, że dla kobiety to będzie 165, a dla mężczyzny 175.

    <sport_activity> - na podstawie tekstu wpisanego przez użytkownika określ jego aktywność sportową  w skali od 1 do 11, gdzie:

    1 oznacza praktycznie wyłącznie siedzący lub półleżacy tryb życia na kanapie.
    2 to najwyżej umiarkowany ruch po mieszkaniu,
    3 to okazyjne spacery na odcinku 1-2 kilometrów,
    4 oznacza w miarę regularne, kilka razy w tygodniu, półgodzinne spacery,
    5 to już codzienny spacer, często z psem, czasem kilkuminutowy sprint za autobusem,
    6 to osoba dla której przebiegnięcie lekkim truchtem jednego lub dwóch kilometrów nie stanowi większego problemu,
    7 to osoba sporadycznie uprawiająca sport, czasem biorąca udział w zajęciach typu aerobik lub raz w tygodniu szalejąca na parkiecie w dyskotece.
    8 to osoba regularnie uprawiająca sport, kilka razy w tygodniu uczęszczająca na siłownię.
    9 to osoba, która regularnie biega, ale tylko na odcinku kilku kilometrów, półmaraton to już będzie dla niej wyzwanie.
    10 to osoba, dla której przebiegnięcie półmaratonu nie jest żadnym problemem i będzie się starała zając miejsce w pierwszej setce,
    11 oznacza zawodowego maratończyka, dla którego taki półmaraton to bułka z masłem.

    Jeśli na podstawie tekstu użytkownika nie będziesz w stanie określić jego aktywności sportowej,przyjmij 6.

    Zwróć wartości jako obiekt json z następującymi kluczami:
    - gender - string 'K' lub 'M'
    - age - integer
    - weight - integer
    - height - integer
    - sport_activity - integer

    Upewnij się, że wszystkie klucze mają przypisane im odpowiednie wartości.

    Oto przykład tekstu, z którego należy wyciągnąć informacje:
    ```
    Mam na imie Rafał, mam 50 lat, 90 kg, 170, chodzę czasem na siłownię.
    ```

    W tym przypadku odpowiedź powinna wyglądać tak:
    {
    "gender": "M",
    "age": 50,
    "weight": 90,
    "height": 170,
    "sport_activity": 7
    }

    Oto kolejny przykład tekstu, z którego należy wyciągnąć informacje:
    ```
    Ada, mam już 3 dychy na karku, trochę gruba, ale bez przesady bo tylko 82, a zresztą dużo palę, a od tego się chudnie podobno, ruszam się jak sprzątam albo idę na zakupy.
    ```

    W tym przypadku odpowiedź powinna wyglądać tak:
    {
    "gender": "K",
    "age": 30,
    "weight": 82,
    "height": 165,
    "sport_activity": 2
    }

    I jeszcze jeden przykład:
    ```
    Sto lat, sto lat, niech żyje żyje nam, nie wstaje z kanapy.
    ```

    W tym przypadku odpowiedź powinna wyglądać tak:
    {
    "gender": "M",
    "age": 100,
    "weight": 80,
    "height": 175,
    "sport_activity": 1
    }

    """

    messages = [
        {
            "role": "system",
            "content": prompt,
        },
        {
            "role": "user",
            "content": f"```{text}```",
        },
    ]

    chat_completion = llm_client.chat.completions.create(
        response_format={"type": "json_object"},
        messages=messages,
        model="gpt-4o-mini",
    )
    response = json.loads(chat_completion.choices[0].message.content)

    # Ekstrakcja wartości z response z obsługą błędów
    try:
        gender = response['gender']
        age = response['age']
        weight = response['weight']
        height = response['height']
        sport_activity = response['sport_activity']
    except KeyError as e:
        print(f"Brakujący klucz w odpowiedzi: {e}")

    return gender, age, weight, height, sport_activity


def calculate_time_to_run_5k(gender, age, weight, height, sport_activity):

    # inicjalizacja
    time = 0

    # Obliczanie BMI
    bmi = calculate_bmi(weight, height)

    # Bazowe czasy w SEKUNDACH na 5km
    if sport_activity == 1:
        time = 3500  # 59 minut - bardzo wolny spacer
    elif sport_activity == 2:
        time = 3100  # 51 minut - wolny spacer
    elif sport_activity == 3:
        time = 2800  # 46 minut - spacer
    elif sport_activity == 4:
        time = 2500  # 41 minut - marsz
    elif sport_activity == 5:
        time = 2200  # 36 minut - szybki marsz
    elif sport_activity == 6:
        time = 1900  # 31 minut - trucht
    elif sport_activity == 7:
        time = 1700  # 28 minut - wolny bieg
    elif sport_activity == 8:
        time = 1500  # 25 minut - przyzwoity, amatorski bieg
    elif sport_activity == 9:
        time = 1300  # 22 minut - dobry czas
    elif sport_activity == 10:
        time = 1100  # 18 minut - bardzo dobry czas
    else:  # 11
        time = 900   # 15 minut - świetny czas

    # Obliczanie BMI i jego wpływ
    bmi = calculate_bmi(weight, height)

    if bmi >= 35:
        time *= 2    # +100% czasu dla znacznej otyłości
    elif bmi >= 30:
        time *= 1.25    # +25% czasu dla otyłości
    elif bmi >= 25:
        time *= 1.10    # +10% czasu dla nadwagi
    elif bmi < 18.5:
        time *= 1.05    # +5% czasu dla znacznej niedowagi (braku mięśni)

    # Wpływ płci
    if gender == "K":
        time *= 1.05    # +5% czasu dla kobiet

    # Wpływ wieku
    if age >= 65:
        time *= 1.05   # +5% czasu dla starszych
    elif age >= 45:
        time *= 1.05    # +5% czasu dla średniego wieku

    return round(time)  # zwracamy czas w SEKUNDACH


# Wprowadzenie tytułu aplikacji
st.markdown("<h1 style='text-align: center;'>Aplikacja do Wyliczania czasu na półmaraton wrocławski</h1>", unsafe_allow_html=True)
st.write("")
st.write("")

# Tekst powitalny
st.write("Witaj w aplikacji do wyliczania czasu, w jakim uda ci się pokonać dystans półmaratonu wrocławskiego, jeśli oczywiście zechcesz wziąć w nim udział.")
st.write("")

# Tworzymy pole tekstowe
user_input = st.text_area("Podaj proszę swój wiek, płeć, wagę i wzrost. A także napisz trochę o swojej aktywności fizycznej. Jakie sporty uprawiasz i z jakim natężeniem.", height=100,   max_chars=250)

if user_input and not st.session_state.data_extracted:

    response = get_data_from_text(user_input)
    if response:
        gender, age, weight, height, sport_activity = response

        # Zapisz wartości w session_state
        st.session_state.gender = "Mężczyzna" if gender == "M" else "Kobieta"
        st.session_state.age = age
        st.session_state.weight = weight
        st.session_state.height = height
        st.session_state.sport_activity = sport_activity

        # Oznacz, że dane zostały juz wyciągnięte
        st.session_state.data_extracted = True

if user_input:

    # Ustawienia ograniczeń
    AGE_MIN, AGE_MAX = 10, 100
    WEIGHT_MIN, WEIGHT_MAX = 45, 350
    HEIGHT_MIN, HEIGHT_MAX = 120, 250

    # Obliczanie BMI
    bmi = calculate_bmi(st.session_state.weight, st.session_state.height)

    st.write("")
    st.write(' Jeśli coś pokręciłem (a jestem tylko biedną, sztuczną inteligencją), to z góry przepraszam. Na szczęście możesz ręcznie wprowadzić odpowiednie poprawki.')

    # Moj wesoły obrazek
    st.image('ewolucja.png')

    # Ustawianie kolumn
    col1, col2, col3 = st.columns([0.15, 5, 0.15])

    with col1:
        st.write("")

    with col2:

        # Callback dla suwaka
        def update_activity():
            st.session_state.sport_activity = st.session_state.activity_slider

        current_activity = st.slider(
            "Stopień aktywności fizycznej:",
            min_value=1,
            max_value=11,
            value=st.session_state.sport_activity,
            key='activity_slider',
            on_change=update_activity
        )

        # Lista napisów odpowiadających pozycjom suwaka
        napisy = [
            "Władca kanapy",
            "Mistrz kulinarnego maratonu",
            "Medal za walkę z grawitacją",
            "Biegacz do lodówki",
            "Stylowy spacerniak",
            "Sprintem, to co najwyżej na przystanek",
            "Szef porannych rozciągów",
            "Wyginam śmiało ciało... dla mnie to mało!",
            "Król Biceps Pierwszy",
            "Szaleństwo cardio",
            "Szybki jak Sonic"
        ]

        # Wyświetlanie napisu w zależności od pozycji suwaka, z centrowaniem
        st.markdown(
            f"<h5 style='text-align: center;'>{napisy[current_activity - 1]}</h5>",
            unsafe_allow_html=True
        )
        st.write("")

    with col3:
        st.write("")

    with st.form("input_form"):
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1, 5, 1, 5, 1, 5, 1, 5, 1])

        with col1:
            st.write("")

        with col2:
            # Płeć
            gender_index = 0 if st.session_state.gender == "Mężczyzna" else 1
            st.session_state.gender = st.selectbox(
                "Płeć:",
                options=["Mężczyzna", "Kobieta"],
                index=gender_index)

        with col3:
            st.write("")

        with col4:
            # Wiek
            age_input = st.number_input(
                "Wiek (lata):",
                value=st.session_state.age,
                min_value=AGE_MIN,
                max_value=AGE_MAX,
                step=1
            )
            st.session_state.age = validate_input(age_input, AGE_MIN, AGE_MAX)

        with col5:
            st.write("")

        with col6:
            # Waga
            weight_input = st.number_input(
                "Waga (kg):",
                value=st.session_state.weight,
                min_value=WEIGHT_MIN,
                max_value=WEIGHT_MAX,
                step=1
            )
            st.session_state.weight = validate_input(weight_input, WEIGHT_MIN, WEIGHT_MAX)

        with col7:
            st.write("")

        with col8:
            # Wzrost
            height_input = st.number_input(
                "Wzrost (cm):",
                value=st.session_state.height,
                min_value=HEIGHT_MIN,
                max_value=HEIGHT_MAX,
                step=1
            )
            st.session_state.height = validate_input(height_input, HEIGHT_MIN, HEIGHT_MAX)

        with col9:
            st.write("")

        st.write("")
        st.write("")

        # Przycisk do zatwierdzenia danych
        submit_button = st.form_submit_button("Zatwierdź zmiany")

        if submit_button:

            current_gender = "K" if st.session_state.gender == "Kobieta" else "M"
            speed = calculate_time_to_run_5k(
                current_gender,
                st.session_state.age,
                st.session_state.weight,
                st.session_state.height,
                st.session_state.sport_activity
            )

            # Utworzenie df z danymi
            df = pd.DataFrame({
                'gender': current_gender,
                'age': st.session_state.age,
                'speed': speed
            }, index=[0])
            df.columns = ['Płeć', 'Wiek', '5 km Czas']

            # Wykonanie predykcji i odczyt wyniku
            prediction = predict_model(model, data=df)
            czas = int(prediction.loc[0, 'prediction_label'])

            if speed > 2840:
                czas = int(speed * 4.2)

            # seconds = format_time(czas)
            total_minutes = czas // 60
            hours = total_minutes // 60
            minutes = total_minutes % 60

            # Zastosowanie reguł zaokrąglania
            if hours >= 5:
                minutes = 0  # Zwraca godziny i 0 minut
            elif 2 <= hours < 5:
                # Zaokrąglamy do kwadransów
                minutes = (minutes // 15) * 15
            else:
                # Zaokrąglamy do 5 minut
                minutes = (minutes // 5) * 5

            if hours >= 5:
                napis = 'Przewidywany czas biegu (jeśli można tak to nazwać) wynosi powyżej 5 godzin. Może więc warto zacząć raczej od spacerów? I zastanowić się poważnie nad zmianą trybu życia?'
            elif hours > 1 and hours < 5 and minutes > 0:
                napis = f"Przewidywany czas biegu wynosi {hours} godziny i {minutes} minut."
            elif hours > 1 and hours < 5 and minutes == 0:
                napis = f"Przewidywany czas biegu wynosi {hours} godziny."
            elif hours == 1 and minutes > 0:
                napis = f"Przewidywany czas biegu wynosi {hours} godzinę i {minutes} minut."
            elif hours == 1 and minutes == 0:
                napis = f"Przewidywany czas biegu wynosi {hours} godzinę."
            st.markdown(f"<h6 style='font-size: 24px;'>{napis}</h6>", unsafe_allow_html=True)
