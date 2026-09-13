print("================================")
print("        CHAOS ENGINE")
print("================================")

print("1. Normal")
print("2. Heavy Rain")
print("3. Flood")
print("4. Flash Flood")
print("5. Recovery")
print("6. Exit")

choice = input("Choose an incident: ")

if choice == "1":
    from flood_simulator import run_simulation
    print("\n✅ NORMAL CONDITIONS STARTED!")
    run_simulation("NORMAL")

elif choice == "2":
    from flood_simulator import run_simulation
    print("\n🌧️ HEAVY RAIN STARTED!")
    run_simulation("HEAVY_RAIN")

elif choice == "3":
    from flood_simulator import run_simulation
    print("\n🌊 FLOOD INCIDENT STARTED!")
    run_simulation("FLOOD")

elif choice == "4":
    from flood_simulator import run_simulation
    print("\n🚨 FLASH FLOOD INCIDENT STARTED!")
    run_simulation("FLASH_FLOOD")

elif choice == "5":
    from flood_simulator import run_simulation
    print("\n💧 RECOVERY STARTED!")
    run_simulation("RECOVERY")

elif choice == "6":
    print("\nExiting Chaos Engine...")

else:
    print("\n❌ Invalid choice")