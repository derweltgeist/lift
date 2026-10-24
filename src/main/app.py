from nicegui import ui
import random

jumlahOrang = []

def autoOrang():
    for jumlah in jumlahOrang:
        jumlah.value = float(random.randint(0,10))


def autoLantai():
    jumlahLantai.value = float(random.randint(2,20))

@ui.refreshable
def daftarOrang():
    jumlahOrang.clear()
    with ui.grid(columns = 5):
        for i in range(int(jumlahLantai.value)):
            jumlah = ui.number(label=f"Lantai {i+1}", value=5)
            jumlahOrang.append(jumlah)

ui.label("Simulasi Lift").style('font-size: 48px; font-weight: bold;')

with ui.row():
    with ui.card():
        ui.label("Orang & Lantai").style('font-size: 24px; font-weight: bold;')
        with ui.column():
            with ui.row():
                jumlahLantai = ui.number(label="Jumlah Lantai", value=10, on_change=lambda: daftarOrang.refresh())
                ui.button("Auto Generate Jumlah Lantai", on_click=autoLantai)
                tinggiLantai = ui.number(label="Tinggi Lantai (m)", value=3)
            ui.label("Orang per Lantai").style('font-size: 16px; font-weight: bold;')
            daftarOrang()      
            ui.button("Auto Generate Orang", on_click=autoOrang)
    with ui.column():
        with ui.card():
            ui.label("Lift & Counterweight").style('font-size: 24px; font-weight: bold;')
            with ui.row():
                massaSangkarLift = ui.number(label="Massa Sangkar Lift (kg)", value=0)
                massaCounterweight = ui.number(label="Massa Counterweight (kg)", value=0)
        with ui.card():
            ui.label("Tali & Katrol Governor (Safety)").style('font-size: 24px; font-weight: bold;')
            with ui.column():
                rapatMassaTaliGovernor = ui.number(label="Rapat Massa Tali (kg/m)", value=0)
                ultimateTensileStrengthGovernor = ui.number(label="Ultimate Tensile Strength (N)", value=0)
                radiusKatroGovernor = ui.number(label="Radius Katrol (m)", value=0)
                gayaGesekKatrolGovernor = ui.number(label="Gaya Gesek Katrol (N)", value=0)
    with ui.card():
        ui.label("Tali & Katrol Utama").style('font-size: 24px; font-weight: bold;')
        with ui.column():
            rapatMassaTaliUtama = ui.number(label="Rapat Massa Tali (kg/m)", value=0)
            jumlahTali = ui.number(label="Jumlah Tali", value=0)
            ultimateTensileStrengthUtama = ui.number(label="Ultimate Tensile Strength (N)", value=0)
            radiusKatrolUtama = ui.number(label="Radius Katrol (m)", value=0)
            gayaGesekKatrolUtama = ui.number(label="Gaya Gesek Katrol (N)", value=0)  
    


ui.run(title="Simulasi Lift Kelompok 8 BerKom K-31")


