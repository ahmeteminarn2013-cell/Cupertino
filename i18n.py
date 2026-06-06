#!/usr/bin/env python3
"""Cupertino — basit çoklu dil (i18n) modülü.

Sistem dilini (LANG / LC_MESSAGES) algılar, desteklenmeyen dilde İngilizce'ye düşer.
Kullanım:
    from i18n import t
    t("dock")  -> "Dock" / "Док" / ...
"""
import os

# Desteklenen diller: en, tr, es, de, fr, ru, pt, zh
STRINGS = {
    # ---- Control Panel (Ayar Merkezi) ----
    "app_title":    {"en": "Cupertino Settings", "tr": "Cupertino Ayar Merkezi", "es": "Ajustes de Cupertino",
                     "de": "Cupertino-Einstellungen", "fr": "Réglages Cupertino", "ru": "Настройки Cupertino",
                     "pt": "Configurações Cupertino", "zh": "Cupertino 设置"},
    "sec_top":      {"en": "Top Bar (Menu Bar)", "tr": "Üst Panel (Menü Çubuğu)", "es": "Barra superior (menú)",
                     "de": "Obere Leiste (Menüleiste)", "fr": "Barre supérieure (menu)", "ru": "Верхняя панель (меню)",
                     "pt": "Barra superior (menu)", "zh": "顶栏（菜单栏）"},
    "sec_dock":     {"en": "Dock", "tr": "Dock", "es": "Dock", "de": "Dock", "fr": "Dock", "ru": "Док",
                     "pt": "Dock", "zh": "程序坞"},
    "sec_blur":     {"en": "Frosted Glass (Blur)", "tr": "Buzlu Cam (Blur)", "es": "Cristal esmerilado (desenfoque)",
                     "de": "Milchglas (Unschärfe)", "fr": "Verre dépoli (flou)", "ru": "Матовое стекло (размытие)",
                     "pt": "Vidro fosco (desfoque)", "zh": "毛玻璃（模糊）"},
    "transparency": {"en": "Transparency", "tr": "Transparanlık", "es": "Transparencia", "de": "Transparenz",
                     "fr": "Transparence", "ru": "Прозрачность", "pt": "Transparência", "zh": "透明度"},
    "height":       {"en": "Height", "tr": "Yükseklik", "es": "Altura", "de": "Höhe", "fr": "Hauteur",
                     "ru": "Высота", "pt": "Altura", "zh": "高度"},
    "dock_bg":      {"en": "Background opacity", "tr": "Arka plan koyuluğu", "es": "Opacidad del fondo",
                     "de": "Hintergrund-Deckkraft", "fr": "Opacité du fond", "ru": "Непрозрачность фона",
                     "pt": "Opacidade do fundo", "zh": "背景不透明度"},
    "dock_size":    {"en": "Dock size", "tr": "Dock boyutu", "es": "Tamaño del dock", "de": "Dock-Größe",
                     "fr": "Taille du dock", "ru": "Размер дока", "pt": "Tamanho do dock", "zh": "程序坞大小"},
    "corner":       {"en": "Corner radius", "tr": "Köşe yuvarlaklığı", "es": "Radio de esquina",
                     "de": "Eckenradius", "fr": "Rayon des coins", "ru": "Скругление углов",
                     "pt": "Raio dos cantos", "zh": "圆角半径"},
    "preview":      {"en": "Window preview", "tr": "Pencere önizleme", "es": "Vista previa de ventana",
                     "de": "Fenstervorschau", "fr": "Aperçu de fenêtre", "ru": "Предпросмотр окна",
                     "pt": "Pré-visualização", "zh": "窗口预览"},
    "preview_size": {"en": "Preview size", "tr": "Önizleme boyutu", "es": "Tamaño de vista previa",
                     "de": "Vorschaugröße", "fr": "Taille de l'aperçu", "ru": "Размер предпросмотра",
                     "pt": "Tamanho da prévia", "zh": "预览大小"},
    "autohide":     {"en": "Auto-hide", "tr": "Otomatik gizle", "es": "Ocultar automáticamente",
                     "de": "Automatisch ausblenden", "fr": "Masquer automatiquement", "ru": "Автоскрытие",
                     "pt": "Ocultar automaticamente", "zh": "自动隐藏"},
    "blur_on":      {"en": "Blur enabled", "tr": "Blur açık", "es": "Desenfoque activado", "de": "Unschärfe an",
                     "fr": "Flou activé", "ru": "Размытие вкл", "pt": "Desfoque ativado", "zh": "启用模糊"},
    "blur_strength":{"en": "Blur strength", "tr": "Blur şiddeti", "es": "Intensidad del desenfoque",
                     "de": "Unschärfestärke", "fr": "Intensité du flou", "ru": "Сила размытия",
                     "pt": "Intensidade do desfoque", "zh": "模糊强度"},
    "ready":        {"en": "Ready", "tr": "Hazır", "es": "Listo", "de": "Bereit", "fr": "Prêt",
                     "ru": "Готово", "pt": "Pronto", "zh": "就绪"},
    # ---- Control Center (Kontrol Merkezi) ----
    "darkmode":     {"en": "Dark Mode", "tr": "Karanlık Mod", "es": "Modo oscuro", "de": "Dunkelmodus",
                     "fr": "Mode sombre", "ru": "Тёмный режим", "pt": "Modo escuro", "zh": "深色模式"},
    "on":           {"en": "On", "tr": "Açık", "es": "Activado", "de": "Ein", "fr": "Activé",
                     "ru": "Вкл", "pt": "Ligado", "zh": "开"},
    "off":          {"en": "Off", "tr": "Kapalı", "es": "Desactivado", "de": "Aus", "fr": "Désactivé",
                     "ru": "Выкл", "pt": "Desligado", "zh": "关"},
    "display":      {"en": "Display", "tr": "Ekran", "es": "Pantalla", "de": "Bildschirm", "fr": "Écran",
                     "ru": "Экран", "pt": "Tela", "zh": "显示"},
    "sound":        {"en": "Sound", "tr": "Ses", "es": "Sonido", "de": "Ton", "fr": "Son",
                     "ru": "Звук", "pt": "Som", "zh": "声音"},
    "not_playing":  {"en": "Not playing", "tr": "Çalmıyor", "es": "Nada en reproducción", "de": "Keine Wiedergabe",
                     "fr": "Aucune lecture", "ru": "Ничего не играет", "pt": "Nada tocando", "zh": "未播放"},
    # ---- Apple (Elma) Menüsü ----
    "am_about":     {"en": "About This Mac", "tr": "Bu Mac Hakkında", "es": "Acerca de este Mac",
                     "de": "Über diesen Mac", "fr": "À propos de ce Mac", "ru": "Об этом Mac",
                     "pt": "Sobre este Mac", "zh": "关于本机"},
    "am_sysset":    {"en": "System Settings…", "tr": "Sistem Ayarları…", "es": "Ajustes del Sistema…",
                     "de": "Systemeinstellungen…", "fr": "Réglages Système…", "ru": "Системные настройки…",
                     "pt": "Ajustes do Sistema…", "zh": "系统设置…"},
    "am_appstore":  {"en": "App Store…", "tr": "App Store…", "es": "App Store…", "de": "App Store…",
                     "fr": "App Store…", "ru": "App Store…", "pt": "App Store…", "zh": "App Store…"},
    "am_recent":    {"en": "Recent Items", "tr": "Son Kullanılanlar", "es": "Ítems recientes",
                     "de": "Benutzte Objekte", "fr": "Éléments récents", "ru": "Недавние объекты",
                     "pt": "Itens recentes", "zh": "最近使用的项目"},
    "am_no_recent": {"en": "No Recent Items", "tr": "Son Kullanılan Yok", "es": "Sin ítems recientes",
                     "de": "Keine benutzten Objekte", "fr": "Aucun élément récent", "ru": "Нет недавних",
                     "pt": "Nenhum item recente", "zh": "无最近项目"},
    "am_clear_menu":{"en": "Clear Menu", "tr": "Menüyü Temizle", "es": "Vaciar menú", "de": "Menü löschen",
                     "fr": "Vider le menu", "ru": "Очистить меню", "pt": "Limpar menu", "zh": "清除菜单"},
    "am_forcequit": {"en": "Force Quit…", "tr": "Zorla Çık…", "es": "Forzar salida…", "de": "Sofort beenden…",
                     "fr": "Forcer à quitter…", "ru": "Завершить принудительно…", "pt": "Forçar encerrar…",
                     "zh": "强制退出…"},
    "am_sleep":     {"en": "Sleep", "tr": "Uyku", "es": "Reposo", "de": "Ruhezustand", "fr": "Suspendre",
                     "ru": "Режим сна", "pt": "Repouso", "zh": "睡眠"},
    "am_restart":   {"en": "Restart…", "tr": "Yeniden Başlat…", "es": "Reiniciar…", "de": "Neustart…",
                     "fr": "Redémarrer…", "ru": "Перезагрузить…", "pt": "Reiniciar…", "zh": "重新启动…"},
    "am_shutdown":  {"en": "Shut Down…", "tr": "Kapat…", "es": "Apagar…", "de": "Ausschalten…",
                     "fr": "Éteindre…", "ru": "Выключить…", "pt": "Desligar…", "zh": "关机…"},
    "am_lock":      {"en": "Lock Screen", "tr": "Ekranı Kilitle", "es": "Bloquear pantalla",
                     "de": "Bildschirm sperren", "fr": "Verrouiller l'écran", "ru": "Заблокировать экран",
                     "pt": "Bloquear tela", "zh": "锁定屏幕"},
    "am_logout":    {"en": "Log Out…", "tr": "Oturumu Kapat…", "es": "Cerrar sesión…", "de": "Abmelden…",
                     "fr": "Déconnexion…", "ru": "Выйти…", "pt": "Encerrar sessão…", "zh": "退出登录…"},
    "am_chip":      {"en": "Processor", "tr": "İşlemci", "es": "Procesador", "de": "Prozessor",
                     "fr": "Processeur", "ru": "Процессор", "pt": "Processador", "zh": "处理器"},
    "am_memory":    {"en": "Memory", "tr": "Bellek", "es": "Memoria", "de": "Speicher", "fr": "Mémoire",
                     "ru": "Память", "pt": "Memória", "zh": "内存"},
    "am_startupdisk": {"en": "Startup disk", "tr": "Başlangıç diski", "es": "Disco de arranque",
                     "de": "Startvolume", "fr": "Disque de démarrage", "ru": "Загрузочный диск",
                     "pt": "Disco de arranque", "zh": "启动磁盘"},
    "am_kernel":    {"en": "Kernel", "tr": "Çekirdek", "es": "Núcleo", "de": "Kernel", "fr": "Noyau",
                     "ru": "Ядро", "pt": "Kernel", "zh": "内核"},
    "am_graphics":  {"en": "Graphics", "tr": "Grafik", "es": "Gráficos", "de": "Grafik", "fr": "Graphismes",
                     "ru": "Графика", "pt": "Gráficos", "zh": "显卡"},
    "am_more_info": {"en": "More Info…", "tr": "Daha Fazla Bilgi…", "es": "Más información…",
                     "de": "Weitere Infos…", "fr": "Plus d'infos…", "ru": "Подробнее…",
                     "pt": "Mais informações…", "zh": "更多信息…"},
    # ---- Elma menüsü onay uyarısı ----
    "am_cancel":    {"en": "Cancel", "tr": "İptal", "es": "Cancelar", "de": "Abbrechen",
                     "fr": "Annuler", "ru": "Отмена", "pt": "Cancelar", "zh": "取消"},
    "am_detail":    {"en": "Open apps will close.", "tr": "Açık uygulamalar kapanacak.",
                     "es": "Las apps abiertas se cerrarán.", "de": "Offene Apps werden geschlossen.",
                     "fr": "Les apps ouvertes se fermeront.", "ru": "Открытые приложения закроются.",
                     "pt": "Apps abertos serão fechados.", "zh": "打开的应用将关闭。"},
    "am_q_shutdown":{"en": "Are you sure you want to shut down your computer now?",
                     "tr": "Bilgisayarı şimdi kapatmak istediğinize emin misiniz?"},
    "am_q_restart": {"en": "Are you sure you want to restart your computer now?",
                     "tr": "Bilgisayarı şimdi yeniden başlatmak istediğinize emin misiniz?"},
    "am_q_logout":  {"en": "Are you sure you want to log out now?",
                     "tr": "Şimdi oturumu kapatmak istediğinize emin misiniz?"},
    "am_do_shutdown": {"en": "Shut Down", "tr": "Kapat", "es": "Apagar", "de": "Ausschalten",
                     "fr": "Éteindre", "ru": "Выключить", "pt": "Desligar", "zh": "关机"},
    "am_do_restart": {"en": "Restart", "tr": "Yeniden Başlat", "es": "Reiniciar", "de": "Neustart",
                     "fr": "Redémarrer", "ru": "Перезагрузить", "pt": "Reiniciar", "zh": "重启"},
    "am_do_logout": {"en": "Log Out", "tr": "Oturumu Kapat", "es": "Cerrar sesión", "de": "Abmelden",
                     "fr": "Déconnexion", "ru": "Выйти", "pt": "Encerrar sessão", "zh": "退出"},
    # ---- Spotlight ----
    "sp_placeholder": {"en": "Spotlight Search", "tr": "Spotlight Arama", "es": "Búsqueda Spotlight",
                     "de": "Spotlight-Suche", "fr": "Recherche Spotlight", "ru": "Поиск Spotlight",
                     "pt": "Busca Spotlight", "zh": "聚焦搜索"},
    "sp_calc":      {"en": "Calculator", "tr": "Hesap makinesi", "es": "Calculadora", "de": "Rechner",
                     "fr": "Calculatrice", "ru": "Калькулятор", "pt": "Calculadora", "zh": "计算器"},
    "sp_app":       {"en": "Application", "tr": "Uygulama", "es": "Aplicación", "de": "Anwendung",
                     "fr": "Application", "ru": "Приложение", "pt": "Aplicativo", "zh": "应用程序"},
    "sp_web":       {"en": "Search the web for “{}”", "tr": "Web'de “{}” ara",
                     "es": "Buscar “{}” en la web", "de": "Web nach „{}“ durchsuchen",
                     "fr": "Rechercher « {} » sur le web", "ru": "Искать «{}» в интернете",
                     "pt": "Pesquisar “{}” na web", "zh": "在网络上搜索“{}”"},
    "sp_web_sub":   {"en": "Web Search", "tr": "Web Araması", "es": "Búsqueda web", "de": "Websuche",
                     "fr": "Recherche web", "ru": "Веб-поиск", "pt": "Busca na web", "zh": "网络搜索"},
    # ---- Kilit ekranı / profil ----
    "sec_lock":     {"en": "Lock Screen", "tr": "Kilit Ekranı", "es": "Pantalla de bloqueo",
                     "de": "Sperrbildschirm", "fr": "Écran de verrouillage", "ru": "Экран блокировки",
                     "pt": "Tela de bloqueio", "zh": "锁屏"},
    "profile_name": {"en": "Name", "tr": "İsim", "es": "Nombre", "de": "Name", "fr": "Nom",
                     "ru": "Имя", "pt": "Nome", "zh": "名称"},
    "profile_photo":{"en": "Profile photo", "tr": "Profil fotoğrafı", "es": "Foto de perfil",
                     "de": "Profilbild", "fr": "Photo de profil", "ru": "Фото профиля",
                     "pt": "Foto de perfil", "zh": "头像"},
    "choose":       {"en": "Choose…", "tr": "Seç…", "es": "Elegir…", "de": "Wählen…", "fr": "Choisir…",
                     "ru": "Выбрать…", "pt": "Escolher…", "zh": "选择…"},
    "saved":        {"en": "Saved", "tr": "Kaydedildi", "es": "Guardado", "de": "Gespeichert",
                     "fr": "Enregistré", "ru": "Сохранено", "pt": "Salvo", "zh": "已保存"},
}


def _detect() -> str:
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(var, "")
        if val:
            code = val.split(":")[0].split(".")[0].split("_")[0].lower()
            if code in ("en", "tr", "es", "de", "fr", "ru", "pt", "zh"):
                return code
    return "en"


LANG = _detect()


def t(key: str) -> str:
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(LANG) or entry.get("en") or key
