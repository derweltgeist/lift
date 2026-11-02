import random
import sys
from pathlib import Path
import traceback

from nicegui import ui

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.main.simulator import Simulate

jumlahOrang = []
jumlahNaik = []
jumlahTurun = []

MassaOrang = 70.0

def angka(kotak):
    return float(kotak.value or 0)

def collectData():
    return{
        "jumlahLantai" : jumlahLantai.value
    }

def kumpulkanHuman():
    human = {}
    for i in range(len(jumlahOrang)):
        orang = int(jumlahOrang[i].value or 0)
        human[i+1] = {
            "human": orang,
            "mass": orang * MassaOrang,
            "up": bool(jumlahNaik[i].value),
            "down": bool(jumlahTurun[i].value),
        }
    return human

def kumpulkanConf():
    return {
        "gravity": angka(gravitasi),
        "acceleration": angka(percepatan),
        "max_motor_force": angka(gayaKatrol),
        "max_cable_force": angka(ultimateTensileStrengthUtama) * angka(jumlahTali),
        "lift_mass": angka(massaSangkarLift),
        "counterweight_mass": angka(massaCounterweight),
        "lift_passenger_mass": 0.0,
        "pulley_rot_inertia": angka(inersiaKatrol),
        "pulley_friction": angka(gayaGesekKatrolUtama),
        "lift_friction": angka(liftFriction),
        "counterweight_friction": angka(counterweightFriction),
        "pulley_coefficient": angka(koefisienGayaGesekKatrolUtama),
        "radius": angka(radiusKatrolUtama),
        "wrap_angle": angka(wrapAngle),
        "distance": angka(tinggiLantai),
        "step": angka(waktu),
        "speed": angka(kecepatanMaks),
        "position": int(lantaiLift.value),
    }

def tampilkanIndikator(pesan):
    ui.notify(pesan, type="negative", close_button=True)

def tampilkanGrafik(posisi, kecepatan, step, waktu=None):
    if not waktu or len(waktu) != len(posisi):
        waktu = [i * step for i in range(len(posisi))]
    grafik.options["series"][0]["data"] = [[t, s] for t, s in zip(waktu, posisi)]
    grafik.options["series"][1]["data"] = [[t, v] for t, v in zip(waktu, kecepatan)]
    print("it runs!")
    grafik.update()

def klikSimulasi():
    human = kumpulkanHuman()
    conf = kumpulkanConf()
    posisi = int(lantaiLift.value)
    adaPermintaan = any((d["up"] or d["down"]) and i != posisi for i, d in human.items())
    if not adaPermintaan:
        tampilkanIndikator("Centang minimal satu Naik/Turun di lantai selain lantai lift")
        return
    try:
        sim = Simulate(conf)
        sim(human)
        tampilkanGrafik(sim.s, sim.v, conf["step"], getattr(sim, "t", None))
        ui.notify("Simulasi selesai", type="positive")
    except Exception:
        tampilkanIndikator("Terdapat galat internal, silahkan cek konsol/terminal.")
        traceback.print_exc()
   

def autoOrang():
    for jumlah in jumlahOrang:
        jumlah.value = float(random.randint(0,10))
 
def autoLantai():
    jumlahLantai.value = float(random.randint(2,20))

@ui.refreshable
def daftarOrang():
    jumlahOrang.clear()
    jumlahNaik.clear()
    jumlahTurun.clear()
    with ui.grid(columns=5):
        for i in range(int(jumlahLantai.value)):
            with ui.card():
                jumlah = ui.number(label=f"Lantai {i+1}", value=5)
                jumlahOrang.append(jumlah)
                naik = ui.checkbox("Naik")
                turun = ui.checkbox("Turun")
                jumlahNaik.append(naik)
                jumlahTurun.append(turun)

ui.label("Simulasi Lift").style('font-size: 48px; font-weight: bold;')

with ui.card():
    ui.label("Orang & Lantai").style('font-size: 24px; font-weight: bold;')
    with ui.column():
        with ui.row():
            jumlahLantai = ui.number(label="Jumlah Lantai", value=5, on_change=lambda: daftarOrang.refresh())
            tinggiLantai = ui.number(label="Tinggi Lantai (m)", value=3)
            lantaiLift = ui.number(label="Lantai Lift Sekarang", value=1)
        ui.label("Orang per Lantai").style('font-size: 16px; font-weight: bold;')
        daftarOrang()
        with ui.row():
            ui.button("Auto Generate Orang", on_click=autoOrang)
            ui.button("Auto Generate Jumlah Lantai", on_click=autoLantai)
            ui.button("Jalankan Simulasi", on_click=klikSimulasi)

with ui.row():
    with ui.card():
        ui.label("Lift & Counterweight").style('font-size: 24px; font-weight: bold;')
        with ui.row():
            massaSangkarLift = ui.number(label="Massa Sangkar Lift (kg)", value=500)
            massaCounterweight = ui.number(label="Massa Counterweight (kg)", value=2000)
        with ui.row():
            liftFriction = ui.number(label="Gaya Gesek Lift (N)", value=10)
            counterweightFriction = ui.number(label="Gaya Gesek Counterweight (N)", value=10)      
    with ui.card():
        ui.label("Tali & Katrol").style('font-size: 24px; font-weight: bold;')
        with ui.row():
            with ui.column():
                jumlahTali = ui.number(label="Jumlah Tali", value=4)
                ultimateTensileStrengthUtama = ui.number(label="Gaya Tegangan Tali Maks per Tali (N)", value=50000)
                wrapAngle = ui.number(label="Sudut lilitan tali (rads)", value=3.14)
                gayaKatrol = ui.number(label="Gaya Katrol Maks (N)", value=10)
            with ui.column():
                radiusKatrolUtama = ui.number(label="Radius Katrol (m)", value=0.3)
                gayaGesekKatrolUtama = ui.number(label="Gaya Gesek Katrol (N)", value=50)
                koefisienGayaGesekKatrolUtama = ui.number(label="Koefisien Gaya Gesek Katrol (N)", value=0.5)
                inersiaKatrol = ui.number(label="Inersia Rotasi Katrol (kg m^2)", value=5)
    with ui.card():
        ui.label("Hal Lain").style('font-size: 24px; font-weight: bold;')
        with ui.row():
            with ui.column():
                kecepatanMaks = ui.number(label="Kecepatan Preferensi (m/s)", value=2.5)
                percepatan = ui.number(label="Percepatan Preferensi (m/s²)", value=1.0)
            with ui.column():
                gravitasi = ui.number(label="Percepatan Gravitasi (m/s^2)", value=10)
                waktu = ui.number(label="Step Waktu (detik)", value=0.5)

grafik = ui.echart({
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["Posisi (m)", "Kecepatan (m/s)"]},
    "xAxis": {"type": "value", "name": "Waktu (s)"},
    "yAxis": [
        {"type": "value", "name": "Posisi (m)"},
        {"type": "value", "name": "Kecepatan (m/s)"},
    ],
    "series": [
        {"name": "Posisi (m)", "type": "line", "showSymbol": False, "data": []},
        {"name": "Kecepatan (m/s)", "type": "line", "showSymbol": False, "data": []},
    ],
}).classes("w-full h-96")


ui.run(title="Simulasi Lift Kelompok 8 BerKom K-37")