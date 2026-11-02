import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from physics import Physics

# =========== KONFIGURASI, SILAHKAN UBAH SENDIRI ===========

O  = 0 # Batas toleransi
D  = 0 # Peningkatan massa penumpang sebelum binary search.
SF = 0 # Safety factor, nilai 0 < SF <= 1, semakin kecil semakin ketat.

configuration = {
"lift_mass"               : 0 # Massa lift.
,"counterweight_mass"     : 0 # Massa counterweight.
,"pulley_rot_inertia"     : 0 # Inersia rotasi katrol.
,"gravity"                : 0 # Konstanta gravitasi.
,"acceleration"           : 0 # Akselerasi preferensi.
,"lift_friction"          : 0 # Gaya gesek lift.
,"counterweight_friction" : 0 # Gaya gesek counterweight
,"pulley_friction"        : 0 # Gaya gesek katrol.
,"pulley_coefficient"     : 0 # Koefisien gaya gesek katrol.
,"radius"                 : 0 # Radius katrol.
,"wrap_angle"             : 0 # Sudut lilitan kabel lift.
,"max_motor_force"        : 0 # Gaya motor maksimal.
,"max_cable_force"        : 0 # Gaya kabel maksimal.
}


# Variabel tampung.

lower_bound = 0
upper_bound = 0

# Mulai iterasi sampai terjadi kegagalan.
counter = 0 # Sekadar counter saja.
success = 0 # Massa penumpang terakhir kali yang sukses.
fail    = 0 # Massa penumpang pertama kali yang gagal.

# Loop sampai gagal
while True:
    new_conf = configuration
    new_conf['lift_passenger_mass'] = D * counter
    try:
        Physics(new_conf)()
        success = new_conf['lift_passenger_mass']
        counter += 1
    except ZeroDivisionError:
        print("ERROR: Configuration is invalid in first try, zero division error is detected.")
        exit(1)
    except Exception:
        if counter == 0:
            print("ERROR: Configuration is invalid in first try.")
            raise Exception
        else:
            fail = new_conf['lift_passenger_mass']
            break

# Jika sudah gagal, maka...
lower_bound    = success
upper_bound    = fail
median         = (lower_bound + upper_bound) / 2
success_median = 0
fail_median    = 0
depth          = 0

while True:
    new_conf = configuration
    new_conf['lift_passenger_mass'] = median # pyright: ignore[reportArgumentType]
    if upper_bound - lower_bound <= O: # sudah sama atau lebih kecil dari batas toleransi.
        print("\n==== HASIL ====")
        print(f"- Latest success median : {success_median}")
        print(f"- Latest failed median  : {fail_median}")
        print(f"- Upper bound           : {upper_bound}")
        print(f"- Lower bound           : {lower_bound}")
        print(f"- Range                 : {upper_bound - lower_bound}")
        print(f"- Depth                 : {depth}")
        print("----------")
        print(f"Nilai massa penumpang yang sudah di-adjust oleh Safety Factor: {SF * success_median} kg")
        exit(0)
    try:
        Physics(new_conf)()
        lower_bound = median
        sucess_median = median
        median = (lower_bound + upper_bound) / 2
    except Exception:
        upper_bound = median
        fail_median = median
        median = (lower_bound + upper_bound) / 2
    depth += 1