from core import Adb, compare

adb = Adb(r"C:\Users\Konrad\Desktop\platform-tools-latest-windows\platform-tools\adb.exe")

print("Urządzenia:", adb.devices())
print("Pamięci:", adb.list_storages())
print("Foldery w Music:", adb.list_dirs("/storage/6666-3832/Music"))

plan = compare(
    adb,
    r"C:\Users\Konrad\Desktop\moje rzeczy\Moje piosenki",
    "/storage/6666-3832/Music/Samsung/Moje piosenki",
)
print(f"Komputer: {plan.local_count}, telefon: {plan.phone_count}")
print("Do skopiowania:", len(plan.to_copy), "| nadmiarowe:", len(plan.extra))