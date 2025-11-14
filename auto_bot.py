from bot import TradingBot
import time

def main():
    bot = TradingBot()
    
    while True:
        try:
            print("🔄 Запускаю анализ...")
            bot.run_once()
            print("💤 Жду 5 минут...\n")
            time.sleep(300)  # 5 минут
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
