import uvicorn
import logging
from fastapi import FastAPI, Request, HTTPException
from telegram import Update

from core.config import settings
from api.router import api_router
from bot.runner import create_bot_app

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_router, prefix=settings.API_V1_STR)

# Telegram webhook configuration
WEBHOOK_PATH = f"/telegram/webhook/{settings.TELEGRAM_TOKEN}"
if settings.PUBLIC_BASE_URL:
    WEBHOOK_URL = f"{settings.PUBLIC_BASE_URL}{WEBHOOK_PATH}"
else:
    WEBHOOK_URL = None

# Build PTB Application
application = create_bot_app(settings)

@app.get("/", summary="Health check")
def root():
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Starting bot application. PUBLIC_BASE_URL={settings.PUBLIC_BASE_URL!r}")
    logging.info(f"Computed WEBHOOK_URL={WEBHOOK_URL!r}")
    await application.initialize()
    await application.start()
    # Set webhook if public URL is provided; otherwise, ensure webhook is deleted
    if WEBHOOK_URL:
        try:
            await application.bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
            logging.info("Webhook set successfully")
        except Exception as e:
            logging.exception(f"Failed to set webhook: {e}")
    else:
        try:
            await application.bot.delete_webhook(drop_pending_updates=True)
            logging.info("Webhook deleted (no PUBLIC_BASE_URL configured)")
        except Exception as e:
            logging.exception(f"Failed to delete webhook: {e}")

@app.on_event("shutdown")
async def on_shutdown():
    # Clean shutdown and optional webhook cleanup
    try:
        await application.bot.delete_webhook(drop_pending_updates=False)
    except Exception:
        pass
    await application.stop()
    await application.shutdown()

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    if not WEBHOOK_URL:
        raise HTTPException(status_code=503, detail="Webhook URL not configured")
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    logging.info(f"Received Telegram update: keys={list(data.keys())}")
    update = Update.de_json(data=data, bot=application.bot)
    try:
        logging.info(f"Processing update_id={getattr(update, 'update_id', None)}")
    except Exception:
        pass
    await application.process_update(update)
    return {"ok": True}

@app.get("/telegram/webhook-info", summary="Inspect Telegram webhook info")
async def telegram_webhook_info():
    info = await application.bot.get_webhook_info()
    return info.to_dict()

@app.post("/telegram/reset-webhook", summary="Reset Telegram webhook based on PUBLIC_BASE_URL")
async def telegram_reset_webhook():
    if WEBHOOK_URL:
        await application.bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
        return {"ok": True, "action": "set", "url": WEBHOOK_URL}
    else:
        await application.bot.delete_webhook(drop_pending_updates=True)
        return {"ok": True, "action": "deleted"}

if __name__ == "__main__":
    host = "127.0.0.1"
    port = int(getattr(settings, "PORT", 8080))
    uvicorn.run("main:app", host=host, port=port)
