# Wyróżnienia z rozmowy i rozwoju projektu "Photo Frame Drop"

Zapis postępów podczas tworzenia pełnoprawnego dodatku "Photo Frame Drop" do środowiska Home Assistant. Możesz tu zajrzeć w przyszłości, by w mgnieniu oka przypomnieć sobie, jak to zostało zbudowane.

---

## 1. Architektura dodatku
Po przeanalizowaniu struktury zorientowaliśmy się, że to nie jest tylko zbiór statycznych plików dla "App", a prawdziwy **Home Assistant Add-on**. 

Opiera się o konteneryzacją Dockera i zarządza nim Supervisor. Ostatecznie przeszliśmy z prostej, blokującej warianty pythonowej paczki na profesjonalny standard:
*   **Obraz Bazowy:** Oficjalny obraz `ghcr.io/home-assistant/base-python`
*   **Skrypty S6-Overlay:** Głównym plikiem ładującym serwer jest skrypt powłoki używający `bashio` (zlokalizowany w `rootfs/etc/services.d/photo_frame_drop/run`). Wczytuje on z walidacją plik konfiguracyjny (ustawiony z interfejsu HA) prosto do zmiennych środowiskowych.
*   **Backend Aiohttp:** Synchroniczny *FastAPI* rzucający błędem na dużych plikach został z sukcesem zastąpiony nowoczesnym, wysoce responsywnym i w 100% asynchronicznym środowiskiem `aiohttp`.

## 2. Ingress & Proxy
Udostępnienie interfejsu w panelu lewym (tzw. Sidebar) wymusiło na nas wprowadzenie specjalnej autoryzacji URL zwanej **Ingress**. 
Wszystkie pliki `.html` czy linkowanie stylów korzystają ze zmiennej `base_path`, opartej na headerze `X-Ingress-Path`, dzięki czemu nikt nie zostanie przypadkowo wylogowany i nie urwie mu sesji "Timeoutem 524" od Cloudflare'a. Dodatek działa również "natywnie" na samodzielnie wystawionym, dedykowanym porcie 8099.

## 3. Optymalizacje w Galerie i Plikach
*   **Miniaturki (Thumbnails):** Pliki 10MB po załadowaniu zarzynały przeglądarkę i Internet. Utworzyliśmy proces używający `ThreadPoolExecutor` i paczki graficznej `Pillow`. Teraz w tle obrabia ona każde zdjęcie zmniejszając do 256x256, odwraca je pion/poziom dzięki flagom z EXIFa i ukrywa w cache w folderze `.thumbs`.
*   **Unikanie nadpisywania:** Zabezpieczyliśmy system nadpisujący pliki. Jeśli wrzucisz 5 takich samych plików `image.png`, do ich nazwy doklei się elegancki wygenerowany identyfikator (UUID), żeby nic na ramce nie przepadło.

## 4. Wyśrubowane Bezpieczeństwo
Otrzymaliśmy zewnętrzny i bardzo restrykcyjny raport bezpieczeństwa, z którego wprowadziliśmy absolutnie wszystko:
*   **Brak podatności Path Traversal**: Uniemożliwiono poruszanie się po systemie znakami (np. `../../secret`) zmuszając do rygorystycznego blokowania w obrębie dysku przy usuwaniu z użyciem `is_relative_to`.
*   **Brute-Force & Rate Limits**: Wyciągnęliśmy prawdziwe IP użytkowników z użyciem `X-Forwarded-For`. Każdy dostaje maksymalnie 5 prób na zalogowanie w przeciągu 5 minut (In-memory storage).
*   **Klucze sesji**: Posiadają dodatkowy, mocny hash generowany z dynamicznego skryptu odpalonego raz przy starcie systemu. 
*   **CSRF & Secure Cookies**: Ciasteczka same flagują się jako bezpieczne przy ruchu HTTPS, a API wymaga nagłówków asynchronicznych i AJAXowych do przepchnięcia np. komendy wylogowywania (brak możliwości wklejenia pułapek "wyloguj/usuń" jako link z zewnątrz).

## 5. Integracja z Home Assistantem
Dodaliśmy mechanizm, w którym system HA informuje (poprzez dzwonek na aplikacji/interfejsie) o nowych plikach prosto od dodatku, za pomocą `SUPERVISOR_TOKEN` oraz uprawnienia API Core `homeassistant_api: true`. A jeżeli wrzucasz ich np. 50 w drag-and-drop - kod w Pythonie poczeka z `asyncio.sleep` aż skończysz i na koniec wyśle *tylko jedno* powiadomienie grupowe oszczędzając baterię w Twoim telefonie (Debouncing). Dodałem też dzisiaj, z Twojej inicjatywy, możliwość przesyłania powiadomień po błędnej próbie logowania!

## 6. Udogodnienia interfejsu (UI)
*   Dodano **Tłumaczenia interfejsu** zarówno od strony samego Home Assistanta (opcje konfiguracyjne dodatku - plik w `translations/pl.yaml`), jak i we front-endzie dla końcowego klienta - wbudowany przełącznik z flagą używający LocalStorage do przytrzymania Twoich ustawień (PL/EN).
*   Skonfigurowaliśmy edytowalny tekst prosto pod tytułem `Photo Frame Drop`, pozwalający zostawić instrukcję dla np. członków rodziny.

Gdybyś kiedykolwiek miał problem z powracaniem do kodu, ten plik uratuje naszą rozmowę!
