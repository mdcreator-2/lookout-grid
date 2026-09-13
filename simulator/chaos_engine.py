from flood_simulator import run_simulation as run_flood
from fire_simulator import run_simulation as run_fire
from aqi_simulator import run_simulation as run_aqi


while True:

    print("""
========================================
             CHAOS ENGINE
========================================

FLOOD
1.  🌊 Flood
2.  ⚡ Flash Flood
3.  🌱 Flood Recovery

FOREST FIRE
4.  🔥 Forest Fire
5.  🔥🔥 Severe Forest Fire
6.  🌱 Fire Recovery

AIR QUALITY
7.  🌫️ AQI Pollution
8.  ☠️ Severe AQI
9.  🌱 AQI Recovery

SYSTEM
10. 🌤️ Normal
11. 📊 System Status
12. 🚪 Exit

========================================
""")

    choice = input("Choose an incident: ")


    # FLOOD
    if choice == "1":

        print("\n🌊 FLOOD INCIDENT STARTED!")

        run_flood("FLOOD")


    elif choice == "2":

        print("\n⚡ FLASH FLOOD INCIDENT STARTED!")

        run_flood("FLASH_FLOOD")


    elif choice == "3":

        print("\n🌱 FLOOD RECOVERY STARTED!")

        run_flood("RECOVERY")


    # FOREST FIRE
    elif choice == "4":

        print("\n🔥 FOREST FIRE INCIDENT STARTED!")

        run_fire("FIRE")


    elif choice == "5":

        print("\n🔥🔥 SEVERE FOREST FIRE STARTED!")

        run_fire("SEVERE_FIRE")


    elif choice == "6":

        print("\n🌱 FOREST FIRE RECOVERY STARTED!")

        run_fire("RECOVERY")


    # AQI
    elif choice == "7":

        print("\n🌫️ AQI POLLUTION INCIDENT STARTED!")

        run_aqi("POLLUTION")


    elif choice == "8":

        print("\n☠️ SEVERE AQI INCIDENT STARTED!")

        run_aqi("SEVERE_POLLUTION")


    elif choice == "9":

        print("\n🌱 AQI RECOVERY STARTED!")

        run_aqi("RECOVERY")


    # NORMAL
    elif choice == "10":

        print("\n🌤️ NORMAL ENVIRONMENT STARTED!")

        run_aqi("NORMAL")


    # STATUS
    elif choice == "11":

        print("""
========================================
           CHAOS ENGINE STATUS
========================================

✅ Flood simulator
✅ 100 fake sensor nodes
✅ Multiple flood conditions
✅ Recovery scenario
✅ JSON sensor structure
✅ MQTT publishing
✅ Docker/Mosquitto setup
✅ MQTT reception tested

🔥 Forest Fire simulator
🌫️ AQI simulator
🎮 Chaos Engine integration

========================================
""")


    # EXIT
    elif choice == "12":

        print("\nExiting Chaos Engine...")
        break


    else:

        print("\n❌ Invalid choice. Choose 1-12.")