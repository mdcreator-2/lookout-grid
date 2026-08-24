# Lookout Grid

Lookout Grid is an integrated smart grid monitoring and predictive management platform.

## Repository Structure & Team Ownership

```
lookout-grid/
├── edge/          ← Abhirup (ESP32 firmware, C++ code)
├── gateway/       ← Abhirup + Aamir (RPi gateway software)
├── backend/       ← Aamir (FastAPI, database, MQTT)
├── frontend/      ← Abhay (React dashboard)
├── ml/            ← Kaif (models, notebooks, datasets)
├── simulator/     ← Ayesha (fake data generators for testing)
├── docs/          ← Taha (research, PPT content)
└── shared/        ← Aamir maintains, EVERYONE reads
    └── schema.json
```
