import subprocess
import time
import sys

def main():
    print("🚀 АВТОМАТИЧЕСКИЙ ЗАПУСК БОТА")
    print("📱 Бот будет работать пока открыт Codespace")
    
    while True:
        try:
            print("\n" + "="*50)
            print("🔄 Запускаю бота...")
            
            # Запускаем бота
            process = subprocess.Popen([sys.executable, "bot_advanced.py"])
            
            # Ждем завершения или перезапускаем через 6 часов
            time.sleep(6 * 60 * 60)  # 6 часов
            
            print("🔄 Перезапускаю бота...")
            process.terminate()
            process.wait()
            
        except KeyboardInterrupt:
            print("\n🛑 Остановка бота...")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 60 секунд...")
            time.sleep(60)

if __name__ == "__main__":
    main()
