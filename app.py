import streamlit as st

# FUNKCJE


# Funkcja do walidacji wartości
def validate_input(value, min_value, max_value):
    if value < min_value:
        return min_value
    elif value > max_value:
        return max_value
    return value


# Wprowadzenie tytułu aplikacji
st.markdown("<h1 style='text-align: center;'>Aplikacja do Wyliczania czasu na półmaraton wrocławski</h1>", unsafe_allow_html=True)
st.write("")
st.write("")

# Tekst powitalny
st.write("Witaj w aplikacji do wyliczania czasu, w jakim uda ci się pokonać dystans półmaratonu wrocławskiego, jeśli oczywiście zechcesz wziąć w nim udział.")
st.write("")

# Tworzymy pole tekstowe
user_input = st.text_area("Podaj proszę swój wiek, płeć, wagę i wzrost. A także napisz trochę o swojej aktywności sportowej. A jeśli biegasz, to podaj na jakim dystansie i swój czas na nim.", height=100)

age = 35         # Zmienna dla wieku
weight = 80      # Zmienna dla wagi
height = 175     # Zmienna dla wzrostu
gender = "M"     # Domyślna płeć

# Ustawienia ograniczeń
AGE_MIN, AGE_MAX = 10, 100
WEIGHT_MIN, WEIGHT_MAX = 40, 350
HEIGHT_MIN, HEIGHT_MAX = 120, 250

st.write("")
st.write(' Jeśli coś pokręciłem (a jestem tylko biedną, sztuczną inteligencją), to możesz wprowadzić ręcznie odpowiednie poprawki.')

col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1, 5, 1, 5, 1, 5, 1, 5, 1])

with col1:
    st.write("")

with col2:
    # Płeć
    gender = st.selectbox("Płeć:", options=["Mężczyzna", "Kobieta"], index=0)

with col3:
    st.write("")

with col4:
    # Wiek
    age_input = st.number_input("Wiek (lata):", value=age, min_value=AGE_MIN, max_value=AGE_MAX, key="age_input", step=1)
    age_input = validate_input(age_input, AGE_MIN, AGE_MAX)
    age = age_input

with col5:
    st.write("")

with col6:
    # Waga
    weight_input = st.number_input("Waga (kg):", value=weight, min_value=WEIGHT_MIN, max_value=WEIGHT_MAX, key="weight_input", step=1)
    weight_input = validate_input(weight_input, WEIGHT_MIN, WEIGHT_MAX)
    weight = weight_input

with col7:
    st.write("")

with col8:
    # Wzrost
    height_input = st.number_input("Wzrost (cm):", value=height, min_value=HEIGHT_MIN, max_value=HEIGHT_MAX, key="height_input", step=1)
    height_input = validate_input(height_input, HEIGHT_MIN, HEIGHT_MAX)
    height = height_input

with col9:
    st.write("")

st.write("")
st.write("")

# Moj wesoły obrazek
st.image('ewolucja.png')

# Ustawianie kolumn
col1, col2, col3 = st.columns([0.15, 5, 0.15])

with col1:
    st.write("")

with col2:
    sport_activity = st.slider(
        "Stopień aktywności fizycznej:",
        min_value=1,
        max_value=11,
        value=5
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
        f"<h5 style='text-align: center;'>{napisy[sport_activity - 1]}</h5>",
        unsafe_allow_html=True
    )

with col3:
    st.write("")

# Wyświetlenie końcowych wartości
st.write(f"Płeć: {gender}")
st.write(f"Wiek: {age} lat")
st.write(f"Waga: {weight} kg")
st.write(f"Wzrost: {height} cm")
