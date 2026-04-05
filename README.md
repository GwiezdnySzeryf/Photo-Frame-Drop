# Photo Frame Drop

Add-on do Home Assistanta pozwalający na łatwe wrzucanie i zarządzanie zdjęciami dla cyfrowej ramki na zdjęcia z dowolnego miejsca.

## Funkcje
- Piękny, nowoczesny interfejs użytkownika
- Łatwe wrzucanie zdjęć (Drag & Drop)
- Galeria wgranych zdjęć z możliwością ich usuwania
- Ochrona hasłem dostępu
- Integracja z systemem powiadomień Home Assistanta
- Zdjęcia lądują bezpośrednio w folderze `/media` Home Assistanta

## Instalacja

1. Przejdź do **Ustawienia** -> **Dodatki** w swoim Home Assistant.
2. Kliknij **SKLEP Z DODATKAMI** (prawy dolny róg).
3. Kliknij ikonę trzech kropek w prawym górnym rogu i wybierz **Repozytoria**.
4. Dodaj URL tego repozytorium GitHub i kliknij DODAJ.
5. Zamknij okno, odśwież stronę.
6. Znajdź **Photo Frame Drop** na liście i zainstaluj.
7. Przejdź do zakładki **Konfiguracja** dodatku, ustaw hasło (domyślnie `admin`) oraz folder docelowy w media (domyślnie `digital_frame`). Zapisz.
8. Uruchom dodatek.

## Dostęp z zewnątrz

Dostęp do Add-onu spoza sieci lokalnej jest możliwy, jeśli wystawisz port `8000` (lub inny, który skonfigurujesz w opcjach dodatku) na swoim routerze lub za pomocą odwrotnego proxy (np. Nginx Proxy Manager, Cloudflare Tunnels). 

Możesz też dodać stronę w swoim panelu jako `iframe` podając w nim link do Twojego HA na danym porcie. Pamiętaj by korzystając z iframe dodać odpowiednią konfigurację portów.
