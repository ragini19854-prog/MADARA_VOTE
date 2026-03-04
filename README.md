# Giveaway Management Bot

Production-ready Telegram giveaway management bot built with **Python 3.11+, aiogram 3.x, aiosqlite, dotenv**.

## Features
- Full start menu with inline controls
- New Giveaway FSM (title, channel verification, mode)
- Paid + free modes
- Deep-link participation (`/start giveaway_{id}`)
- Vote buttons in channel posts
- Membership-verified voting
- Auto vote removal via `ChatMemberUpdated`
- Paid vote approvals and host-side manual vote add
- Leaderboard + giveaway management panel
- Owner panel (`/ownerpanel`, `/ban`, `/unban`, `/broadcast`, `/addowner`)
- Add Channel/Add Group and post creator flow

## Run
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Architecture
- `main.py` bootstraps bot and dispatcher
- `config.py` env settings loader
- `database.py` async sqlite schema and data access
- `handlers/` routers
- `keyboards/` inline keyboards
- `states/` FSM states
- `middlewares/` security middleware
- `utils/` helper utilities
