#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
from telegram.ext import Application

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def test_connection():
    print("🤖 Testing minimal bot connection...")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    try:
        await app.initialize()
        print("✅ Bot initialized successfully!")
        
        await app.start()
        print("✅ Bot started successfully!")
        
        print("🔍 Testing get_me...")
        me = await app.bot.get_me()
        print(f"✅ Bot info: {me.first_name} (@{me.username})")
        
        await app.stop()
        print("✅ Bot stopped cleanly")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())