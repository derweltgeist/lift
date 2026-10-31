import math
import random
import sys
from pathlib import Path

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
        human[i] = {
            "human": orang,
            "mass": orang * MassaOrang,
            "up": bool(jumlahNaik[i].value),
            "down": bool(jumlahTurun[i].value),
        }
    return human

def kumpulkanConf():
    return {
        "gravity": 9.81,
        "acceleration": angka(percepatan),
        "max_motor_force": 100000.0,
        "max_cable_force": angka(ultimateTensileStrengthUtama) * angka(jumlahTali),
        "lift_mass": angka(massaSangkarLift),
        "counterweight_mass": angka(massaCounterweight),
        "lift_passenger_mass": 0.0,
        "pulley_rot_inertia": 5.0,
        "pulley_friction": angka(gayaGesekKatrolUtama),
        "lift_friction": 0.01,
        "counterweight_friction": 0.01,
        "pulley_coefficient": 0.5,
        "radius": angka(radiusKatrolUtama),
        "wrap_angle": math.pi,
        "distance": angka(tinggiLantai),
        "step": 0.05,
        "speed": angka(kecepatanMaks),
        "position": int(lantaiLift.value or 0),
    }

def tampilkanIndikator(pesan):
    ui.notify(pesan, type="negative", close_button=True)

def tampilkanGrafik(posisi, kecepatan, step, waktu=None):
    if not waktu or len(waktu) != len(posisi):
        waktu = [i * step for i in range(len(posisi))]
    grafik.options["series"][0]["data"] = [[t, s] for t, s in zip(waktu, posisi)]
    grafik.options["series"][1]["data"] = [[t, v] for t, v in zip(waktu, kecepatan)]
    grafik.update()

def klikSimulasi():
    human = kumpulkanHuman()
    conf = kumpulkanConf()
    posisi = int(lantaiLift.value or 0)
    adaPermintaan = any((d["up"] or d["down"]) and i != posisi for i, d in human.items())
    if not adaPermintaan:
        tampilkanIndikator("Centang minimal satu Naik/Turun di lantai selain lantai lift")
        return
    try:
        sim = Simulate(conf)
        sim(conf, human)
    except Exception as e:
        tampilkanIndikator(f"Simulasi gagal: {type(e).__name__}: {e}")
        return
    tampilkanGrafik(sim.s, sim.v, conf["step"], getattr(sim, "t", None))
    ui.notify("Simulasi selesai", type="positive")

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
            ui.button("Auto Generate Jumlah Lantai", on_click=autoLantai)
            tinggiLantai = ui.number(label="Tinggi Lantai (m)", value=3)
            lantaiLift = ui.number(label="Lantai Lift Sekarang", value=0)
        ui.label("Orang per Lantai").style('font-size: 16px; font-weight: bold;')
        daftarOrang()
        ui.button("Auto Generate Orang", on_click=autoOrang)

with ui.row():
    with ui.card():
        ui.label("Lift & Counterweight").style('font-size: 24px; font-weight: bold;')
        with ui.row():
            massaSangkarLift = ui.number(label="Massa Sangkar Lift (kg)", value=500)
            massaCounterweight = ui.number(label="Massa Counterweight (kg)", value=2000)
        with ui.row():
            kecepatanMaks = ui.number(label="Kecepatan Maks (m/s)", value=2.5)
            percepatan = ui.number(label="Percepatan (m/s²)", value=1.0)
    with ui.card():
        ui.label("Tali & Katrol Governor (Safety)").style('font-size: 24px; font-weight: bold;')
        with ui.column():
            rapatMassaTaliGovernor = ui.number(label="Rapat Massa Tali (kg/m)", value=0.2)
            ultimateTensileStrengthGovernor = ui.number(label="Ultimate Tensile Strength (N)", value=20000)
            radiusKatroGovernor = ui.number(label="Radius Katrol (m)", value=0.15)
            gayaGesekKatrolGovernor = ui.number(label="Gaya Gesek Katrol (N)", value=20)
    with ui.card():
        ui.label("Tali & Katrol Utama").style('font-size: 24px; font-weight: bold;')
        with ui.column():
            rapatMassaTaliUtama = ui.number(label="Rapat Massa Tali (kg/m)", value=0.5)
            jumlahTali = ui.number(label="Jumlah Tali", value=4)
            ultimateTensileStrengthUtama = ui.number(label="Ultimate Tensile Strength (N)", value=50000)
            radiusKatrolUtama = ui.number(label="Radius Katrol (m)", value=0.3)
            gayaGesekKatrolUtama = ui.number(label="Gaya Gesek Katrol (N)", value=50)

ui.button("Jalankan Simulasi", on_click=klikSimulasi)

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